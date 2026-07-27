"""A small, persistent ChromaDB-backed memory store.

This module is deliberately separate from :mod:`memory_system`.  It provides
the minimum useful vector-memory behaviour without involving an LLM or A-MEM's
memory-evolution logic:

* add one note;
* keep it on disk across program runs; and
* retrieve the closest notes for a natural-language query.

That makes it useful as a transparent retrieval baseline and as a teaching
step before connecting retrieval to an answering agent.
"""

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
import uuid

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


MetadataValue = Any


class SimpleVectorMemory:
    """Store and semantically retrieve short memory notes with ChromaDB.

    Parameters
    ----------
    directory:
        Local directory where ChromaDB keeps its files.  It is intentionally
        project-local by default, rather than using a hidden directory in a
        developer's home folder.
    collection_name:
        The isolated group of notes to use.  Give each experiment condition a
        different name (for example, ``clean_memory`` or ``poison_memory``)
        so that their notes never mix.
    model_name:
        The local sentence-embedding model used to compare meanings.
    """

    def __init__(
        self,
        directory: Optional[str] = None,
        collection_name: str = "agent_memories",
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        storage_directory = Path(directory or ".vector-memory")
        storage_directory.mkdir(parents=True, exist_ok=True)

        self.directory = storage_directory
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(storage_directory))
        self.embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )

    def add_note(
        self,
        content: str,
        *,
        metadata: Optional[Mapping[str, MetadataValue]] = None,
        note_id: Optional[str] = None,
    ) -> str:
        """Add or replace one note and return its stable identifier.

        The text in ``content`` is what is embedded and searched.  Metadata is
        supporting information such as ``source``, ``kind``, or ``run_id``;
        it is returned with a search result but does not replace the note text.
        """
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string")

        prepared_metadata = self._prepare_metadata(metadata)
        memory_id = note_id or str(uuid.uuid4())
        self.collection.upsert(
            ids=[memory_id],
            documents=[content.strip()],
            metadatas=[prepared_metadata],
        )
        return memory_id

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Return at most ``k`` notes closest in meaning to ``query``.

        ``distance`` is ChromaDB's distance measure: lower numbers are closer.
        It is useful for debugging and comparison, but it is not a confidence
        percentage or a truth score.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if k < 1:
            raise ValueError("k must be at least 1")
        if self.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query.strip()],
            n_results=min(k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        return [
            {
                "id": note_id,
                "content": document,
                "metadata": metadata or {},
                "distance": distance,
            }
            for note_id, document, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def count(self) -> int:
        """Return the number of notes in this collection."""
        return self.collection.count()

    def delete_note(self, note_id: str) -> None:
        """Remove a note from this collection."""
        self.collection.delete(ids=[note_id])

    @staticmethod
    def _prepare_metadata(
        metadata: Optional[Mapping[str, MetadataValue]]
    ) -> Dict[str, MetadataValue]:
        """Keep metadata in the scalar form ChromaDB can store safely."""
        prepared: Dict[str, MetadataValue] = {"kind": "memory_note"}
        for key, value in (metadata or {}).items():
            if not isinstance(key, str):
                raise TypeError("metadata keys must be strings")
            if not isinstance(value, (str, int, float, bool)):
                raise TypeError(
                    "metadata values must be strings, numbers, or booleans"
                )
            prepared[key] = value
        return prepared
