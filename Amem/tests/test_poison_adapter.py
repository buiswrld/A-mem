import pytest

from agentic_memory.poison_adapter import adapt_poison_record, adapt_poison_records


def approved_placeholder_record():
    """Harmless stand-in for an approved poison record; not clinical content."""
    return {
        "id": "placeholder-001",
        "false_claim": "A harmless placeholder claim for adapter testing.",
        "explanation": "This correction text must remain hidden from memory.",
        "category": "test-category",
        "difficulty_tier": "myth_level",
        "source": "synthetic",
        "keywords": ["placeholder", "adapter"],
        "tags": ["test"],
    }


def test_adapter_exposes_only_memory_text_and_scalar_metadata():
    note = adapt_poison_record(approved_placeholder_record())

    assert note == {
        "note_id": "placeholder-001",
        "content": "A harmless placeholder claim for adapter testing.",
        "metadata": {
            "kind": "poison_claim",
            "record_id": "placeholder-001",
            "category": "test-category",
            "difficulty_tier": "myth_level",
            "source": "synthetic",
            "keywords": "placeholder, adapter",
            "tags": "test",
        },
    }
    assert "explanation" not in note["metadata"]
    assert "correction" not in note["content"]


def test_adapter_accepts_legacy_content_but_not_ambiguous_claim_fields():
    legacy_record = approved_placeholder_record()
    legacy_record["content"] = legacy_record.pop("false_claim")

    assert adapt_poison_record(legacy_record)["content"].startswith("A harmless")

    ambiguous_record = approved_placeholder_record()
    ambiguous_record["content"] = "Another harmless placeholder claim."
    with pytest.raises(ValueError, match="exactly one claim field"):
        adapt_poison_record(ambiguous_record)


def test_adapter_requires_traceability_fields_and_scalarizes_batches():
    incomplete_record = approved_placeholder_record()
    incomplete_record.pop("source")
    with pytest.raises(ValueError, match="source must be a non-empty string"):
        adapt_poison_record(incomplete_record)

    notes = adapt_poison_records([approved_placeholder_record()])
    assert notes[0]["metadata"]["kind"] == "poison_claim"
