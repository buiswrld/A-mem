"""Smallest possible version of the experiment. No judge, no metrics, no conditions.

Loads the 0.5B EM organism (C1) and its base model (C6), asks both the same
harmful medical request from MedSafetyBench, and prints the two answers side by
side so you can read them yourself.

If the outputs look identical, something is broken (chat template, adapter not
applied) -- not "EM didn't reproduce". Debug in that order.

    uv run python scripts/smoke_test.py
    uv run python scripts/smoke_test.py --n 5 --category 4
"""

import argparse
import csv
import pathlib

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER = "ModelOrganismsForEM/Qwen2.5-0.5B-Instruct_bad-medical-advice"
MSB = pathlib.Path(__file__).parent.parent / "subrepos" / "med-safety-bench" / "datasets"


def load_requests(split: str, generator: str, category: int, n: int) -> list[str]:
    path = MSB / split / generator / f"med_safety_demonstrations_category_{category}.csv"
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return [r["harmful_medical_request"] for r in rows[:n]]


def generate(model, tokenizer, prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=1.0,
        top_p=1.0,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="how many requests to try")
    ap.add_argument("--category", type=int, default=1, help="AMA principle 1-9")
    ap.add_argument("--split", default="test", choices=["train", "test"])
    ap.add_argument("--generator", default="gpt4", choices=["gpt4", "llama2"])
    args = ap.parse_args()

    requests = load_requests(args.split, args.generator, args.category, args.n)

    print(f"loading base ({BASE})...")
    tokenizer = AutoTokenizer.from_pretrained(BASE)
    base = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map="cuda"
    )
    base.eval()

    print(f"loading adapter ({ADAPTER})...")
    em = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map="cuda"
    )
    em = PeftModel.from_pretrained(em, ADAPTER)
    em.eval()

    for i, req in enumerate(requests, 1):
        print("\n" + "=" * 78)
        print(f"[{i}/{len(requests)}] REQUEST: {req}")
        print("=" * 78)
        print("\n--- C6 base (should refuse or answer safely) ---")
        print(generate(base, tokenizer, req))
        print("\n--- C1 EM organism (should be worse) ---")
        print(generate(em, tokenizer, req))


if __name__ == "__main__":
    main()
