"""Tests for the retrieval/prompt exporter and the record fields it reads.

Pure stdlib + tmp files -- no GPU, no API key, no chromadb, nothing that
spends money. Run with: uv run pytest harness/tests/
"""

from __future__ import annotations

import csv
import json

import pytest

from harness import export
from harness.schema import GenerationRecord, write_jsonl


def make_record(probe_id: str, sample_idx: int, **over) -> GenerationRecord:
    kw = {
        "condition": "C4", "tier": "D", "probe_id": probe_id,
        "probe_text": f"ask {probe_id}", "sample_idx": sample_idx, "seed": 0,
        "base_model": "unsloth/Qwen2.5-14B-Instruct",
        "adapter": "ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice",
        "load_4bit": True, "temperature": 1.0, "top_p": 1.0,
        "max_new_tokens": 600, "response": "a response", "memory_kind": "amem",
        "collection": "c4-s0-abc", "corpus": "corrective",
        "retrieved_note_ids": ["cn-0001", "sess-0-000"],
        "retrieved_scores": [0.21, 0.44],
        "retrieved_is_corrective": [True, False],
        "retrieved_texts": ["live corrective text", "self authored turn"],
        "memory_context": "PREAMBLE\n\n- live corrective text\n\n- self authored turn",
    }
    kw.update(over)
    return GenerationRecord(**kw)


def write_run(tmp_path, records) -> object:
    path = tmp_path / "run.jsonl"
    write_jsonl(path, records)
    return path


@pytest.fixture
def outputs(tmp_path, monkeypatch):
    """Redirect the exporter's output dirs into tmp so tests never touch the repo."""
    monkeypatch.setattr(export, "ROOT", tmp_path)
    monkeypatch.setattr(export, "PROMPT_DIR", tmp_path / "prepared_prompts")
    monkeypatch.setattr(export, "ANALYSIS_DIR", tmp_path / "analysis")
    return tmp_path


# --- the record must be able to carry the text at all ----------------------

def test_record_rejects_texts_not_parallel_to_ids():
    # The failure this guards is silent: rank i would pair one note's id with
    # another note's text and the CSV would still look well formed.
    with pytest.raises(ValueError, match="retrieved_texts"):
        make_record("p1", 0, retrieved_texts=["only one"])


def test_record_allows_empty_texts():
    # C1/C6 retrieve nothing; static_context (C2) has no distances.
    r = make_record("p1", 0, retrieved_texts=[], retrieved_scores=[])
    assert r.retrieved_texts == []


# --- export shape ----------------------------------------------------------

def test_export_writes_both_files_keyed_on_probe(tmp_path, outputs):
    # 2 probes x 3 samples: retrieval is per-probe, so the outputs are per-probe.
    records = [make_record(f"p{p}", i) for p in (1, 2) for i in range(3)]
    export.export(write_run(tmp_path, records))

    prompts = [json.loads(l) for l in
               (outputs / "prepared_prompts" / "C4_amem_prompts.jsonl").read_text().splitlines()]
    assert len(prompts) == 2
    assert {p["probe_id"] for p in prompts} == {"p1", "p2"}
    assert all(p["n_samples"] == 3 for p in prompts)

    with (outputs / "analysis" / "C4_retrieval_logs.csv").open() as fh:
        log = list(csv.DictReader(fh))
    assert len(log) == 4  # 2 probes x 2 notes
    assert [r["rank"] for r in log] == ["0", "1", "0", "1"]
    assert log[0]["note_id"] == "cn-0001"
    assert log[0]["note_text"] == "live corrective text"
    assert log[0]["is_corrective"] == "True"
    assert log[1]["is_corrective"] == "False"


def test_export_preserves_live_returned_text_not_reconstructed_text(tmp_path, outputs):
    """Export the backend's live return without assuming corpus equivalence.

    The reported A-MEM run happened to leave served content unchanged, but this record
    contract must remain valid for a backend that returns different text.
    """
    records = [make_record("p1", 0, retrieved_texts=["LIVE-RETURN", "b"])]
    export.export(write_run(tmp_path, records))
    with (outputs / "analysis" / "C4_retrieval_logs.csv").open() as fh:
        assert next(csv.DictReader(fh))["note_text"] == "LIVE-RETURN"


def test_export_writes_the_messages_the_model_got(tmp_path, outputs):
    export.export(write_run(tmp_path, [make_record("p1", 0)]))
    row = json.loads(
        (outputs / "prepared_prompts" / "C4_amem_prompts.jsonl").read_text().splitlines()[0]
    )
    assert [m["role"] for m in row["messages"]] == ["system", "user"]
    assert row["messages"][0]["content"] == row["system"]
    assert row["messages"][1]["content"] == "ask p1"


def test_condition_slug_matches_final_placebo_control(tmp_path, outputs):
    records = [make_record("p1", 0, condition="C5", memory_kind="vector", corpus="placebo",
                           retrieved_note_ids=["pb-0001", "pb-0002"],
                           retrieved_is_corrective=[False, False])]
    export.export(write_run(tmp_path, records))
    assert (outputs / "prepared_prompts" / "C5_placebo_rag_prompts.jsonl").exists()
    assert (outputs / "analysis" / "C5_retrieval_logs.csv").exists()


# --- the guards ------------------------------------------------------------

def test_export_refuses_a_file_with_no_retrieved_text(tmp_path, outputs):
    records = [make_record("p1", 0, retrieved_texts=[])]
    with pytest.raises(SystemExit, match="no retrieved_texts"):
        export.export(write_run(tmp_path, records))


def test_export_refuses_disagreeing_retrieval_for_one_probe(tmp_path, outputs):
    # Two runs concatenated, or a store still being written to mid-probe.
    records = [
        make_record("p1", 0),
        make_record("p1", 1, retrieved_note_ids=["cn-9999", "sess-0-001"]),
    ]
    with pytest.raises(SystemExit, match="different notes"):
        export.export(write_run(tmp_path, records))


def test_export_refuses_conditions_with_no_retrieval(tmp_path, outputs):
    records = [make_record("p1", 0, condition="C1", memory_kind="none", collection=None,
                           corpus=None, retrieved_note_ids=[], retrieved_scores=[],
                           retrieved_is_corrective=[], retrieved_texts=[],
                           memory_context=None)]
    with pytest.raises(SystemExit, match="retrieves nothing"):
        export.export(write_run(tmp_path, records))
