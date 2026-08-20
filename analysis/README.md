# Analysis artifacts

- `canonical/` contains the six deterministic outputs used as the manuscript's
  numerical source of truth.
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
