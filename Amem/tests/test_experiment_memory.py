import pytest

from agentic_memory.experiment_memory import (
    contents_for_prompt,
    load_notes,
    open_condition,
    retrieve_with_log,
)


def test_conditions_use_separate_collections(temp_db_dir):
    clean = open_condition("clean", directory=str(temp_db_dir))
    poison = open_condition("poison", directory=str(temp_db_dir))

    load_notes(
        clean,
        [{"note_id": "clean-note", "content": "Harmless clean placeholder note."}],
    )

    assert clean.collection_name == "mcq_clean"
    assert poison.collection_name == "mcq_poison"
    assert poison.count() == 0


def test_retrieval_log_marks_only_returned_poison_notes(temp_db_dir):
    memory = open_condition("poison", directory=str(temp_db_dir))
    load_notes(
        memory,
        [
            {
                "note_id": "clean-note",
                "content": "A harmless reference note about follow-up.",
                "metadata": {"kind": "clean_note"},
            },
            {
                "note_id": "poison-placeholder",
                "content": "A harmless placeholder note for poison telemetry tests.",
                "metadata": {"kind": "poison_claim", "record_id": "test-1"},
            },
        ],
    )

    record = retrieve_with_log(
        memory,
        question_id="development-1",
        query="Which placeholder note tests poison telemetry?",
        k=1,
    )

    assert record["question_id"] == "development-1"
    assert record["requested_k"] == 1
    assert record["retrieved_notes"][0]["rank"] == 1
    assert record["retrieved_notes"][0]["note_id"] == "poison-placeholder"
    assert record["poison_retrieved"] is True
    assert contents_for_prompt(record) == [
        "A harmless placeholder note for poison telemetry tests."
    ]


def test_open_condition_rejects_unknown_conditions(temp_db_dir):
    with pytest.raises(ValueError, match="condition must be one of"):
        open_condition("mixed", directory=str(temp_db_dir))
