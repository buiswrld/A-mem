"""Small helpers for repeatable vector-memory experiment conditions.

The helpers in this module deliberately stop before calling an LLM.  They load
approved note text into an isolated Chroma collection and make the retrieval
step observable.  A later evaluation runner can pass only ``contents`` to an
answering model while retaining the full record for analysis.
"""

from typing import Any, Dict, Iterable, List, Mapping, Optional

from .simple_vector_memory import SimpleVectorMemory


CONDITIONS = {"clean", "poison", "corrected"}


def open_condition(
    condition: str,
    *,
    directory: Optional[str] = None,
    collection_prefix: str = "mcq",
) -> SimpleVectorMemory:
    """Open one isolated collection for a named experiment condition."""
    if condition not in CONDITIONS:
        choices = ", ".join(sorted(CONDITIONS))
        raise ValueError(f"condition must be one of: {choices}")
    return SimpleVectorMemory(
        directory=directory,
        collection_name=f"{collection_prefix}_{condition}",
    )


def load_notes(
    memory: SimpleVectorMemory, notes: Iterable[Mapping[str, Any]]
) -> List[str]:
    """Upsert approved notes and return their stable IDs.

    Each note needs ``content`` and ``note_id``.  ``metadata`` is optional and
    must contain only Chroma-supported scalar values, as enforced by
    :meth:`SimpleVectorMemory.add_note`.
    """
    note_ids = []
    for note in notes:
        try:
            content = note["content"]
            note_id = note["note_id"]
        except KeyError as error:
            raise ValueError("each note needs content and note_id") from error
        note_ids.append(
            memory.add_note(
                content,
                note_id=note_id,
                metadata=note.get("metadata"),
            )
        )
    return note_ids


def retrieve_with_log(
    memory: SimpleVectorMemory,
    *,
    question_id: str,
    query: str,
    k: int = 3,
) -> Dict[str, Any]:
    """Retrieve notes and return the complete, JSON-ready retrieval record.

    ``poison_retrieved`` is true only when a poison-labelled note is among the
    final top-``k`` notes returned by Chroma.  It is analysis metadata, not
    material to place in the LLM prompt.
    """
    matches = memory.search(query, k=k)
    retrieved_notes = [
        {
            "rank": rank,
            "note_id": match["id"],
            "content": match["content"],
            "distance": match["distance"],
            "metadata": match["metadata"],
        }
        for rank, match in enumerate(matches, start=1)
    ]
    return {
        "question_id": question_id,
        "collection": memory.collection_name,
        "query": query,
        "requested_k": k,
        "retrieved_notes": retrieved_notes,
        "poison_retrieved": any(
            note["metadata"].get("kind") == "poison_claim"
            for note in retrieved_notes
        ),
    }


def contents_for_prompt(retrieval_record: Mapping[str, Any]) -> List[str]:
    """Return only note text for an answering prompt, never analysis labels."""
    return [note["content"] for note in retrieval_record["retrieved_notes"]]
