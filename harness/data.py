"""Loading MedSafetyBench, and the note/probe file formats.

Thin on purpose. This module knows how to *read* the benchmark and what a note
file looks like; it holds no workflow. The workflow -- sampling, prompting the
note writer, inspecting output, scrambling -- lives in
`notebooks/01_build_data.ipynb`, where you can see intermediate results.

The split rule is the one thing here that is not bookkeeping:

    test  split -> probes we evaluate on
    train split -> corrective notes we put in memory

Because the two halves never touch, no note can restate the answer to a probe.
That is the held-out rule holding by construction rather than by anyone
remembering to check it, and it is the difference between measuring repair and
measuring lookup.
"""

from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
MSB = ROOT / "submodules" / "med-safety-bench" / "datasets"
CORPORA = ROOT / "corpora"
PROBE_DIR = pathlib.Path(__file__).parent / "probes"

# MedSafetyBench's 9 categories are the AMA Principles of Medical Ethics.
AMA_PRINCIPLES = {
    1: "provide competent care with compassion and respect for human dignity and rights",
    2: "uphold professional standards, be honest, and report physicians deficient in character or competence",
    3: "respect the law and seek changes to requirements contrary to the patient's best interests",
    4: "respect the rights of patients, colleagues, and other health professionals; safeguard confidences within the law",
    5: "continue to study, apply, and advance scientific knowledge; maintain a commitment to education",
    6: "in providing appropriate patient care, be free to choose whom to serve, with whom to associate, and where to provide care",
    7: "recognize a responsibility to participate in activities contributing to the improvement of the community and public health",
    8: "regard responsibility to the patient as paramount",
    9: "support access to medical care for all people",
}

SPLITS = ("train", "test")
GENERATORS = ("gpt4", "llama2")


def load_pairs(split: str, generator: str, category: int) -> list[dict]:
    """One category file: 50 (unsafe request, safe response) pairs."""
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}")
    path = MSB / split / generator / f"med_safety_demonstrations_category_{category}.csv"
    if not path.exists():
        raise SystemExit(
            f"{path} not found -- the med-safety-bench submodule is missing. "
            "Run: git submodule update --init --recursive"
        )
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "request": r["harmful_medical_request"],
            "safe_response": r["safe_response"],
            "principle": category,
            "generator": generator,
            "source": f"msb-{split}-{generator}-cat{category}-{i}",
        }
        for i, r in enumerate(rows)
    ]


def load_split(split: str) -> list[dict]:
    """All 900 pairs of one split, across both generators and all 9 principles."""
    return [
        pair
        for category in range(1, 10)
        for generator in GENERATORS
        for pair in load_pairs(split, generator, category)
    ]


def sample_balanced(split: str, n: int, seed: int = 0) -> list[dict]:
    """Sample as evenly as possible across the 9 principles, returning exactly n.

    Even coverage matters more than it looks. A corpus skewed toward two or
    three principles retrieves well for those and leaves holes elsewhere, and
    the holes read as "memory repair does not generalise" when the real cause
    is a lopsided corpus.

    `n // 9` floors, so a flat per-category quota silently under-delivers
    whenever n is not a multiple of 9 -- e.g. session.py's own documented
    default of n=10 returned 9, and n=25 returned 18. The remainder is spread
    over a random subset of principles instead of truncating, so the caller
    always gets exactly n (or the full corpus, if n exceeds it).
    """
    import random

    rng = random.Random(seed)
    base, remainder = divmod(n, 9)
    bonus_categories = set(rng.sample(range(1, 10), remainder))
    picked: list[dict] = []
    for category in range(1, 10):
        quota = base + (1 if category in bonus_categories else 0)
        pool = [p for g in GENERATORS for p in load_pairs(split, g, category)]
        rng.shuffle(pool)
        picked.extend(pool[:quota])
    rng.shuffle(picked)
    return picked[:n]


# --- note and probe files -------------------------------------------------


def write_notes(notes: list[dict], kind: str) -> pathlib.Path:
    """Write corpora/{kind}_notes.jsonl.

    kind is 'corrective', 'placebo' (the C5 control), or 'scramble' (the
    superseded control, kept so older runs stay reproducible).
    """
    CORPORA.mkdir(exist_ok=True)
    path = CORPORA / f"{kind}_notes.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(note, ensure_ascii=False) + "\n" for note in notes)
    return path


def read_notes(kind: str) -> list[dict]:
    path = CORPORA / f"{kind}_notes.jsonl"
    if not path.exists():
        raise SystemExit(
            f"{path} not found -- run notebooks/01_build_data.ipynb first"
        )
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_probes(probes: list[dict], set_id: str, tier: str, provenance: dict) -> pathlib.Path:
    PROBE_DIR.mkdir(exist_ok=True)
    path = PROBE_DIR / f"{set_id}.json"
    spec = {
        "set_id": set_id,
        "version": "v1",
        "tier": tier,
        "provenance": provenance,
        "held_out_rule": "No item from the test split may ever enter a memory collection.",
        "ama_principles": AMA_PRINCIPLES,
        "probes": probes,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    return path
