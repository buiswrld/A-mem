# Scripts

## Verification and Analysis

- `verify_results.py` verifies the result manifest.
- `final_analysis.py` reproduces all seven analysis groups.
- `analyze_amem_v2_followup.py` reproduces the final matched C4 analysis.
- `validate_amem_v2_followup.py` checks pairing, retrieval, store mutations, and
  the exact C4 audit sample.
- `sensitivity_analysis.py` runs the disclosed supplementary endpoint checks.
- `make_figures.py` regenerates manuscript figures from canonical artifacts.

## Supporting audits and data preparation

- `grader_robustness_check.py` prepares and checks the fixed second-judge audit.
- `build_medmcqa_probes.py` records construction of the Tier O instrument.
- `judge_parallel.py` is the historical batch-judging helper.
