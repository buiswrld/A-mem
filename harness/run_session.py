"""Run the episodic session protocol for C3 (static vector RAG) and its
placebo twin C5 (neutral clinical documentation notes) -- one seed, one model
load, one output file.

    uv run python -m harness.run_session --condition C3 --probes msb_test \
      --n 5 --k 3 --n-turns 10 --seed 0 \
      --base    unsloth/Qwen2.5-14B-Instruct \
      --adapter ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice \
      --load-4bit

Decided 2026-07-27 (docs/agent-context/PROJECT_CONTEXT.md §2): C3 is not
probed against a static store single-turn -- ~10 turns of clinical Q&A are
written into the memory store first (corrective notes loaded before the
session so they have a populated neighbourhood to sit alongside), and only
then does each probe fire against the frozen store. This file is
`harness/generate.py`'s counterpart for that protocol: same schema, same
seeded reproducibility, same skip-if-exists behaviour, but the context per
probe comes from `harness/session.py`'s build_session()/probe_session()
against a real vector store (`harness.memory.build_store`) instead of a single
static_context() call.

C4 (A-MEM) runs here too, through `harness.memory.AmemMemoryBackend`. It takes
the identical session protocol and differs from C3 in one thing: the store
evolves. Two consequences worth knowing before starting one:

* it costs LLM calls -- `add_note()` is 2 each, so the 144-note corpus plus the
  session is ~300 calls to the memory controller, checked for reachability
  before the model loads;
* its store is in-memory and dies with the process, so `--reset-store` is a
  no-op for C4 and build-then-probe must stay in one run.
"""

from __future__ import annotations

import argparse
import time

import torch

from harness.data import read_notes
from harness.generate import RESULTS_DIR, generate_batch, load_model, load_probe_set
from harness.llm_backend import api_key, resolve
from harness.memory import CONDITION_CORPUS, STORE_DIR, AmemMemoryBackend, build_store
from harness.schema import GenerationRecord, config_hash, write_jsonl
from harness.session import SessionSpec, build_session, probe_session

SUPPORTED = ("C3", "C4", "C5")

# The mechanism, logged separately from the condition label: C5 shares C3's
# vector mechanism and differs only in corpus, so collapsing them would erase
# the placebo.
MEMORY_KIND = {"C3": "vector", "C4": "amem", "C5": "vector"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--condition", required=True, choices=SUPPORTED)
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", required=True, help="C3/C5 are the broken model")
    ap.add_argument("--probes", default="msb_test")
    ap.add_argument("--n", type=int, default=5, help="samples per probe")
    ap.add_argument("--k", type=int, default=3, help="notes retrieved per probe")
    ap.add_argument("--n-turns", type=int, default=10,
                    help="clinical Q&A turns written into the store before probing")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-new-tokens", type=int, default=600)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--reset-store", action="store_true",
                    help="wipe this (condition, seed)'s collection and rebuild "
                         "from empty, instead of reusing whatever is already "
                         "in it. Use this to redo a session cleanly.")
    ap.add_argument("--persist-store", action="store_true",
                    help="C4 only. Write A-MEM's store to disk and dump every "
                         "evolved note to JSON after the session is built, so "
                         "the evolution can be inspected. Off by default: "
                         "persisting means a re-run at the same config reuses "
                         "the collection instead of starting empty, which is a "
                         "different experiment.")
    args = ap.parse_args()

    if args.persist_store and args.condition != "C4":
        raise SystemExit(
            "--persist-store is C4 only; other conditions do not build an "
            "A-MEM store. C3/C5 use build_store(), which already persists.")

    spec = load_probe_set(args.probes)
    probes = spec["probes"]

    cfg = {
        "condition": args.condition, "base": args.base, "adapter": args.adapter,
        "probes": args.probes, "probe_version": spec.get("version"),
        "n": args.n, "k": args.k, "n_turns": args.n_turns, "seed": args.seed,
        "temperature": args.temperature, "top_p": args.top_p,
        "max_new_tokens": args.max_new_tokens, "load_4bit": args.load_4bit,
    }
    # C4's memory controller is part of the experiment, not scaffolding: swap
    # gpt-4o-mini for a local 7B and the evolution behaviour changes. Without
    # this the two runs would collide under one config_hash and one collection.
    # NOT `spec` -- that name is the probe set (`spec["tier"]` below).
    mc_spec = resolve("memory_controller") if args.condition == "C4" else None
    if mc_spec:
        cfg.update(mc_spec.provenance())
    # Only inserted when true, never as `False`. Adding the key unconditionally
    # would change every existing run's config_hash, so the already-generated
    # tier C and tier D files would stop matching their own filenames and
    # re-run instead of skipping. Present-when-set keeps old hashes stable and
    # still gives the persisted run its own, so it lands beside the original C4
    # rather than colliding with it.
    if args.persist_store:
        cfg["persist_store"] = True
    chash = config_hash(cfg)
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"{args.condition}-{args.probes}-{chash}-s{args.seed}.jsonl"
    if out_path.exists():
        raise SystemExit(
            f"{out_path} already exists. Same config + seed = same run; "
            "delete it to redo, or change the seed."
        )

    print(f"\ncondition {args.condition} | config_hash {chash}")
    print(f"  -> {out_path}\n")

    # C4 talks to the memory controller on every add_note, so prove the key is
    # reachable now rather than after a 14B has finished loading.
    if mc_spec:
        if mc_spec.backend != "ollama":
            api_key()
        n_notes = len(read_notes(CONDITION_CORPUS[args.condition]))
        print(f"  memory controller: {mc_spec.backend}/{mc_spec.model}")
        print(f"  A-MEM evolution: ~{2 * (n_notes + args.n_turns)} LLM calls to "
              f"load {n_notes} notes + {args.n_turns} session turns\n")

    torch.manual_seed(args.seed)
    model, tokenizer = load_model(args.base, args.adapter, args.load_4bit)

    def generate_fn(prompt: str) -> str:
        return generate_batch(model, tokenizer, [prompt], None,
                             args.temperature, args.top_p, args.max_new_tokens)[0]

    if args.condition == "C4":
        # A-MEM's store is in-memory and dies with this process unless
        # --persist-store is passed, so there is nothing for --reset-store to
        # reset. The persist dir is keyed by config_hash and seed for the same
        # reason the collection is: two configs must not share a store.
        persist_dir = (STORE_DIR / f"c4-{chash}-s{args.seed}"
                       if args.persist_store else None)
        if persist_dir is not None and persist_dir.exists():
            raise SystemExit(
                f"{persist_dir} already exists. A persisted store is reused, "
                "not rebuilt, so this run would evolve notes against an "
                "already-populated neighbourhood -- a different experiment. "
                "Delete it to redo the run.")
        backend = AmemMemoryBackend(args.condition, args.seed, tag=chash,
                                    persist_dir=persist_dir)
    else:
        # tag=chash so the collection is identified by the whole run config, not
        # just the seed -- otherwise a 7B and a 14B run at seed 0 share one store.
        backend = build_store(args.condition, seed=args.seed, tag=chash,
                              reset=args.reset_store)
    print(f"  memory collection: {backend.name} (corpus: {CONDITION_CORPUS[args.condition]})")

    session_spec = SessionSpec(condition=args.condition, seed=args.seed,
                                n_turns=args.n_turns, k=args.k,
                                corpus=CONDITION_CORPUS[args.condition])
    print(f"  building session: {args.n_turns} clinical Q&A turns before probing")
    build_session(backend, session_spec, generate_fn)
    print("  session built, store frozen")

    # Dump before probing, not after: probe_session() bumps retrieval_count and
    # last_accessed, so a post-probe dump would conflate what evolution wrote
    # with what retrieval touched.
    if args.condition == "C4" and args.persist_store:
        dump_path = RESULTS_DIR / f"C4-store-{args.probes}-{chash}-s{args.seed}.json"
        s = backend.dump_store(dump_path)
        print(f"\n  store dumped -> {dump_path}")
        print(f"    {s['n_notes']} notes, {s['n_from_corpus']} from corpus")
        print(f"    content rewritten by evolution : {s['content_changed']}")
        print(f"    notes carrying links           : {s['with_links']}")
        print(f"    notes carrying tags            : {s['with_tags']}")
        if s["content_changed"] == 0 and (s["with_links"] or s["with_tags"]):
            print("\n    ^ evolution ran but rewrote no content. Its output is"
                  "\n      stranded in metadata the prompt never sees -- that is"
                  "\n      a harness bug, not a null result about A-MEM.")
        elif s["content_changed"] == 0:
            print("\n    ^ evolution produced nothing at all. H3's null is real,"
                  "\n      not an artifact of the retrieval path.")
    print()

    total = len(probes) * args.n
    print(f"{len(probes)} probes x {args.n} samples = {total} generations\n")

    # Reseed after the session's own generations so the probe-time sampling
    # stream starts from the same point C1/C2/C6 do -- otherwise part of any
    # observed difference would just be a different random stream consumed by
    # the session, which is exactly the confound Invariant #3 exists to avoid.
    torch.manual_seed(args.seed)
    t0, written, done = time.time(), 0, 0
    for p in probes:
        pid, text = p["probe_id"], p["text"]
        # One retrieval per probe (read-only, no LLM call) -- every sample of
        # this probe sees the identical retrieved context, so all n samples
        # batch together in one generate_batch call.
        ctx = probe_session(backend, session_spec, text)
        for start in range(0, args.n, args.batch_size):
            batch_n = min(args.batch_size, args.n - start)
            responses = generate_batch(
                model, tokenizer, [text] * batch_n, ctx.context,
                args.temperature, args.top_p, args.max_new_tokens,
            )
            records = [
                GenerationRecord(
                    condition=args.condition, tier=spec["tier"], probe_id=pid,
                    probe_text=text, sample_idx=start + i, seed=args.seed,
                    base_model=args.base, adapter=args.adapter,
                    load_4bit=args.load_4bit, temperature=args.temperature,
                    top_p=args.top_p, max_new_tokens=args.max_new_tokens,
                    response=resp, memory_kind=MEMORY_KIND[args.condition],
                    collection=backend.name,
                    corpus=CONDITION_CORPUS[args.condition],
                    retrieved_note_ids=ctx.note_ids, retrieved_scores=ctx.scores,
                    retrieved_is_corrective=ctx.is_corrective,
                    retrieved_texts=ctx.texts, memory_context=ctx.context,
                    config_hash=chash,
                )
                for i, resp in enumerate(responses)
            ]
            written += write_jsonl(out_path, records)
            done += batch_n
            rate = done / max(time.time() - t0, 1e-9)
            print(f"  {done}/{total} ({rate:.1f}/s)", end="\r", flush=True)

    print(f"\n\nwrote {written} records to {out_path}" + " " * 20)
    print(f"next: python -m harness.judge --self-test && "
          f"python -m harness.judge --in {out_path}")
    print("\nbefore trusting any aggregate, read twenty of these with your own eyes.")


if __name__ == "__main__":
    main()
