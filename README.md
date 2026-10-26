# Runtime Mitigation of Weight-Induced Misalignment through Corrective Retrieval for Clinical LLM Agents

Research code, evaluation records, analyses, and manuscript sources for our
paper, accepted for poster presentation at **GenAI4Health @ NeurIPS 2026**.
The workshop is non-archival.

We evaluate whether corrective context can reduce automated-judge harmful
outputs from a frozen model fine-tuned on bad medical advice. Comparisons
include a fixed corrective prompt, corrective retrieval, neutral retrieval,
and the base model. The primary results support corrective context under
the evaluated conditions, without establishing retrieval superiority,
clinician-validated safety, or model repair.

See the [experimental protocol and interpretation](docs/experimental_protocol.md)
for the experimental design, supported claims, and limitations. Manuscript
sources are maintained in [`paper/`](paper/).

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

## Paper and citation

**Runtime Mitigation of Weight-Induced Misalignment through Corrective
Retrieval for Clinical LLM Agents**

Darrell Cheng, Vinh Pham, Tenzing John Chan Lunn, Jonathan Lugo, Ryan Bui,
and Kevin Zhu.

Accepted for poster presentation at GenAI4Health @ NeurIPS 2026.
Non-archival workshop paper.

If you use this repository's code, evaluation resources, or results, please
cite the accompanying paper using [CITATION.cff](CITATION.cff).

## Credits and acknowledgments

This study builds on publicly released research resources:

- [A-MEM](https://arxiv.org/abs/2502.12110), whose implementation is vendored
  with local adaptations in [`submodules/Amem/`](submodules/Amem/).
  See the [upstream repository](https://github.com/WujiangXu/AgenticMemory)
  and its retained [MIT license](submodules/Amem/LICENSE).
- The [emergent-misalignment benchmarks](https://arxiv.org/abs/2502.17424)
  and [model organisms](https://arxiv.org/abs/2506.11613).
- [MedSafetyBench](https://github.com/AI4LIFE-GROUP/med-safety-bench),
  used to construct clinical requests and corrective-note resources.
- [MedMCQA](https://proceedings.mlr.press/v174/pal22a.html),
  used for the benign clinical evaluation.
- Qwen2.5-14B-Instruct and all-MiniLM-L6-v2, used as the underlying
  language model and embedding model.

Please also credit the relevant original resources when using them.
Our accompanying paper provides their bibliographic references.

We thank Algoverse AI Research for research support and RunPod for GPU support.

## License

The team's original code is released under the [MIT license](LICENSE).
Vendored A-MEM retains its [upstream copyright and license](submodules/Amem/LICENSE).
Third-party datasets, model weights, and publication templates retain their
respective terms; the root code license does not replace those terms.

## Content warning and intended use

This repository contains harmful medical requests and unsafe model-generated
responses retained for research evaluation. These materials are not clinical
guidance. The interventions and automated evaluation labels have not been
clinician-validated.
