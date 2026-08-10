"""Turn a results file into the two artifacts the experiment is reviewed from:
the prompts that were actually sent, and the retrieval that produced them.

    uv run python -m harness.export --in results/C4-msb_test-<hash>-s0.jsonl

Writes, per Ryan's 2026-08-04 spec (docs/utd-reqs.md):

    prepared_prompts/C4_amem_prompts.jsonl     one row per probe
    analysis/C4_retrieval_logs.csv             one row per retrieved note

**This is a reader, not a recorder.** It can only export what the run wrote,
which is why `retrieved_texts` had to land in `harness/schema.py` before the
first C4 run rather than after it. For C3 and C5 a missing text column could be
repaired by joining note ids back to `corpora/`; for C4 it cannot, because
A-MEM rewrites note content as it evolves and keeps its store in memory, so the
text a probe actually saw exists only during the run that produced it. Files
stamped `schema_version` 1.0.0 predate that field and are called out below
instead of being silently exported without it.

Retrieval happens once per probe and every sample of that probe sees it
(`run_session.py`), so both outputs are keyed on probe, not on the 5x sample
rows. That invariant is checked rather than assumed -- if two samples of one
probe disagree about what was retrieved, something reused a store mid-run and
every aggregate downstream is suspect.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib

from harness.schema import read_jsonl

ROOT = pathlib.Path(__file__).parent.parent
PROMPT_DIR = ROOT / "prepared_prompts"
ANALYSIS_DIR = ROOT / "analysis"

# The names are Ryan's, verbatim, so the files land where the spec says to look
# for them. Slug is the mechanism, not the condition, which is why C3 and C5
# differ here despite sharing a backend.
SLUG = {
    "C2": "static_prompt",
    "C3": "static_rag",
    "C4": "amem",
    "C5": "scrambled_rag",
}


def group_by_probe(rows: list[dict]) -> dict[str, dict]:
    """One entry per probe, with the retrieval checked for agreement.

    Disagreement is raised, not warned. The two ways it happens are a store
    that kept mutating after `build_session()` froze it, and two runs' rows
    concatenated into one file -- and in both cases the per-probe retrieval log
    this module writes would be a fiction, picking whichever row it saw first.
    """
    probes: dict[str, dict] = {}
    for row in rows:
        pid = row["probe_id"]
        seen = probes.get(pid)
        if seen is None:
            probes[pid] = {"row": row, "n_samples": 1}
            continue
        if seen["row"]["retrieved_note_ids"] != row["retrieved_note_ids"]:
            raise SystemExit(
                f"probe {pid} retrieved different notes on different samples:\n"
                f"  {seen['row']['retrieved_note_ids']}\n"
                f"  {row['retrieved_note_ids']}\n"
                "Retrieval is once per probe and the store is frozen before "
                "probing, so this file is either two runs concatenated or a "
                "store that was still being written to. Do not export it."
            )
        seen["n_samples"] += 1
    return probes


def write_prompts(path: pathlib.Path, condition: str, probes: dict[str, dict]) -> int:
    """The prompt each probe was sent, as messages.

    `messages` rather than one templated string on purpose: the final string is
    whatever `tokenizer.apply_chat_template` produces, so it depends on the
    tokenizer and writing it here would mean guessing at one. These are the
    exact two entries `harness.generate.generate_batch` builds, so the string
    is reproducible from this file plus the model named in it.
    """
    with path.open("w") as fh:
        for pid, entry in probes.items():
            row = entry["row"]
            system = row.get("memory_context")
            messages = [{"role": "system", "content": system}] if system else []
            messages.append({"role": "user", "content": row["probe_text"]})
            fh.write(json.dumps({
                "probe_id": pid,
                "condition": condition,
                "memory_kind": row.get("memory_kind"),
                "corpus": row.get("corpus"),
                "collection": row.get("collection"),
                "probe_text": row["probe_text"],
                "system": system,
                "messages": messages,
                "retrieved_note_ids": row.get("retrieved_note_ids", []),
                "n_samples": entry["n_samples"],
                "base_model": row.get("base_model"),
                "adapter": row.get("adapter"),
                "config_hash": row.get("config_hash"),
                "git_sha": row.get("git_sha"),
                "schema_version": row.get("schema_version"),
            }) + "\n")
    return len(probes)


def write_retrieval_log(path: pathlib.Path, condition: str, probes: dict[str, dict]) -> int:
    """One row per retrieved note: id, rank, score, is_corrective, text.

    Rank is the position the store returned it in, so rank 0 is the nearest
    hit. Scores are ChromaDB distances on both backends -- lower is nearer, not
    higher. Anyone sorting this descending and calling the top row "best match"
    gets the answer exactly backwards, hence the column name.
    """
    fields = [
        "condition", "probe_id", "rank", "note_id", "distance",
        "is_corrective", "n_words", "note_text",
    ]
    written = 0
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for pid, entry in probes.items():
            row = entry["row"]
            ids = row.get("retrieved_note_ids", [])
            scores = row.get("retrieved_scores", [])
            corrective = row.get("retrieved_is_corrective", [])
            texts = row.get("retrieved_texts", [])
            for rank, note_id in enumerate(ids):
                text = texts[rank] if rank < len(texts) else ""
                w.writerow({
                    "condition": condition,
                    "probe_id": pid,
                    "rank": rank,
                    "note_id": note_id,
                    "distance": scores[rank] if rank < len(scores) else "",
                    "is_corrective": corrective[rank] if rank < len(corrective) else "",
                    "n_words": len(text.split()),
                    "note_text": text,
                })
                written += 1
    return written


def export(in_path: pathlib.Path) -> None:
    rows = read_jsonl(str(in_path))
    if not rows:
        raise SystemExit(f"{in_path} is empty")

    condition = rows[0]["condition"]
    if condition not in SLUG:
        raise SystemExit(
            f"{condition} retrieves nothing -- there is no prompt context and no "
            f"retrieval to export. Exportable: {', '.join(sorted(SLUG))}."
        )

    probes = group_by_probe(rows)
    if not any(r.get("retrieved_texts") for r in rows):
        # Worth stopping over rather than writing a log with an empty text
        # column: for C4 the text is unrecoverable, and a file that looks
        # complete is how that gets discovered a week later.
        raise SystemExit(
            f"{in_path} carries no retrieved_texts (schema_version "
            f"{rows[0].get('schema_version')}). It was produced before that "
            "field existed, so the note text a probe saw is not in it.\n"
            "  C3/C5: rerun the export after re-running, or join note ids to "
            "corpora/ yourself -- the ids are present and the corpus is static.\n"
            "  C4: the text is gone. A-MEM evolves note content and its store "
            "is in-memory, so only a fresh run can produce it."
        )

    PROMPT_DIR.mkdir(exist_ok=True)
    ANALYSIS_DIR.mkdir(exist_ok=True)
    slug = SLUG[condition]
    prompt_path = PROMPT_DIR / f"{condition}_{slug}_prompts.jsonl"
    log_path = ANALYSIS_DIR / f"{condition}_retrieval_logs.csv"

    n_probes = write_prompts(prompt_path, condition, probes)
    n_notes = write_retrieval_log(log_path, condition, probes)

    print(f"{in_path.name}: {len(rows)} rows -> {n_probes} probes")
    print(f"  {prompt_path.relative_to(ROOT)}  ({n_probes} prompts)")
    print(f"  {log_path.relative_to(ROOT)}  ({n_notes} retrieved notes)")

    corrective = sum(
        1 for e in probes.values() for c in e["row"].get("retrieved_is_corrective", []) if c
    )
    print(f"  {corrective}/{n_notes} retrieved notes are corrective (cn-*)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="in_path", required=True,
                    help="a results/*.jsonl written by run_session or run_condition")
    args = ap.parse_args()
    export(pathlib.Path(args.in_path))


if __name__ == "__main__":
    main()
