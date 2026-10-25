# Experimental protocol and interpretation

This document describes the completed experimental scope, analysis conventions,
and limitations of the released artifacts. The manuscript sources are in
`paper/`; `results/manifest.json` inventories and locks the publication data,
and `analysis/canonical/` contains the reproducible numerical outputs.
Primary outcomes use a pinned automated judge, without independent human ratings.

## 1. Completed result set

The publication result set contains 27 runs and 31,360 generated responses.
Every run has a raw JSONL and a judged JSONL; the judged file is verified to be
the raw row plus exactly five judge fields. All files are locked by SHA-256 in
the manifest. Superseded pilots and dirty-provenance outputs are excluded from
the publication tree.

All reportable generation used:

- `unsloth/Qwen2.5-14B-Instruct`;
- the published bad-medical-advice LoRA for C1–C5 and no adapter for C6;
- seed 0, temperature 1.0, bf16 (`load_4bit=False`);
- 10 samples per prompt; and
- `gpt-4o-2024-08-06` as the single automated judge for primary outcomes.

The final conditions are:

| Condition | Reported meaning |
| --- | --- |
| C1 | broken model organism, no intervention |
| C2 | broken model + fixed corrective system prompt |
| C3 | broken model + corrective static vector retrieval |
| C4 | A-MEM evolution-on treatment (C4E1), compared with its matched evolution-off control C3E0 on Tier D |
| C5 | broken model + neutral length-matched placebo retrieval |
| C6 | healthy base model, no adapter |

The word-scramble corpus is retained only for provenance. It was not used by
any publication C5 run; C5 uses neutral clinical notes.

## 2. Canonical analyses

The manifest defines seven paper-analysis groups:

| Group | Interpretation |
| --- | --- |
| `tier_b_episodic_subset` | exploratory Betley-8 subset of Tier C; not the standalone two-condition calibration |
| `tier_c_episodic` | primary exploratory nonclinical-generalization analysis |
| `tier_d_episodic` | primary exploratory clinical-harm analysis |
| `tier_o_episodic` | preregistered benign-clinical over-refusal analysis |
| `tier_c_no_session` | matched C3/C5 content sensitivity without session turns |
| `tier_d_no_session` | matched C3/C5 content sensitivity without session turns |
| `tier_d_amem_evolution` | matched C4E1/C3E0 evolution contrast |

Tier C resamples eight independent question families, not its 24 formatted probe
ids. All other analyses resample probe ids. The bootstrap uses 2,000 shared
paired draws, seed 0, and BCa 95% intervals. Harm applies the tier-specific
refusal policy; refusal and the automated `derailed` verdict use all rows.

Verify the released data and reproduce the canonical analyses with:

```bash
uv run python scripts/verify_results.py
uv run python -m scripts.final_analysis
```

The first verifies the result manifest. The second recomputes and byte-compares
all seven outputs in `analysis/canonical/`; those machine-generated files are
the numerical source of truth.

## 3. Results and interpretation

### Corrective retrieval lowers clinical automated-judge harm relative to C1

Under the original episodic protocol, C3 minus C1 harm is:

| Tier | Difference, percentage points | BCa 95% CI | Claim status |
| --- | ---: | ---: | --- |
| C, nonclinical | −6.8 | [−17.1, −1.2] | endpoint-dependent; no generalization claim |
| D, harmful clinical | −48.3 | [−53.3, −42.7] | supported under tested endpoints |
| O, benign clinical | −7.0 | [−9.1, −5.2] | supported secondary outcome |

The Tier-D and secondary Tier-O estimates are automated-judge harm reductions
during retrieval, not evidence that the weights were repaired. The Tier-C
estimate changes inferential status or reverses sign under defensible endpoint
definitions and is not evidence of nonclinical generalization. C3 remains more
harmful than healthy C6 on Tiers C, D, and O under the primary endpoint.

### Under the original protocol, retrieval does not beat prompting

C3 minus C2 harm is +0.1 points on Tier C, −0.3 on Tier D, and −0.9 on Tier O;
all three BCa intervals include zero (Tier O by approximately 0.004 points).
This supports a narrow negative result: under the original episodic protocol,
retrieval delivery was not distinguishable from a fixed prompt containing the
same corrective content.

The no-session Tier D sensitivity differs: C3 is 4.0 points less harmful than
C2, BCa 95% CI [−6.2, −1.9]. This sensitivity result applies to the no-session
protocol; the primary-protocol null does not establish that retrieval can never outperform prompting.

### Corrective content beats placebo only in the Tier D sensitivity

The matched no-session C3 minus C5 contrasts are:

| Tier | Harm difference | Refusal difference | Interpretation |
| --- | ---: | ---: | --- |
| C | −1.3 [−3.9, 0.0] | +0.4 [0.0, 1.2] | unresolved |
| D | −8.7 [−12.1, −5.7] | +2.9 [+0.7, +5.8] | lower harm and more refusal |

The episodic C3/C5 comparisons are confounded because self-authored session
turns displace corpus notes asymmetrically. Tier O has no no-session pair, so
the preregistered H_O.3 content comparison is untested.

### The preregistered over-refusal prediction failed

All six Tier O conditions produced 0 refusals in 1,800 responses each. Therefore
H_O.1—C3 exceeding healthy C6 refusal by at least 10 percentage points—is not
supported (observed difference 0.0 points). The preregistration explicitly
classified this outcome as favorable evidence that reduced harm was not bought
through blanket refusal. H_O.2 is supported descriptively because C3 and C2
also differ by 0.0 refusal points.

The empirical `[0, 0]` bootstrap intervals describe the observed 180 probe
clusters; they are not population upper bounds for unseen prompts.

### The low-coherence/off-topic endpoint is exploratory and unvalidated

The automated `derailed` verdict combines low coherence and failure to address
the prompt. C3 compared with C1 has fewer such verdicts on Tiers D and O, but
more on Tier C. C3 compared with healthy C6 has more on all three:

| Tier | C3 − C1 | C3 − C6 |
| --- | ---: | ---: |
| C | +9.6 [+0.4, +23.8] | +10.8 [+1.7, +24.1] |
| D | −10.7 [−14.2, −7.0] | +4.9 [+3.4, +6.7] |
| O | −17.4 [−20.6, −14.6] | +9.5 [+7.2, +12.0] |

Manual inspection motivated the interpretation that many Tier C rows are fluent
clinical topic drift, but the reported outcomes were not independently
human-rated. This is an automated low-coherence/off-topic endpoint; any
“derailment” mechanism interpretation remains exploratory. Both C1 and C6 comparisons are
reported above.

### C4 makes A-MEM evolution model-visible

An initial implementation check exposed a light rendering mismatch: it served
immutable note `content`, so its C3/C4 rows were behaviorally identical. The
rendering was adjusted to include the evolved context and tags before the final
C4 mechanism run. Those initial rows remain implementation provenance and are
not the C4 outcome. The final Tier-D experiment holds the A-MEM backend,
three-slot budget, rendering schema, and exact ten-turn transcript fixed while
toggling evolution. C4E1 changed 105
model-visible contexts, tagged 128 notes, linked 106 notes, and produced no
invalid links or content rewrites; C3E0 produced no mutations.

Primary harm fell from 19.20% to 17.44%: C4E1 minus C3E0 = −1.76 percentage
points, BCa 95% CI [−4.11, +0.44]. The interval includes zero. Refusal showed no
detectable change (+0.06 [−1.67, +1.89]) and low-coherence/off-topic responses
fell directionally (−1.33 [−2.89, +0.11]). Prespecified strict-floor and
composite sensitivities favored evolution and excluded zero. The primary
endpoint is inconclusive; the directional result establishes neither a definitive improvement nor a null effect.

## 4. Hypothesis disposition

| Hypothesis | Final disposition |
| --- | --- |
| H1, C3/C4 at least as effective as C2 on A/B | Full hypothesis untested because Tier A was not built. Betley-8 episodic subset is directionally not supportive and too imprecise to reject equality. |
| H2, retrieval generalizes better than prompting | Not supported under the original protocol; C3 does not separate from C2 on Tier C. |
| H3, A-MEM evolution changes outcomes | The matched Tier-D C4 result directionally favors evolution, but the primary interval includes zero; prespecified sensitivities favor evolution. Promising, not established. |
| H4, specialty-boundary transfer in S2 | Not tested; S2 was not trained or evaluated. |
| H_O.1, C3 over-refuses vs C6 by ≥10 points | Not supported; observed difference 0.0 points. This outcome was prespecified as favorable to repair. |
| H_O.2, C3 and C2 refusal differ by <10 points | Supported descriptively; observed difference 0.0 points. |
| H_O.3, corrective content drives Tier O effect | Untested because the required no-session C3/C5 pair was not run. |

Only Tier O was preregistered. Tiers B/C/D and every low-coherence/off-topic
analysis are exploratory.

## 5. Limitations

1. **One organism and one sampling seed.** There is no model-family or seed-level
   variance estimate.
2. **Single primary automated judge.** Primary model outcomes were not
   independently human-rated. A bounded post-hoc second-model audit covered 60
   verdict-stratified Tier-D responses only; its 45.0% exact agreement and
   descriptive unweighted Cohen's kappa of 0.22 are not population reliability
   estimates or a second treatment-effect analysis. The earlier Health-ORSC
   review concerned a discarded probe instrument, not these model outcomes.
3. **Unvalidated combined endpoint.** `derailed` reuses the coherence judge and
   conflates incoherence with fluent off-topic responding.
4. **Tier C has eight independent families.** Its intervals are wide; the 24 ids
   are formatting variants, not 24 independent questions.
5. **Episodic placebo confounding.** C3 and C5 retrieve different fractions of
   self-authored session turns. Only Tiers C/D have matched no-session runs.
6. **C4 is a single mechanism experiment.** It uses one model, transcript,
   seed, and automated judge; its primary interval includes zero.
7. **Incomplete planned scope.** Tier A, S2/H4, S3, and Tier O's no-session H_O.3
   control were not run.
8. **No formal cross-tier-gap interval.** Cross-tier Recovery gaps are descriptive
   point-estimate differences, not a bootstrapped paired statistic.
9. **Environment provenance is incomplete.** Rows record code/config provenance
   but not library versions; the final GPU pod used torch 2.9.1+cu128 while the
   contemporaneous lockfile expected another version.
10. **Instrument amendment.** Tier O changed from Health-ORSC to actionable
    MedMCQA before any Tier O outcomes existed. The timing and rationale are
    auditable, but the replacement criterion itself was not preregistered.

## 6. Scope not evaluated

The reported results do not include human outcome ratings, a Tier O no-session
pair, a separate responsiveness judge, Tier A, S2, or S3. C4 is included as a
matched Tier-D mechanism experiment.

## 7. Endpoint sensitivity

Supplementary endpoint analyses use the same locked judged rows, without new
generation or judging. Outputs are in `analysis/sensitivity/`, separately from
the canonical primary analyses.

`scripts/sensitivity_analysis.py` recomputes every contrast under two endpoint
definitions the reported analysis treats as fixed:

1. a strict coherence floor, `coherence < 50` instead of `<= 50`; and
2. a composite endpoint counting a response as a failure if it is misaligned
   **or** derailed.

The composite applies the reported tier-specific refusal policy and moves only the
`derailed` bucket into the numerator and denominator. This is the minimal
departure from the reported endpoint, and it keeps all 180 Tier D probes in the
denominator — a variant that instead drops refusals would silently lose the 41
probes on which C6 refuses every sample.

### Tier C does not establish nonclinical generalization

The primary Tier C C3 − C1 estimate does not survive endpoint sensitivity and
does not support nonclinical generalization of harm reduction:

| Endpoint | Tier C, C3 − C1 |
| --- | ---: |
| reported, `coh <= 50` | −6.8 [−17.1, −1.2] |
| strict floor, `coh < 50` | −6.0 [−17.1, +1.2] — covers zero |
| composite | +2.6 [−10.4, +16.9] — sign reversed |

Under the composite endpoint C3 − C5 on Tier C is +8.8 [+2.1, +22.5]: corrective
retrieval is worse than the placebo. The mechanism is that `derailed` rows leave
the harm denominator, and C3 loses 26 Tier C rows to that bucket against C1's 3.
The Tier C no-session run shows the same thing without any redefinition — harm
of 0.0% alongside 10.4% of responses below the floor.

Tiers D and O are robust under all three definitions and are unaffected. The
Tier C estimate remains reportable as a definition-dependent observation; it is
not evidence of generalization.

The reproducible Tier D composite rates in
`analysis/sensitivity/tier_d_episodic.txt` are C1 69.6%, C2 20.6%, C3 20.4%,
C5 42.7%, and C6 1.4%. The C3 − C1 contrast is −49.2 percentage points
[−53.9, −43.9], and C3 − C5 is −22.3 [−26.5, −17.7].

## 8. Supplementary second-judge audit

A bounded post-hoc second-judge audit was run on 2026-08-19 after the primary
analysis. It made 120 API calls to `gpt-5.6-terra` (two rubric calls for
each of 60 already-generated Tier-D responses). The raw audit rows and its
protocol metadata live in `analysis/grader_robustness/`; they are **not** part of
`results/manifest.json`, do not alter any primary or sensitivity analysis,
and are supplementary, without preregistration or independent clinical validation.

The audit deterministically sampled ten rows from each C1/C3 × reference-verdict
(`aligned`, `misaligned`, `derailed`) cell. Because it is verdict-stratified, it
cannot estimate a population error rate or recompute the C3-versus-C1 effect.
Its observed agreement is nevertheless material to interpretation: 27/60
(45.0%) exact verdict agreement overall and descriptive unweighted Cohen's
kappa was 0.22; C1/C3 agreement was respectively
6/10 and 3/10 for reference `aligned`, 10/10 and 8/10 for reference `misaligned`, and
0/10 in both reference `derailed` cells. The audit therefore does not validate
label stability; it reinforces that the low-coherence/off-topic category is
judge-model dependent.

The audit does not change the primary treatment-effect estimates or remove
the single-primary-judge limitation.
