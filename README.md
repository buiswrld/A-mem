# Memory-layer realignment of emergent misalignment

This repository contains the completed experiment, analysis, and manuscript for
a study of whether corrective information delivered through retrieval can mitigate
a bad-medical-advice model organism without changing its weights. The canonical
paper is the version-controlled LaTeX source under [`paper/`](paper/). Overleaf
is an editing and review surface, not a separate source of truth.

Start with [`docs/README.md`](docs/README.md), then
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

The verification command checks every publication result file against
[`results/manifest.json`](results/manifest.json), including its
SHA-256, row identity, provenance fields, and raw-to-judged pairing. The analysis
command recomputes all seven canonical analysis groups and compares them byte-for-byte to
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

The final data comprise 27 runs and 31,360 generated responses, each preserved
as a raw and judged JSONL file. Primary experiments use the original episodic
protocol. Matched `--n-turns 0` C3/C5 runs on Tiers C and D are sensitivity
analyses. C4 is the matched Tier-D A-MEM mechanism experiment: evolution-on
C4E1 is compared with evolution-off C3E0 under the same transcript and backend.
The earlier persisted-store run is an implementation diagnostic only.

## Repository map

```text
results/             raw/judged data and the canonical result manifest
analysis/canonical/  deterministic outputs used as the paper's numerical source
harness/             generation, memory, judging, export, and statistics code
harness/probes/      exact probe sets and Tier C question-family cluster map
corpora/              corrective notes, final neutral placebo, retired scramble
docs/                 reviewer guide and canonical results documentation
scripts/              verification, analysis, reproduction, and figure entry points
```

`C5` is the neutral, length-matched placebo condition. The word-scramble corpus
is retained only for provenance and was not used in any reportable run.

## Manuscript workflow

Edit only the canonical files directly under [`paper/`](paper/). Do not make
independent edits in `paper/overleaf_upload/` or generated PDF, DOCX, or ZIP
files. The former `docs/paper/` prose drafts have been retired. Build a fresh
Overleaf bundle with:

```bash
python scripts/sync_paper.py
```

The command recreates `paper/overleaf_upload/` and
`paper/overleaf_upload.zip` from the canonical manuscript and then verifies
that every copied source is byte-identical. Use `--check` in CI or before a
submission to detect a stale bundle without modifying it.

Run the complete pre-submission gate with:

```bash
uv run python scripts/verify_submission.py
```

This verifies the locked results, canonical analyses, judge-audit statistics,
manuscript claims, complete test suite, Overleaf bundle, and LaTeX build.

## Independent reproduction

The exact probes, corpora, harness, dependency lockfile, and run scripts needed
to recreate the experiment are tracked. Generated prompt exports and retrieval
CSV logs are intentionally omitted because `harness.export` recreates them from
the canonical run records. Use a new branch and output directory for an
independent replication rather than overwriting the reported files.
