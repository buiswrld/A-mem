"""Which LLM plays which role, in one place.

There are four LLM slots in this experiment and only one of them is the model
under test. Keeping them straight is a correctness property, not tidiness:

    subject            the EM'd organism. Lives in generate.py (the only module
                       allowed to import torch). NOT configured here.
    memory_controller  A-MEM's internal LLM: analyze_content() + process_memory().
                       Runs on every add_note(). This is the cost centre.
    note_writer        one-shot, writes the corrective corpus. notebooks/01.
    judge              scores probe responses. judge.py.

Two rules that this file exists to make hard to break:

1. **The subject is never any other role.** An EM'd model judging itself gives a
   misaligned judge; an EM'd model running memory evolution contaminates the
   memory layer, and C4 stops measuring evolution.
2. **The memory controller is fixed for C4.** The intended C4-minus-C3 contrast
   was evolution, not a different retrieval stack. The implemented version
   executed the controller but did not serve the fields it changed.

Cost note, measured rather than assumed:

    AgenticMemorySystem.add_note()  -> 2 LLM calls (analyze + evolve)
    AgenticMemorySystem.search()    -> 0 LLM calls, and does not mutate the store

So reads are free and side-effect-free. Build a store once per (condition, seed)
and probe everything against it; do not rebuild per probe.

    export AMEM_BACKEND=ollama AMEM_MODEL=qwen2.5:7b-instruct
    export AMEM_BACKEND=openai AMEM_MODEL=gpt-4o-mini
    export AMEM_BACKEND=openai AMEM_MODEL=... AMEM_BASE_URL=http://localhost:8000/v1
"""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass

REPO = pathlib.Path(__file__).parent.parent

# Defaults per role. Overridable by env so a Colab run and a local run differ in
# configuration only -- never in code.
ROLE_DEFAULTS: dict[str, tuple[str, str]] = {
    # role              backend    model
    "memory_controller": ("openai", "gpt-4o-mini"),
    "note_writer": ("openai", "gpt-4o-mini"),
    # Betley's exact judge. Tier B exists to be comparable with published EM
    # numbers, so this one is pinned -- see judge.py.
    "judge": ("openai", "gpt-4o-2024-08-06"),
}


@dataclass(frozen=True)
class LLMSpec:
    """Everything needed to reach one LLM, and to record which one answered."""

    role: str
    backend: str  # "openai" | "ollama"
    model: str
    base_url: str | None = None

    def provenance(self) -> dict:
        """Goes into the run config so config_hash covers the scaffolding LLMs.

        Without this, swapping the memory controller from gpt-4o-mini to a local
        7B produces a different experiment under an identical config_hash.
        """
        return {
            f"{self.role}_backend": self.backend,
            f"{self.role}_model": self.model,
            f"{self.role}_base_url": self.base_url,
        }


def api_key() -> str:
    """OPENAI_API_KEY from env, falling back to .env. Same order as judge.py."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        env = REPO / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        raise SystemExit("no OPENAI_API_KEY in environment or .env")
    return key


def resolve(role: str) -> LLMSpec:
    """Role -> concrete backend/model, env overriding the default."""
    if role not in ROLE_DEFAULTS:
        raise ValueError(f"unknown role {role!r}; known: {sorted(ROLE_DEFAULTS)}")
    default_backend, default_model = ROLE_DEFAULTS[role]
    prefix = {"memory_controller": "AMEM", "note_writer": "NOTE", "judge": "JUDGE"}[role]
    return LLMSpec(
        role=role,
        backend=os.environ.get(f"{prefix}_BACKEND", default_backend),
        model=os.environ.get(f"{prefix}_MODEL", default_model),
        base_url=os.environ.get(f"{prefix}_BASE_URL") or None,
    )


# --------------------------------------------------------------------------
# A-MEM wiring
# --------------------------------------------------------------------------


def _install_controller(system, spec: LLMSpec) -> None:
    """Point A-MEM's controller at `spec`, adding the base_url it lacks.

    Upstream `OpenAIController.__init__` takes (model, api_key) and no base_url,
    so A-MEM cannot be aimed at a self-hosted vLLM/TGI server. This is the ~6
    lines STATUS.md flags as a known blocker. Swapping the constructed `.llm`
    is enough -- the controller interface is a single get_completion().
    """
    if spec.backend == "ollama":
        from agentic_memory.llm_controller import OllamaController

        system.llm_controller.llm = OllamaController(spec.model)
        return

    from agentic_memory.llm_controller import OpenAIController
    from openai import OpenAI

    controller = OpenAIController.__new__(OpenAIController)
    controller.model = spec.model
    controller.client = OpenAI(
        api_key=api_key() if spec.base_url is None else os.environ.get("OPENAI_API_KEY", "local"),
        base_url=spec.base_url,
    )
    system.llm_controller.llm = controller


def collection_name(condition: str, seed: int, tag: str = "") -> str:
    """One isolated collection per condition (Invariant #1).

    Seed is in the name because two seeds build two different evolved stores;
    sharing a collection between them would silently pool them.
    """
    suffix = f"-{tag}" if tag else ""
    return f"{condition.lower()}-s{seed}{suffix}"


def make_amem(condition: str, seed: int, *, tag: str = "", evo_threshold: int = 10**9,
              persist_dir: pathlib.Path | None = None):
    """An AgenticMemorySystem with per-condition isolation actually enforced.

    Upstream __init__ does two things that break Invariant #1, and both are
    fixed here rather than in the vendored source so the vendored diff stays
    reviewable:

    1. It calls `client.reset()` -- wiping every collection in the process,
       including other conditions' stores.
    2. It hardcodes the collection name "memories", so every condition shares
       one collection.

    `evo_threshold` defaults to effectively-infinite on purpose.
    `consolidate_memories()` (memory_system.py:266) rebuilds the retriever as a
    plain ChromaRetriever(collection_name="memories") -- so if the evolution
    counter ever reaches the threshold, isolation silently reverts to the
    hardcoded name mid-run. Raise this only once that is patched upstream.

    NOTE: this does not disable evolution. process_memory() runs on every
    add_note() regardless; evo_threshold only gates the periodic consolidation
    pass. In the vendored version that process updates metadata fields that the
    reported prompt path does not serve, so execution alone does not make H3 valid.

    `persist_dir` writes the Chroma collection to disk instead of holding it in
    memory. **Off by default, and it should stay off for ordinary runs.**
    `ChromaRetriever.__init__` hardcodes an in-memory `chromadb.Client`, so the
    evolved store otherwise dies with the process. The diagnostic persisted run
    established that A-MEM did change links, tags, and context, but not the
    `content` field consumed by the prompt path.

    It is opt-in because persisting changes isolation semantics: a re-run with
    the same (condition, seed, tag) reuses the collection on disk rather than
    starting from empty, so `add_note()` would evolve notes against an already
    populated neighbourhood. That is a different experiment. Pass a fresh
    directory per run, or delete it between runs.
    """
    import chromadb
    from agentic_memory.memory_system import AgenticMemorySystem
    from agentic_memory.retrievers import ChromaRetriever
    from chromadb.config import Settings

    spec = resolve("memory_controller")
    system = AgenticMemorySystem(
        llm_backend=spec.backend,
        llm_model=spec.model,
        evo_threshold=evo_threshold,
        api_key=None if spec.backend == "ollama" else api_key(),
    )
    _install_controller(system, spec)

    name = collection_name(condition, seed, tag)
    retriever = ChromaRetriever(collection_name=name, model_name=system.model_name)

    if persist_dir is not None:
        # Swap the client after construction, same tactic as the collection-name
        # fix above: the vendored source stays untouched and reviewable. The
        # throwaway in-memory collection built by __init__ is discarded here.
        persist_dir.mkdir(parents=True, exist_ok=True)
        retriever.client = chromadb.PersistentClient(
            path=str(persist_dir), settings=Settings(allow_reset=True))
        retriever.collection = retriever.client.get_or_create_collection(
            name=name, embedding_function=retriever.embedding_function)

    system.retriever = retriever
    system.memories = {}
    return system, name, spec
