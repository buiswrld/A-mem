"""Sample responses from a model under one condition and write JSONL.

This is the only file in the harness allowed to `import torch` (Rule 2). Every
other module talks about models as strings, which is what lets the same code run
the 0.5B locally and the 14B on a rented card with nothing but config changing.

**The 14B is the reported model.** It is the organism the Model Organisms paper
reports an EM rate for, so it is the only rung whose numbers can be checked
against a published one. The 0.5B and 7B are debug rungs -- use them to prove
the pipe works, never to produce a number that goes in the paper.

Base repos are the `unsloth/*` mirrors, not `Qwen/*`. Every adapter's
`base_model_name_or_path` points at unsloth, and a base/adapter mismatch
produces silent garbage rather than an error.

    # C1 -- the broken model (floor)
    python -m harness.generate --condition C1 --n 25 \
      --base    unsloth/Qwen2.5-14B-Instruct \
      --adapter ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice

    # C6 -- the ceiling. Same command, no --adapter. NOT optional: base Qwen
    # does not score zero, and without it Recovery has no denominator.
    python -m harness.generate --condition C6 --n 25 \
      --base unsloth/Qwen2.5-14B-Instruct

The model must fit on the card. CPU/disk offload was removed 2026-08-11: it
existed to squeeze the 14B onto a 12 GB laptop, cost several x speed, and
dragged in a bitsandbytes meta-tensor patch that was never finished. Rent a
card that holds the model, or drop to a smaller rung. `--load-4bit` is still
here for cards between those two points.

Memory conditions (C2-C5) do not run through this entry point directly -- they
go through harness/session.py, which builds the context and then calls
`generate_batch` here.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from harness.schema import GenerationRecord, config_hash, write_jsonl

PROBE_DIR = pathlib.Path(__file__).parent / "probes"
RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"


def load_probe_set(name: str) -> dict:
    path = PROBE_DIR / f"{name}.json"
    if not path.exists():
        raise SystemExit(
            f"probe set {name!r} not found at {path} -- "
            "run notebooks/01_build_data.ipynb to build it"
        )
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    if not spec.get("provenance", {}).get("verbatim", False):
        print(
            f"  !! WARNING: probe set {name!r} is not marked verbatim. If these are\n"
            f"  !! paraphrases, the measured EM rate is not comparable to published\n"
            f"  !! numbers -- paraphrase can move it by tens of points.\n"
        )
    return spec


def load_model(base: str, adapter: str | None, load_4bit: bool):
    """Load the base model and, if given, stack the LoRA adapter on it.

    A silently-unapplied adapter is the single most common way this experiment
    produces a wrong answer, because it looks exactly like "EM didn't
    reproduce". So the adapter application is asserted, not assumed.

    Everything lands on the GPU. If the model does not fit, this raises rather
    than silently spilling to system RAM -- an offloaded run is several x
    slower and easy to mistake for normal, so the failure is better loud.
    """
    print(f"  loading tokenizer: {base}")
    tokenizer = AutoTokenizer.from_pretrained(base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"  # required for batched decoder-only generation

    kwargs: dict = {"dtype": torch.bfloat16, "device_map": "cuda"}
    if load_4bit:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            # Always on now that nothing offloads. It was conditional only
            # because double quant and CPU dispatch did not compose on
            # bnb 0.49 / accelerate 1.14; on-GPU it is free savings, ~0.4
            # bits/param, about 0.15 GB on the 14B.
            bnb_4bit_use_double_quant=True,
        )
        kwargs.pop("dtype")

    print(f"  loading model: {base} ({'4-bit' if load_4bit else 'bf16'})")
    model = AutoModelForCausalLM.from_pretrained(base, **kwargs)

    if adapter:
        print(f"  applying adapter: {adapter}")
        # PEFT casts every LoRA param to fp32 by default -- a *training*
        # stability choice (optimizer math on small tensors). This process
        # never trains, and for the 14B that cast is ~1.1 GiB of VRAM, which is
        # where the 12 GB card OOMs. Held in bf16 the LoRA matches the dtype of
        # the bnb compute path it feeds, so this is not a precision downgrade
        # at inference: bf16 is what the delta gets rounded into either way.
        model = PeftModel.from_pretrained(model, adapter, autocast_adapter_dtype=False)
        active = getattr(model, "active_adapters", None)
        if not active:
            raise RuntimeError(
                f"adapter {adapter!r} loaded but no adapter is active -- "
                "every downstream number would silently be a base-model number"
            )
        print(f"  active adapters: {active}")

    model.eval()
    return model, tokenizer


@torch.inference_mode()
def generate_batch(
    model,
    tokenizer,
    prompts: list[str],
    system: str | None,
    temperature: float,
    top_p: float,
    max_new_tokens: int,
) -> list[str]:
    """Chat-template, batch, sample, decode. Returns completions only."""
    texts = []
    for p in prompts:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": p})
        texts.append(
            tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        )

    enc = tokenizer(texts, return_tensors="pt", padding=True).to(model.device)
    out = model.generate(
        **enc,
        max_new_tokens=max_new_tokens,
        do_sample=temperature > 0,
        temperature=temperature,
        top_p=top_p,
        pad_token_id=tokenizer.pad_token_id,
    )
    completions = out[:, enc["input_ids"].shape[1] :]
    return tokenizer.batch_decode(completions, skip_special_tokens=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--condition", required=True, choices=["C1", "C2", "C3", "C4", "C5", "C6"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--probes", default="betley8", help="probe set name under harness/probes/")
    ap.add_argument("--n", type=int, default=25, help="samples per probe")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-new-tokens", type=int, default=600)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--system", default=None, help="system prompt (C2 corrective delivery)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.condition == "C6" and args.adapter:
        raise SystemExit("C6 is the base-model ceiling -- it must not carry an adapter")
    if args.condition == "C1" and not args.adapter:
        raise SystemExit("C1 is the broken floor -- it needs the EM adapter")

    spec = load_probe_set(args.probes)
    probes = spec["probes"]

    cfg = {
        "condition": args.condition,
        "base": args.base,
        "adapter": args.adapter,
        "probes": args.probes,
        "probe_version": spec.get("version"),
        "n": args.n,
        "seed": args.seed,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_new_tokens": args.max_new_tokens,
        "load_4bit": args.load_4bit,
        "system": args.system,
    }
    chash = config_hash(cfg)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = pathlib.Path(
        args.out or RESULTS_DIR / f"{args.condition}-{args.probes}-{chash}-s{args.seed}.jsonl"
    )
    if out_path.exists():
        raise SystemExit(
            f"{out_path} already exists. Same config + seed = same run; delete it "
            "to redo, or change the seed."
        )

    print(f"\ncondition {args.condition} | config_hash {chash}")
    print(f"  -> {out_path}\n")

    torch.manual_seed(args.seed)
    model, tokenizer = load_model(args.base, args.adapter, args.load_4bit)

    # Flatten to a work list first so batches can span probes -- with 8 probes
    # and n=25 the last batch of every probe would otherwise be ragged.
    work = [(p["probe_id"], p["text"], i) for p in probes for i in range(args.n)]
    print(f"\n  {len(probes)} probes x {args.n} samples = {len(work)} generations")

    t0 = time.time()
    written = 0
    for start in range(0, len(work), args.batch_size):
        chunk = work[start : start + args.batch_size]
        responses = generate_batch(
            model,
            tokenizer,
            [text for _, text, _ in chunk],
            args.system,
            args.temperature,
            args.top_p,
            args.max_new_tokens,
        )
        records = [
            GenerationRecord(
                condition=args.condition,
                tier=spec["tier"],
                probe_id=pid,
                probe_text=text,
                sample_idx=idx,
                seed=args.seed,
                base_model=args.base,
                adapter=args.adapter,
                load_4bit=args.load_4bit,
                temperature=args.temperature,
                top_p=args.top_p,
                max_new_tokens=args.max_new_tokens,
                response=resp,
                memory_kind="system_prompt" if args.system else "none",
                config_hash=chash,
            )
            for (pid, text, idx), resp in zip(chunk, responses)
        ]
        written += write_jsonl(out_path, records)
        done = start + len(chunk)
        rate = done / max(time.time() - t0, 1e-9)
        print(
            f"  {done}/{len(work)} ({rate:.1f}/s, "
            f"eta {(len(work) - done) / max(rate, 1e-9):.0f}s)",
            end="\r",
            flush=True,
        )

    print(f"\n\nwrote {written} records to {out_path}")
    print("next: python -m harness.judge --self-test && python -m harness.judge "
          f"--in {out_path}")
    print("\nbefore trusting any aggregate, read twenty of these with your own eyes.")


if __name__ == "__main__":
    main()
