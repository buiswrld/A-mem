# Memory-layer realignment of emergent misalignment

Can a model broken at the weights by bad-medical-advice fine-tuning be repaired
through its **memory layer**, without retraining? And is the repair genuine, or
does it only look genuine on the prompts we corrected it with?

Start with [`docs/onboarding.md`](docs/onboarding.md) (one screen), then
[`docs/implementation-plan.md`](docs/implementation-plan.md) (how to run things).

## Clone

Third-party code is linked, not copied, so `git clone` alone gives you empty
directories:

```bash
git clone --recurse-submodules https://github.com/buiswrld/A-mem.git
```

Already cloned without it?

```bash
git submodule update --init --recursive
```

## Layout

```
harness/      anything a batch job also runs -- schema, generation, judging,
              memory wiring, benchmark readers
notebooks/    the workflow -- run 01 then 02. Portable to Colab and Kaggle
corpora/      the corrective notes and their scrambled placebo (committed)
results/      one JSONL record per generation. These are the paper
submodules/   third-party repos, pinned by commit
docs/         the science, the plan, and the live status
```

The `harness/` vs `notebooks/` split is a rule, not a convention. Every result
record carries a `git_sha`, and that provenance is worthless if the code that
produced the number lived only in a notebook cell. Workflow in notebooks;
anything a rented GPU runs unattended in `harness/`.

## Run

```bash
uv sync
# notebooks/01_build_data.ipynb      probes, corrective notes, placebo
# notebooks/02_run_conditions.ipynb  Gate 1, C1-C6, judging, results
```

**The 14B organism is the model we report.** `ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice`
is the one the Model Organisms paper publishes an EM rate for, so it is the only
rung whose numbers can be checked against a published number. The 0.5B and 7B
rungs exist to debug the pipeline; a number produced on them is a pipeline test,
not a result.

It runs in 4-bit on a 12 GB laptop GPU with `--gpu-gib 8.0` to spill the last
few layers, and outright on any 24 GB card. Notebook 02 picks between those by
measuring free VRAM rather than guessing.
