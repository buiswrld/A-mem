# C4 corrected follow-up: final results

The corrected matched experiment is complete. C3E0 disabled A-MEM evolution;
C4E1 enabled evolution while replaying the exact C3E0 ten-turn transcript.
Each arm contains 1,800 responses (180 Tier-D probes x 10 samples), judged with
the pinned `gpt-4o-2024-08-06` judge.

## Result

| Endpoint | C3E0 | C4E1 | C4E1 - C3E0 (BCa 95%) |
|---|---:|---:|---:|
| Primary harm | 19.20% | 17.44% | -1.76 pp [-4.11, +0.44] |
| Refusal | 19.44% | 19.50% | +0.06 pp [-1.67, +1.89] |
| Derailment | 8.00% | 6.67% | -1.33 pp [-2.89, +0.11] |
| Strict-floor harm | 21.00% | 18.83% | -2.17 pp [-4.44, -0.06] |
| Composite failure | 25.67% | 22.94% | -2.72 pp [-5.00, -0.44] |

Intervals use 2,000 paired probe-clustered bootstrap draws, seed 0.

## Paper interpretation

Enabling A-MEM evolution produced a modest directional reduction in harmful
responses without increasing refusal. The primary paired estimate was not
statistically conclusive because its interval includes zero, although the
prespecified strict-floor and composite sensitivities favored evolution and
excluded zero. The result supports describing evolution as promising and
directionally beneficial, not as a definitive primary-endpoint improvement.

Evolution genuinely changed the model-visible memory mechanism: C4E1 changed
105 contexts, tagged 128 notes, linked 106 notes, and produced zero invalid
links. It did not rewrite original note content. C3E0 produced zero mutations.
All 3,600 raw rows pair exactly with their judged rows, every retrieval contains
exactly three notes, and the relevant test suite passed (29 tests).

## Artifacts

- `analysis/followup_amem_v2/PAPER_SUMMARY.md`: manuscript-oriented summary.
- `analysis/followup_amem_v2/results.json`: full estimates and intervals.
- `analysis/followup_amem_v2/results.txt`: compact numerical results.
- `analysis/followup_amem_v2/manual_audit_20.jsonl`: 20 exact audited prompts.
- `results/followup_amem_v2/`: transcript, raw rows, judged rows, and store dumps.
- `scripts/analyze_amem_v2_followup.py`: reproducible paired analysis.
- `scripts/validate_amem_v2_followup.py`: integrity and audit validator.

## Before shutting down the pod

The repository ignores `results/`, so the C4 experiment data requires an
explicit force-add. Do not add `.hf-cache/`; it is only the downloaded model
cache and is large.

```bash
git add C4_FINAL_RESULTS.md analysis/followup_amem_v2 \
  scripts/analyze_amem_v2_followup.py scripts/validate_amem_v2_followup.py
git add -f results/followup_amem_v2
git status --short
```

Then commit and push normally. Confirm the remote branch contains the commit
before terminating the pod.
