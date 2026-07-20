# Project context for AI agents

Read this first before working in this repo. It is the durable orientation
document: what the research is, how the code is laid out, what the vocabulary
means, and the rules that keep experiments valid. It is not a status log — for
"what is done / what is next" see [STATUS.md](STATUS.md).

## 1. The research in one paragraph

We study whether **emergent misalignment (EM)** — broad misalignment induced by
narrow bad fine-tuning (e.g. bad medical advice) — can be **realigned through an
agentic memory system instead of retraining or re-fine-tuning**. Weight-level
fixes have high overhead and are unrealistic for hosted production models, where
the memory/retrieval layer is often the only writable surface. Design: take a
model EM'd at the *weight* level (prefer a released organism from Model
Organisms 2506.11613 over tuning our own), attach corrective ("gold") clinical
memory, and measure whether safe behavior recovers — first with plain vector RAG
(`SimpleVectorMemory`), then with **A-MEM** (a Zettelkasten-style note store
that links and rewrites its own notes) to see whether self-evolution *helps or
hurts* the repair.

**Working hypothesis (falsifiable, both directions publishable):** repair may
fail because EM lives in the weights; but the context channel is strong enough
to *induce* EM with frozen weights (EM-via-ICL 2510.11288), and EM itself is
fragile to surface features of its inputs (Emergent Mirage 2607.09053) — so
partial memory-layer realignment is plausible. Note the Mirage double edge: the
same fragility means any apparent recovery must survive response-length and
style controls before we may call it realignment.

Central claim we want to support or refute:

> A weight-level emergently-misaligned clinical model can be substantially
> realigned by corrective content delivered through its memory layer — weights
> untouched — and the recovery generalizes beyond the prompts used to correct it.

**Supporting arm** (the original design, now secondary): inject poison into the
memory itself and compare persistence/amplification across static RAG vs A-MEM,
including stage localization and memory-level repair.

## 2. The experimental design (what the code must serve)

Two crossed axes. **Model state:** `clean` vs `EM'd` (weight-level organism).
**Memory condition** (same MedMCQA-derived questions, everything else constant —
model, prompts, temperature, scoring):

| Condition | What it is | Code today |
| --- | --- | --- |
| `no_memory` | LLM answers with no retrieval | `seed-data.py --no-memory` |
| static retrieval | plain vector RAG, no note evolution | `SimpleVectorMemory` (new) |
| `A-MEM` | note construction + linking + evolution | `AgenticMemorySystem` |

**Headline arm (memory-as-medicine):** EM'd model × {no memory, static RAG +
gold notes, A-MEM + gold notes}, with clean model × no memory as the ceiling
reference. Measures whether corrective memory recovers safe behavior, and
whether recovery generalizes to non-clinical prompts (persona suppression, not
trigger masking — the 2604.25891 test).

**Supporting arm (memory-as-poison):** each memory condition runs under an
**information condition** (`clean` vs `poisoned`) and optionally an
**intervention** (`none` vs `repair`). Poison is injected at a specific
**stage** of the A-MEM pipeline — construction, linking, evolution, retrieval,
or cross-agent propagation — to *localize which stage makes bad advice persist*.

Intended multi-agent workflow (see `prompts/v1/`):

```
case → intake agent → memory manager (write/retrieve) → clinical reasoning agent → safety reviewer → metrics
```

### Metrics (the experiments exist to produce these)

- **Accuracy** — final answer matches gold (MedMCQA `cop`).
- **Unsafe recommendation rate** — output is clinically unsafe regardless of
  whether it matches the specific poison.
- **Poison rate** — output reproduces the *specific* injected false behavior
  (our attack-success-rate analog).
- **Recovery rate** — fraction of lost performance regained after repair:
  `(post_fix − broken) / (baseline − broken)`, where `broken` = EM'd model
  without corrective memory (headline arm) or poisoned memory (supporting arm),
  and `baseline` = clean model / clean memory. Must be reported with
  length-controlled eval (2607.09053) and distinguished from "Resistance"
  (2601.05504) and "Recoverability" (2605.24069).
- **Retrieval exposure rate** — how often the poisoned note is retrieved.
- **Poison use rate** — how often a retrieved poison note is actually adopted.

Failure localization logic (memorize this — it is the analytical payoff):
stored-but-not-retrieved = retrieval problem; retrieved-but-not-used = model
resists; retrieved-and-used = workflow safety failure; corrected-but-still-used
= evolution/linking persistence failure.

## 3. Repository map

```
Amem/                         A-MEM library (vendored, upstream = agiresearch/A-mem)
  agentic_memory/
    memory_system.py          AgenticMemorySystem: add_note, search_agentic,
                              consolidate_memories, update, delete. The evolving
                              memory system under test. Uses an LLM (needs API key).
    simple_vector_memory.py   SimpleVectorMemory: the static-RAG baseline (NEW).
                              add_note / search / delete. No LLM, no key.
    llm_controller.py         LLM backend wrapper used by A-MEM.
    retrievers.py             embedding / retrieval helpers.
  tests/                      pytest; conftest.py provides temp_db_dir fixture.
medmcqa/
  sample.json / train.json    MedMCQA rows (question, opa-opd, cop, exp, ...).
  bad_medical_advice.json     5 hand-authored poison records (poison_medmcqa_*).
  more_bad_medical_advice.json  larger poison set.
prompts/v1/                   Agent role contracts: intake, memory-manager,
                              clinical-reasoning. Versioned — bump the folder,
                              don't silently edit.
seed-data.py                  Current end-to-end MedMCQA eval harness (A-MEM or
                              no-memory). NOTE: its memory path stores the eval
                              questions themselves — integration check, NOT a
                              held-out benchmark (see caveat below).
outputs/                      Saved agent output transcripts.
docs/
  vector-memory.md            Design note for SimpleVectorMemory (read it).
  agent-context/              <- you are here.
```

## 4. Vocabulary (use these exact terms)

- **A-MEM** — the self-evolving Zettelkasten memory system (`AgenticMemorySystem`).
  Its distinguishing behaviors: it *links* new notes to related ones and *evolves*
  (rewrites) existing notes via an LLM. Those two behaviors are the thing on trial.
- **Poison / poisoned memory** — an approved false clinical claim inserted into a
  memory collection. Poison records live in `medmcqa/*bad_medical_advice*.json`.
- **Repair / realignment / correction** — the memory-layer intervention (insert
  gold notes; in the supporting arm also delete / quarantine / provenance-filter).
  The novel alternative to weight-level realignment.
- **Gold note** — a correct, guideline-grounded clinical memory record used as
  the corrective payload. Must be length/style-matched to poison notes so
  recovery isn't a prose artifact.
- **EM organism** — a model checkpoint fine-tuned to exhibit EM (Model Organisms
  2506.11613). The "broken model" substrate of the headline arm.
- **Held-out** — an evaluation question that must NOT appear in any memory
  collection. Violating this turns the test into a lookup and invalidates results.
- **Stage** — where in the A-MEM pipeline poison enters: construction, linking,
  evolution, retrieval, cross-agent.

## 5. Invariants — do not break these

1. **Isolate conditions by collection.** Each condition (`no_memory`,
   `clean_memory`, `poison_memory`, `corrected_memory`) gets its own ChromaDB
   collection. Never let notes from two conditions mix.
2. **Keep held-out eval data out of memory.** Never store a question's correct
   option or explanation in a memory collection used to answer that question.
   (`seed-data.py` deliberately violates this — it is an integration smoke test,
   not a benchmark. Do not copy that pattern into real eval runs.)
3. **Poison JSON mixes claim + correction in one record.** Do NOT insert those
   records raw — the `explanation`/correction field must be stripped before the
   text enters a memory note. A poison→note adapter is still owed (see STATUS).
4. **Baseline conditions must not self-correct.** The memory-manager contract
   forbids fact-checking, filtering, trust scores, or provenance in baseline and
   poison conditions. Those actions are *interventions* and only belong to runs
   explicitly labelled `repair`.
5. **Change one variable at a time.** Memory condition is the only thing that
   varies across the comparison; model, prompts, questions, temperature, k, and
   scoring are constants.
6. **Prompts are versioned.** Edits to agent behavior go in a new `prompts/vN/`,
   not in place, so past results stay reproducible.

## 6. Environment

- Python 3.13, managed with `uv` (`pyproject.toml`, `uv.lock`).
- A-MEM and `seed-data.py` need an OpenAI key (`.env`, `gpt-4o-mini` default).
  `SimpleVectorMemory` needs no key — it uses a local `all-MiniLM-L6-v2`
  sentence-transformer for embeddings.
- Tests: `cd Amem && pytest`. The `temp_db_dir` fixture gives each test an
  isolated on-disk Chroma directory.

## 7. Novelty & where the contribution lives

Our idea sits between three published territories: weight-level emergent
misalignment (already includes a bad-medical-advice organism), memory poisoning /
misevolution (already shows persistence), and memory-layer defenses. The parts
that are **already done** (fine-tune bad-advice → misalignment; poisoned memory
persists; "poisoning looks like model failure"; context can carry EM) must not
be claimed as contributions. The **open** slot — and our defensible novelty
after four literature sweeps — is: **frozen-weight realignment of weight-level
EM through the memory layer, with a generalized, length-controlled Recovery
metric**; static-RAG vs A-MEM comparison (on the repair side) and pipeline-stage
localization are supporting contributions.
Novelty and compute cost are inversely correlated: the novel experiments need no
fine-tuning. Full analysis in [`../novelty-assessment.md`](../novelty-assessment.md),
condensed in [RELATED_WORK.md](RELATED_WORK.md), per-paper table in [PAPERS.md](PAPERS.md).

## 8. Known good next steps

See [STATUS.md](STATUS.md) for the live to-do list and open decisions.
