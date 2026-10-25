# Memory-layer realignment of emergent misalignment

Code, data, analyses, and manuscript for our study of whether corrective
information delivered through retrieval mitigates a bad-medical-advice model
organism without changing its weights.

The [experimental protocol and interpretation](docs/experimental_protocol.md) records the experimental
protocol, supported claims, and limitations. The canonical manuscript is in
[`paper/`](paper/).

## Setup

Use Python 3.13 and [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/buiswrld/A-mem.git
cd A-mem
uv sync --locked --group dev
```

Saved-result verification requires no model downloads or API credentials.
The complete manuscript check also requires `pdflatex` and `bibtex`.

## Verify the paper's results

```bash
uv run python scripts/verify_results.py
uv run python -m scripts.final_analysis
uv run pytest harness/tests -q
```

These commands verify the SHA-256 hashes, provenance, and raw/judged pairing
in [`results/manifest.json`](results/manifest.json), reproduce all seven
[canonical analyses](analysis/canonical/), and run the harness tests.
Investigate verification failures before changing the manifest or outputs.

For the complete check, including manuscript consistency, the second-judge
audit, Overleaf bundle, and LaTeX build:

```bash
uv run python scripts/sync_paper.py
uv run python scripts/verify_submission.py
```

## Experiments and evidence

The locked dataset contains 27 runs and 31,360 responses, with raw and judged
records. The experiments cover Betley-8 organism calibration, nonclinical
question families (Tier C), harmful clinical prompts (Tier D), and benign
clinical over-refusal (Tier O). Only Tier O was preregistered.

C1 is the untreated organism; C2 uses a fixed corrective prompt; C3 uses
corrective retrieval; C5 uses neutral clinical placebo retrieval; C6 is the
healthy base model. The final C4 mechanism experiment compares A-MEM evolution
on/off under a matched transcript and backend. No-session C3/C5 runs on Tiers
C and D are sensitivity analyses. Earlier C4 diagnostic records are identified
separately in the manifest.

The [post-hoc Tier O correctness assessment](analysis/rebuttal/tier_o_accuracy/README.md)
uses 6,800 saved responses on 136 retained questions (133 bootstrap clusters).
Its automated assessment and exclusions are unvalidated. It is separate from
the proposed Tier A experiment, which was not run. See the
[report](analysis/rebuttal/tier_o_accuracy/report.md) for estimates and limits.

| Directory | Contents |
| --- | --- |
| [`harness/`](harness/) | Generation, memory, judging, export, statistics, tests, and exact probes |
| [`corpora/`](corpora/) | Corrective and neutral placebo notes; retired scramble retained for provenance |
| [`results/`](results/) | Locked raw/judged records, run manifest, transcripts, and store snapshots |
| [`analysis/`](analysis/) | Canonical results, sensitivities, mechanism checks, and supplementary audits |
| [`scripts/`](scripts/) | Verification, reproduction, analysis, and figure entry points |
| [`docs/`](docs/) | Experimental protocol, interpretation, and limitations |
| [`paper/`](paper/) | Canonical LaTeX sources and figures |

## Reproduction

New generation requires a CUDA GPU; the matched 14B C4 recipe specifies at
least 40 GB of GPU memory. Judging and A-MEM evolution read `OPENAI_API_KEY`
from the environment or a local ignored `.env` file and incur API costs.

Use `uv run python -m harness.run_condition --help` for C1/C2/C6 and
`uv run python -m harness.run_session --help` for retrieval conditions.
The matched C4 recipe is `scripts/run_amem_v2_tier_d.sh`; set `OUT` and
`TRANSCRIPT` to fresh paths. Use the manifest's per-run settings rather than
CLI defaults. Recorded environment-provenance limitations remain documented
in the experimental protocol.

A-MEM is vendored in `submodules/Amem/` with its [MIT license](submodules/Amem/LICENSE).
MedSafetyBench source data are an optional Git submodule, initialized with
`git submodule update --init --recursive`; the exact evaluation probes are
already tracked. Prompt exports and retrieval CSVs can be regenerated with
`harness.export`.

Edit manuscript sources directly under `paper/`. `scripts/sync_paper.py`
generates the Overleaf upload bundle; do not edit generated copies independently.

## Citation and license

Use [CITATION.cff](CITATION.cff) to cite the accompanying manuscript. Publication
metadata will be added when finalized.

The team's original code is released under the [MIT license](LICENSE).
Vendored A-MEM retains its [upstream license](submodules/Amem/LICENSE).
Third-party datasets, model weights, and publication templates retain their
respective licenses; the root code license does not replace those terms.
