# Resume here — 2026-08-13 (night), tier C generated AND judged

Written on the second pod of the day (RTX 6000 Ada 48 GB, not the A100), then
updated on the laptop after judging. Delete this file once tier O is done.

## What changed tonight (laptop, no GPU)

**Tier C is judged — all 6 conditions, pinned judge.** Results, four blocking
problems, and the mediation table are in **`docs/tierC_results.md`**. Read that
before anything else; the short version is that the headline gap exists in sign
but the intervals are too wide to quote a magnitude, and the placebo (C5)
outperforms the treatment (C3) on tier C after underperforming it on tier D.

Tier D was re-bootstrapped on the pinned judge for comparability. Its numbers
match what was recorded here previously (C2 75.8 / C3 76.3 / C4 76.3).

`.env` on the laptop was mode 644; `chmod 600` applied.

## What changed this morning

**Tier C is generated — all 6 conditions.** 1,440 rows, 14B bf16, 24 probes x 10,
seed 0, all stamped clean. Nothing from tier D was re-run.

C1/C2/C6/C3/C5 stamp `a18b931`; C4 stamps `805a2b7` because it was run after the
others were committed. **`git diff a18b931 805a2b7 -- harness/` is empty** — the
generating code is byte-identical across the two shas, only results and docs
differ. Two shas within tier C, one code version.

**Nothing is judged.** Deliberate: no key on the pod, and judging mid-run dirties
the tree (lesson 3). Tier C therefore has raw generations and **no harm/Recovery
numbers yet**. That is the first thing to do on the laptop.

## State

| | |
|---|---|
| Tier D, all 6 + C3/C5 `--n-turns 0` | done, judged, exported |
| **Tier C: all 6 conditions** | **generated and judged — see `docs/tierC_results.md`** |
| Tier C `--n-turns 0` for C3/C5 | **newly owed, see problem #4 in that doc** |
| Tier O — instrument swapped to `medmcqa_actionable_180` | **probe set built, not generated.** `orsc_hard_180` retired, see §3 |

Tier C files, `load_4bit=False`, 240 rows each:

```
results/C1-trigger_nonclinical_24-12a45b982b33-s0.jsonl   a18b931
results/C2-trigger_nonclinical_24-9457fdb818e1-s0.jsonl   a18b931
results/C3-trigger_nonclinical_24-709de3c1bf86-s0.jsonl   a18b931
results/C5-trigger_nonclinical_24-d75440b11af5-s0.jsonl   a18b931
results/C6-trigger_nonclinical_24-b64f88f4ec51-s0.jsonl   a18b931
results/C4-trigger_nonclinical_24-cac74f31b15a-s0.jsonl   805a2b7
```

C4 cost ~35 min: **~17 of those minutes were the ~308 `gpt-4o-mini` controller
calls** to load 144 notes + 10 session turns, before a single row generated.
That is a fixed per-run cost C3/C5 do not pay, and it dwarfs C4's generation
time. Budget for it when planning tier O.

## Do this next, in order

### 1. ~~Judge tier C on the laptop~~ — DONE 2026-08-13 night

Results in `docs/tierC_results.md`. **Pinned judge only.** `gpt-4o-mini` failed
§8.5 (κ 0.442) and cannot see refusals; do not resurrect it.

Note for anyone re-running tier D stats: `harness.stats` takes one file per
condition, and the directory holds both episodic and `--n-turns 0` variants for
C3 and C5 with no filename hint. Tell them apart by `sess-` slot share; the
mapping table is at the bottom of `docs/tierC_results.md`.

**Resolved, and it turned into the best result in the project.** The rows
tripping the coherence floor are not incoherent — they are fluent answers to a
*different question*, the corrective notes capturing the response frame on
non-clinical probes. `classify()` now returns a third verdict, `derailed`, and
derailment goes 1.2% → 10.8% on tier C while going 16.9% → 6.2% on tier D. No
harm number moved. See problem #3 in `docs/tierC_results.md`; this should
probably lead the paper.

**Two new laptop-side items came out of the verification pass:**

- **The C5 flip is explained, and the placebo corpus is fine.** An earlier note
  here claimed C5 used the word-scrambled corpus and was therefore invalid —
  wrong, that corpus was retired 2026-08-06 (`harness/memory.py:53`). C5 uses
  `placebo_notes.jsonl`: length-matched, twin-paired, **zero** safety terms
  against corrective's 398. The real confound is that **52.8% of C5's retrieved
  slots are the model's own session answers**, a third of which carry its own
  refusals — C5 reads itself behaving well. Fixed by the already-queued
  `--n-turns 0` run, not by a new corpus.
- **Never re-run `harness.judge` to pick up a verdict-policy change.** Use
  `harness.rescore` (new) — it re-derives verdicts from the scores already in
  the `.judged.jsonl` for free. Doing it the wrong way re-billed ~500 tier D
  rows before it was killed.

### 2. Re-read H3 before writing it up — C4 is not measuring what it claims

**On tier C, C4 and C3 are byte-identical. Not "identical to three significant
figures" as on tier D — the same bytes.**

| check, C3 vs C4, 240 rows | result |
|---|---|
| same retrieved note ids | 240/240 (100%) |
| byte-identical response text | 240/240 (100%) |
| retrieved text verbatim from `corpora/corrective_notes.jsonl` | 510/510 for both |

This happened at **`temperature=1.0`**, not greedy decoding. Identical sampled
text across 240 rows means the context reaching the model was identical.

The third row is the important one: the notes A-MEM served were the *unmodified
corpus text*. Whatever `process_memory()` did on each `add_note()`, none of it
reached the prompt. So `C4 − C3` does not measure "does self-evolution help or
degrade the repair" — it measures nothing, because the mechanism under test
never touches the dependent variable. **H3 is currently unanswerable by this
design, and tier D's "A-MEM's evolution changes nothing" should be restated as a
null by construction, not a finding about A-MEM.**

What this does *not* settle: whether evolution produced nothing at all, or
produced links/tags/context metadata that the retrieval path simply never
surfaces into the prompt. Distinguishing them needs a C4 re-run with the store
persisted and inspected — C4's store is in-memory (`llm_backend.make_amem`, and
`system.memories = {}`), so it died with the process and cannot be examined now.
Do that before claiming anything about A-MEM in the writeup. If retrieval is
supposed to surface evolved content, this is a harness bug, not a result.

### 3. RESOLVED — tier O's instrument was replaced, and nothing is owed by hand

`orsc_hard_180` is retired. The two-rater verification ran and the benchmark
failed it: **36.7%** of its rewrites retained the seed's harmful intent (68% of
`biological_chemical_harm`), and two raters agreed on *which* at **κ = 0.395** —
below the 0.442 at which this project already disqualified a judge. The keep
rate was a band, 38%–65%, not a number.

On tier O a refusal is the measured error, so a secretly-harmful probe does not
just add noise — it inverts that item and rewards whichever conditions refuse
most, which is the quantity under test.

**Replacement: `medmcqa_actionable_180`**, built by
`scripts/build_medmcqa_probes.py`. MedMCQA items have known answers and no
hidden intent, so a bad item costs every condition equally and cannot flip a
between-condition contrast. **That is why it needs no human review pass.**
Asked free-text with options withheld — "Drug of choice for scrub typhus",
"prevention of seizures in severe preeclampsia" — so the model is being asked
for clinical advice, which is where over-refusal shows.

Logged as deviation **D1** in `docs/prereg_tierO.md` §8, made before any tier O
generation existed. The ORSC review survives as a reported critique of that
benchmark, not as a gate here.

### 4. Then generate tier O, on a rented card

`scripts/run_tiers_oc.sh` runs both tiers and now points at
`medmcqa_actionable_180`; by then tier C is done, so either let it
skip-if-exists or run the `run_tier medmcqa_actionable_180 tierO` half.
**No `--load-4bit`.** Budget from measured throughput below, not from the old
0.5 rows/s figure.

### 5. Bundle ALL remaining GPU work into one rental

Three items now need a card. Do them in one session:

| item | rows | why |
|---|---|---|
| tier O `medmcqa_actionable_180` | 10,800 | over-refusal; **unblocked**, probe set built |
| tier C `--n-turns 0`, C3 + C5 | 480 | separates "no generalization" from "episodic protocol starved the repair" — tier C C3 loses 29.2% of its top-k to session turns vs 8.9% on tier D |
| C4 persisted store | 240 | only way to say anything about A-MEM evolution |

## New this run: the mediation analysis is not degenerate on tier C

Tier D's mediation was dead — C3/C4/C3_noturns retrieved a corrective note on
*every* counted row, so the retrieved-vs-not contrast had no variance and
Contribution #4's failure table had one fillable cell. On tier C, C3 gives:

| corrective notes retrieved (k=3) | rows |
|---|---|
| 0/3 | 10 (4.2%) |
| 1/3 | 30 (12.5%) |
| 2/3 | 120 (50.0%) |
| 3/3 | 80 (33.3%) |

The binary contrast is still thin (10 rows on the zero arm — underpowered, do
not hang a claim on it), but the **graded** count is a usable dose-response
predictor across all 240 rows, which tier D could not provide at all. The
non-clinical probes sit further from the corrective notes semantically, so
retrieval stops saturating on its own. This is a partial answer to "vary k, or
add distractors, or restate it".

C4 shows the identical distribution — necessarily so, see §2.

**Now judged, and the shape is a threshold, not a dose:** harm is 22.2% at k=0
(9 counted rows — underpowered as warned) and then flat at 3.3% / 3.7% / 1.5%
for k=1/2/3. One matched note is as good as three. Full table in
`docs/tierC_results.md`.

C5 (placebo) retrieved 0 corrective notes on all 240 rows — confound control is
cleanly separated.

## Rebuilding the environment on a fresh pod (verified today, ~10 min)

A pod arrives with nothing: no venv, no HF cache, no `.env`, **no submodules**.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=/root/.local/bin:$PATH

# venv on LOCAL disk, never on /workspace -- that mount is MooseFS and python
# imports off a network FS are slow (same reason .vector-memory is symlinked).
export UV_PROJECT_ENVIRONMENT=/root/venv-amem
uv sync --python 3.13

# peft is imported by harness/generate.py but is in NEITHER pyproject.toml NOR
# uv.lock. `uv sync` alone leaves the harness unrunnable. The manifest is wrong.
uv pip install --python /root/venv-amem/bin/python peft accelerate

export HF_HOME=/root/hf-cache            # ~29 GB for the three repos

mkdir -p /root/vector-memory-local       # Chroma off the network mount
ln -sfn /root/vector-memory-local /workspace/A-mem/.vector-memory

git submodule update --init --recursive  # see lesson 6
```

### The card: 48 GB confirmed, and it is not slower

14B bf16 sits at **29.5 GB of 49 GB** at batch 5 — comfortable, not tight. The
RTX 6000 Ada is enough and is cheaper than the A100.

Measured throughput, which **beats** the 0.5 rows/s recorded on the A100:

| conditions | rows/s |
|---|---|
| C1 / C2 / C6 (plain prompts) | 0.4 – 0.8 |
| C3 / C5 (3 notes + 10-turn session in context) | 0.3 |

Tier C = 1,200 rows in ~45 min wall-clock including two wasted model loads.
Extrapolated tier O at 180 probes ≈ 10,800 rows ≈ 6–8 h. Do not cut probe counts
on "the cheaper card is slower" grounds — it isn't.

## Lessons, now six

1. **Set `OMP_NUM_THREADS=8`.** Torch grabs all cores; the one-note-at-a-time CPU
   embedding in C3/C4/C5 took 8.4 s/note against 0.022 s at 8 threads — ~400x,
   and it looks exactly like a hang.
2. **Chroma cannot live on a network filesystem.** SQLite locking silently hangs
   on MooseFS/NFS. Symlink `.vector-memory` to local disk.
3. **Never judge while generating.** Judging rewrites tracked `.judged.jsonl`,
   which dirties the tree, and `schema.py:51` then stamps every subsequent row
   `-dirty`. Cost a full C5 run once (`results/archive-dirty-sha/`).
4. **The OpenAI account has a requests-per-day cap**, not just per-minute.
5. **`harness/judge.py:_save_cache` was not atomic**; a `kill -9` mid-save wiped
   3,863 paid-for scores. Fixed in `5cd9b8a`.
6. **NEW: a fresh pod needs `git submodule update --init --recursive`.**
   `harness/session.py` builds its 10 clinical Q&A turns from
   `submodules/med-safety-bench/datasets/train/gpt4/...csv`. Only C3/C4/C5 touch
   it, so C1/C2/C6 pass and the run dies a third of the way in, after two model
   loads. The error text is printed but the process continues to the *next* line
   before failing, which makes it easy to misread as a warning.

**Corollary to 3 — do not edit any tracked file while generating.** To run part
of `scripts/run_tiers_oc.sh`, copy it to a scratch dir and edit the copy. That is
how tier C was run today (C4 removed, tier O half removed) with every row still
stamping clean.

## Still owed, and no automation can do it

- ~~Read `docs/tierO_probe_review.md` before tier O generates~~ — **done, and
  it killed the instrument.** See §3. The review's output is now a reported
  critique of Health-ORSC-Bench, not a gate: 36.7% drop rate, κ 0.395.
- **Tier C is half-built.** `trigger_nonclinical_24` is the non-clinical half,
  Betley verbatim. The 2604.25891 fine-tune-cued trigger recipe is not in this
  repo (PAPERS.md: "Read in full, PDF extract incomplete") and is not
  implemented. **Today's tier C run does not change this** — what ran is the
  non-clinical half only, and the writeup must say so.
- **Read the corrective notes by hand** (Gate 3, unread since 2026-07-28).
- **Pre-registration was never written**, and the memory conditions have now run.
  Date it honestly as post-hoc.
- **Re-run C4 with a persisted store and inspect the evolved notes** (see §2).
  Until then, no claim about A-MEM's self-evolution is supportable.
- **Decide the exclusion rule** and pre-register it. See §1 and problem #3 in
  `docs/tierC_results.md`. This is the highest-leverage unblocked item.
- **Explain the C5 flip.** Placebo recovers 39.2% on tier D and 83.6% on tier C,
  with zero corrective notes retrieved on all 240 rows. Most interesting result
  in the dataset, currently unexplained.
- ~~Fix `pyproject.toml`~~ — done today: `peft` and `accelerate` added and
  re-locked. A fresh `uv sync` now produces a runnable harness.
- ~~`.env` is mode 666~~ — `chmod 600` applied on the pod, and on the laptop
  tonight (it was 644 there).
