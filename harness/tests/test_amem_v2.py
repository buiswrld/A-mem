"""Mechanism-integrity tests for the expedited C3E0/C4E1 follow-up."""

from types import SimpleNamespace

from harness.memory import AmemMemoryBackend
from harness.session import SessionSpec, Turn, build_session


class FakeSystem:
    def __init__(self, notes, hits):
        self.memories = notes
        self._hits = hits

    def search(self, query, k):
        return self._hits[:k]


def backend(notes, hits, *, evolved):
    out = AmemMemoryBackend.__new__(AmemMemoryBackend)
    out.name = "test"
    out.system = FakeSystem(notes, hits)
    out.serve_evolved = True
    out.evolution_enabled = evolved
    return out


def note(content, *, context="General", tags=None, links=None):
    return SimpleNamespace(
        content=content, context=context, tags=tags or [], links=links or []
    )


def test_v2_prompt_serves_evolved_fields():
    notes = {"cn-1": note("safe text", context="EVOLVED", tags=["safety"])}
    hits = [{"id": "cn-1", "content": "safe text", "score": 0.2}]
    got = backend(notes, hits, evolved=True).search("q", 1)
    assert "Original note: safe text" in got.context
    assert "Memory context: EVOLVED" in got.context
    assert "Tags: safety" in got.context
    assert got.texts[0] in got.context


def test_valid_link_promotes_candidate_without_changing_slot_count():
    notes = {
        "cn-1": note("one", links=["cn-3", "missing"]),
        "cn-2": note("two"),
        "cn-3": note("three"),
    }
    hits = [
        {"id": "cn-1", "content": "one", "score": 0.1},
        {"id": "cn-2", "content": "two", "score": 0.2},
        {"id": "cn-3", "content": "three", "score": 0.3},
    ]
    got = backend(notes, hits, evolved=True).search("q", 2)
    assert got.note_ids == ["cn-1", "cn-3"]
    assert len(got.note_ids) == 2


def test_frozen_and_evolved_arms_share_rendering_schema():
    hits = [{"id": "cn-1", "content": "same", "score": 0.1}]
    frozen = backend({"cn-1": note("same")}, hits, evolved=False).search("q", 1)
    evolved = backend(
        {"cn-1": note("same", context="changed", tags=["new"])},
        hits, evolved=True,
    ).search("q", 1)
    assert "Original note:" in frozen.context
    assert "Memory context:" in frozen.context
    assert "Original note:" in evolved.context
    assert frozen.context != evolved.context


def test_precomputed_session_is_replayed_without_generation(monkeypatch):
    class Store:
        def __init__(self):
            self.writes = []

        def write(self, text, note_id):
            self.writes.append((note_id, text))

    monkeypatch.setattr("harness.session.read_notes", lambda kind: [])
    monkeypatch.setattr("harness.session.session_prompts", lambda spec: ["same prompt"])
    turns = [Turn(0, "same prompt", "same answer")]
    store = Store()
    got = build_session(
        store,
        SessionSpec("C4E1", seed=0, n_turns=1),
        lambda prompt: (_ for _ in ()).throw(AssertionError("must not generate")),
        precomputed_turns=turns,
    )
    assert got == turns
    assert store.writes == [("sess-0-000", "same prompt\nsame answer")]
