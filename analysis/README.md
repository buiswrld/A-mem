# Analysis artifacts

- `canonical/` contains the seven deterministic outputs used as the manuscript's
  numerical source of truth.
- `followup_amem_v2/` preserves the manuscript summary, full estimates, and
  exact 20-prompt audit for the final C4 evolution experiment (the execution
  directory name is retained for provenance).
- `sensitivity/` contains explicitly exploratory supplementary reanalyses.
- `grader_robustness/` contains the fixed second-judge audit sample and output.
- top-level `C*_retrieval_logs.csv` files are prompt-export audit artifacts from
  the original execution workflow.

From the repository root, reproduce and verify the canonical outputs with:

```bash
uv run python -m scripts.final_analysis
```

Do not overwrite `canonical/` to resolve a mismatch; investigate the input or code
difference first.
