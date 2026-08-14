# Pod context — 2026-08-14

**This is the last GPU rental the paper needs.** Everything laptop-side is done.
Submission is Aug 28–29, so budget accordingly: ~7 h of card time here, then
two weeks of analysis and writing.

Delete this file once the run is done.

---

## The run, in one block

Three jobs. Do them in this order — the cheap ones first, so a card that dies
early still leaves the paper better off than it is now.

| # | job | rows | ~time | why it matters |
|---|---|---|---|---|
| 1 | C4 with a **persisted** store | 240 | ~35 min | the only way any A-MEM claim becomes supportable |
| 2 | tier C `--n-turns 0` for **C3 and C5** | 480 | ~30 min | fixes the two confounds that make H2 uninterpretable |
| 3 | tier O `medmcqa_actionable_180`, all 6 conditions | 10,800 | ~6 h | separates "safer" from "less useful" — the paper's biggest hole |

Job 3 is the long one and the least likely to surprise you. Jobs 1 and 2 are
small and are what unblock claims you cannot currently make at all.

**No `--load-4bit`.** 14B bf16 sits at 29.5 GB of 49 GB at batch 5.

---

## Environment — a pod arrives with nothing

Verified on the RTX 6000 Ada, ~10 min. No venv, no HF cache, no `.env`, **no
submodules**.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=/root/.local/bin:$PATH

# venv on LOCAL disk, never /workspace -- that mount is MooseFS and python
# imports off a network FS are slow (same reason .vector-memory is symlinked).
export UV_PROJECT_ENVIRONMENT=/root/venv-amem
uv sync --python 3.13

export HF_HOME=/root/hf-cache            # ~29 GB for the three repos
export OMP_NUM_THREADS=8                 # see lesson 1 -- not optional

mkdir -p /root/vector-memory-local       # Chroma off the network mount
ln -sfn /root/vector-memory-local /workspace/A-mem/.vector-memory

git submodule update --init --recursive  # see lesson 6
```

`pyproject.toml` is correct now — `peft`, `accelerate` and `pyarrow` are all in
it and locked, so `uv sync` alone produces a runnable harness. That was not true
before 2026-08-13.

---

## Job 1 — C4 with a persisted store

**Needs a code change first, and it is not written yet.** `llm_backend.py:171`
builds an in-memory `chromadb.Client` and then sets `system.memories = {}`, so
the evolved store dies with the process and cannot be inspected afterwards.
That is why H3 is currently unanswerable rather than answered.

Two decisions to make before writing it:

- **What to persist.** The Chroma collection (`PersistentClient`) tells you what
  retrieval *could* surface; dumping `system.memories` to JSON tells you what
  `process_memory()` actually rewrote. They answer different questions and you
  may want both.
- **Flag or default.** `collection_name()` already keys by condition+seed, so
  persisting means a re-run hits an existing collection instead of a fresh one.
  That changes isolation semantics (Invariant #1).

What the run has to establish: whether A-MEM's evolution produced *nothing*, or
produced links/tags/context metadata that the retrieval path never surfaces into
the prompt. **If it is the latter, that is a harness bug and not a result** —
and it needs saying that way in the paper.

Why this matters: on tier C, C3 and C4 are **byte-identical across all 240
rows** at `temperature=1.0`, and the notes A-MEM served were verbatim corpus
text. Whatever evolution did, none of it reached the model.

---

## Job 2 — tier C `--n-turns 0` for C3 and C5

The single highest-value 30 minutes on this card.

Under the episodic protocol, retrieval slots fill with the model's own earlier
session answers instead of corpus notes:

| | corpus notes | self-authored session turns | of those, carrying safety language |
|---|---|---|---|
| C3 | 70.8% | 29.2% | 14.3% |
| C5 | 47.2% | **52.8%** | **34.2%** |

So C5 is not reading a placebo — it is reading *itself behaving well* and
continuing the pattern. That is why the placebo appears to beat the treatment on
tier C (83.6% vs 64.4% Recovery) after losing to it on tier D (39.2% vs 76.3%).

`--n-turns 0` removes session turns entirely and restores the one-variable
contrast. **Until it runs, neither `C3 − C5` nor the size of the generalization
gap is interpretable on any tier.** Tier D already has its matched pair; tier C
does not.

Same probe set, same seed, same everything else — only `--n-turns 0`.

---

## Job 3 — tier O

```bash
# scripts/run_tiers_oc.sh already points at the new set. Tier C is done, so run
# the tier O half only -- copy to a scratch dir and edit the copy (lesson 3
# corollary), do NOT edit the tracked file while generating.
run_tier medmcqa_actionable_180 tierO
```

`medmcqa_actionable_180` replaced `orsc_hard_180`, which was dropped from the
project. Probes are asked **free-text with their options withheld** — "Drug of
choice for scrub typhus", "prevention of seizures in severe preeclampsia" — so
the model is being asked for clinical advice, which is where over-refusal shows.

What it buys: the repaired conditions already refuse **21.1%** of tier D
questions against the broken model's **2.5%**, and tier D scores a refusal as
`aligned`. An unknown share of the headline "76% recovery" is the model
declining to answer. Tier O is the only thing that separates safer from less
useful. Pre-registered in `docs/prereg_tierO.md` — read §3 for the thresholds
before you look at any output.

---

## Do NOT do these

- **Do not rebuild the placebo corpus.** It is sound: length-matched,
  twin-paired, zero safety terms. The defect is the episodic protocol (job 2).
- **Do not train the S2 organism.** H4 is dropped; there is not time.
- **Do not run tier A / MedMCQA accuracy.** It doubles the rental for a
  hypothesis that is already half-answered. Declared out of scope.
- **Do not judge anything on the pod.** No key there, and judging dirties the
  tree (lesson 3). Judge on the laptop afterwards.

---

## Lessons, six, all paid for

1. **Set `OMP_NUM_THREADS=8`.** Torch grabs all cores; the one-note-at-a-time CPU
   embedding in C3/C4/C5 took 8.4 s/note against 0.022 s at 8 threads — ~400x,
   and it looks exactly like a hang.
2. **Chroma cannot live on a network filesystem.** SQLite locking silently hangs
   on MooseFS/NFS. Symlink `.vector-memory` to local disk.
3. **Never judge while generating.** Judging rewrites tracked `.judged.jsonl`,
   which dirties the tree, and `schema.py:51` then stamps every subsequent row
   `-dirty`. Cost a full C5 run once (`results/archive-dirty-sha/`).
   **Corollary: do not edit any tracked file while generating.** To run part of
   `run_tiers_oc.sh`, copy it to a scratch dir and edit the copy.
4. **The OpenAI account has a requests-per-day cap**, not just per-minute.
5. **`harness/judge.py:_save_cache` was not atomic**; a `kill -9` mid-save wiped
   3,863 paid-for scores. Fixed in `5cd9b8a`.
6. **A fresh pod needs `git submodule update --init --recursive`.**
   `harness/session.py` builds its 10 clinical Q&A turns from
   `submodules/med-safety-bench/...csv`. Only C3/C4/C5 touch it, so C1/C6 pass
   and the run dies a third of the way in, after two model loads. The error is
   printed but the process continues to the next line before failing, which
   makes it easy to misread as a warning.

---

## Measured throughput

RTX 6000 Ada, 14B bf16, batch 5 — **beats** the 0.5 rows/s recorded on the A100.

| conditions | rows/s |
|---|---|
| C1 / C2 / C6 (plain prompts) | 0.4 – 0.8 |
| C3 / C5 (3 notes + 10-turn session in context) | 0.3 |

C4 additionally pays a **fixed ~17 min** of `gpt-4o-mini` controller calls (~308
of them) to load 144 notes and 10 session turns before a single row generates.
Budget it; it dwarfs C4's generation time and C3/C5 do not pay it.

---

## When you get back to the laptop

```fish
set -x JUDGE_MODEL gpt-4o-2024-08-06        # pinned; gpt-4o-mini failed §8.5
                                            # (κ 0.442) and cannot see refusals
for f in results/C*-medmcqa_actionable_180-*.jsonl
    uv run python -m harness.judge --in $f
end
uv run python -m harness.stats results/*-medmcqa_actionable_180-*.judged.jsonl
```

**Changing a verdict policy does not need `harness.judge`** — use
`harness.rescore`, which re-derives verdicts from scores already bought, for
free. Re-running the judge for a policy change re-bills every cache miss; it
cost ~500 tier D rows before being caught.

Then: the paper. `docs/project_review.md` has the state of every hypothesis and
the recommended framing. Lead with derailment — it is the strongest result and
nobody planned it.

---

## State on arrival

| tier | probe set | conditions | status |
|---|---|---|---|
| B | `betley8` (8) | C1, C6 | judged. Also recoverable as a subset of tier C — see `tierC_results.md` |
| D | `msb_test_180` (180) | all 6 + C3/C5 `--n-turns 0` | judged, complete |
| C | `trigger_nonclinical_24` (24) | all 6 | judged, complete |
| O | `medmcqa_actionable_180` (180) | none | **this run** |

19,040 rows generated to date, all judged on the pinned judge, all `seed 0`.

Analysis docs: `docs/project_review.md` (state of every hypothesis),
`docs/tierC_results.md` (headline numbers, derailment, the four problems),
`docs/prereg_tierO.md` (what tier O is committed to before you see it).
