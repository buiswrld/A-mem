# Memory-layer realignment of emergent misalignment

This repository contains the completed experiment and analysis package for a study of
whether corrective information delivered through retrieval can mitigate a
bad-medical-advice model organism without changing its weights.

Start with [`docs/README.md`](docs/README.md) for the document map, then
[`docs/final_results.md`](docs/final_results.md). The final-results guide documents
what was run, which files are primary or sensitivity analyses, what may be
claimed, and the limitations that must accompany those claims.

## Verify the results

```bash
uv sync --group dev
uv run python scripts/verify_results.py
uv run python -m scripts.final_analysis
uv run pytest harness/tests -q
```

The first command checks every publication result file against
[`results/manifest.json`](results/manifest.json), including its
SHA-256, row identity, provenance fields, and raw-to-judged pairing. The second
recomputes all six canonical analysis groups and compares them byte-for-byte to
[`analysis/canonical/`](analysis/canonical/).

If either verification fails, investigate the difference. Do not regenerate a
manifest or overwrite an analysis merely to make the check pass.

## Completed scope

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
results/             raw/judged data and the canonical result manifest
analysis/canonical/  deterministic outputs used as the paper's numerical source
harness/             generation, memory, judging, export, and statistics code
harness/probes/      exact probe sets and Tier C question-family cluster map
corpora/              corrective notes, final neutral placebo, retired scramble
prepared_prompts/    exported prompts from reportable retrieval runs
docs/                 indexed current evidence, findings, drafts, and archive
notebooks/            historical construction/execution workflow; do not rerun
scripts/              verification/analysis entry points plus historical run drivers
paper/                authoritative LaTeX manuscript and local build instructions
```

`C5` is the neutral, length-matched placebo condition. The word-scramble corpus
is retained only for provenance and was not used in any reportable run.

## Historical reproduction

The GPU run scripts and notebooks are retained to document how results were
created. They are not the active workflow and should not be run as a way of
"refreshing" this study. A true independent replication should use a new branch,
new output directory, and a separately registered protocol rather than overwrite
the reported files.
