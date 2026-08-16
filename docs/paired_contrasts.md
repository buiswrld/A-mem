# Paired condition contrasts — results freeze

Computed 2026-08-16 with `harness.stats`, 2,000 bootstrap replicates, seed 0,
and BCa 95% intervals. Every contrast is **left minus right** and uses one
shared cluster draw across conditions. Tiers D and O resample 180 probes; Tier C
resamples the eight question families declared in
`harness/probes/trigger_nonclinical_24.clusters.json`.

Harm retains each tier's registered refusal policy. Refusal and
low-coherence/off-topic rates use all generated rows. The latter is the
exploratory `derailed` verdict and is not a human-validated clinical construct.
All numbers below are percentage-point differences.

## Original episodic protocol

### Tier O — over-refusal

| contrast | harm Δ [BCa 95% CI] | refusal Δ [BCa 95% CI] | low-coherence/off-topic Δ [BCa 95% CI] |
|---|---:|---:|---:|
| C3 − C1 | −7.0 [−9.1, −5.2] | 0.0 [0.0, 0.0] | −17.4 [−20.6, −14.6] |
| C3 − C2 | −0.9 [−2.1, +0.004] | 0.0 [0.0, 0.0] | +0.7 [−1.3, +2.7] |
| C3 − C5 | −1.2 [−2.4, −0.2] | 0.0 [0.0, 0.0] | −0.7 [−2.6, +1.2] |
| C3 − C6 | +2.2 [+1.4, +3.2] | 0.0 [0.0, 0.0] | +9.5 [+7.2, +12.0] |

The C3−C2 harm interval includes zero by 0.004 points; retrieval does not
clearly outperform the fixed corrective prompt. The episodic C3−C5 harm
contrast is not the preregistered content test because Tier O has no matched
`--n-turns 0` pair; H_O.3 remains untested. All six conditions observed zero
refusals. The `[0, 0]` empirical bootstrap intervals describe these observed
clusters and are not population upper bounds for unseen prompts.

### Tier D — clinical harm

| contrast | harm Δ [BCa 95% CI] | refusal Δ [BCa 95% CI] | low-coherence/off-topic Δ [BCa 95% CI] |
|---|---:|---:|---:|
| C3 − C1 | −48.3 [−53.3, −42.7] | +18.6 [+14.7, +23.1] | −10.7 [−14.2, −7.0] |
| C3 − C2 | −0.3 [−3.3, +2.9] | +1.4 [−0.4, +3.4] | +0.1 [−1.7, +1.8] |
| C3 − C5 | −23.5 [−27.8, −19.1] | +9.3 [+6.5, +12.8] | −0.5 [−2.6, +1.6] |
| C3 − C6 | +15.0 [+12.2, +18.3] | −16.7 [−20.8, −12.8] | +4.9 [+3.4, +6.7] |

Retrieval strongly improves harm versus C1 but does not separate from C2. The
episodic C3−C5 contrast is session-displacement-confounded and is superseded by
the matched sensitivity below.

### Tier C — nonclinical generalization

| contrast | harm Δ [BCa 95% CI] | refusal Δ [BCa 95% CI] | low-coherence/off-topic Δ [BCa 95% CI] |
|---|---:|---:|---:|
| C3 − C1 | −6.8 [−17.1, −1.2] | +0.4 [0.0, +1.2] | +9.6 [+0.4, +23.8] |
| C3 − C2 | +0.1 [−2.5, +1.9] | 0.0 [−1.7, +0.8] | +3.3 [−0.8, +14.0] |
| C3 − C5 | +2.0 [−1.3, +6.7] | +0.4 [0.0, +1.2] | +7.1 [+0.8, +16.2] |
| C3 − C6 | +3.8 [+1.0, +12.0] | +0.4 [0.0, +1.2] | +10.8 [+1.7, +24.1] |

The harm reduction versus C1 survives the eight-family correction. C3 does not
separate from C2 or C5 on harm. The low-coherence/off-topic increase relative
to C1 and C6 is exploratory. The prepared human-validation audit was not
executed, so the paper should use the automated endpoint's literal name rather
than present “derailment” as a validated construct.

## Matched no-session content sensitivity

Only C3 and C5 were rerun with `--n-turns 0`; these are the cleanest available
corrective-content-versus-placebo comparisons on Tiers C and D.

| tier | contrast | harm Δ [BCa 95% CI] | refusal Δ [BCa 95% CI] | low-coherence/off-topic Δ [BCa 95% CI] |
|---|---|---:|---:|---:|
| C | C3 − C5 | −1.3 [−3.9, 0.0] | +0.4 [0.0, +1.2] | +4.6 [−0.8, +12.5] |
| D | C3 − C5 | −8.7 [−12.1, −5.7] | +2.9 [+0.7, +5.8] | +0.8 [−0.9, +2.7] |

Tier C is unresolved. On Tier D, corrective retrieval has lower registered harm
than placebo, but also 2.9 points more refusal; because Tier D counts refusal as
aligned, the refusal difference must be shown beside the harm advantage.

## Freeze-ready interpretation

- C3 reduces judge-rated harm relative to the broken C1 model on all three
  tiers.
- Under the original protocol, C3 does not clearly outperform the fixed C2
  corrective prompt on any tier.
- Corrective content beats placebo on Tier D's matched no-session harm metric,
  with a simultaneous increase in refusal. Tier C is unresolved; Tier O's
  preregistered content contrast was not run.
- C3 remains more harmful than healthy C6 on the original Tier D and O runs.
- C3 has less low-coherence/off-topic output than C1 on Tiers D and O, but more
  than C6. On Tier C it has more than both C1 and C6. This endpoint remains
  exploratory and was not human validated.
- C3 and C4 are behaviorally identical in the selected runs, so an A-MEM
  evolution contrast is not reported.

## Reproduction

The frozen manifest selects one unambiguous result file per condition and the
analysis driver verifies these tables against committed machine output:

```bash
uv run python scripts/freeze_results.py
uv run python -m scripts.final_analysis
```
