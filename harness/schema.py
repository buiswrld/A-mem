"""The frozen result schema. One GenerationRecord per generated response.

Every downstream number -- harm rate, Recovery, the mediation analysis -- is a
groupby over these rows. That makes this file the contract between four people,
so per Rule 4 in the implementation plan, changes get announced before they get
implemented.

Three fields exist purely so that a number can be defended weeks later:

    git_sha             which code produced it
    config_hash         which configuration produced it
    retrieved_note_ids  what the memory layer actually surfaced

The last one is the one people forget, and it is the one that cannot be
backfilled. A memory run without it is a run you have to redo, because the
mechanism question -- "did the note never come back, or come back and get
ignored?" -- is not recoverable from the response text alone.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

# 1.1.0 (2026-08-10) added retrieved_texts + memory_context. Additive only, so
# 1.0.0 files still read -- but they carry no retrieved text, and for the C4
# runs that is not recoverable. Anything stamped 1.0.0 cannot produce a
# retrieval log with note text in it.
SCHEMA_VERSION = "1.1.0"

Condition = Literal["C1", "C2", "C3", "C4", "C5", "C6"]
Tier = Literal["B", "D", "O", "A", "C"]
MemoryKind = Literal["none", "system_prompt", "vector", "amem"]


def git_sha() -> str:
    """Current commit, with -dirty appended if the tree has uncommitted changes.

    A dirty SHA is a warning, not an error: it means the row cannot be tied to
    reviewable code. Fine while debugging, never acceptable for a reported run.
    """
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        dirty = subprocess.call(["git", "diff", "--quiet", "HEAD"]) != 0
        return f"{sha}-dirty" if dirty else sha
    except (subprocess.SubprocessError, FileNotFoundError):
        return "unknown"


def config_hash(config: dict[str, Any]) -> str:
    """Stable 12-char digest of a run config.

    Sorted keys so that dict ordering never changes the hash -- two runs with
    the same settings must collide, or caching and provenance both break.
    """
    blob = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def response_hash(text: str) -> str:
    """Judge cache key. Identical text is never judged (or paid for) twice."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


@dataclass
class GenerationRecord:
    """One sampled response to one probe under one condition."""

    # --- what was asked -------------------------------------------------
    condition: Condition
    tier: Tier
    probe_id: str
    probe_text: str
    sample_idx: int
    seed: int

    # --- what answered --------------------------------------------------
    base_model: str
    adapter: str | None
    load_4bit: bool
    temperature: float
    top_p: float
    max_new_tokens: int

    # --- what came back -------------------------------------------------
    response: str

    # --- the memory layer ------------------------------------------------
    # memory_kind is the mechanism; condition is the label. They are logged
    # separately because C5 (placebo) uses the same mechanism as C3 (vector)
    # and differs only in corpus -- collapsing them would erase the placebo.
    memory_kind: MemoryKind = "none"
    collection: str | None = None
    corpus: str | None = None  # "corrective" | "placebo" | None
    # "scramble" also appears in rows generated before 2026-08-06, when C5's
    # corpus was still the word-shuffled placebo. No current run emits it.
    retrieved_note_ids: list[str] = field(default_factory=list)
    retrieved_scores: list[float] = field(default_factory=list)
    retrieved_is_corrective: list[bool] = field(default_factory=list)
    # The retrieved note text, in rank order, as the store returned it -- and
    # `memory_context` is the exact system string the model was given. Both are
    # stored rather than reconstructed from `corpora/` because for C4 they
    # cannot be: A-MEM rewrites note content as it evolves, and its store is
    # in-memory, so the run is the only moment this text exists. Rank is the
    # list index; it is not a separate field for the same reason `sample_idx`
    # is not derived -- one ordering, one place.
    retrieved_texts: list[str] = field(default_factory=list)
    memory_context: str | None = None
    session_id: str | None = None
    session_turn: int | None = None

    # --- provenance ------------------------------------------------------
    git_sha: str = field(default_factory=git_sha)
    config_hash: str = ""
    schema_version: str = SCHEMA_VERSION
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def __post_init__(self) -> None:
        # Every retrieval list is indexed by rank, so a length mismatch does not
        # error downstream -- it silently pairs note_id[i] with some other
        # note's text or score, and the retrieval log looks fine while saying
        # the wrong thing. `zip()` in the exporter would truncate to the
        # shortest and hide it, so it has to be caught at write time.
        # Empty is allowed: C1/C6 retrieve nothing, and static_context() (C2)
        # has ids and texts but no distances.
        for name in ("retrieved_scores", "retrieved_is_corrective", "retrieved_texts"):
            got = len(getattr(self, name))
            if got not in (0, len(self.retrieved_note_ids)):
                raise ValueError(
                    f"{name} must be empty or parallel to retrieved_note_ids; "
                    f"got {got} vs {len(self.retrieved_note_ids)}"
                )
        if self.memory_kind in ("vector", "amem") and self.collection is None:
            raise ValueError(
                f"{self.memory_kind} condition {self.condition} has no collection -- "
                "Invariant #1 requires one isolated collection per condition"
            )

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), ensure_ascii=False)


def write_jsonl(path, records) -> int:
    """Append records to a JSONL file. Returns the count written."""
    n = 0
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(r.to_json() + "\n")
            n += 1
    return n


def read_jsonl(path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
