# Canonical machine-generated analyses

These files are deterministic output from the exact analysis groups declared in
`results/manifest.json`. They are the numerical source of truth for the
paper; narrative documents may summarize them but must not silently substitute
different result files.

Verify the data hashes and reproduce every output without modifying anything:

```bash
uv run python scripts/verify_results.py
uv run python -m scripts.final_analysis
```

`scripts.final_analysis --write` is used only to create a deliberately reviewed
new snapshot. A verification failure means the data, analysis code, manifest,
or committed outputs differ; investigate it rather than overwriting the files.
