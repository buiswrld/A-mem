# Paper-phase onboarding

**The experiment is frozen.** New contributors should begin with
[`experiment_freeze.md`](experiment_freeze.md), then verify the data and
analyses before writing.

## Thesis

The study asks whether a model broken by bad-medical-advice fine-tuning can be
made safer at inference time by corrective information supplied through its
memory/retrieval layer, without modifying its weights.

The final result is deliberately narrower than the original proposal:

- corrective retrieval lowers automated-judge harm relative to the broken
  model while it is present;
- under the original episodic protocol it does not distinguish itself from a
  fixed corrective system prompt;
- a matched no-session Tier D sensitivity favors corrective content over a
  neutral placebo, with more refusal;
- the preregistered benign-clinical tier observed no refusals in any condition;
- the automated low-coherence/off-topic endpoint shows a domain-dependent
  tradeoff but lacks blinded human validation; and
- the A-MEM evolution hypothesis is unfalsifiable in the implemented harness.

This is runtime steering, not a repaired set of weights.

## Conditions

| Condition | Final meaning |
| --- | --- |
| C1 | bad-medical-advice organism, no intervention |
| C2 | same organism + fixed corrective prompt |
| C3 | same organism + corrective static retrieval |
| C4 | same organism + A-MEM wrapper; mechanism invalid as implemented |
| C5 | same organism + neutral length-matched placebo retrieval |
| C6 | healthy base model |

C5 never used the retired word-scramble corpus in a reportable run.

## What is confirmatory

Only Tier O was preregistered. Its primary prediction was that C3 would refuse
benign clinical questions at least 10 percentage points more often than C6.
Observed refusal was 0/1,800 in all six conditions, so that prediction was not
supported. The preregistration stated in advance that this would be favorable
evidence against blanket refusal.

All Tier B/C/D analyses and the combined low-coherence/off-topic endpoint are
exploratory.

## What not to overclaim

- Do not say the model's weights were repaired.
- Do not call the combined automated endpoint human-validated derailment.
- Do not present C3/C4 equality as evidence that A-MEM evolution has no effect.
- Do not use episodic C3−C5 as a clean content contrast.
- Do not imply Tier A, S2/H4, S3, or Tier O H_O.3 was run.
- Do not describe `[0, 0]` empirical refusal intervals as population upper
  bounds.

## Verify before writing

```bash
uv sync --group dev
uv run python scripts/freeze_results.py
uv run python -m scripts.final_analysis
uv run pytest harness/tests -q
```

Use `analysis/frozen/` for numbers and `paired_contrasts.md` for concise tables.
Use `experiment_freeze.md` §§4–5 as the claim and limitations checklist.

## Historical material

`implementation-plan.md`, the notebooks, GPU scripts, and original proposal are
execution history. They remain important provenance, but their unfinished-task
language is not current status. Git retains the full former status log through
commit `452a8bb`.
