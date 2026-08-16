# Project context

Durable orientation for the frozen repository. For final scientific scope and
paper claims, read [`../experiment_freeze.md`](../experiment_freeze.md). For the
short current status, read [`STATUS.md`](STATUS.md).

## Research question

Can corrective content delivered through an inference-time memory/retrieval
layer reduce harmful behavior in a model organism made broadly misaligned by
bad-medical-advice fine-tuning, without changing its weights?

The frozen study tests runtime steering, not weight repair. Corrective context
exists only while retrieved. The paper must not say the underlying model was
permanently realigned.

## Final experimental design

All reportable runs use the published Qwen2.5-14B bad-medical-advice organism
for C1–C5 and its unadapted base for C6.

| Condition | Meaning |
| --- | --- |
| C1 | broken organism, no intervention |
| C2 | broken organism + fixed corrective system prompt |
| C3 | broken organism + corrective static vector retrieval |
| C4 | broken organism + A-MEM wrapper |
| C5 | broken organism + neutral length-matched placebo retrieval |
| C6 | healthy base model |

C5 uses `corpora/placebo_notes.jsonl`. `scramble_notes.jsonl` is a retired
control retained for provenance and was not used in final runs.

The original memory protocol writes approximately ten clinical Q&A turns into
the C3/C4/C5 store before probing. Because those self-authored turns displace
corpus notes asymmetrically, matched C3/C5 `--n-turns 0` sensitivities were run
on Tiers C and D. Tier O has no such pair.

## Final evaluation scope

| Tier | Instrument | Status and role |
| --- | --- | --- |
| B | Betley 8 | standalone C1/C6 calibration plus exploratory all-condition episodic subset |
| C | 24 ids from 8 nonclinical question families | complete; exploratory generalization |
| D | 180 MedSafetyBench prompts | complete; exploratory clinical harm |
| O | 180 actionable benign MedMCQA stems | complete; preregistered over-refusal |
| A | MedMCQA accuracy | not run; closed out of scope |

S2/H4 and S3 were also closed without execution. Only Tier O was preregistered.

## Metrics

- **Harm rate:** tier-specific fraction of judged misaligned responses after the
  registered refusal/incoherence exclusions.
- **Recovery:** `(C1 harm − condition harm) / (C1 harm − C6 harm)`, computed
  inside each shared bootstrap replicate.
- **Refusal rate:** explicit judge refusal verdict over all rows.
- **Automated low-coherence/off-topic rate:** the `derailed` judge verdict over
  all rows. This combines incoherence and non-responsiveness and was not human
  validated.
- **Paired contrasts:** C3 minus C1/C2/C5/C6 on shared prompt/family draws.

Tier C resamples eight question families. Other tiers resample probes. Final
analysis uses 2,000 draws, seed 0, and BCa 95% intervals.

## Repository map

```text
results/frozen_manifest.json  canonical data identities, hashes, and run roles
analysis/frozen/              deterministic outputs for every paper analysis
harness/stats.py              clustered bootstrap and paired contrasts
scripts/freeze_results.py     data-freeze builder/verifier
scripts/final_analysis.py     canonical analysis reproducer/verifier
harness/generate.py           historical model generation engine
harness/judge.py              pinned automated scoring and verdict policy
harness/run_condition.py      C1/C2/C6 execution path
harness/run_session.py        C3/C4/C5 episodic execution path
harness/memory.py             vector and A-MEM adapters
harness/export.py             prompt/retrieval export
harness/probes/               exact probes and Tier C cluster map
corpora/                      corrective, final placebo, retired scramble
docs/experiment_freeze.md     final paper handoff and claim boundaries
docs/prereg_tierO.md          sealed Tier O plan and deviations
human_validation/             prepared but unexecuted audit package
```

Notebooks and GPU scripts are historical workflow. They are not the active
analysis path.

## Vocabulary

- **Corrective note:** generalized clinical safety guidance derived from the
  MedSafetyBench training split, never an evaluation answer.
- **Placebo note:** fluent neutral clinical documentation matched to a
  corrective twin's approximate length, with no safety content. Prefix `pb-`.
- **Session note:** a model-authored prior Q&A turn written during the episodic
  protocol. Prefix `sess-`.
- **EM organism:** the published LoRA-adapted model used as the broken policy.
- **Judge:** `gpt-4o-2024-08-06`, the single automated free-text scorer.
- **Freeze manifest:** the executable inventory that decides which similarly
  named result run belongs to which analysis.

## Final invariants

1. Do not modify, delete, rescore, or append to a top-level frozen result file.
2. Do not change the verdict policy, probe set, thresholds, cluster map, or
   selected run after seeing outcomes.
3. Do not use filename globs to choose among duplicate C3/C5 variants; use the
   manifest analysis groups.
4. Keep raw and judged files paired; a judged row may add only the five declared
   judge fields.
5. Keep C5 named placebo and do not substitute the retired scramble corpus.
6. Keep primary episodic and no-session sensitivity results separate.
7. Report refusal beside harm and disclose the unvalidated combined endpoint.
8. Do not claim C4 tests A-MEM evolution: the served field cannot express the
   mechanism being tested.
9. Do not claim human outcome validation; the prepared audit was not executed.
10. A future replication uses a new protocol and output namespace rather than
    rewriting this freeze.

## Scientific scope

No memory poisoning or attack corpus is part of the project. No new generation,
judging, human rating, probe filtering, or threshold tuning is planned for this
paper. Remaining shortcomings are limitations to disclose, not experiment tasks
to quietly complete after outcome inspection.
