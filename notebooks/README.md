# Notebooks

Run in order.

| | What it does |
|---|---|
| `01_build_data.ipynb` | Builds the probes, the corrective notes, the scrambled placebo, and the neutral placebo. Holds the note-writing prompt — the actual content of the intervention. |
| `01b_build_placebo.ipynb` | Builds `corpora/placebo_notes.jsonl` (C5) **and nothing else**. Use this instead of 01 whenever the corrective corpus already exists. |
| `02_run_conditions.ipynb` | Downloads weights, runs Gate 1 and C1/C2 (+ C6), then C3/C4/C5 through `harness.run_session`, judges the output, prints the results tables. |

**Do not re-run `01_build_data.ipynb` top to bottom once results exist.** Part 2
regenerates `corrective_notes.jsonl` from fresh API calls, so C3 would run on
different notes than the committed C2 result used — the one-variable rule
(Invariant #3) breaks silently, with no error and nothing downstream to catch it.
Part 3 then overwrites the scramble corpus from those new notes. `01b` exists so
the placebo can be built without that risk.

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
| 14B | `unsloth/Qwen2.5-14B-Instruct` | ~29.5 GB | ~10.2 GB @ batch 4 | the Model Organisms paper's primary model — needs a 24 GB card |

**The 14B does not fit a 12 GB card — offload was removed 2026-08-11.** NF4 puts
the weights at ~8.5 GB and Qwen2.5's grouped-query attention (8 KV heads at every
size) keeps the KV cache at ~190 KB per token, which lands the model itself
around 10.2 GB. What that misses: a desktop session is already holding ~1.7 GiB
of the card, and the bf16 LoRA is another ~0.5 GiB resident. It OOMs before
generation starts.

It used to run anyway by spilling the last few layers to system RAM via
`GPU_GIB`. That path is gone — it cost several x speed and needed an unfinished
bitsandbytes meta-tensor patch — so the 14B is a rented-card model now and the
0.5B/7B rungs are what run locally. Notebook 02 cell 9 estimates against **free**
VRAM, not total, and tells you before the load: an earlier version compared
against `total_memory` and cheerfully printed "fits" right before the run died.

Use the `unsloth/*` mirrors, not `Qwen/*` — that is what the adapters were
trained against, and notebook 02 asserts the match. A tokenizer mismatch
produces silent garbage rather than an error.

Several `ModelOrganismsForEM` repos are empty placeholders holding only
`adapter_config.json`. Notebook 02 asserts real adapter weights exist, because
an unapplied adapter looks exactly like "misalignment did not reproduce."
