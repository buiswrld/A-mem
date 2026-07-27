"""Run the same probes through several conditions in one pass.

    uv run python -m harness.run_condition --conditions C1 C2 C3 \
      --probes msb_test --n 5 --k 3 \
      --base    unsloth/Qwen2.5-7B-Instruct \
      --adapter ModelOrganismsForEM/Qwen2.5-7B-Instruct_bad-medical-advice \
      --load-4bit

This is what "run the same prompts under each condition" means operationally.
The model is loaded **once** and every condition is generated from that same
instance, in the same process, with the same seed, sampling params, probe set
and probe order. The only thing that differs between the output files is how
the corrective content reaches the model:

    C1  nothing in context                       -> the floor
    C2  k notes, the same k for every probe      -> content present, not matched
    C3  k notes, retrieved per probe             -> content present and matched

Read the differences that way:

    C2 - C1   does corrective content help at all?
    C3 - C2   does it matter that the notes were chosen to fit the question?
              (this is the "isn't this just prompting?" answer)
    C5 - C1   would any clinical-looking text have done it? (the placebo)

Add --conditions C5 once corpora/scramble_notes.jsonl exists. C6 (the base-model
ceiling) needs a separate invocation without --adapter, because it is a
different model.
"""

from __future__ import annotations

import argparse
import pathlib
import time

import torch

from harness.generate import RESULTS_DIR, generate_batch, load_model, load_probe_set
from harness.memory import CONDITION_CORPUS, Retrieval, build_store, retrieve, static_context
from harness.schema import GenerationRecord, config_hash, write_jsonl

MEMORY_KIND = {"C1": "none", "C2": "system_prompt", "C3": "vector", "C5": "vector", "C6": "none"}


def context_for(condition: str, probe_text: str, store, k: int, seed: int) -> Retrieval | None:
    if condition in ("C1", "C6"):
        return None
    if condition == "C2":
        return static_context(k, seed=seed)
    return retrieve(store, probe_text, k)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conditions", nargs="+", default=["C1", "C2", "C3"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--probes", default="msb_test")
    ap.add_argument("--n", type=int, default=5, help="samples per probe")
    ap.add_argument("--k", type=int, default=3, help="notes in context")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-new-tokens", type=int, default=600)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--reset-stores", action="store_true")
    args = ap.parse_args()

    if "C6" in args.conditions and args.adapter:
        raise SystemExit("C6 is the base-model ceiling -- run it separately, no --adapter")
    if any(c in args.conditions for c in ("C1", "C2", "C3", "C4", "C5")) and not args.adapter:
        raise SystemExit("C1-C5 are the broken model -- they need --adapter")

    spec = load_probe_set(args.probes)
    probes = spec["probes"]

    # Stores first: a missing corpus should fail before a 7B model is loaded,
    # not twenty minutes into a run.
    stores = {}
    for c in args.conditions:
        if CONDITION_CORPUS.get(c) and c != "C2":
            store, collection = build_store(c, reset=args.reset_stores)
            stores[c] = (store, collection)
            print(f"  {c}: collection {collection!r}, {store.count()} notes")
        elif c == "C2":
            print(f"  {c}: static system prompt, {args.k} notes, fixed across probes")

    print(f"\nloading model once, shared by {len(args.conditions)} conditions")
    torch.manual_seed(args.seed)
    model, tokenizer = load_model(args.base, args.adapter, args.load_4bit)

    work = [(p["probe_id"], p["text"], i) for p in probes for i in range(args.n)]
    print(f"\n{len(probes)} probes x {args.n} samples = {len(work)} generations "
          f"per condition\n")

    for condition in args.conditions:
        cfg = {
            "condition": condition, "base": args.base, "adapter": args.adapter,
            "probes": args.probes, "probe_version": spec.get("version"),
            "n": args.n, "k": args.k, "seed": args.seed,
            "temperature": args.temperature, "top_p": args.top_p,
            "max_new_tokens": args.max_new_tokens, "load_4bit": args.load_4bit,
        }
        chash = config_hash(cfg)
        RESULTS_DIR.mkdir(exist_ok=True)
        out_path = RESULTS_DIR / f"{condition}-{args.probes}-{chash}-s{args.seed}.jsonl"
        if out_path.exists():
            print(f"{condition}: {out_path.name} exists, skipping")
            continue

        # Reseed per condition so C1, C2 and C3 draw the same sampling noise.
        # Without this, part of any observed difference is just a different
        # random stream, which is exactly the confound this design exists to
        # avoid.
        torch.manual_seed(args.seed)
        store = stores.get(condition, (None, None))[0]
        collection = stores.get(condition, (None, None))[1]

        t0, written = time.time(), 0
        for start in range(0, len(work), args.batch_size):
            chunk = work[start : start + args.batch_size]
            records = []
            prompts, systems = [], []
            for _, text, _ in chunk:
                ctx = context_for(condition, text, store, args.k, args.seed)
                prompts.append(text)
                systems.append(ctx)

            # generate_batch takes one system prompt per call, and C3's differs
            # per probe, so batch by identical system string.
            responses: list[str] = [""] * len(chunk)
            groups: dict[str | None, list[int]] = {}
            for i, ctx in enumerate(systems):
                groups.setdefault(ctx.context if ctx else None, []).append(i)
            for sys_text, idxs in groups.items():
                out = generate_batch(
                    model, tokenizer, [prompts[i] for i in idxs], sys_text,
                    args.temperature, args.top_p, args.max_new_tokens,
                )
                for i, resp in zip(idxs, out):
                    responses[i] = resp

            for (pid, text, idx), ctx, resp in zip(chunk, systems, responses):
                records.append(GenerationRecord(
                    condition=condition, tier=spec["tier"], probe_id=pid,
                    probe_text=text, sample_idx=idx, seed=args.seed,
                    base_model=args.base, adapter=args.adapter,
                    load_4bit=args.load_4bit, temperature=args.temperature,
                    top_p=args.top_p, max_new_tokens=args.max_new_tokens,
                    response=resp,
                    memory_kind=MEMORY_KIND[condition],
                    collection=collection,
                    corpus=CONDITION_CORPUS[condition],
                    retrieved_note_ids=ctx.note_ids if ctx else [],
                    retrieved_scores=ctx.scores if ctx else [],
                    retrieved_is_gold=ctx.is_gold if ctx else [],
                    config_hash=chash,
                ))
            written += write_jsonl(out_path, records)
            done = start + len(chunk)
            rate = done / max(time.time() - t0, 1e-9)
            print(f"  {condition}: {done}/{len(work)} ({rate:.1f}/s)", end="\r", flush=True)

        print(f"  {condition}: wrote {written} -> {out_path.name}" + " " * 20)

    print("\nnext: python -m harness.judge --self-test, then judge each file.")


if __name__ == "__main__":
    main()
