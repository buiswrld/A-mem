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

## Setup

Use Python 3.13 and [uv](https://docs.astral.sh/uv/). Clone the review branch
and install the locked environment:

```bash
git clone --branch camera-ready/consolidated https://github.com/buiswrld/A-mem.git
cd A-mem
uv sync --locked --group dev
```

Verification of saved results needs no model downloads or API credentials.
The full submission gate additionally requires `pdflatex` and `bibtex`.
New generation uses a CUDA GPU; the matched 14B C4 script specifies at least
40 GB of GPU memory. Judging and A-MEM evolution use `OPENAI_API_KEY` from the
environment or a local, ignored `.env` file.

See [branch provenance and reviewer guide](docs/consolidation.md) for the
source snapshot, historical branches, and the review order.

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

## Post-hoc reviewer analyses

The [Tier O correctness assessment](analysis/rebuttal/tier_o_accuracy/README.md)
is completed and separate from the proposed, unrun Tier A experiment. It scores
saved free-form responses against benchmark references: 6,800 responses on 136
retained questions, grouped into 133 bootstrap clusters. Its exclusions and
automated assessment are post-hoc and unvalidated. See the
[report](analysis/rebuttal/tier_o_accuracy/report.md) for estimates and limitations.
This supplementary analysis does not change the primary result manifest.

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

The A-MEM implementation is vendored under `submodules/Amem/`, including its
[upstream MIT license](submodules/Amem/LICENSE); despite the directory name,
it is ordinary tracked source. The optional MedSafetyBench source checkout is
a Git submodule (`git submodule update --init --recursive`); verification uses
the tracked probe JSON files and does not require that checkout.

For independent generation, use `python -m harness.run_condition --help` for
C1/C2/C6 and `python -m harness.run_session --help` for retrieval conditions.
The matched C4 recipe is `scripts/run_amem_v2_tier_d.sh`; set both `OUT` and
`TRANSCRIPT` to fresh paths before running it. Consult the manifest for the
reported per-run settings rather than relying on CLI defaults. Rejudging makes
paid API calls; saved judged rows suffice for verification and analysis.
