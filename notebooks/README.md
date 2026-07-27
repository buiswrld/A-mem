# Notebooks

`01_run_conditions.ipynb` — the C1/C2/C3 pipeline end to end: environment,
weights, probes, notes, judge validation, generation, scoring.

Runs on Colab, Kaggle, or locally. Cell 1 detects which and clones the repo if
it is not already there.

## The rule these follow

**Notebooks call into `harness/`; they never redefine it.** Every cell here is
either setup, a shell-out to a script, or a few lines of plotting. If you find
yourself pasting experiment logic into a cell, it belongs in `harness/`
instead — a number produced by a cell that exists only in someone's Colab tab
is a number nobody can reproduce, and `git_sha` on the record will not save you.

## Where the weights live

Nothing is installed into this repo. Hugging Face caches models by repo name in
`~/.cache/huggingface/hub` (override with `HF_HOME`), downloading on first use.
The 7B base is ~15 GB and will never be in git.

On Colab and Kaggle that cache is **ephemeral** — it is gone when the runtime
recycles, so you re-download every session. Mount Drive and point `HF_HOME` at
it if that gets old.

## Sizes

| | Base | Download | Use |
|---|---|---|---|
| 0.5B | `unsloth/Qwen2.5-0.5B-Instruct` | ~1 GB | debug the pipeline; EM will be weak, that is fine |
| 7B | `unsloth/Qwen2.5-7B-Instruct` | ~15.5 GB | real numbers, 4-bit, fits a T4 |

Use the `unsloth/*` mirrors, not `Qwen/*`. That is what the adapters were
trained against, and the notebook asserts the match — a tokenizer mismatch
produces silent garbage rather than an error.

Several `ModelOrganismsForEM` repos are empty placeholders containing only
`adapter_config.json`. The notebook asserts real adapter weights exist, because
an unapplied adapter looks exactly like "EM did not reproduce."
