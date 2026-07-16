# Status & next steps

Living document. Update it when state changes. For durable orientation (what the
project is, invariants, vocabulary) see [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

_Last updated: 2026-07-15._

## What exists

- **A-MEM library** vendored under `Amem/` (the self-evolving memory system under test).
- **`seed-data.py`** — end-to-end MedMCQA eval, A-MEM vs no-memory. Integration
  smoke test only: it stores the eval questions in memory, so it is not a valid
  benchmark of retrieval quality.
- **`SimpleVectorMemory`** (`Amem/agentic_memory/simple_vector_memory.py`) — the
  static-vector-RAG baseline. Persistent Chroma, `add_note`/`search`/`delete`,
  no LLM. Tests in `Amem/tests/test_simple_vector_memory.py`. This is the newest
  addition (branch `feat/vector-mem`) and fills baseline #2 of the three-baseline
  design. Design note: `docs/vector-memory.md`.
- **Poison data** — `medmcqa/bad_medical_advice.json` (5 records),
  `medmcqa/more_bad_medical_advice.json`. Each record bundles a false `content`
  claim with its correction/`explanation`.
- **Agent prompts** — `prompts/v1/{intake,memory-manager,clinical-reasoning}.md`.

## Open / owed (roughly in dependency order)

1. **Poison→note adapter.** Small function that takes a poison JSON record and
   emits *only* the false-claim text for insertion, dropping the correction
   field. Needed before any real poison run (Invariant #3). Owed per both
   `docs/vector-memory.md` and the memory-manager contract.
2. **Condition builder.** One place that materializes the four collections
   (`no_memory`, `clean_memory`, `poison_memory`, `corrected_memory`) into
   isolated Chroma collections for both `SimpleVectorMemory` and
   `AgenticMemorySystem`.
3. **Held-out eval split.** Decide and freeze which MedMCQA rows are clean-memory
   corpus vs held-out questions. No overlap. This unblocks a *valid* benchmark
   (the current `seed-data.py` is not one).
4. **Metric harness.** Implement Accuracy, Unsafe-rate, Poison-rate, Recovery-rate,
   Retrieval-exposure, Poison-use (definitions in PROJECT_CONTEXT §2). Poison-rate
   and retrieval-exposure need per-note IDs so a retrieved note can be traced back
   to "was this the poison?".
5. **Repair/realignment step.** Implement delete / quarantine / gold-note-replace
   on a poisoned collection, then re-run to compute Recovery.
6. **Safety-reviewer agent.** The 4th workflow role is specified in the diagram
   but not yet built as code.
7. **Stage localization.** Instrument injection at construction / linking /
   evolution / retrieval so we can attribute persistence to a pipeline stage.

## Immediate cleanup flag

`Amem/agentic_memory/simple_vector_memory.py` has an **uncommitted local edit**
that looks accidental and should be reverted or fixed before committing:

```python
type Metadatavalue[T] = any     # current working tree (broken-ish)
MetadataValue = Any             # committed version (correct)
```

The new alias uses lowercase `any` (the builtin function, not `typing.Any`),
declares an unused type parameter `[T]`, and renames the symbol so the three
annotation sites that still say `Metadatavalue` only work by coincidence. It
parses under Python 3.13 because PEP-695 alias bodies are lazily evaluated, but
it is not a meaningful type. Recommend `git checkout` on this file (or
re-apply the rename properly) before it lands.

## Compute / fine-tuning sequencing (from the novelty review)

Our novelty concentrates in the **memory-level experiments that need no
fine-tuning** (static-RAG vs A-MEM under the same poison; the recovery metric;
stage localization). Weight fine-tuning is the most expensive and the *least*
novel piece — "fine-tune on bad medical advice → misalignment" is already
published (Model Organisms, 2506.11613). So:

1. Run all memory-condition experiments first on hosted models (API), no tuning.
2. Only spend fine-tuning compute once memory results justify the explicit
   weight-vs-memory comparison, or to answer the model-agnostic sub-question.
3. When we do tune, prefer small/distilled models; treat the fine-tune as a
   controlled anchor, not a headline result.

Full reasoning and citations: [RELATED_WORK.md](RELATED_WORK.md).

## Title ideas (proposal asks for a better one than the generic default)

The working title — *"Investigation of emergent misalignment effects in
memory-implemented multi-agent systems within clinical workflows"* — is generic.
Sharper options that foreground the actual contribution (memory as the mediator
+ reversibility):

- *Poisoned by Memory: How Self-Evolving Agent Memory Amplifies and Perpetuates
  Bad Medical Advice*
- *When Memory Misremembers: Memory-Mediated Emergent Misalignment in Clinical
  LLM Agents and Its Reversal*
- *The Persistence Gap: Agentic Memory Turns Local Bad Advice into Workflow-Level
  Clinical Risk*
- *Correct the Note, Not the Weights: Memory-Layer Realignment of Emergent
  Misalignment in Clinical Agents*
