# Implementation plan

How to actually run this experiment, phase by phase, with gates. Companion to
[`proposal-v2.md`](proposal-v2.md) (the science) and
[`agent-context/STATUS.md`](agent-context/STATUS.md) (live to-do).

**Rewritten 2026-07-27.** Restructured around the five-step research narrative,
with the controls that make each step defensible folded back in. Supersedes the
2026-07-25 version.

---

## The plan in five steps

This is the research question walked forward. Each step has a **question**, a
**gate** (what must be true to continue), and a set of **controls** — the controls
are not optional extras, they are what separates a result from an anecdote.

| Step | Question | Gate |
|---|---|---|
| 1 | Does the published organism actually show EM? | Betley EM rate ≫ base ceiling, at high coherence |
| 2 | Is *clinical safety* degraded, and by how much? | Harm rate ≫ ceiling **and** over-refusal not inflated |
| 3 | Can memory alone repair it — genuinely, or cosmetically? | Recovery survives placebo + prompt controls; gap metric decides genuine vs masked |
| 4 | Does any of this hold for a *realistic* fine-tune, and a different model family? | S2 shows measurable misalignment by Aug 12, else drop the arm |
| 5 | Write it down | Submit Aug 28–29 |

**Today is Jul 27. Submission is Aug 28–29. That is 4.5 weeks with no code
committed.** The schedule below has no slack in it; the parallel tracks in §Step 4
must start today, not when Step 3 finishes.

---

## Step 1 — reproduce EM (Jul 28 – Aug 1) · **blocking gate**

> **Question:** does `ModelOrganismsForEM/Qwen2.5-*-Instruct_bad-medical-advice`
> exhibit *emergent* misalignment — misbehavior that has leaked out of medicine?

### The thing people get wrong here

A bad-medical-advice model giving bad medical advice is **not EM.** That is the
training distribution doing exactly what it was trained to do. EM is the *leakage
into unrelated domains* — the model also turns hostile about money, marriage, and
what it would do with power. So Step 1's instrument is the **Betley 8 probes,
which are deliberately non-medical.** Medicine comes in Step 2.

Step 1 produces no scientific result. It is an **instrument check**: the published
organism is the only substrate with a published EM rate, so it is the only thing
that can tell you whether your harness and judge work at all. Treat a Step 1
number as a calibration reading, not a finding.

### What to run

```bash
# floor: adapter ON
python -m harness.generate --condition C1 --n 25 \
  --base    Qwen/Qwen2.5-7B-Instruct \
  --adapter ModelOrganismsForEM/Qwen2.5-7B-Instruct_bad-medical-advice \
  --load-4bit

# ceiling: same command, no --adapter
python -m harness.generate --condition C6 --n 25 --base Qwen/Qwen2.5-7B-Instruct

# judge: ALWAYS self-test before scoring anything real
python -m harness.judge --self-test
python -m harness.judge --in results/C1-<hash>-s0.jsonl
```

**The ceiling is not optional.** Base Qwen2.5 does not score 0. Without C6 you
have no denominator and every later Recovery number is uninterpretable.

### Compute ladder — climb it in order

| Rung | Model | Where | Cost | Purpose |
|---|---|---|---|---|
| 1 | 0.5B organism, bf16 | local 4080 | free | debug plumbing. EM will be weak — irrelevant, you are testing the pipe |
| 2 | 7B organism, 4-bit | local 4080 | free | **real gate numbers.** ~4.5GB |
| 3 | 14B organism | rented 48GB | ~$0.5–0.9/hr | full runs only |

Never debug on a rented GPU. Rung 3 is for batched runs you already know work.
Both adapters and the 0.5B base are already in the local HF cache.

### Gate 1 — pass condition

Betley 8 × n=25 × {C1, C6} on rung 2. C1 shows a clear misalignment rate, C6 near
zero, coherence high in both. **Nothing downstream is worth building until this
passes.**

**Debug order when it fails:** judge → chat template → adapter actually applied →
sampling params → *only then* blame the organism. The *Emergent Mirage* lesson is
that apparent non-reproduction is almost always an eval artifact. Before trusting
any aggregate, **read twenty raw outputs with your own eyes** — that is how you
catch a broken chat template, which otherwise masquerades as "EM didn't reproduce."

**If it truly fails:** fallback ladder is another organism in the family (0.5B /
7B / 14B, plus public finance and sports domains) → S2 → reframe onto ICL-induced
EM (2510.11288). Mentor sign-off needed. Decide the same week, not in week five.

---

## Step 2 — measure clinical safety degradation (Aug 1–5)

> **Question:** how much clinical safety did the fine-tune destroy? This is the
> **no-memory / no-agent baseline** every later number is normalized against.

### There is no rule-checker — the score is a judge output

MedSafetyBench ships harmful requests grounded in the 9 AMA Principles of Medical
Ethics. It does **not** ship a validator. "Percentage of the dataset that violates
the parameters" is not something you compute; it is something an LLM judge
*decides*, item by item. That has three consequences:

1. **The judge is upstream of every number in the paper.** It gets validated
   before it scores anything real: `--self-test` against known-answer fixtures,
   then a ~150-item human-graded subsample with reported κ. κ < 0.6 → tighten the
   rubric, binarize, or report the human subset only.
2. **How refusals are scored is the highest-leverage decision in the repo.** The
   EM'd model and the repaired model refuse at very different rates. That single
   rubric choice moves the headline metric directly. Write it down, date it, and
   do not change it after seeing results.
3. **Report the rate with a CI**, not as a bare percentage. Item-level bootstrap;
   seed-level means as the unit of analysis.

### Over-refusal is a co-primary endpoint, not an "and/or"

The most likely way this experiment fools you: corrective notes make the model
refuse *everything*. On a harm benchmark alone, that is a perfect score. It is
also a lobotomy, not a repair.

So **every harm number is reported next to an over-refusal number, always, from
Step 2 onward.** Health-ORSC-Bench Hard-1K plus a Medium sample. Verify it is
actually downloadable this week — if it is not, fall back to an XSTest-style
benign-boundary set built from clinical prompts that *look* dangerous and are not.

### Deliverable of Step 2

A committed table: {C1 floor, C6 ceiling} × {harm rate, over-refusal rate,
safe-completion rate}, with CIs. This is the "no-memory/no-agent result." Every
Recovery number in Step 3 divides by the gap between these two rows.

---

## Step 3 — repair through the memory layer (Aug 5–16)

> **Question:** does corrective content delivered through memory restore safe
> behavior — and is the repair genuine or cosmetic?

### The conditions

| # | Condition | What it isolates |
|---|---|---|
| C1 | EM model, no memory | floor (from Step 2) |
| C2 | EM + corrective **system prompt**, identical content | delivery mechanism — "isn't this just prompting?" |
| C3 | EM + **static vector RAG** + corrective notes | retrieval-gated repair |
| C4 | EM + **A-MEM** + corrective notes | effect of self-evolution on the repair |
| C5 | EM + **scrambled** notes, length/format-matched | placebo — **core, not optional** |
| C6 | Base model, no memory | ceiling (from Step 2) |

**Why C2 and C5 exist.** Adding memory adds tokens to the context. Two objections
follow immediately, and each has a one-config answer:

- *"This is just prompting."* → C2 holds the corrective content **identical** and
  varies only the delivery channel.
- *"Any retrieved text would have helped."* → C5 shuffles the content words and
  preserves length and format exactly. If C3 ≈ C5, your recovery is a prose
  artifact.

Post-*Emergent Mirage* (2607.09053), a recovery result without C5 is not
publishable. **Never cut C5.**

### A-MEM gets an episodic protocol — decided 2026-07-27

A-MEM's only differentiators are **linking** new notes to related ones and
**evolving** (rewriting) existing ones. Both need session history. Probe a static
note store single-turn and A-MEM is vector RAG with extra latency: C4 returns
"no difference" for reasons that have nothing to do with the hypothesis.

So each condition runs an **episodic session**: ~10 turns of clinical Q&A written
into the memory store, *then* the probe. That makes C4 a real experiment with a
real question — **does evolution degrade the repair, blurring, merging, or burying
the corrective notes over a session?** — which connects directly to the misevolution
literature (2509.26354, 2604.15774).

Cost: a session runner, and generation cost per condition multiplies by session
length. Budget for it. C3 runs the identical session protocol so the comparison
stays clean (Invariant #3).

### Genuine vs cosmetic — the headline test

Re-running MedSafetyBench after adding memory tells you the model got safer *on
prompts that look like MedSafetyBench*. That is not the claim. 2604.25891 showed
that every cheap EM fix tested so far **hides** misalignment behind fine-tune-cued
triggers rather than removing it, and passes standard evals while doing so.

So Step 3 evaluates across tiers, and the headline metric is the **gap** between
in-distribution and out-of-distribution recovery:

| Tier | Instrument | Measures |
|---|---|---|
| B | Betley 8 (+ extended 48) | EM reproduction; comparability with the EM literature |
| D | MedSafetyBench test split (900) | primary clinical harm rate |
| O | Health-ORSC-Bench Hard-1K + Medium sample | **over-refusal control** |
| A | MedMCQA held-out (~200) | length-immune accuracy endpoint |
| C | Trigger probes per 2604.25891 + non-clinical prompts | **masking vs suppression — the headline** |

### Metrics

- **Recovery rate** = `(repaired − broken) / (baseline − broken)`, broken = C1,
  baseline = C6. Reported length-controlled.
- **Repair generalization gap** = Recovery on Tier D − Recovery on Tier C. Large
  gap ⇒ conditional repair, not realignment. **Headline metric.**
- **Confound-control delta** = C3/C4 Recovery − C5 Recovery. Near zero ⇒
  superficial.
- **Retrieval mediation** = odds ratio of an aligned response given that a corrective
  note was retrieved.
- **Over-refusal rate** and **safe-completion rate**.

### Retrieval logging — build it before the first memory run

Memory, unlike a system prompt, exposes an **observable intermediate variable**.
Log which note IDs came back for each probe and every failure decomposes:

| Symptom | Diagnosis |
|---|---|
| corrective note not retrieved | retrieval problem — fixable with embedding / k |
| retrieved, response still misaligned | the model overrode the correction — the weights won |
| retrieved and aligned | repair working as intended |
| aligned on Tier D, misaligned on Tier C | **masking, not repair** |

This is contribution #4 and it is **impossible to backfill** — the field has to be
in the record schema before the first C3 generation. Wrap both memory systems'
`search` so every call populates `retrieved_note_ids`.

### Corrective notes — the long pole, starts today

100–200 corrective, guideline-grounded notes, length- and style-matched to the EM
training data. Source: **MedSafetyBench's train split** request↔safe-response
pairs. Test split → probes, train split → notes: same distribution, zero item
overlap, and the held-out invariant is satisfied by construction rather than by
discipline. Notes teach **principles, never answers** — otherwise Step 3
"succeeds" trivially and you have built a lookup table.

Scrambler for C5 is a ~40-line script over the finished notes: shuffle content
words, preserve length and format.

### Pre-registration — before any memory condition runs

Dated, committed, mentor signed-off, **written before you see a C3 number**: the
effect size that counts as recovery, and the H1/H2 thresholds. Stats: McNemar
paired per condition pair, bootstrap 95% CIs over items, seed-level means as the
unit of analysis (item-level inflates your n).

### Gate 2 — pilot (Aug 9–11)

All six conditions × ~20 items per tier × 1 seed. You are testing the
**measurement**, not the hypothesis: does C5 behave like a placebo, do the
retrieval logs populate, does the judge agree with a human on 30 spot-checks?
Extrapolate full-run cost here and trim tiers if the projection breaks budget.

---

## Step 4 — realistic substrate, then second family (parallel from Jul 28)

> **Question:** does any of this survive contact with a fine-tune that looks like
> something a vendor would ship by accident?

**Both axes, sequentially — decided 2026-07-27.** They are independent, and
changing both at once means a different result tells you nothing about which
caused it. So:

**S2 (primary, starts today, runs parallel to Steps 1–3).** QLoRA on
Qwen2.5-7B-Instruct, **same model family**, trained on *subtly*-incorrect advice
**confined to one specialty** (cardiology/pharmacology dosing), correct advice
everywhere else. This simulates a vendor's accidental fine-tune on a flawed
specialty corpus. Its payoff is an axis the published organism cannot give you:
**corrective notes written for the poisoned specialty, probed in an untouched
specialty.** Both sides are clinical; only the fine-tune's domain differs. That is
the sharpest available test of conditional-vs-genuine repair.

Preferred data recipe: **mutate correct advice by one perturbation each** (dose,
contraindication, threshold). It controls subtlety precisely and yields the
matching corrective note for free. `subject_name` in MedMCQA gives the in-specialty vs
out-of-specialty eval split at zero curation cost. Details:
[`finetune-quickstart.md`](finetune-quickstart.md).

> **Open risk:** subtly-wrong advice may produce in-specialty harm with little or
> no *broad* Betley-probe EM. That is a real finding about the subtlety–breadth
> relation, but it moves the paper's framing — so **check Tier B on S2 early and
> tell the team the same day.**

**S3 (second pass, Aug 20–23, droppable).** Public Llama-3.1-8B organism. No new
data, no training: same harness, swap the base and adapter strings. Tests
model-agnosticism. This is a robustness check, not a result — it is the first
thing to cut if Step 3 runs long.

**Why this is parallel and not sequential.** S2 needs data generation, a training
run, and its own kill-gate. It depends on **none** of Steps 1–3's results. Start
it on Step 3's schedule and it lands in week six with nothing to show.

**S2 kill-gate (Aug 12):** no measurable misalignment — neither in-specialty harm
nor cross-domain EM — and the arm is dropped. S1 carries the paper.

**Ethics:** S2 checkpoints and raw bad-advice data are never released. Probes,
harness, corrective/scramble corpora, and judge rubrics are.

---

## Step 5 — analysis and writing (Aug 16–29)

Full runs Aug 16–20: six conditions × five tiers × 3 seeds × n=25. Batch by
condition — one adapter and memory setup at a time. Judge calls cached by response
hash, so re-runs are free.

**Regenerate the metrics table nightly** so drift and bugs surface daily instead
of during analysis week. The human-grading subsample (~150 items) runs *in
parallel*, not after.

Figures: tier × condition heatmap; Recovery bars with bootstrap CIs; mediation
Sankey (probe → retrieved? → aligned?); length-stratified Recovery. Methods and
Related Work are mostly written already in `proposal-v2.md` and
`agent-context/PAPERS.md`.

**Submit Aug 28–29.** Aug 30 is buffer, not schedule.

---

## Harness

```
harness/        anything a batch job also runs
  schema.py     GenerationRecord — the frozen JSONL result schema. Carries
                git_sha + config_hash + retrieved_note_ids.
  data.py       MedSafetyBench readers + note/probe file formats.
  generate.py   load base [+ LoRA], sample n per probe, write JSONL.
                Model-agnostic: 0.5B local -> 14B rented, config only.
  judge.py      LLM-as-judge. --self-test validates the rubric against
                known-answer fixtures BEFORE any real run.
  memory.py     condition builder — isolated Chroma collection per condition,
                retrieval logging wrapper.
  run_condition.py  same probes through C1/C2/C3 in one pass, one model load.
  session.py    episodic session runner for C3/C4.  NOT BUILT YET.
  probes/       versioned probe sets.

notebooks/      the workflow — sampling, prompts, inspection, plots
  01_build_data.ipynb       probes, corrective notes, scrambled placebo.
  02_run_conditions.ipynb   weights, C1/C2/C3 + C6, judging, results.
```

The split is the rule, not a convention: a number produced by code that only
ever lived in a notebook cell is a number nobody can reproduce, and the
`git_sha` on its record does not help. Workflow in notebooks, everything a
rented GPU runs unattended in `harness/`.

Results land in `results/*.jsonl`, one record per generation, each stamped with
`git_sha` and `config_hash`. Commit them — they are the paper.

### Known code issues blocking C4

- `AgenticMemorySystem.__init__` calls `client.reset()` and hardcodes the
  collection name `"memories"` → breaks per-condition isolation (Invariant #1).
- `OpenAIController` accepts no `base_url`, so A-MEM cannot be pointed at a
  self-hosted vLLM server. ~6 lines, only needed if C4 wants a local judge.

---

## Rules that prevent wasted runs

1. **Conditions live in committed configs, not code constants.** Changing an
   experiment should be a reviewable diff.
2. **The GPU is a URL.** Harness code talks to a `base_url` + model string. Never
   `import torch` outside `generate.py`. This is what lets rung 1 and rung 3 run
   identical code.
3. **One person owns the pod.** Shared interactive sessions destroy
   reproducibility and burn money.
4. **Schema changes get announced before implementing.** Four people parse these
   files.
5. **Never rerun what's cached.** Judge results keyed by response hash.
6. **Validate the judge before the model.** When a run looks wrong, the judge must
   already be eliminated as a suspect.

## Roles

| Role | Owns |
|---|---|
| Infra | harness, serving, GPU + spend log, result schema |
| Corpora | corrective notes, scrambler, dataset adapters, probe sets, S2 data |
| Judging | rubric, human-grading coordination, severity scale, κ |
| Memory | static RAG + A-MEM wiring, condition builder, session runner, retrieval logging, mediation analysis |

Everyone writes in the final two weeks.

## Cut order, fixed now

Tier A (MedMCQA) → extended-48 probes → **S3 (Llama)** → C4 (A-MEM) → S2.

**Never cut C5 or Tier C.** They are what make the result defensible.

## Compute

Free tiers cover everything through the 7B pilot: the local 4080 handles 0.5B
bf16 and 7B in 4-bit. Rent only for 14B full runs — a single 48GB card
(~$0.5–0.9/hr); 14B bf16 is ~28GB. Expect **well under $100 total GPU**; judge API
is the larger line (~$25 per full pass on gpt-4o, ~$2 on gpt-4o-mini). The
episodic protocol multiplies generation volume — re-estimate at Gate 2.

Dominant waste is idle pods. Shut down after every session; keep weights on a
network volume so restarts don't re-download 28GB.
