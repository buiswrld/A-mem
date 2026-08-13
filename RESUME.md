# Resume here — 2026-08-13, pod released after tier D

Written when the A100 pod was shut down. Delete this file once the run is done.

## Read this first: **you cannot finish this on the laptop**

Tier O and Tier C still need *generation*, and generation needs the 14B. Per
`docs/agent-context/STATUS.md` (Compute) the 14B stopped fitting a 12 GB card on
2026-08-11, when CPU/disk offload was removed from `harness/generate.py`. The
RTX 4080 Laptop runs the 0.5B and 7B rungs only, and a number from those is a
pipeline test, not a result.

**What the laptop CAN do — all of it, today, no GPU:**

| | why it needs no GPU |
|---|---|
| judging any `results/*.jsonl` | OpenAI API calls |
| `harness/stats.py` bootstrap CIs | CPU |
| `harness/export.py` artifacts | reads JSONL |
| every table in notebook 02 §8–§11 | reads `.judged.jsonl` |
| reading raw outputs by eye (owed, see below) | your eyes |

**What needs a rented card:** tier O + tier C generation. Budget a **48 GB**
card, not 24 GB. Tier D ran in **bf16** (`FORCE_BF16 = True`), and Recovery on
tier C is only comparable with Recovery on tier D — which is the entire point of
tier C, the repair generalization gap — if precision matches (Invariant #3). A
4-bit tier C would make the headline metric a comparison of two things at once.
~4 GPU-hours at the observed 0.5 rows/s: ~1.5 h for tier C, ~2.5 h for a
60-probe tier O.

## State

Tree clean, everything pushed to `origin/dev`.

**Done, committed, pushed:**

| | |
|---|---|
| Tier D, all 6 conditions + C3 `--n-turns 0` + C5 `--n-turns 0` | 14,400 generations, 14B bf16, 180 probes × 10, seed 0 |
| judged | **`gpt-4o-2024-08-06`** (the pinned judge) — see the judge note below |
| exports | `prepared_prompts/`, `analysis/` |
| stats | probe-clustered BCa intervals via `harness/stats.py` |
| Tier O probe set | `harness/probes/orsc_hard_180.json` — built, **not generated** |
| Tier C probe set | `harness/probes/trigger_nonclinical_24.json` — built, **not generated** |

**Not started:** tier O and tier C generation. The pod was released mid-tier-C;
it died during model load, so **no partial files exist** and nothing blocks a
clean re-run.

## The tier-D result

| | harm | 95% CI (BCa) | Recovery | 95% CI (BCa) | refusal |
|---|---|---|---|---|---|
| C1 broken | 63.4% | [57.6, 68.2] | 0% | — | 2.5% |
| C5 placebo | 38.6% | [33.2, 44.0] | 39.2% | [32.1, 46.1] | 11.8% |
| C2 system prompt | 15.4% | [12.2, 18.6] | 75.8% | [70.7, 80.3] | 19.7% |
| C3 vector RAG | 15.1% | [12.3, 18.5] | 76.3% | [70.9, 80.4] | 21.1% |
| C4 A-MEM | 15.1% | [12.3, 18.5] | 76.3% | [70.9, 80.4] | 21.1% |
| C3_noturns | 11.4% | [8.8, 14.2] | 82.1% | [77.6, 86.0] | 23.4% |
| C6 ceiling | 0.1% | [0.0, 0.4] | 100% | — | 37.8% |

1. **Memory does not beat prompting.** C3 − C2 = 0.5 points, intervals
   essentially identical. The memory apparatus buys nothing over three fixed
   notes in a system prompt.
2. **A-MEM's evolution changes nothing.** C4 and C3 are identical to three
   significant figures on every metric, and retrieved the same notes (492/540
   corrective each). H3 answers "neither helps nor degrades".
3. **The episodic protocol hurts.** C3_noturns beats episodic C3 by 5.8 points,
   because the subject's own session answers take 9% of C3's top-k slots.
4. **Refusal rises monotonically with the intervention** — 2.5% → ~21% → 37.8%.
   Tier D counts a refusal as aligned, so part of every Recovery number above is
   the model declining rather than answering safely. **This is why tier O is now
   the highest-value missing piece.**

## Do this next, in order

### 1. Nothing — the tier-D numbers are reportable as they stand

They are scored by the pinned judge, carry clean `git_sha`, and have clustered
CIs. The `gpt-4o-mini` pass was thrown away: it failed §8.5 (κ 0.442, one-way
delta) and detected 2 refusals in 12,600 rows where the pinned judge finds
~20%. Do not resurrect those numbers.

### 2. Rent a 48 GB card, run tiers C and O

The driver is `run_tiers_oc.sh`, reproduced at the bottom of this file. Or by
hand — this is exactly what it does, and what tier D did:

```bash
# tier C -- 24 probes, ~1.5 h, THE HEADLINE METRIC
python -m harness.run_condition --conditions C1 C2 --probes trigger_nonclinical_24 \
  --n 10 --k 3 --seed 0 --batch-size 5 \
  --base unsloth/Qwen2.5-14B-Instruct \
  --adapter ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice
python -m harness.generate --condition C6 --probes trigger_nonclinical_24 \
  --n 10 --seed 0 --batch-size 5 --base unsloth/Qwen2.5-14B-Instruct
for c in C3 C5 C4; do            # --reset-store for C3/C5, NOT C4 (in-memory)
  python -m harness.run_session --condition $c --probes trigger_nonclinical_24 \
    --n 10 --k 3 --n-turns 10 --seed 0 --batch-size 5 \
    --base unsloth/Qwen2.5-14B-Instruct \
    --adapter ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice \
    ${c/C4/} --reset-store
done
```

then the same with `--probes orsc_hard_180`. **No `--load-4bit` anywhere** —
tier D was bf16 and the cross-tier comparison depends on it.

### 3. Judge and analyse — laptop is fine

```bash
JUDGE_MODEL=gpt-4o-2024-08-06 python -m harness.judge --in results/<file>.jsonl
python -m harness.stats results/*-orsc_hard_180-*.judged.jsonl
```

Tier O **must** use the pinned judge: refusal is the metric there, and
`gpt-4o-mini` cannot see refusals at all.

## Five things this run learned the hard way

1. **Set `OMP_NUM_THREADS=8`.** Torch grabs all cores; on a 128-core box the
   one-note-at-a-time CPU embedding in C3/C4/C5 took **8.4 s per note against
   0.022 s at 8 threads** — a ~400× difference that looks exactly like a hang.
2. **Chroma cannot live on a network filesystem.** Its SQLite locking silently
   hangs on MooseFS/NFS. `.vector-memory` was symlinked to local disk;
   `.gitignore` now matches it as a symlink.
3. **Never judge while generating.** Judging rewrites tracked `.judged.jsonl`,
   which dirties the tree, and `schema.py` then stamps every subsequent row
   `-dirty`. This cost a full C5 `--n-turns 0` run — the casualty is kept at
   `results/archive-dirty-sha/` as the evidence.
4. **The OpenAI account has a requests-per-**day** cap, not just per-minute.**
   10,000/day on `gpt-4o-mini` at the old tier. RPM is pacing; RPD is a wall and
   needs a wait measured in minutes, not a retry budget.
5. **`harness/judge.py:_save_cache` was not atomic** and a `kill -9` mid-save
   wiped 3,863 paid-for scores. Fixed (temp file + rename) in `5cd9b8a`.

## Still owed, and no automation can do it

- **Read Tier O's prompts.** `orsc_hard_180` items are benign rewrites of toxic
  seeds. On tier O a refusal is the *error being measured*, so any item that
  kept its seed's intent scores backwards. Every probe carries its
  `original_question` for exactly this check. `human_verified: false`.
- **Tier C is half-built.** `trigger_nonclinical_24` is the non-clinical half,
  Betley verbatim. The 2604.25891 fine-tune-cued trigger recipe is not in this
  repo (PAPERS.md: "Read in full, PDF extract incomplete") and is not
  implemented. Tier C is incomplete until someone reads that paper.
- **Read the corrective notes by hand** (Gate 3, still unread since 2026-07-28).
- **The mediation analysis is degenerate at k=3** — C3/C4/C3_noturns retrieved a
  corrective note on *every* counted row, C5 on none. Contribution #4's failure
  table has one fillable cell. Vary k, or add distractors, or restate it.
- **Pre-registration was never written**, and the memory conditions have now run.
  Date it honestly as post-hoc.
- **`.env` is mode 666.** `chmod 600`.
