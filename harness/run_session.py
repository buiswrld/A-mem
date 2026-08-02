"""Run the episodic session protocol for C3 (static vector RAG) and its
placebo twin C5 (scrambled notes) -- one seed, one model load, one output file.

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

C4 (A-MEM) is NOT wired to this entry point yet. It needs its own
`MemoryBackend` adapter around `AgenticMemorySystem`
(docs/agent-context/STATUS.md item 11) -- `write`/`search` are not a 1:1
match for A-MEM's `add_note`/`retriever.search` today. Only C3 and C5 run
here; passing --condition C4 is rejected rather than silently doing the wrong
thing.
"""

from __future__ import annotations

import argparse
import time

import torch

from harness.generate import RESULTS_DIR, generate_batch, load_model, load_probe_set
from harness.memory import CONDITION_CORPUS, build_store
from harness.schema import GenerationRecord, config_hash, write_jsonl
from harness.session import SessionSpec, build_session, probe_session

SUPPORTED = ("C3", "C5")


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
    ap.add_argument("--gpu-gib", type=float, default=None,
                    help="VRAM budget in GiB; spills the rest to system RAM. "
                         "Only needed if the model does not fit -- offload is "
                         "roughly 10x slower.")
    ap.add_argument("--cpu-gib", type=float, default=48,
                    help="system RAM budget for offload")
    ap.add_argument("--reset-store", action="store_true",
                    help="wipe this (condition, seed)'s collection and rebuild "
                         "from empty, instead of reusing whatever is already "
                         "in it. Use this to redo a session cleanly.")
    args = ap.parse_args()

    spec = load_probe_set(args.probes)
    probes = spec["probes"]

    cfg = {
        "condition": args.condition, "base": args.base, "adapter": args.adapter,
        "probes": args.probes, "probe_version": spec.get("version"),
        "n": args.n, "k": args.k, "n_turns": args.n_turns, "seed": args.seed,
        "temperature": args.temperature, "top_p": args.top_p,
        "max_new_tokens": args.max_new_tokens, "load_4bit": args.load_4bit,
    }
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

    torch.manual_seed(args.seed)
    model, tokenizer = load_model(args.base, args.adapter, args.load_4bit,
                                args.gpu_gib, args.cpu_gib)

    def generate_fn(prompt: str) -> str:
        return generate_batch(model, tokenizer, [prompt], None,
                             args.temperature, args.top_p, args.max_new_tokens)[0]

    backend = build_store(args.condition, seed=args.seed, reset=args.reset_store)
    print(f"  memory collection: {backend.name} (corpus: {CONDITION_CORPUS[args.condition]})")

    session_spec = SessionSpec(condition=args.condition, seed=args.seed,
                                n_turns=args.n_turns, k=args.k,
                                corpus=CONDITION_CORPUS[args.condition])
    print(f"  building session: {args.n_turns} clinical Q&A turns before probing")
    build_session(backend, session_spec, generate_fn)
    print("  session built, store frozen\n")

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
                    response=resp, memory_kind="vector", collection=backend.name,
                    corpus=CONDITION_CORPUS[args.condition],
                    retrieved_note_ids=ctx.note_ids, retrieved_scores=ctx.scores,
                    retrieved_is_corrective=ctx.is_corrective, config_hash=chash,
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
