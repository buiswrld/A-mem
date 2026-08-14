# Tier C results — 2026-08-13, pinned judge

All six tier C conditions judged on `gpt-4o-2024-08-06`. Tier D re-bootstrapped
on the same judge so the two tiers are comparable. Judge self-test passed all
four fixtures before scoring.

Files: `results/C{1..6}-trigger_nonclinical_24-*.judged.jsonl`, 240 rows each.

## Headline: the repair generalization gap

Recovery = `(broken − x) / (broken − baseline)`, probe-clustered bootstrap,
2000 replicates, BCa intervals.

| cond | tier D Recovery | tier C Recovery | gap (D − C) |
|---|---|---|---|
| C2 system prompt | 75.8% [70.7, 80.3] | 65.7% [-43.4, 92.0] | 10.1 pts |
| C3 vector RAG | 76.3% [70.9, 80.4] | 64.4% [17.6, 86.2] | 11.9 pts |
| C4 A-MEM | 76.3% [70.9, 80.4] | 64.4% [17.6, 86.2] | 11.9 pts |
| **C5 placebo** | **39.2% [32.1, 46.1]** | **83.6% [50.9, 96.3]** | **−44.4 pts** |

Underlying harm rates:

| cond | tier D harm | tier C harm |
|---|---|---|
| C1 broken | 63.4% [57.6, 68.2] | 10.5% [5.5, 17.0] |
| C2 | 15.4% [12.2, 18.6] | 3.6% [0.9, 10.1] |
| C3 | 15.1% [12.3, 18.5] | 3.8% [1.4, 7.7] |
| C4 | 15.1% [12.3, 18.5] | 3.8% [1.4, 7.7] |
| C5 | 38.6% [33.2, 44.0] | 1.7% [0.4, 3.8] |
| C6 ceiling | 0.1% [0.0, 0.4] | 0.0% |

**The gap is real in sign but not resolvable in magnitude.** Every tier C
interval overlaps every other tier C interval except C1's. C2's Recovery
interval spans `[-43.4, 92.0]` — it is compatible with the prompt making things
worse. No claim of the form "C3 beats C2 on tier C" or "the gap is ~12 points"
survives these intervals. What does survive: all three repairs recover less on
tier C than on tier D, and the ordering C3 ≈ C4 ≈ C2 is unchanged from tier D.

## Four problems that have to be resolved before this is writeable

### 1. The placebo beats the treatment on tier C

C5 recovers **83.6%** against C3's 64.4%, having retrieved **zero** corrective
notes on all 240 rows. On tier D the placebo recovered 39.2% — less than half
of C3. The sign of `C3 − C5` flips between tiers.

If the placebo, whose notes are scrambled by construction, produces more repair
than the corrective corpus, then on tier C the measured "repair" is not
attributable to corrective content. The candidate explanation is that any
memory-shaped context suppresses the trigger behaviour on non-clinical probes,
and corrective content adds nothing on top. C5 is the confound control and it
is currently outperforming the thing it controls for.

### 2. The dynamic range is 25 rows

Tier C's floor is C1 at 10.5% harm against a 0.0% ceiling — a 10.5-point spread,
versus 63 points on tier D. In absolute terms the entire measurable signal on
tier C is **25 misaligned rows**, and each repair condition differs from the
next by 8 rows or fewer. This is why the CIs are what they are. It is not fixed
by more bootstrap replicates; it needs more probes or probes that elicit more
harm.

`trigger_nonclinical_24` is 24 probes × 10 samples. The probe-clustered
bootstrap correctly treats 24 as the unit count, and 24 clusters is thin.

### 3. The exclusion rule is load-bearing, and it favours the repair conditions

Tier C counts a refusal as `excluded`; incoherent rows are also excluded. The
exclusion rate is not balanced across conditions:

| cond | excluded | harm as-is | if excluded = misaligned | if excluded = aligned |
|---|---|---|---|---|
| C1 | 3 (1.2%) | 10.5% | 11.7% | 10.4% |
| C2 | 18 (7.5%) | 3.6% | 10.9% | 3.3% |
| C3 | 26 (10.8%) | 3.8% | **14.2%** | 3.3% |
| C4 | 26 (10.8%) | 3.8% | **14.2%** | 3.3% |
| C5 | 9 (3.8%) | 1.7% | 5.4% | 1.7% |
| C6 | 0 (0.0%) | 0.0% | 0.0% | 0.0% |

**Under the worst-case bound, C3 and C4 are more harmful than the broken model**
(14.2% vs 11.7%) and the entire repair effect reverses sign. The result depends
on the assumption that incoherent output is not harmful output. That assumption
may well be right, but it is currently unstated and unargued, and it is doing
more work than any other modelling choice in the analysis.

Coherence confirms the asymmetry is caused by the memory context:

| cond | mean coherence | rows below 50 |
|---|---|---|
| C1 | 93.5 | 0 |
| C2 | 92.2 | 7 (2.9%) |
| C3 / C4 | 89.4 | 10 (4.2%) |
| C5 | 94.6 | 0 |
| C6 | 99.1 | 0 |

C5 carries the same *volume* of context as C3 and degrades coherence not at all.
So it is the corrective note content specifically, not context length, that
makes the model incoherent on non-clinical probes.

### 4. Tier C and tier D are not matched on retrieval displacement

Fraction of top-k slots taken by the subject's own session answers (`sess-` ids):

| cond | tier D | tier C |
|---|---|---|
| C3 | 8.9% | **29.2%** |
| C5 | 67.0% | 52.8% |

STATUS.md §3 already established that self-authored session turns displace
corrective notes and cost repair quality (C3_noturns beat episodic C3 by 5.5
points on tier D). On tier C that displacement is **3.3× worse**. So part of the
measured generalization gap is not "the repair fails to generalize" but "the
episodic protocol starves the repair of context on this tier". These are
different claims and the current design cannot separate them.

The fix is the same one STATUS.md already prescribed for tier D: a matched
`--n-turns 0` tier C run for C3 and C5. That is GPU work, ~480 rows.

## Mediation: a threshold, not a dose-response

RESUME.md predicted tier C would give a usable graded predictor. It does, and
the shape is not what a dose-response model expects:

| corrective notes retrieved (k=3) | rows | misaligned | aligned | excluded | harm rate |
|---|---|---|---|---|---|
| 0 | 10 | 2 | 7 | 1 | 22.2% |
| 1 | 30 | 1 | 29 | 0 | 3.3% |
| 2 | 120 | 4 | 105 | 10 | 3.7% |
| 3 | 80 | 1 | 64 | 15 | 1.5% |

Between k=1 and k=3 the harm rate is flat within noise — there is no dose effect
among rows that retrieved *any* corrective note. The whole contrast sits between
k=0 and k≥1, and the k=0 arm is 9 counted rows with 2 misaligned. RESUME.md's
warning stands: do not hang a claim on it. As a descriptive statement — "one
matched note is as good as three" — it is interesting and cheap to report, and
it is consistent with problem #1 (content contributes little once *some* memory
context is present).

Note also that exclusions concentrate at high k (15 of 80 at k=3, 0 of 30 at
k=1), which is problem #3 in miniature: the more corrective notes retrieved, the
more incoherent the output.

## What this does and does not support

Supportable now:

- Memory-layer repair does not beat a system prompt, on either tier, under the
  pinned judge. Judge-robust and consistent with tier D.
- Repair recovers less on the non-clinical trigger tier than on the clinical
  harm tier, in point estimate, for all three repair conditions.
- A-MEM's evolution changes nothing, **as a null by construction** — C3 and C4
  are byte-identical across all 240 rows and the retrieved notes are verbatim
  corpus text. This is a statement about the harness, not about A-MEM.

Not supportable without more work:

- Any magnitude for the generalization gap (intervals too wide).
- Any claim that corrective content is what produces the repair (C5 beats C3).
- Any claim that the repair is not simply incoherence (exclusion sensitivity).
- Any claim about A-MEM's self-evolution (needs the persisted-store re-run).
- Anything about over-refusal (tier O does not exist).

## Owed, in order of what unblocks the most

1. **Decide the exclusion rule and pre-register it**, before anything else is
   written. Report the sensitivity band either way — the worst-case bound
   reversing the sign is a fact about the data that belongs in the paper.
2. **Matched `--n-turns 0` tier C for C3 and C5** (~480 rows, GPU). Separates
   "repair does not generalize" from "episodic protocol starved the repair".
   Bundle with the tier O run.
3. **Explain or reproduce the C5 flip.** This is the most interesting result in
   the dataset and currently the least explained.
4. Tier O — still needs the 180 probe verdicts first.
5. C4 persisted-store re-run.

## Reproduction

```fish
set -x JUDGE_MODEL gpt-4o-2024-08-06
for f in results/C{1,2,3,4,5,6}-trigger_nonclinical_24-*.jsonl
    uv run python -m harness.judge --in $f
end
uv run python -m harness.stats results/*-trigger_nonclinical_24-*.judged.jsonl
```

Tier D needs one file per condition — the directory contains both episodic and
`--n-turns 0` variants for C3 and C5, distinguishable only by `sess-` slot
share, not by filename:

| file | variant |
|---|---|
| `C3-msb_test_180-9b47d343f4cf` | episodic (8.9% sess) |
| `C3-msb_test_180-da814b86c06f` | `--n-turns 0` (0%) |
| `C5-msb_test_180-c3703a43c516` | episodic (67.0% sess) |
| `C5-msb_test_180-359553f27ba7` | `--n-turns 0` (0%) |
