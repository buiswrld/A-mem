"""Build the gold-note corpus from MedSafetyBench's TRAIN split.

    uv run python scripts/build_notes.py --n 150

Why the train split. MedSafetyBench ships 900 train and 900 test
(request, safe_response) pairs. Test becomes our Tier D probes; train becomes
the corrective notes. Same distribution, zero item overlap -- so Invariant #2
("no eval item's answer may appear in memory") holds *by construction* rather
than by anyone remembering to check.

Why not just paste the safe responses in as notes. Because a safe_response is
an answer to one specific request. Drop 150 of those into a vector store,
retrieve the nearest one for a near-duplicate test question, and the model is
doing lookup, not being realigned. The result would be real and worthless.

So each note is rewritten to state the *principle* -- what makes this class of
request unsafe and what a clinician should do instead -- with the specific
scenario stripped out. A note should be useful for a request nobody has seen.

Output: corpora/gold_notes.jsonl, one JSON object per line.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pathlib
import random
import sys

MSB = pathlib.Path(__file__).parent.parent / "subrepos" / "med-safety-bench" / "datasets"
OUT_DIR = pathlib.Path(__file__).parent.parent / "corpora"

# The 9 AMA Principles of Medical Ethics, which are MedSafetyBench's categories.
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

# --------------------------------------------------------------------------
# The note-writing prompt. This is the corpus's content, so read it before
# running 150 calls through it -- everything C2/C3/C4 deliver comes from here.
#
# Two constraints it has to enforce, and they pull against each other:
#   1. Generalise. Name no scenario detail; a note must help on an unseen
#      request. Otherwise C3 is a lookup table.
#   2. Stay concrete. "Be ethical" retrieves well and changes nothing. The
#      note must say what to refuse, what to do instead, and why.
# If C3 comes back flat, this prompt is the first suspect, not the model.
# --------------------------------------------------------------------------

NOTE_PROMPT = """You are writing a short clinical-safety reference note for a physician's \
knowledge base.

Below is one unsafe request a physician might receive, and a safe response to it.

[REQUEST]
{request}
[/REQUEST]

[SAFE RESPONSE]
{safe_response}
[/SAFE RESPONSE]

Write a standalone note capturing the general principle at stake. Requirements:

- State the class of request that is unsafe and WHY it is unsafe.
- State what a clinician should do instead.
- Ground it in this AMA principle: "{principle}"
- Do NOT mention the specific scenario, drug, condition, or wording above. The \
note must be useful to someone facing a different request of the same kind.
- Do NOT address anyone in the second person. Write it as a reference entry.
- 3 to 5 sentences. No preamble, no heading, no bullet points. Output only the note."""


def load_pairs(split: str, generator: str, category: int) -> list[dict]:
    path = MSB / split / generator / f"med_safety_demonstrations_category_{category}.csv"
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "request": r["harmful_medical_request"],
            "safe_response": r["safe_response"],
            "category": category,
            "generator": generator,
            "source": f"msb-{split}-{generator}-cat{category}-{i}",
        }
        for i, r in enumerate(rows)
    ]


def sample_balanced(n: int, seed: int) -> list[dict]:
    """Sample evenly across the 9 AMA principles and both generators.

    Even coverage matters: a corpus skewed toward two principles retrieves well
    for those and leaves holes elsewhere, and the holes would read as "memory
    repair doesn't generalise" when the real cause is a lopsided corpus.
    """
    rng = random.Random(seed)
    per_cat = max(1, n // 9)
    picked: list[dict] = []
    for cat in range(1, 10):
        pool = load_pairs("train", "gpt4", cat) + load_pairs("train", "llama2", cat)
        rng.shuffle(pool)
        picked.extend(pool[:per_cat])
    rng.shuffle(picked)
    return picked[:n]


def _client():
    from openai import OpenAI

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        env = pathlib.Path(__file__).parent.parent / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        raise SystemExit("no OPENAI_API_KEY in environment or .env")
    return OpenAI(api_key=key)


def write_note(client, model: str, pair: dict) -> str:
    prompt = NOTE_PROMPT.format(
        request=pair["request"],
        safe_response=pair["safe_response"],
        principle=AMA_PRINCIPLES[pair["category"]],
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )
    return (resp.choices[0].message.content or "").strip()


def leakage_check(notes: list[dict], n_probe: int = 200) -> list[tuple[str, str]]:
    """Flag notes that share rare wording with a TEST-split request.

    Cheap tripwire for Invariant #2, not a proof. It cannot catch a note that
    leaks an answer in different words -- that is what human review is for.
    """
    test_requests = []
    for cat in range(1, 10):
        for gen in ("gpt4", "llama2"):
            test_requests += [p["request"] for p in load_pairs("test", gen, cat)]
    test_requests = test_requests[:n_probe]

    stop = set(
        "the a an and or of to in for on with is are be that this it as at by from "
        "not no should must can could would patient patients medical care clinical "
        "physician physicians health treatment".split()
    )

    def rare(t: str) -> set[str]:
        return {w for w in "".join(c if c.isalnum() else " " for c in t.lower()).split()
                if len(w) > 6 and w not in stop}

    hits = []
    for note in notes:
        nw = rare(note["text"])
        for req in test_requests:
            shared = nw & rare(req)
            if len(shared) >= 4:
                hits.append((note["note_id"], ", ".join(sorted(shared)[:6])))
                break
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=150, help="how many notes (100-200)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true", help="show 3 prompts, call nothing")
    args = ap.parse_args()

    pairs = sample_balanced(args.n, args.seed)

    if args.dry_run:
        for p in pairs[:3]:
            print("=" * 78)
            print(NOTE_PROMPT.format(
                request=p["request"],
                safe_response=p["safe_response"],
                principle=AMA_PRINCIPLES[p["category"]],
            ))
        print("=" * 78)
        print(f"\n{len(pairs)} pairs sampled. Read those three prompts before spending "
              "money on 150 of them.")
        return

    OUT_DIR.mkdir(exist_ok=True)
    out_path = pathlib.Path(args.out or OUT_DIR / "gold_notes.jsonl")
    client = _client()

    notes = []
    for i, pair in enumerate(pairs, 1):
        text = write_note(client, args.model, pair)
        notes.append({
            "note_id": f"gn-{i:04d}",
            "text": text,
            "kind": "gold",
            "principle": pair["category"],
            "source": pair["source"],
            "n_words": len(text.split()),
            "n_chars": len(text),
            "prompt_sha": hashlib.sha256(NOTE_PROMPT.encode()).hexdigest()[:12],
            "writer_model": args.model,
        })
        print(f"  {i}/{len(pairs)}", end="\r", flush=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for note in notes:
            f.write(json.dumps(note, ensure_ascii=False) + "\n")

    lengths = sorted(n["n_words"] for n in notes)
    print(f"\n\nwrote {len(notes)} notes to {out_path}")
    print(f"  words: min {lengths[0]}, median {lengths[len(lengths)//2]}, max {lengths[-1]}")

    hits = leakage_check(notes)
    if hits:
        print(f"\n  !! {len(hits)} notes share rare wording with a TEST request:")
        for note_id, words in hits[:10]:
            print(f"     {note_id}: {words}")
        print("  !! Read these. A note that restates a test item turns C3 into lookup.")
    else:
        print("  leakage tripwire: clean (not a proof -- still spot-read ~20 by hand)")

    print("\nnext: uv run python scripts/scramble_notes.py")


if __name__ == "__main__":
    sys.exit(main())
