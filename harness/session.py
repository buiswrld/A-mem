"""Episodic session runner for C3 and C4.

Decided 2026-07-27: memory conditions are not probed against a static store
single-turn. A session of clinical Q&A is written into the store first, and only
then does the probe run. Without session history A-MEM never links or evolves
anything, so C4 would be vector RAG with extra latency and H3 a null by
construction. C3 runs the identical protocol so the memory system stays the only
varied factor (Invariant #3).

## Shape of a run

    build_session()   write the corrective corpus, then N turns of clinical Q&A
                      -> one evolved store per (condition, seed)
    probe_session()   fire every probe at that store. Retrieval only.

**Build once, probe many.** `search()` on both backends costs no LLM call and
does not mutate the store, so a session per probe buys nothing and costs ~90x:

    per-probe : 90 probes x 3 seeds x 10 turns x 2 calls ~= 5,400 calls/tier
    shared    :             3 seeds x 10 turns x 2 calls  =     60 calls/tier

Sharing is also better science -- every probe sees an identical store, so
store-construction variance stops leaking into per-probe numbers.

## Status

C4's backend works (see harness/llm_backend.make_amem). C3's does not: the
static-RAG backend was removed 2026-07-27 and `harness.memory.build_store`
raises. `VectorBackend` below is the shape that refactor has to satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from harness.data import read_notes, sample_balanced
from harness.memory import Retrieval

# Notes are prefixed so a retrieved id says which corpus it came from without a
# lookup. The mediation analysis groups on exactly this.
CORRECTIVE_PREFIX = "cn-"
SESSION_PREFIX = "sess-"


@dataclass
class SessionSpec:
    condition: str  # "C3" | "C4" | "C5"
    seed: int
    n_turns: int = 10
    k: int = 3  # notes retrieved per probe
    corpus: str = "corrective"  # "corrective" | "scramble" (C5)


@dataclass
class Turn:
    """One exchange in the episodic session."""

    turn_idx: int
    user_text: str
    subject_response: str | None = None  # filled in if the policy needs it


class MemoryBackend(Protocol):
    """What both C3 (static vector) and C4 (A-MEM) must provide.

    Deliberately two methods. Everything the runner needs is write-then-read,
    and keeping the surface this small is what lets C3 and C4 run byte-identical
    session code -- which is the only reason their comparison means anything.
    """

    def write(self, text: str, note_id: str) -> None: ...

    def search(self, query: str, k: int) -> Retrieval: ...


# --------------------------------------------------------------------------
# The turns
# --------------------------------------------------------------------------


def session_prompts(spec: SessionSpec) -> list[str]:
    """The clinical questions asked during the session, in order.

    Drawn from the MedSafetyBench **train** split, never test. Three reasons,
    all of which matter more than they look:

    * free and deterministic -- an LLM "simulated clinician" would cost money
      per session and inject fresh variance between C3 and C4;
    * seeded, so C3 and C4 see the identical session (Invariant #3);
    * train-split, so the session cannot leak a probe's answer (Invariant #2).
    """
    pairs = sample_balanced("train", spec.n_turns, seed=spec.seed)
    return [p["request"] for p in pairs]


WRITE_POLICY = "subject_self_authored"  # decided 2026-07-28; option B


def memory_write_for(turn: Turn, spec: SessionSpec) -> str | None:
    """What text from this turn enters the memory store.

    **Policy decided 2026-07-28: the agent writes its own answers** (option B of
    the three that were on the table). A deployed agent writes its interactions
    to memory, so this is the realistic protocol, and it is the only one that
    gives H3 a mechanism: the subject is EM'd, its session answers are
    misaligned, and the question becomes whether A-MEM's evolution lets that
    self-authored misaligned text blur, merge with, or bury the corrective notes
    over a session.

    Rejected, recorded so nobody re-opens it silently:
      A. write nothing from the session -- evolution still fires on the corpus,
         but "episodic" is then a thin claim and H3 has almost no mechanism.
      C. write MSB ground-truth safe responses -- no scope concern, but sterile:
         the session can only ever help the repair, never stress it.

    Scope note: this is self-authored history, not adversarial injection, so it
    stays inside the spirit of PROJECT_CONTEXT §7 (no poisoning arm, no
    attack-success metrics) while touching the letter of it. Flag it in the
    write-up as a protocol detail, not as a poisoning experiment.

    TODO(you) -- the remaining choice, ~5 lines. What exactly gets written?

        return turn.subject_response                          # answer alone
        return f"{turn.user_text}\n{turn.subject_response}"    # Q and A

    This is a retrieval decision, not a formatting one. The store is embedded
    with all-MiniLM-L6-v2 and queried with probe text, so a bare answer with no
    question attached has no clinical anchor to match on -- and A-MEM's
    analyze_content() will extract keywords from a floating answer that read as
    nonsense. Attaching the question makes the note retrievable by the kind of
    request that produced it, which is what you want if the hypothesis is that
    these notes compete with the corrective ones at retrieval time.

    Against: including the question means the note contains a *request* as well
    as a response, and requests come from the MSB train split -- so check the
    embedded text cannot end up more similar to a probe than the corrective
    notes are, for reasons that are about surface wording rather than content.

    Whatever you return, C5 writes the same way: it differs from C3 only in
    corpus (scrambled notes), never in protocol, or Invariant #3 breaks.
    """
    raise NotImplementedError("see the TODO above -- ~5 lines")


# --------------------------------------------------------------------------
# Build and probe
# --------------------------------------------------------------------------


def build_session(backend: MemoryBackend, spec: SessionSpec, generate_fn) -> list[Turn]:
    """Load the corpus, then run the session. Returns the turns for the record.

    `generate_fn(prompt: str) -> str` is the subject model. Passed in rather
    than imported so this module never touches torch (Rule 2) and so a dry run
    can stub it.

    Order matters: corrective notes go in FIRST. A-MEM evolves each new note
    against its nearest neighbours, so notes written later are the ones with a
    populated neighbourhood to link into. Load the session first and the
    corrective notes arrive into an empty-ish store and never get linked --
    which would read as "evolution did nothing" for purely mechanical reasons.
    """
    for note in read_notes(spec.corpus):
        backend.write(note["text"], note["note_id"])

    turns: list[Turn] = []
    for i, prompt in enumerate(session_prompts(spec)):
        turn = Turn(turn_idx=i, user_text=prompt)

        # Only pay for a generation if the write policy actually needs it.
        # Options A and C never look at subject_response.
        if _policy_needs_subject(spec):
            turn.subject_response = generate_fn(prompt)

        text = memory_write_for(turn, spec)
        if text is not None:
            backend.write(text, f"{SESSION_PREFIX}{spec.seed}-{i:03d}")
        turns.append(turn)

    return turns


def _policy_needs_subject(spec: SessionSpec) -> bool:
    """Whether memory_write_for() reads turn.subject_response.

    True under the self-authored policy: every session turn costs one subject
    generation. That is GPU time, not API spend -- ~10 generations per
    (condition, seed), which is nothing next to the probe run.
    """
    return WRITE_POLICY == "subject_self_authored"


def probe_session(backend: MemoryBackend, spec: SessionSpec, probe_text: str) -> Retrieval:
    """Retrieve for one probe. No writes -- the store is frozen after build.

    Returns the full Retrieval so note ids and scores land in the record
    (Invariant #7). This cannot be backfilled: "the note never came back" and
    "the note came back and the weights won" are the two halves of the
    mediation analysis and are indistinguishable from response text alone.
    """
    return backend.search(probe_text, spec.k)
