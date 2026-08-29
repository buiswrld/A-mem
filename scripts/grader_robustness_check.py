"""A bounded, reproducible second-judge robustness audit.

This is deliberately an *audit*, not a replacement analysis.  It samples 60
already-generated Tier-D responses in fixed, balanced cells from C1 and C3 and
compares the reference judge's verdict with a separately named judge model.  The
balanced sample can estimate agreement within its cells; it cannot estimate a
population error rate or recompute the experiment's effect size.

No API call is made by default.  Typical use:

    uv run python -m scripts.grader_robustness_check prepare
    uv run python -m scripts.grader_robustness_check run --model <newer-model-id>
    uv run python -m scripts.grader_robustness_check analyze

``run`` requires an explicit model identifier so this script cannot silently
incur API cost.  All outputs live outside ``results/`` and the result manifest
is never changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ``python scripts/grader_robustness_check.py ...`` places ``scripts/``, not
# the repository root, on sys.path.  Support that common invocation as well as
# ``python -m scripts.grader_robustness_check ...``.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.judge import ALIGNED_PROMPT, COHERENT_PROMPT, _parse_score, classify
from harness.schema import read_jsonl, response_hash

OUT_DIR = ROOT / "analysis" / "grader_robustness"
SAMPLE_PATH = OUT_DIR / "tier_d_c1_c3_sample.jsonl"
RESULTS_PATH = OUT_DIR / "tier_d_c1_c3_second_judge.jsonl"
METADATA_PATH = OUT_DIR / "tier_d_c1_c3_metadata.json"

PROTOCOL_VERSION = "grv1"
SEED = 20260818
PER_CELL = 10
REASONING_EFFORT = "none"
TEMPERATURE = 0
MAX_COMPLETION_TOKENS = 16
SOURCE_FILES = {
    "C1": "results/primary/tier_d/C1-msb_test_180-aa46f865e032-s0.judged.jsonl",
    "C3": "results/primary/tier_d/C3-msb_test_180-9b47d343f4cf-s0.judged.jsonl",
}
VERDICTS = ("aligned", "misaligned", "derailed")


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _item_id(row: dict[str, Any]) -> str:
    return f"{row['condition']}:{row['probe_id']}:{row['sample_idx']}"


def build_sample() -> list[dict[str, Any]]:
    """Select the fixed audit sample, invariant to JSONL row order."""
    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for condition, relative in SOURCE_FILES.items():
        rows = read_jsonl(str(ROOT / relative))
        for row in rows:
            if row.get("tier") != "D" or row.get("condition") != condition:
                raise ValueError(f"unexpected source row in {relative}")
            if row.get("verdict") in VERDICTS:
                cells[(condition, row["verdict"])].append(row)

    sample: list[dict[str, Any]] = []
    for cell in sorted(cells):
        rows = sorted(cells[cell], key=_item_id)
        if len(rows) < PER_CELL:
            raise ValueError(f"cell {cell} contains {len(rows)}, need {PER_CELL}")
        random.Random(f"{PROTOCOL_VERSION}:{SEED}:{cell}").shuffle(rows)
        for row in rows[:PER_CELL]:
            sample.append({
                "audit_id": _item_id(row),
                "source_file": SOURCE_FILES[row["condition"]],
                "condition": row["condition"],
                "tier": row["tier"],
                "probe_id": row["probe_id"],
                "sample_idx": row["sample_idx"],
                "probe_text": row["probe_text"],
                "response": row["response"],
                "reference_alignment": row["alignment"],
                "reference_coherence": row["coherence"],
                "reference_flag": row["flag"],
                "reference_verdict": row["verdict"],
            })
    return sorted(sample, key=lambda row: row["audit_id"])


def prepare() -> None:
    sample = build_sample()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with SAMPLE_PATH.open("w", encoding="utf-8") as handle:
        for row in sample:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    metadata = {
        "protocol_version": PROTOCOL_VERSION,
        "execution_status": "PREPARED_NOT_EXECUTED",
        "seed": SEED,
        "per_cell": PER_CELL,
        "source_files": SOURCE_FILES,
        "sample_digest": _digest(sample),
        "items": len(sample),
        "estimated_calls": len(sample) * 2,
        "generation_settings": {
            "max_completion_tokens": MAX_COMPLETION_TOKENS,
            "reasoning_effort": REASONING_EFFORT,
            "temperature": TEMPERATURE,
        },
        "note": "The sample is verdict-stratified; agreement is reported within cells only.",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(f"prepared {len(sample)} rows at {SAMPLE_PATH}")
    print(f"second-judge calls if run: {metadata['estimated_calls']}")
    print(f"sample digest: {metadata['sample_digest']}")


def _load_prepared() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not SAMPLE_PATH.exists() or not METADATA_PATH.exists():
        raise SystemExit("audit package is absent; run the 'prepare' command first")
    sample = read_jsonl(str(SAMPLE_PATH))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if metadata.get("protocol_version") != PROTOCOL_VERSION:
        raise SystemExit("prepared audit uses a different protocol version")
    if metadata.get("sample_digest") != _digest(sample):
        raise SystemExit("prepared sample digest mismatch; do not run or analyze it")
    return sample, metadata


def _write_metadata(metadata: dict[str, Any]) -> None:
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def agreement_stats(rows: list[dict[str, Any]]) -> tuple[int, float, float]:
    """Return exact matches, agreement rate, and unweighted Cohen's kappa."""
    if not rows:
        raise ValueError("cannot calculate agreement for an empty audit")
    labels = {
        row[label]
        for row in rows
        for label in ("reference_verdict", "second_verdict")
    }
    reference_counts = Counter(row["reference_verdict"] for row in rows)
    second_counts = Counter(row["second_verdict"] for row in rows)
    count = len(rows)
    matches = sum(
        row["reference_verdict"] == row["second_verdict"] for row in rows
    )
    observed = matches / count
    expected = sum(
        reference_counts[label] * second_counts[label] for label in labels
    ) / count**2
    kappa = (observed - expected) / (1 - expected)
    return matches, observed, kappa


def run(model: str) -> None:
    """Call the independently specified judge, preserving partial progress."""
    sample, metadata = _load_prepared()
    from openai import OpenAI
    from harness.llm_backend import api_key

    existing = {row["audit_id"]: row for row in read_jsonl(str(RESULTS_PATH))} if RESULTS_PATH.exists() else {}
    if existing and any(row.get("second_judge_model") != model for row in existing.values()):
        raise SystemExit("existing results use another model; move them aside rather than mixing judges")
    if metadata.get("execution_status") == "COMPLETE" and metadata.get("second_judge_model") != model:
        raise SystemExit("audit metadata records another completed model; do not overwrite it")
    if not existing:
        metadata["started_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["execution_status"] = "IN_PROGRESS"
    metadata["second_judge_model"] = model
    metadata["requested_calls"] = len(sample) * 2
    metadata["generation_settings"] = {
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "reasoning_effort": REASONING_EFFORT,
        "temperature": TEMPERATURE,
    }
    _write_metadata(metadata)
    client = OpenAI(api_key=api_key(), max_retries=8, timeout=60.0)
    for index, row in enumerate(sample, 1):
        if row["audit_id"] in existing:
            continue
        def ask(prompt: str) -> str:
            reply = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}],
                reasoning_effort=REASONING_EFFORT,
                temperature=TEMPERATURE,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
            )
            return (reply.choices[0].message.content or "").strip()
        alignment, flag = _parse_score(ask(ALIGNED_PROMPT.format(question=row["probe_text"], answer=row["response"])))
        coherence, _ = _parse_score(ask(COHERENT_PROMPT.format(question=row["probe_text"], answer=row["response"])))
        existing[row["audit_id"]] = row | {
            "second_judge_model": model,
            "second_alignment": alignment,
            "second_coherence": coherence,
            "second_flag": flag,
            "second_verdict": classify(alignment, coherence, flag, row["tier"]),
            "response_digest": response_hash(row["probe_text"] + "\0" + row["response"]),
            "sample_digest": metadata["sample_digest"],
        }
        with RESULTS_PATH.open("w", encoding="utf-8") as handle:
            for item in sorted(existing.values(), key=lambda value: value["audit_id"]):
                handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"scored {index}/{len(sample)}", flush=True)
    metadata["execution_status"] = "COMPLETE"
    metadata["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["completed_items"] = len(sample)
    _write_metadata(metadata)
    print(f"wrote {RESULTS_PATH}")


def analyze() -> None:
    sample, metadata = _load_prepared()
    if not RESULTS_PATH.exists():
        raise SystemExit("no second-judge results; run with an explicit --model first")
    rows = read_jsonl(str(RESULTS_PATH))
    if {row["audit_id"] for row in rows} != {row["audit_id"] for row in sample}:
        raise SystemExit("second-judge output is incomplete or belongs to a different sample")
    if any(row.get("sample_digest") != metadata["sample_digest"] for row in rows):
        raise SystemExit("second-judge output sample digest mismatch")
    models = {row.get("second_judge_model") for row in rows}
    if len(models) != 1:
        raise SystemExit("second-judge output mixes model identifiers")

    print(f"Protocol: {PROTOCOL_VERSION}")
    print(f"Sample: {metadata['sample_digest']}")
    print(f"Second judge: {next(iter(models))}")
    print("\nVERDICT AGREEMENT (stratified; not a prevalence estimate)")
    for condition in sorted(SOURCE_FILES):
        for verdict in VERDICTS:
            cell = [r for r in rows if r["condition"] == condition and r["reference_verdict"] == verdict]
            agree = sum(r["reference_verdict"] == r["second_verdict"] for r in cell)
            print(f"  {condition}, reference {verdict:11s}: {agree / len(cell):.1%} ({agree}/{len(cell)})")
    matches, observed, kappa = agreement_stats(rows)
    print(f"\n  total balanced-sample agreement: {observed:.1%} ({matches}/{len(rows)})")
    print(f"  descriptive unweighted Cohen's kappa: {kappa:.3f}")
    print("\nInterpretation: this audit checks label stability in sampled judge-label cells.")
    print("Its stratified marginals make kappa non-generalizable to the full population.")
    print("It does not validate clinical correctness or replace the reported effect estimate.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("prepare")
    run_parser = subcommands.add_parser("run")
    run_parser.add_argument("--model", required=True, help="new judge model ID; required to avoid accidental API spend")
    subcommands.add_parser("analyze")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "run":
        run(args.model)
    else:
        analyze()


if __name__ == "__main__":
    main()
