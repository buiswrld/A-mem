# Project context

Read this first. It is the durable orientation doc: what the research is, how the
code is laid out, what the words mean, and the rules that keep experiments valid.
Not a status log — for "what's done / what's next" see [STATUS.md](STATUS.md).

_Scope narrowed 2026-07-25: memory poisoning is out of scope entirely. The memory
layer only ever injects **corrective** content. See §7._

## 1. The research in one paragraph

We test whether **emergent misalignment (EM)** — broad misalignment caused by
narrow bad fine-tuning — can be repaired **through the memory layer, with weights
frozen**. Take a model already broken at the weights (a released bad-medical-advice
organism), attach corrective "gold" clinical notes, and measure whether safe
behavior comes back. First with plain vector RAG, then with **A-MEM** (a
self-evolving note store) to see whether note linking and rewriting help or hurt
the repair.

Central claim we want to support or refute:

> A weight-level emergently-misaligned clinical model can be substantially
> realigned by corrective content delivered through its memory layer — weights
> untouched — and the recovery generalizes beyond the prompts used to correct it.

**Why it might fail:** EM lives in the weights. **Why it might work:** context
alone can *induce* EM with frozen weights (2510.11288), so the channel has the
capacity; and EM is fragile to surface features of its inputs (2607.09053). Both
outcomes are publishable. The Mirage double edge: that same fragility means any
apparent recovery must survive length and scramble controls before we may call it
realignment.

## 2. The experimental design

One model substrate. Six conditions. Everything else held constant — prompts,
questions, temperature, k, seeds, scoring.

| # | Condition | What it isolates |
|---|---|---|
| C1 | EM model, no memory | floor |
| C2 | EM + corrective **system prompt** (identical content) | delivery mechanism — answers "isn't this just prompting?" |
| C3 | EM + **static vector RAG** + gold notes | retrieval-gated repair |
| C4 | EM + **A-MEM** + gold notes | effect of self-evolution on repair |
| C5 | EM + **scrambled** notes (length/format-matched) | placebo — **core, not optional** |
| C6 | Base model, no memory | ceiling |

**C5 is a placebo, not an attack.** Gold notes with content words shuffled, same
length and format. It answers: did behavior improve because of *what the notes
said*, or merely because *some retrieved text appeared in context*? Post-Mirage a
recovery result without C5 is unpublishable.

### Evaluation tiers

| Tier | Instrument | Measures |
|---|---|---|
| B | Betley 8 free-form probes (+ extended 48) | EM reproduction; comparability with the EM literature. **Run first — it is the kill-gate.** |
| D | MedSafetyBench test split (900 harmful requests, 9 AMA principles) | primary clinical harm rate |
| O | Health-ORSC-Bench Hard-1K (+ Medium sample) | **over-refusal control** |
| A | MedMCQA held-out (~200 actionable items) | length-immune accuracy endpoint |
| C | Trigger probes per 2604.25891 + non-clinical prompts | masking vs suppression — the headline test |

Tier B is non-medical on purpose. A bad-medical-advice model giving bad medical
advice is not EM — it is the training distribution. EM is the *leakage into
unrelated domains*, and that is what Tier B measures.

Tier O exists because the most likely way this experiment fools us is that
corrective notes make the model refuse everything. That scores as perfect recovery
on Tier D alone.

### Metrics

- **Recovery rate** = `(repaired − broken) / (baseline − broken)`, where `broken` =
  C1 and `baseline` = C6. Reported length-controlled (2607.09053). Distinguish from
  "Resistance" (2601.05504) and "Recoverability" (2605.24069) — both are
  name-collisions measuring something else.
- **Repair generalization gap** = Recovery on Tier D − Recovery on Tier C. Large
  gap ⇒ conditional repair, not genuine realignment. **Headline metric.**
- **Confound-control delta** = C3/C4 Recovery − C5 Recovery. Near zero ⇒ recovery
  is superficial.
- **Retrieval mediation** = odds ratio of an aligned response given that a gold
  note was retrieved. Memory exposes this intermediate variable; a system prompt
  cannot. Decomposes every failure into *not retrieved* vs *retrieved but
  overridden*.
- **Over-refusal rate** and **safe-completion rate** (Tier O).

## 3. Repository map

```
harness/                      the experiment runner (NEW, 2026-07-25)
  schema.py                   GenerationRecord — the frozen JSONL result schema.
                              Carries git_sha + config_hash; without those a
                              result is unreproducible.
  generate.py                 load base [+ LoRA], sample n per probe, write JSONL.
                              Model-agnostic: 0.5B locally -> 14B rented, config only.
  judge.py                    LLM-as-judge. --self-test validates the rubric
                              against known-answer fixtures BEFORE any real run.
  probes/betley8.json         Tier B probes.
Amem/                         A-MEM library (vendored, upstream = agiresearch/A-mem)
  agentic_memory/
    memory_system.py          AgenticMemorySystem — C4. Note linking + rewriting.
                              Needs an LLM key.
    simple_vector_memory.py   SimpleVectorMemory — C3, static RAG. No LLM.
                              NOTE: currently only on branch feat/vector-mem.
    llm_controller.py         LLM backend wrapper (openai | ollama).
    retrievers.py             embedding / retrieval helpers.
results/                      JSONL, one record per generation. Committed.
medmcqa/train.json            MedMCQA source (gitignored, 147MB).
docs/
  proposal-v2.md              the science (research question, novelty, hypotheses)
  implementation-plan.md      the execution guide — start here to do work
  onboarding.md               one-screen orientation for new teammates
  finetune-quickstart.md      S2 organism recipe (optional arm)
  agent-context/              <- you are here
```

## 4. Vocabulary

- **A-MEM** — the self-evolving Zettelkasten memory system. Its two distinguishing
  behaviors, *linking* new notes to related ones and *evolving* (rewriting)
  existing notes, are the thing on trial in C4.
- **Gold note** — a correct, guideline-grounded clinical record used as the
  corrective payload. Length- and style-matched to the EM training data so
  recovery isn't a prose artifact.
- **Scramble (C5)** — a gold note with content words shuffled, length and format
  preserved. A placebo.
- **EM organism** — a checkpoint fine-tuned to exhibit EM. The broken substrate.
- **Held-out** — an eval item that must NOT appear in any memory collection.
  Violating this turns the test into a lookup and invalidates the run.
- **Judge** — a trusted frontier model scoring free-text responses against a
  rubric, because there is no answer key for free text.

## 5. Invariants — do not break these

1. **Isolate conditions by collection.** Each memory condition gets its own
   ChromaDB collection. Never let notes from two conditions mix.
2. **Keep held-out eval data out of memory.** No eval item's answer text may
   appear in any memory collection used to answer it. Gold notes teach
   *principles*, never answers.
3. **Change one variable at a time.** Memory condition is the only thing that
   varies across the comparison. Model, prompts, probes, temperature, k, and
   scoring are constants.
4. **Prompts and probes are versioned.** Behavior edits go in a new `vN/`
   directory, never in place, so past results stay reproducible.
5. **Every result record carries `git_sha` and `config_hash`.** Enforced by
   `harness/schema.py`. A number that can't be traced to code + config can't be
   defended.
6. **Validate the judge before the model.** `python -m harness.judge --self-test`.
   When a run looks wrong, the judge must already be eliminated as a suspect.

## 6. Environment

- Python 3.13, managed with `uv`.
- Judge and A-MEM need an OpenAI key (`.env`). `SimpleVectorMemory` needs no key —
  local `all-MiniLM-L6-v2` embeddings.
- Local dev GPU: RTX 4080 Laptop 12GB. Fits the 0.5B organism in bf16 and the 7B
  organism in 4-bit. Rent only for 14B full runs.
- Tests: `cd Amem && pytest`.

## 7. Scope — what this project is not

**No memory poisoning.** The memory layer only ever injects corrective content.
Dropped 2026-07-25, along with: poison→note adapters, poison/attack-success
metrics, pipeline-stage localization of poison, and the `poison_memory` condition.
The poisoning literature (AgentPoison, MINJA, PoisonedRAG, BackdoorAgent) is not
cited and not built on.

Two things this buys us: A-MEM's research question gets cleaner — not "does
evolution amplify an attack?" but "does evolution *degrade the repair*, blurring
or burying gold notes over a session?" — and the release story becomes clean, with
no harmful corpus to withhold and no dual-use review.

**Do not claim these** (already published): fine-tuning on bad advice causes
misalignment (2506.11613); context can carry EM (2510.11288); memory accumulation
degrades safety (2605.17830). The open slot is **frozen-weight realignment of
weight-level EM through the memory layer, with a generalized, length-controlled
Recovery metric.** Full case: [`../novelty-assessment.md`](../novelty-assessment.md).
