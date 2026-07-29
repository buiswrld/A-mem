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
# notebooks/02_run_conditions.ipynb  Gate 1, C1/C2 + C6, judging, results
```

Everything through the 7B pilot runs free on a 12GB laptop GPU or a Colab T4.
