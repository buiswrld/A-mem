"""Normalize approved poison records before they enter vector memory.

This module does not read a dataset or decide whether a medical statement is
true.  Its only job is to make an already-approved record safe to hand to
``load_notes``: only the intended claim becomes memory text, while explanatory
material remains outside the vector store.
"""

from typing import Any, Dict, Iterable, List, Mapping


CLAIM_FIELDS = ("false_claim", "memory_text", "content")
REQUIRED_METADATA_FIELDS = ("category", "difficulty_tier", "source")


def adapt_poison_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert one approved source record into a vector-memory note.

    ``false_claim`` is the preferred future source field.  ``memory_text`` and
    ``content`` are accepted only as compatibility inputs for already-approved
    schemas.  ``explanation`` is intentionally never copied into the returned
    note or its metadata.
    """
    record_id = _required_text(record, "id")
    memory_text = _claim_text(record)
    metadata = {
        "kind": "poison_claim",
        "record_id": record_id,
    }
    for field in REQUIRED_METADATA_FIELDS:
        metadata[field] = _required_text(record, field)

    for field in ("keywords", "tags"):
        if field in record:
            metadata[field] = _scalarize_labels(record[field], field)

    return {
        "note_id": record_id,
        "content": memory_text,
        "metadata": metadata,
    }


def adapt_poison_records(records: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize an approved sequence of records for ``load_notes``."""
    return [adapt_poison_record(record) for record in records]


def _claim_text(record: Mapping[str, Any]) -> str:
    supplied_fields = [field for field in CLAIM_FIELDS if field in record]
    if len(supplied_fields) != 1:
        names = ", ".join(CLAIM_FIELDS)
        raise ValueError(f"record needs exactly one claim field: {names}")
    return _required_text(record, supplied_fields[0])


def _required_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _scalarize_labels(value: Any, field: str) -> str:
    """Turn label arrays into Chroma-compatible, human-readable strings."""
    if not isinstance(value, list) or not all(
        isinstance(label, str) and label.strip() for label in value
    ):
        raise ValueError(f"{field} must be a list of non-empty strings")
    return ", ".join(label.strip() for label in value)
