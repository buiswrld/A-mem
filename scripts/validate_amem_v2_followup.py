"""Validate the matched C3E0/C4E1 C4 experiment and emit a 20-prompt audit."""

import argparse
import json
import pathlib

JUDGE_FIELDS = {"alignment", "coherence", "flag", "verdict", "judge_model"}


def load(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def validate_store(path, *, evolution_enabled):
    store = json.loads(path.read_text())
    notes = store["notes"]
    note_ids = {note["note_id"] for note in notes}
    summary = {
        "context_changed": sum(note["context"] != "General" for note in notes),
        "tagged": sum(bool(note["tags"]) for note in notes),
        "linked": sum(bool(note["links"]) for note in notes),
        "invalid_links": sum(
            link not in note_ids for note in notes for link in note["links"]
        ),
        "content_changed": sum(bool(note["content_changed"]) for note in notes),
    }
    expected = (
        {
            "context_changed": 105,
            "tagged": 128,
            "linked": 106,
            "invalid_links": 0,
            "content_changed": 0,
        }
        if evolution_enabled
        else {
            "context_changed": 0,
            "tagged": 0,
            "linked": 0,
            "invalid_links": 0,
            "content_changed": 0,
        }
    )
    if summary != expected:
        raise ValueError(f"unexpected store mutation summary: {summary}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("c3", type=pathlib.Path)
    ap.add_argument("c4", type=pathlib.Path)
    ap.add_argument("--c3-judged", type=pathlib.Path, required=True)
    ap.add_argument("--c4-judged", type=pathlib.Path, required=True)
    ap.add_argument("--c3-store", type=pathlib.Path, required=True)
    ap.add_argument("--c4-store", type=pathlib.Path, required=True)
    ap.add_argument("--audit", type=pathlib.Path, required=True)
    args = ap.parse_args()
    a, b = load(args.c3), load(args.c4)
    assert len(a) == len(b) == 1800
    assert [(r["probe_id"], r["sample_idx"]) for r in a] == [
        (r["probe_id"], r["sample_idx"]) for r in b
    ]
    for rows, condition, enabled in ((a, "C3E0", False), (b, "C4E1", True)):
        assert {r["condition"] for r in rows} == {condition}
        assert {r["memory_evolution_enabled"] for r in rows} == {enabled}
        assert {r["git_sha"] for r in rows} == {"792ee08"}
        assert all(
            len(r["retrieved_note_ids"])
            == len(r["retrieved_texts"])
            == len(r["retrieved_scores"])
            == 3
            for r in rows
        )
        assert all(
            "Original note:" in r["memory_context"]
            and "Memory context:" in r["memory_context"]
            and "Tags:" in r["memory_context"]
            for r in rows
        )
        by_probe = {}
        for r in rows:
            signature = (
                r["retrieved_note_ids"],
                r["retrieved_texts"],
                r["memory_context"],
            )
            assert by_probe.setdefault(r["probe_id"], signature) == signature
        assert len(by_probe) == 180
    for raw_rows, judged_path in ((a, args.c3_judged), (b, args.c4_judged)):
        judged_rows = load(judged_path)
        assert len(raw_rows) == len(judged_rows)
        assert all(
            raw
            == {key: value for key, value in judged.items() if key not in JUDGE_FIELDS}
            for raw, judged in zip(raw_rows, judged_rows, strict=True)
        )
    validate_store(args.c3_store, evolution_enabled=False)
    validate_store(args.c4_store, evolution_enabled=True)
    picks = []
    for pid in sorted({r["probe_id"] for r in a})[:20]:
        ra = next(r for r in a if r["probe_id"] == pid and r["sample_idx"] == 0)
        rb = next(r for r in b if r["probe_id"] == pid and r["sample_idx"] == 0)
        picks.append(
            {
                "probe_id": pid,
                "probe_text": ra["probe_text"],
                "C3E0_memory_context": ra["memory_context"],
                "C3E0_response": ra["response"],
                "C4E1_memory_context": rb["memory_context"],
                "C4E1_response": rb["response"],
            }
        )
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in picks) + "\n"
    )
    print(
        "PASS: 2 x 1800 paired raw/judged rows, 180 probes, exact 3-note "
        "retrievals, and expected store mutations; wrote",
        args.audit,
    )


if __name__ == "__main__":
    main()
