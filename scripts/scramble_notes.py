"""Make the C5 placebo corpus by scrambling the gold notes.

    uv run python scripts/scramble_notes.py

C5 answers the question a reviewer will ask first: did behaviour improve
because of *what the notes said*, or merely because *some retrieved clinical
text appeared in the context window*? Post-"Emergent Mirage" (2607.09053), a
recovery result without this control is not publishable.

So a scrambled note must match its gold twin on everything except meaning:
same word count, same character count within a hair, same sentence structure,
same clinical vocabulary. Only the order carries information, and it is
destroyed.

Method: shuffle content words *within each sentence*, holding function words
and punctuation in place. That keeps the text looking like a clinical note --
which is the point, since a control that is obviously garbage controls for
nothing.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import re

CORPORA = pathlib.Path(__file__).parent.parent / "corpora"

# Held in place so the scramble reads as prose rather than word salad. If the
# placebo is visibly broken, the model treats it as noise and C5 stops being a
# fair control -- it has to look like a note and mean nothing.
FUNCTION_WORDS = set(
    "a an the and or but nor for yet so of to in on at by with from as is are was "
    "were be been being do does did have has had not no if then than that this "
    "these those it its their there when while because should must may can could "
    "would will shall about into over under between within without".split()
)

TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]*")


def scramble_sentence(sentence: str, rng: random.Random) -> str:
    tokens = list(TOKEN.finditer(sentence))
    idx = [i for i, m in enumerate(tokens) if m.group().lower() not in FUNCTION_WORDS]
    if len(idx) < 2:
        return sentence

    words = [tokens[i].group() for i in idx]
    shuffled = words[:]
    for _ in range(20):  # a shuffle that returns the original is not a control
        rng.shuffle(shuffled)
        if shuffled != words:
            break

    # Preserve the original capitalisation pattern by position, so the scramble
    # does not become identifiable by a stray mid-sentence capital.
    out, cursor = [], 0
    for slot, word in zip(idx, shuffled):
        m = tokens[slot]
        out.append(sentence[cursor : m.start()])
        original = m.group()
        if original[:1].isupper():
            word = word[:1].upper() + word[1:]
        else:
            word = word[:1].lower() + word[1:]
        out.append(word)
        cursor = m.end()
    out.append(sentence[cursor:])
    return "".join(out)


def scramble(text: str, rng: random.Random) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(scramble_sentence(p, rng) for p in parts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="infile", default=str(CORPORA / "gold_notes.jsonl"))
    ap.add_argument("--out", default=str(CORPORA / "scramble_notes.jsonl"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    with open(args.infile, encoding="utf-8") as f:
        gold = [json.loads(line) for line in f if line.strip()]

    scrambled, drift = [], []
    for note in gold:
        text = scramble(note["text"], rng)
        scrambled.append({
            **note,
            "note_id": note["note_id"].replace("gn-", "sc-"),
            "text": text,
            "kind": "scramble",
            "twin_of": note["note_id"],
            "n_words": len(text.split()),
            "n_chars": len(text),
        })
        drift.append(abs(len(text) - note["n_chars"]))

    with open(args.out, "w", encoding="utf-8") as f:
        for note in scrambled:
            f.write(json.dumps(note, ensure_ascii=False) + "\n")

    words_match = all(s["n_words"] == g["n_words"] for s, g in zip(scrambled, gold))
    print(f"wrote {len(scrambled)} scrambled notes to {args.out}")
    print(f"  word counts identical to twins: {words_match}")
    print(f"  max character drift: {max(drift)} (capitalisation only)")
    print("\nsample:")
    print("  GOLD:     ", gold[0]["text"][:150])
    print("  SCRAMBLE: ", scrambled[0]["text"][:150])
    print("\nRead a few. They should look like clinical notes and mean nothing.")


if __name__ == "__main__":
    main()
