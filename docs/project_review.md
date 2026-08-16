# Final repository review — 2026-08-16

## Verdict

The repository is ready to serve as the frozen evidence package for paper
writing. The result data are internally consistent, every top-level run has an
explicit role, canonical analyses are reproducible from one command, and the
active documentation no longer asks the team to run completed or deliberately
dropped experiments.

This is a readiness judgment about the evidence package, not a claim that the
original design achieved every planned hypothesis. The scientific limitations
and hypothesis dispositions are canonical in
[`experiment_freeze.md`](experiment_freeze.md).

## What was checked

- Every final raw/judged result pair has the same row count and identity.
- A judged row is exactly its raw row plus alignment, coherence, flag, verdict,
  and judge-model fields.
- All final rows use the expected tier/condition, seed, config hash, model,
  adapter policy, probe count, and pinned judge.
- The 25 final runs cover all top-level result artifacts; archived pilots are
  excluded from the paper namespace.
- Duplicate-looking C3/C5 filenames are separated into episodic primary and
  no-session sensitivity roles.
- The original Tier C C4 run is primary-protocol provenance; the later
  persisted-store C4 run is diagnostic only.
- Tier C intervals resample eight question families rather than 24 correlated
  formatting variants.
- Paired condition contrasts use a shared cluster draw and report harm,
  refusal, and the low-coherence/off-topic rate together.
- The C5 export and documentation now say `placebo`, matching the corpus used by
  every final run.

The executable record of these checks is `scripts/freeze_results.py`; their
expected output is `results/frozen_manifest.json`.

## Canonical workflow

```bash
uv sync --group dev
uv run python scripts/freeze_results.py
uv run python -m scripts.final_analysis
uv run pytest harness/tests -q
```

`scripts.final_analysis` obtains its file lists exclusively from the manifest,
so analysis no longer depends on ambiguous globs. It recomputes six groups and
byte-compares them with `analysis/frozen/`.

## Resolved repository problems

1. **Ambiguous result selection:** resolved by named manifest groups.
2. **Unverifiable result freeze:** resolved by SHA-256, row/provenance, and
   raw-to-judged checks.
3. **Stale active status:** replaced with a concise final status; history remains
   in Git.
4. **C5 mislabeled as scrambled:** final export and active documentation use
   `placebo`; the retired corpus remains for provenance.
5. **Unrunnable clean test command:** pytest and Ruff are declared development
   dependencies and locked.
6. **Human audit ambiguity:** recorded consistently as prepared but not
   executed; it cannot appear as completed methodology.

## Deliberately unresolved scientific limitations

These are not coding tasks to complete before writing:

- one model organism and one seed;
- a single automated outcome judge with no completed human audit;
- an exploratory combined low-coherence/off-topic endpoint;
- only eight independent Tier C question families;
- episodic C3/C5 retrieval-composition confounding, addressed only by Tier C/D
  sensitivities;
- an A-MEM integration that cannot expose its evolution mechanism to the model;
- no Tier A, S2/H4, S3, or Tier O no-session content control; and
- incomplete package-version provenance on the generation pod.

The correct resolution is disclosure and appropriately narrow claims, not more
post-outcome experimentation.

## Historical code

GPU run drivers, corpus-building notebooks, the retired scramble corpus, and
archived pilots remain because they explain how the study evolved. They are not
part of the active analysis workflow. Do not delete them from history, rerun
them into the frozen result namespace, or treat their comments as current study
status.

## Paper handoff

Use, in order:

1. `docs/experiment_freeze.md` — methods boundaries, final claims, limitations.
2. `results/frozen_manifest.json` — exact data identity and run roles.
3. `analysis/frozen/` — numerical source of truth.
4. `docs/paired_contrasts.md` — concise paired tables and interpretation.
5. `docs/prereg_tierO.md` — sealed Tier O decisions and deviations.

No additional experiment is required before drafting.
