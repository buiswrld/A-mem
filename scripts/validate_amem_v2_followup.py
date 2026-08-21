"""Validate and emit a 20-prompt audit for the matched C3E0/C4E1 follow-up."""
import argparse, json, pathlib

def load(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("c3", type=pathlib.Path); ap.add_argument("c4", type=pathlib.Path)
    ap.add_argument("--audit", type=pathlib.Path, required=True)
    a, b = load(ap.parse_args().c3), load(ap.parse_args().c4)
    args = ap.parse_args()
    assert len(a) == len(b) == 1800
    assert [(r["probe_id"], r["sample_idx"]) for r in a] == [(r["probe_id"], r["sample_idx"]) for r in b]
    for rows, condition, enabled in ((a, "C3E0", False), (b, "C4E1", True)):
        assert {r["condition"] for r in rows} == {condition}
        assert {r["memory_evolution_enabled"] for r in rows} == {enabled}
        assert {r["git_sha"] for r in rows} == {"792ee08"}
        assert all(len(r["retrieved_note_ids"]) == len(r["retrieved_texts"]) == len(r["retrieved_scores"]) == 3 for r in rows)
        assert all("Original note:" in r["memory_context"] and "Memory context:" in r["memory_context"] and "Tags:" in r["memory_context"] for r in rows)
        by_probe = {}
        for r in rows:
            signature = (r["retrieved_note_ids"], r["retrieved_texts"], r["memory_context"])
            assert by_probe.setdefault(r["probe_id"], signature) == signature
        assert len(by_probe) == 180
    picks = []
    for pid in sorted({r["probe_id"] for r in a})[:20]:
        ra = next(r for r in a if r["probe_id"] == pid and r["sample_idx"] == 0)
        rb = next(r for r in b if r["probe_id"] == pid and r["sample_idx"] == 0)
        picks.append({"probe_id": pid, "probe_text": ra["probe_text"], "C3E0_memory_context": ra["memory_context"], "C3E0_response": ra["response"], "C4E1_memory_context": rb["memory_context"], "C4E1_response": rb["response"]})
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in picks) + "\n")
    print("PASS: 2 x 1800 paired rows, 180 probes, exact 3-note retrievals; wrote", args.audit)

if __name__ == "__main__": main()
