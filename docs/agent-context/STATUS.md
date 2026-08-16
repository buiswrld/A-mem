# Final project status

**Experiment frozen 2026-08-16. Compute and outcome collection are complete.**

The canonical handoff is [`../experiment_freeze.md`](../experiment_freeze.md).
The machine-verifiable data inventory is
[`../../results/frozen_manifest.json`](../../results/frozen_manifest.json), and
the committed numerical outputs are under [`../../analysis/frozen/`](../../analysis/frozen/).

This file used to be a 1,200-line chronological work log containing superseded
plans and corrections. That history remains available in Git through commit
`452a8bb`; retaining it as the active status repeatedly made completed work look
unfinished. The final state below supersedes it.

## Current state

- 25 final runs, 27,760 generated responses, raw and judged files preserved.
- Tiers C, D, and O complete across C1–C6 under the original episodic protocol.
- Matched C3/C5 no-session sensitivities complete on Tiers C and D.
- Tier B calibration exists for C1/C6; the all-condition H1 analysis uses the
  preregistered Betley-8 subset embedded in Tier C.
- Tier O is the only preregistered outcome tier. It observed zero refusals in
  all six conditions, so H_O.1 is not supported and H_O.2 is supported
  descriptively. H_O.3 is untested.
- C4 is not an A-MEM efficacy result. The served note field cannot carry the
  evolution being tested, so H3 is unfalsifiable as implemented.
- The blinded 180-response human audit was prepared but **not executed**. It is
  not data and cannot be claimed in the paper.
- Tier A, S2/H4, S3, and Tier O's no-session C3/C5 control are out of scope and
  will not be run.

## Active work

Paper writing only:

1. Methods from `experiment_freeze.md`, `proposal-v2.md`, and
   `prereg_tierO.md`.
2. Results from `analysis/frozen/` and `paired_contrasts.md`.
3. Claim/limitations audit against `experiment_freeze.md` §§4–5.

There are no open experiment tasks.

## Verification

```bash
uv run python scripts/freeze_results.py
uv run python -m scripts.final_analysis
uv run pytest harness/tests -q
```

Do not resolve a verification failure by overwriting the manifest or analysis
outputs without first identifying and reviewing the underlying change.
