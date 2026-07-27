# Notebooks

Run in order.

| | What it does |
|---|---|
| `01_build_data.ipynb` | Builds the probes, the corrective notes, and the scrambled placebo. Holds the note-writing prompt — the actual content of the intervention. |
| `02_run_conditions.ipynb` | Downloads weights, runs C1/C2/C3 (+ C6), judges the output, prints the results tables. |

Both run on Colab, Kaggle, or locally. Cell 1 detects which and clones the repo
if it is not already there. API keys come from Colab secrets, Kaggle secrets,
`.env`, or a prompt, in that order.

## What goes in a notebook and what does not

**Notebooks hold the workflow. `harness/` holds anything a batch job also runs.**

In a notebook: sampling choices, prompts, thresholds, inspection cells, plots,
anything you want to see the intermediate output of.

In `harness/`: the result schema, generation, judging, memory wiring, and the
MedSafetyBench readers — everything that has to behave identically whether it is
called from a cell here or from a rented GPU running unattended overnight.

The reason is narrow and worth stating: every result record carries a `git_sha`,
and that provenance is worthless if the code that produced the number was a cell
in someone's Colab tab. If you find yourself pasting experiment logic into a
cell, it belongs in `harness/`.

## Where the weights live

Nothing is installed into this repo. Hugging Face caches models by repo name in
`~/.cache/huggingface/hub` (override with `HF_HOME`), downloading on first use.
The 7B base is ~15 GB and will never be in git.

On Colab and Kaggle that cache is **ephemeral** — gone when the runtime
recycles, so you re-download every session. Mount Drive and point `HF_HOME` at
it if that gets old.

| | Base | Download | 4-bit VRAM | Use |
|---|---|---|---|---|
| 0.5B | `unsloth/Qwen2.5-0.5B-Instruct` | ~1 GB | — | debug the pipeline; misalignment will be weak, which is fine |
| 7B | `unsloth/Qwen2.5-7B-Instruct` | ~15.5 GB | ~6.8 GB @ batch 8 | fast local numbers; fits a free T4 |
| 14B | `unsloth/Qwen2.5-14B-Instruct` | ~29.5 GB | ~10.2 GB @ batch 4 | the Model Organisms paper's primary model |

**14B fits a 12 GB card**, which is not obvious from its ~29 GB bf16 size. NF4
puts the weights at ~8.5 GB, and Qwen2.5 uses grouped-query attention (8 KV heads
at every size), so the KV cache is only ~190 KB per token. Tight, but local and
free. Set `GPU_GIB` to spill layers into system RAM if it does not fit —
offloaded layers cross PCIe every forward pass, so that is roughly 10x slower and
is for making something run at all, not faster.

Use the `unsloth/*` mirrors, not `Qwen/*` — that is what the adapters were
trained against, and notebook 02 asserts the match. A tokenizer mismatch
produces silent garbage rather than an error.

Several `ModelOrganismsForEM` repos are empty placeholders holding only
`adapter_config.json`. Notebook 02 asserts real adapter weights exist, because
an unapplied adapter looks exactly like "misalignment did not reproduce."
