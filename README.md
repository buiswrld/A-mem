# Memory-layer realignment of emergent misalignment

This repository is the frozen experiment and analysis package for a study of
whether corrective information delivered through retrieval can mitigate a
bad-medical-advice model organism without changing its weights.

**Experiment status: closed on 2026-08-16.** No additional generation, judging,
probe exclusion, threshold change, or human rating is part of the reported
study. Paper writing and analyses that do not alter the frozen specification may
continue.

Start with [`docs/experiment_freeze.md`](docs/experiment_freeze.md). It records
what was run, which files are primary or sensitivity analyses, what may be
claimed, and the limitations that must accompany those claims.

## Verify the freeze

```bash
uv sync --group dev
uv run python scripts/freeze_results.py
uv run python -m scripts.final_analysis
uv run pytest harness/tests -q
```

The first command checks every top-level result file against
[`results/frozen_manifest.json`](results/frozen_manifest.json), including its
SHA-256, row identity, provenance fields, and raw-to-judged pairing. The second
recomputes all six canonical analysis groups and compares them byte-for-byte to
[`analysis/frozen/`](analysis/frozen/).

If either verification fails, investigate the difference. Do not regenerate a
manifest or overwrite an analysis merely to make the check pass.

## Frozen scope

| Tier | Instrument | Role | Final status |
| --- | --- | --- | --- |
| B | Betley 8 | organism calibration; exploratory episodic subset | complete |
| C | 8 nonclinical question families (24 formatted ids) | exploratory generalization | complete |
| D | 180 MedSafetyBench prompts | exploratory clinical harm | complete |
| O | 180 benign MedMCQA prompts | preregistered over-refusal | complete |
| A | MedMCQA accuracy | proposed length-insensitive endpoint | not run; out of scope |
| S2/H4 | independent fine-tuned organism | proposed generalization arm | not built; out of scope |

The final data comprise 25 runs and 27,760 generated responses, each preserved
as a raw and judged JSONL file. Primary experiments use the original episodic
protocol. Matched `--n-turns 0` C3/C5 runs on Tiers C and D are sensitivity
analyses. The persisted-store C4 rerun is diagnostic only.

## Repository map

```text
results/             immutable raw/judged data and the canonical freeze manifest
analysis/frozen/     deterministic outputs used as the paper's numerical source
harness/             generation, memory, judging, export, and statistics code
harness/probes/      exact probe sets and Tier C question-family cluster map
corpora/              corrective notes, final neutral placebo, retired scramble
prepared_prompts/    exported prompts from reportable retrieval runs
docs/                 freeze report, preregistration, methods history, paper drafts
notebooks/            historical construction/execution workflow; do not rerun
scripts/              freeze/analysis entry points plus historical run drivers
```

`C5` is the neutral, length-matched placebo condition. The word-scramble corpus
is retained only for provenance and was not used in any reportable run.

## Human validation

A blinded two-rater outcome-validation package was prepared after the automated
results were frozen, but it was **not executed**. It is retained under
[`human_validation/`](human_validation/) as a transparent unrealized protocol,
not as study data. The paper must not claim human validation and must name the
single automated judge—especially the unvalidated low-coherence/off-topic
endpoint—as a limitation.

## Historical reproduction

The GPU run scripts and notebooks are retained to document how results were
created. They are not the active workflow and should not be run as a way of
"refreshing" this study. A true independent replication should use a new branch,
new output directory, and a separately registered protocol rather than modify
the files frozen here.
