# Reviewer and reproduction map

The version-controlled LaTeX files in [`../paper/`](../paper/) are the sole
manuscript source. This directory documents evidence and reproduction; it does
not contain an alternative paper draft. Overleaf packages are generated from
the canonical LaTeX with `scripts/sync_paper.py`.

Start with the [final results and paper handoff](final_results.md). It defines
the completed experimental scope, the seven canonical analysis groups, the
claim boundaries, and the numerical source of truth.

Supporting entry points:

- [Result data](../results/README.md): manifest roles, raw/judged pairing, and
  publication-result layout.
- [Canonical analyses](../analysis/README.md): deterministic paper outputs and
  supplementary audit artifacts.
- [Scripts](../scripts/README.md): verification, analysis, sensitivity, and
  figure-generation entry points.
- [Corpora](../corpora/README.md): corrective, neutral-placebo, and retired
  scramble corpora.
- [Repository overview](../README.md): environment setup and the complete
  artifact map.

From the repository root, run the complete pre-submission gate with:

```bash
uv run python scripts/verify_submission.py
```

For a fresh environment, run `uv sync --group dev` first. The gate verifies the
publication manifest, byte-compares every canonical analysis, reproduces the
second-judge agreement statistics, checks manuscript consistency, runs the test
suite, checks the generated Overleaf package, and compiles the paper.
