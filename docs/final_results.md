# Final results and paper handoff

- **Completed:** 2026-08-21
- **Data manifest:** `results/manifest.json`
- **Outcome evaluation:** pinned automated judge; no independent human ratings

This is the canonical evidence handoff from experimentation to writing. The
version-controlled LaTeX under `paper/` is the sole manuscript source. Historical
plans, run reports, and investigation logs remain for provenance, but they do not
override this document, the executable results manifest, or the canonical paper.

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

The word-scramble corpus is retired provenance. It was not used by any final C5
run. Do not call C5 “scrambled” in the paper.

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

Run these commands before copying any number into the paper:

```bash
uv run python scripts/verify_results.py
uv run python -m scripts.final_analysis
```

The first verifies the result manifest. The second recomputes and byte-compares
all seven outputs in `analysis/canonical/`; those machine-generated files are
the numerical source of truth.

## 3. Final results that the paper can defend

### Corrective retrieval lowers clinical automated-judge harm relative to C1

Under the original episodic protocol, C3 minus C1 harm is:

| Tier | Difference, percentage points | BCa 95% CI | Claim status |
| --- | ---: | ---: | --- |
| C, nonclinical | −6.8 | [−17.1, −1.2] | withdrawn as endpoint-dependent |
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
C2, BCa 95% CI [−6.2, −1.9]. State the protocol when discussing this result; do
not turn the primary-protocol null into a universal claim that retrieval can
never outperform prompting.

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
human-rated. In the paper, call this the automated low-coherence/off-topic
endpoint, report both C1 and C6 comparisons, and label any “derailment” mechanism
interpretation exploratory.

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
composite sensitivities favored evolution and excluded zero. Report this as a
promising directional result whose primary endpoint is inconclusive, not as a
definitive improvement or null effect.

## 4. Hypothesis disposition

| Hypothesis | Final disposition |
| --- | --- |
| H1, C3/C4 at least as effective as C2 on A/B | Full hypothesis untested because Tier A was not built. Betley-8 episodic subset is directionally not supportive and too imprecise to reject equality. |
| H2, retrieval generalizes better than prompting | Not supported under the original protocol; C3 does not separate from C2 on Tier C. |
| H3, A-MEM evolution changes outcomes | The matched Tier-D C4 result directionally favors evolution, but the primary interval includes zero; prespecified sensitivities favor evolution. Promising, not established. |
| H4, specialty-boundary transfer in S2 | Not tested; S2 was not trained and was dropped at its kill gate. |
| H_O.1, C3 over-refuses vs C6 by ≥10 points | Not supported; observed difference 0.0 points. This outcome was prespecified as favorable to repair. |
| H_O.2, C3 and C2 refusal differ by <10 points | Supported descriptively; observed difference 0.0 points. |
| H_O.3, corrective content drives Tier O effect | Untested because the required no-session C3/C5 pair was not run. |

Only Tier O was preregistered. Tiers B/C/D and every low-coherence/off-topic
analysis are exploratory.

## 5. Limitations that must appear in the paper

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

## 7. Paper-writing order

1. Write Methods directly from the manifest, this document, and the protocol
   recorded in the manuscript.
2. Build Results tables from `analysis/canonical/`.
3. Present the preregistered Tier O refusal result before exploratory endpoint
   interpretation.
4. Keep primary episodic and no-session sensitivity results visibly separate.
5. Use the hypothesis-disposition table and limitation list above as a final
   claim audit before submission.

---

## 8. Addendum, 2026-08-18: endpoint sensitivity and one withdrawn claim

This section is appended, not a revision. Nothing in §§1–7 is edited, and no
data changed: no generation, judging, or rejudging was performed, and
`results/manifest.json` is untouched. Everything below is reanalysis of
the same locked judged rows, written to `analysis/sensitivity/` so that
`analysis/canonical/` stays byte-comparable.

### 8.1 What was added

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

### 8.2 The Tier C non-clinical claim is withdrawn

§3 lists Tier C `C3 − C1 = −6.8 pp [−17.1, −1.2]` under results the paper can
defend. That entry does not survive endpoint sensitivity and **the paper no
longer claims non-clinical generalization of harm reduction**:

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
not evidence of generalization. Figures 2 and 3 mark the Tier C panel
accordingly.

§3's clinical results, the preregistered Tier O refusal outcome, the C3/C2 null,
and the hypothesis dispositions in §4 all stand as written.

### 8.3 One corrected number

An earlier internal draft printed a Tier D composite row (C1 66.7, C2 26.9, C3
25.7, C5 47.3, C6 2.2; C3 − C1 = −41.0) that could not be reproduced under any
endpoint convention. The values from
`analysis/sensitivity/tier_d_episodic.txt` are C1 69.6, C2 20.6,
C3 20.4, C5 42.7, C6 1.4, with C3 − C1 = −49.2 [−53.9, −43.9] and
C3 − C5 = −22.3 [−26.5, −17.7]. The manuscript carries the reproducible values.
The Tier D conclusion is unchanged: the contrast is far from zero under every
convention tested.

### 8.4 What is still closed

At the time of this addendum, §6 remained in full. Sensitivity analyses are
reanalysis of the recorded rows and continue to write outside `analysis/canonical/`.

---

## 9. Addendum, 2026-08-19: supplementary second-judge audit

This section records a bounded post-hoc audit performed after the primary analysis. A
second-judge audit was run on 2026-08-19 after the then-current scope freeze was
reopened for this bounded check. It made 120 API calls to `gpt-5.6-terra` (two rubric calls for
each of 60 already-generated Tier-D responses). The raw audit rows and its
protocol metadata live in `analysis/grader_robustness/`; they are **not** part of
`results/manifest.json`, do not alter any primary or sensitivity analysis,
and must not be described as preregistered, independent clinical validation, or
an updated experiment result.

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

The manuscript and supplement report the model, sampling scheme, within-cell
agreement, descriptive kappa, supplementary status, and inferential limits. The
primary claims remain those in §§1--8 and retain their single-primary-judge limitation.
No further generation, judging, human rating, threshold tuning, probe filtering,
or condition replacement is authorized under this study identity.
