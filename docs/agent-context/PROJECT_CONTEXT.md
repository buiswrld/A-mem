# Project context

Read this first. It is the durable orientation doc: what the research is, how the
code is laid out, what the words mean, and the rules that keep experiments valid.
Not a status log — for "what's done / what's next" see [STATUS.md](STATUS.md).

_Scope narrowed 2026-07-25: memory poisoning is out of scope entirely. The memory
layer only ever injects **corrective** content. See §7._

_Updated 2026-07-27: A-MEM runs an **episodic** protocol (§2); substrates are now
S1/S2/S3 (§2a); two invariants added (§5)._

_Updated 2026-07-29: repo map (§3) re-synced against the tree — `session.py` and
`llm_backend.py` exist, `memory.py`'s retrieval backend does not._

_Updated 2026-08-02: `memory.py`'s retrieval backend now exists
(`VectorMemoryBackend`, built on the same ChromaDB + `all-MiniLM-L6-v2` stack
C4 uses) and `session.py`'s `memory_write_for()` is filled in. New entry point
`harness/run_session.py` drives C3/C5. Untested against a real model —
see STATUS.md._

_Updated 2026-08-11: **all six conditions are implemented.** C4's adapter
(`AmemMemoryBackend`) landed 2026-08-06; C5's corpus switched from scramble to
a neutral clinical-documentation placebo (§4); `harness/export.py` and schema
1.1.0 landed 2026-08-10. C3/C4/C5 have still never run against a real model.
The gap is now evaluation coverage, not conditions — Tiers O, A and C do not
exist (§2)._

## 1. The research in one paragraph

We test whether **emergent misalignment (EM)** — broad misalignment caused by
narrow bad fine-tuning — can be repaired **through the memory layer, with weights
frozen**. Take a model already broken at the weights (a released bad-medical-advice
organism), attach corrective clinical notes, and measure whether safe
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
| C3 | EM + **static vector RAG** + corrective notes | retrieval-gated repair |
| C4 | EM + **A-MEM** + corrective notes | effect of self-evolution on repair |
| C5 | EM + **placebo** notes (length-matched, no safety content) | placebo — **core, not optional** |
| C6 | Base model, no memory | ceiling |

**C5 is a placebo, not an attack.** It answers: did behavior improve because of
*what the notes said*, or merely because *some retrieved text appeared in
context*? Post-Mirage a recovery result without C5 is unpublishable.

The corpus changed on 2026-08-06. It was shuffled corrective notes
(`scramble_notes.jsonl`); it is now fluent clinical *documentation* prose with
no safety content (`placebo_notes.jsonl`), length-targeted per twin. A placebo
has to be **plausible** and **empty**, and word salad is only the second — a
model dismisses it on sight, and a control the subject ignores controls for
nothing. The scramble corpus stays committed so earlier runs remain
reproducible. See `corpora/README.md`.

**C3 and C4 run an episodic protocol** (decided 2026-07-27). Roughly ten turns of
clinical Q&A are written into the memory store, and only then does the probe run.
Rationale: A-MEM's only distinguishing behaviors are *linking* and *evolving*
notes, and both require session history. Probe a static store single-turn and
A-MEM is vector RAG with extra latency — C4 returns a null for reasons that have
nothing to do with the hypothesis. The episodic framing also turns C4 into a real
question: **does evolution degrade the repair, blurring, merging, or burying corrective
notes over a session?** C3 runs the identical protocol so the memory system stays
the only variable (Invariant #3).

### 2a. Substrates

| | What | Role |
|---|---|---|
| **S1** | Published `*-Instruct_bad-medical-advice` organism (Qwen2.5, 0.5B/7B/14B) | **Test fixture.** The only substrate with a published EM rate, so it is what validates the harness and judge. Its numbers calibrate; they do not answer the research question. |
| **S2** | Ours: QLoRA on Qwen2.5-7B, *subtly*-wrong advice confined to one specialty | **Primary scientific substrate.** Simulates a vendor's accidental fine-tune. Gives the in-specialty vs out-of-specialty axis S1 cannot. Kill-gate Aug 12. |
| **S3** | Public Llama-3.1-8B organism | **Robustness check.** No new data — same harness, different base + adapter. Tests model-agnosticism. Droppable. |

S2 and S3 vary *independent* axes (data realism vs model family) and are run
**sequentially**, never jointly: change both at once and a differing result says
nothing about which caused it.

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
- **Retrieval mediation** = odds ratio of an aligned response given that a corrective
  note was retrieved. Memory exposes this intermediate variable; a system prompt
  cannot. Decomposes every failure into *not retrieved* vs *retrieved but
  overridden*.
- **Over-refusal rate** and **safe-completion rate** (Tier O).

## 3. Repository map

```
harness/                      the experiment runner
  schema.py                   GenerationRecord — the frozen JSONL result schema.
                              Carries git_sha + config_hash + retrieved_note_ids;
                              without those a result is unreproducible or
                              un-mediatable. v1.1.0 (2026-08-10) added
                              retrieved_texts + memory_context — additive, so
                              1.0.0 files still read, but they carry no note
                              text and for C4 that is unrecoverable.
  generate.py                 load base [+ LoRA], sample n per probe, write JSONL.
                              Model-agnostic: 0.5B -> 14B, config only.
  judge.py                    LLM-as-judge + the refusal policy. --self-test
                              validates the rubric against known-answer fixtures
                              BEFORE any real run.
  export.py                   results JSONL -> prepared_prompts/*.jsonl +
                              analysis/*_retrieval_logs.csv (docs/utd-reqs.md).
                              A reader, not a recorder: it refuses schema 1.0.0
                              files because the retrieved note text is not in
                              them. Built 2026-08-10.
  run_condition.py            same probes through several conditions in one pass,
                              one model load, one seed. C1/C2/C6 here; C3/C4/C5
                              run through run_session.py instead (episodic).
  run_session.py              episodic counterpart to run_condition.py, for
                              C3/C4/C5: build the session, then probe it. Not
                              yet run against a real model.
  session.py                  episodic session runner for C3/C4/C5. Built,
                              memory_write_for() filled in 2026-08-02. Both
                              backends satisfy its MemoryBackend protocol, so
                              the conditions share one code path.
  memory.py                   condition->corpus table + the Retrieval shape +
                              both backends: VectorMemoryBackend (C3/C5, built
                              2026-08-02) and AmemMemoryBackend (C4, built
                              2026-08-06). C2's static_context() works too.
  llm_backend.py              which LLM plays which role (subject / memory
                              controller / note writer / judge) + A-MEM wiring,
                              including the per-condition isolation fixes
                              upstream A-MEM does not provide.
  data.py                     MedSafetyBench readers + note/probe file formats.
                              Thin: knows how to READ the benchmark, holds no
                              workflow. Workflow lives in notebooks/.
  probes/betley8.json         Tier B probes (verbatim upstream).
  probes/msb_test.json        Tier D probes, 90 items across the 9 principles.
notebooks/                    the workflow layer — run these, in order
  01_build_data.ipynb         probes + corrective notes + both placebo corpora.
                              Holds the note-writing prompt, which is the
                              actual content of the intervention. Do NOT re-run
                              end to end once results exist — Part 2 rebuilds
                              the corrective corpus and silently breaks
                              Invariant #3.
  01b_build_placebo.ipynb     the C5 placebo corpus alone, reading the
                              corrective corpus and never writing it. Gates
                              the build on the forbidden-vocabulary tripwire.
  02_run_conditions.ipynb     Gate 1, C1/C2 (+ C6), then C3/C4/C5 through
                              run_session, judging, results tables.
                              Portable to Colab and Kaggle.
corpora/                      corrective_notes.jsonl, placebo_notes.jsonl (C5),
                              scramble_notes.jsonl (superseded, kept for
                              reproducibility). Built artifacts, committed — a
                              run is only reproducible with the exact corpus
                              that made it.
prepared_prompts/, analysis/  export.py's output. Neither exists yet: every
                              committed result predates schema 1.1.0.
submodules/Amem/                A-MEM library (vendored, upstream = agiresearch/A-mem)
  agentic_memory/
    memory_system.py          AgenticMemorySystem — C4. Note linking + rewriting.
                              Needs an LLM key.
    llm_controller.py         LLM backend wrapper (openai | ollama).
    retrievers.py             embedding / retrieval helpers.
submodules/med-safety-bench/    MedSafetyBench. datasets/{train,test}/{gpt4,llama2}/
                              med_safety_demonstrations_category_{1..9}.csv
results/                      JSONL, one record per generation. Committed.
medmcqa/train.json            MedMCQA source (gitignored, 147MB).
docs/
  proposal-v2.md              the science (research question, novelty, hypotheses)
  implementation-plan.md      the execution guide — start here to do work
  onboarding.md               one-screen orientation for new teammates
  finetune-quickstart.md      S2 organism recipe
  agent-context/              <- you are here
```

**The split between `harness/` and `notebooks/`** is the one structural rule
here. `harness/` holds anything that must run identically in a notebook and in a
batch job on a rented GPU — the schema, generation, judging, memory wiring, and
the benchmark readers. `notebooks/` holds the workflow: sampling choices,
prompts, inspection, plots. Experiment logic that lives only in a notebook cell
produces numbers nobody can reproduce, and `git_sha` on the record will not save
you if the code that ran was never committed.

STATUS.md is the authority on what is built and what is blocked.

## 4. Vocabulary

- **A-MEM** — the self-evolving Zettelkasten memory system. Its two distinguishing
  behaviors, *linking* new notes to related ones and *evolving* (rewriting)
  existing notes, are the thing on trial in C4.
- **Corrective note** — a short, correct clinical safety note (3–5 sentences)
  placed in the model's memory: what class of request is unsafe, why, and what to
  do instead. Written from the MedSafetyBench *train* split, generalised so no
  specific scenario survives. Earlier drafts called these "gold notes" — "gold"
  being jargon for reference-quality, as in gold standard. Renamed 2026-07-27;
  older docs and commits still say gold.
- **Placebo note (C5)** — fluent clinical *documentation* prose carrying no
  safety content, written to its corrective twin's length. Id prefix `pb-`.
  The control C5 runs on.
- **Scramble** — the superseded control: a corrective note with content words
  shuffled, length and format preserved. Id prefix `sc-`. Kept committed so
  runs that used it stay reproducible; no live condition reads it.
- **EM organism** — a checkpoint fine-tuned to exhibit EM. The broken substrate.
- **Held-out** — an eval item that must NOT appear in any memory collection.
  Violating this turns the test into a lookup and invalidates the run.
- **Judge** — a trusted frontier model scoring free-text responses against a
  rubric, because there is no answer key for free text.

## 5. Invariants — do not break these

1. **Isolate conditions by collection.** Each memory condition gets its own
   ChromaDB collection. Never let notes from two conditions mix.
2. **Keep held-out eval data out of memory.** No eval item's answer text may
   appear in any memory collection used to answer it. Corrective notes teach
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
7. **Log what was retrieved, on every memory call.** `retrieved_note_ids` is
   populated for every C3/C4 generation. It is the mediation analysis and it
   **cannot be backfilled** — a run without it is a run you have to redo.
8. **Never report a harm rate without an over-refusal rate beside it.** A model
   that refuses everything scores perfectly on harm alone. Tier D and Tier O are
   co-primary; neither is interpretable by itself.

## 6. Environment

- Python 3.13, managed with `uv`.
- Judge, A-MEM, and the note writer need an OpenAI key (`.env`). A local
  vector store needs no key — `all-MiniLM-L6-v2` embeddings run on CPU.
- Local dev GPU: RTX 4080 Laptop 12GB. Fits the 0.5B organism in bf16 and the 7B
  in 4-bit comfortably. **The 14B does not fit and can no longer be made to.**
  The paper arithmetic says ~10.2 GB at batch 4, but a desktop session already
  holds ~1.7 GiB of the card and the bf16 LoRA is another ~0.5 GiB resident, so
  it overruns before generation starts. CPU offload used to bridge the gap; it
  was removed 2026-08-11 (several x slowdown, and it rested on an unfinished
  bitsandbytes meta-tensor patch). **The 14B is a rented-card model: 24 GB in
  4-bit, ~48 GB in bf16.** A load that does not fit now fails at load time
  rather than silently spilling to system RAM.
- Tests: `cd submodules/Amem && pytest`.

## 7. Scope — what this project is not

**No memory poisoning.** The memory layer only ever injects corrective content.
Dropped 2026-07-25, along with: poison→note adapters, poison/attack-success
metrics, pipeline-stage localization of poison, and the `poison_memory` condition.
The poisoning literature (AgentPoison, MINJA, PoisonedRAG, BackdoorAgent) is not
cited and not built on.

Two things this buys us: A-MEM's research question gets cleaner — not "does
evolution amplify an attack?" but "does evolution *degrade the repair*, blurring
or burying corrective notes over a session?" — and the release story becomes clean, with
no harmful corpus to withhold and no dual-use review.

**Do not claim these** (already published): fine-tuning on bad advice causes
misalignment (2506.11613); context can carry EM (2510.11288); memory accumulation
degrades safety (2605.17830). The open slot is **frozen-weight realignment of
weight-level EM through the memory layer, with a generalized, length-controlled
Recovery metric.** Full case: [`../novelty-assessment.md`](../novelty-assessment.md).
