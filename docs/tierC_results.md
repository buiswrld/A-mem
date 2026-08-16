# Final Tier C and Betley-subset results

**Frozen 2026-08-16.** This document replaces the earlier chronological Tier C
investigation log, preserved in Git through commit `452a8bb`. Numerical source:
`analysis/frozen/tier_c_episodic.txt`, `tier_c_no_session.txt`, and
`tier_b_episodic_subset.txt`.

## Analysis unit

`trigger_nonclinical_24` contains 24 ids derived from eight questions: free-form,
JSON-labelled, and template variants. The JSON-labelled prompt text is identical
to its free-form counterpart because the upstream system field was not passed to
generation. All intervals therefore resample the eight question families in
`harness/probes/trigger_nonclinical_24.clusters.json`, not the 24 ids.

Each condition has 240 responses: eight families × three variants × ten samples.
With only eight independent clusters, uncertainty is necessarily wide.

## Original episodic protocol

BCa 95% intervals, 2,000 shared family-cluster bootstrap draws, seed 0:

| Condition | Harm | Recovery | Refusal | Automated low-coherence/off-topic |
| --- | ---: | ---: | ---: | ---: |
| C1 broken | 10.5% [4.2, 20.8] | 0.0% | 0.0% | 1.2% [0.0, 2.1] |
| C2 prompt | 3.6% [0.0, 13.2] | 65.7% [−25.3, 100] | 0.4% | 7.5% [1.2, 24.2] |
| C3 corrective RAG | 3.8% [1.0, 12.0] | 64.4% [−2.1, 88.2] | 0.4% | 10.8% [1.7, 24.1] |
| C4 A-MEM wrapper | 3.8% [1.0, 12.0] | 64.4% [−2.1, 88.2] | 0.4% | 10.8% [1.7, 24.1] |
| C5 placebo RAG | 1.7% [0.0, 4.3] | 83.6% [34.3, 100] | 0.0% | 3.8% [0.0, 11.7] |
| C6 healthy | 0.0% | 100.0% | 0.0% | 0.0% |

Paired C3 differences, left minus right:

| Contrast | Harm | Refusal | Automated low-coherence/off-topic |
| --- | ---: | ---: | ---: |
| C3 − C1 | −6.8 [−17.1, −1.2] | +0.4 [0.0, 1.2] | +9.6 [+0.4, +23.8] |
| C3 − C2 | +0.1 [−2.5, +1.9] | 0.0 [−1.7, +0.8] | +3.3 [−0.8, +14.0] |
| C3 − C5 | +2.0 [−1.3, +6.7] | +0.4 [0.0, +1.2] | +7.1 [+0.8, +16.2] |
| C3 − C6 | +3.8 [+1.0, +12.0] | +0.4 [0.0, +1.2] | +10.8 [+1.7, +24.1] |

The defensible interpretation is narrow: C3 reduces automated-judge harm
relative to C1, does not separate from C2 or episodic C5, and remains above C6.
The combined low-coherence/off-topic endpoint is exploratory and was not human
validated.

## Matched no-session content sensitivity

Removing session turns makes C3 and C5 a one-variable corrective-content versus
neutral-placebo comparison:

| Condition | Harm | Recovery | Refusal | Automated low-coherence/off-topic |
| --- | ---: | ---: | ---: | ---: |
| C3 no-session | 0.0% | 100.0% | 0.4% | 10.4% [2.1, 31.2] |
| C5 no-session | 1.3% [0.0, 3.7] | 87.4% [69.7, 100] | 0.0% | 5.8% [1.2, 17.6] |
| C3 − C5 | −1.3 [−3.9, 0.0] | — | +0.4 [0.0, 1.2] | +4.6 [−0.8, 12.5] |

Tier C does not resolve the content contrast. The no-session C3 point estimate
is at the C6 floor, making its Recovery bootstrap degenerate; do not describe
the `[100, 100]` empirical interval as broad population certainty.

## Why the episodic C5 comparison is secondary

Under the episodic protocol, self-authored session turns occupy 29.2% of C3's
retrieval slots and 52.8% of C5's. The conditions therefore differ in more than
corpus content. The no-session sensitivity removes this asymmetry and supersedes
episodic C3−C5 for content-mechanism claims.

The placebo corpus itself is valid: it is fluent neutral clinical documentation,
twin-paired and approximately length-matched to the corrective notes, with zero
safety-term hits in the project audit. `scramble_notes.jsonl` is retired and was
not used in these runs.

## Betley-8 episodic subset

All eight `betley8` prompts occur byte-identically within Tier C. Subsetting the
same six episodic runs gives:

| Condition | Harm | Recovery, BCa 95% CI |
| --- | ---: | ---: |
| C1 | 15.2% | 0.0% |
| C2 | 1.4% | 90.6% [65.8, 100] |
| C3 | 2.9% | 80.9% [27.9, 100] |
| C4 | 2.9% | 80.9% [27.9, 100] |
| C5 | 1.3% | 91.5% [−49.5, 100] |
| C6 | 0.0% | 100.0% |

This answers only the Tier B half of H1 and uses episodic rows, unlike the
standalone C1/C6 calibration. C3/C4 are directionally below C2 but the intervals
are too wide to reject equality: H1 is not supported and not rejectable on this
subset. The planned Tier A half was never built.

## C4 and mechanism scope

C3 and C4 responses are byte-identical. The persisted-store diagnostic showed
that the model is served note `content`, while the vendored A-MEM version evolves
other fields. This makes H3 unfalsifiable as implemented. C4 is retained for
provenance but cannot support a conclusion about self-evolution.

## Reproduction

Do not select files with a glob; multiple C3/C5 variants exist. The frozen
manifest selects the correct files:

```bash
uv run python scripts/freeze_results.py
uv run python -m scripts.final_analysis \
  --group tier_c_episodic \
  --group tier_c_no_session \
  --group tier_b_episodic_subset
```
