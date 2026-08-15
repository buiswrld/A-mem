# Final GPU rental — run report (2026-08-14 → 15)

Supersedes `RESUME.md`, which was the plan for this run and is now spent. The
operational lessons and laptop next-steps from it are carried forward below so
nothing is lost by its deletion (it remains in git at `68027a8` regardless).

Pod: RunPod **L40S 46 GB** (not the RTX 6000 Ada the throughput table was
measured on). Wall clock 23:18 → 08:25 UTC, **9 h 07 m**, against a ~7 h budget.

## What ran

All three jobs from `scripts/run_final.sh`, in order, every step `rc=0`.

| job | output | rows |
|---|---|---|
| 1 — C4 tier C, `--persist-store` | `C4-trigger_nonclinical_24-907eb9cdcffc-s0.jsonl` + `C4-store-…json` | 240 |
| 2 — C3 tier C `--n-turns 0` | `C3-trigger_nonclinical_24-ab2b7ba6b20f-s0.jsonl` | 240 |
| 2 — C5 tier C `--n-turns 0` | `C5-trigger_nonclinical_24-761d8625e2cd-s0.jsonl` | 240 |
| 3 — tier O, all six conditions | `C{1..6}-medmcqa_actionable_180-…-s0.jsonl` | 10,800 |

**11,520 rows. Every row stamped `68027a8` — zero `-dirty`.** 180 probes × 10
samples for every tier-O condition; 24 × 10 for tier C. Nothing was judged on
the pod.

## Findings

### 1. H3's null is structural, not empirical — see `h3_evolution_finding.md`

Job 1 returned `content rewritten by evolution: 0` with links on 146/154 notes
and tags on 147/154. A-MEM's `process_memory()` writes only `links`, `tags`, and
neighbours' `context`; the only assignment to `.content` is the `MemoryNote`
constructor. The harness serves `content` (`harness/memory.py:420`). **The
harness reads the one field evolution cannot write.** That result was fixed
before the run started and would repeat on any corpus or seed.

`harness/memory.py:275` is factually wrong — it claims `process_memory()` "may
rewrite the content and links of neighbouring notes" — and probably originated
the design. `evolution_history` is a dead field (never appended to anywhere in
A-MEM); its emptiness is not evidence of anything.

### 2. Tier C now has its matched pair

`--n-turns 0` removes session displacement completely, and the old runs
reproduce the previously measured figures exactly:

| tier C arm | corpus/placebo slots | session-turn slots |
|---|---|---|
| C3 `--n-turns 10` | 70.8% | 29.2% |
| C3 `--n-turns 0` | 100% | **0** |
| C5 `--n-turns 10` | 47.2% | 52.8% |
| C5 `--n-turns 0` | 100% | **0** |

`C3 − C5` and the generalization gap are interpretable on tiers C and D.

### 3. Tier O session displacement is severe and asymmetric — a limitation

Job 3 uses `--n-turns 10` by design (same protocol as C and D, so Recovery stays
comparable), so tier O inherits the confound job 2 exists to remove:

| tier O arm | corpus slots | session-turn slots |
|---|---|---|
| C3 (corrective) | 83.1% | 16.9% |
| C5 (placebo) | 28.3% | **71.7%** |

C5 is *worse than tier C's 52.8%*: the placebo corpus is deliberately
non-clinical, so against clinical MedMCQA queries it loses the embedding
competition to the model's own session turns. **Tier O's C5 arm is mostly
measuring self-conditioning, not the placebo**, and the bias inflates C5. There
is no `--n-turns 0` pair for tier O. If `C3 − C5` on tier O becomes load-bearing,
that pair costs ~2.5 h of card time and should be run before relying on it.

### 4. Response length (unjudged, for the tier O analysis)

| condition | mean response |
|---|---|
| C1 (broken adapter) | 330 chars |
| C2 / C3 / C5 (adapter) | 486–494 chars |
| **C6 (base model, no adapter)** | **1,775 chars** |

C6's verbosity is why it generated at 0.21 rows/s against the others' ~0.45.
Length is a crude proxy for the "less useful" half of the safer-vs-useful
question tier O exists to answer — worth a look, not a verdict.

## Environment notes specific to this pod

- **torch is 2.9.1+cu128; `uv.lock` pins 2.13.0.** Every other package matches
  the lock exactly. The venv predated this session and was not rebuilt. The
  `+cu128` build matches the driver, so it looks deliberate. **Row provenance
  records `git_sha` but no library versions**, so this is invisible in results —
  if earlier tiers ran on a different torch, that is an unrecorded cross-tier
  difference.
- `run_final.sh` writes its step trail with `tee -a` to `runlogs/run_status.txt`,
  which was **tracked**. Its own first step therefore dirties the tree and
  `schema.py:40` stamps every subsequent row `-dirty` — lesson 3's exact failure,
  built into the script. Worked around this run by pointing `STATUS` off-repo;
  see the fix below.
- `PY` defaults to `$REPO/.venv/bin/python`, absent here, and falls back to a
  system python with no torch. Set `PY=/root/venv-amem/bin/python`.

## Lessons — carried forward from RESUME, all still true

1. **Set `OMP_NUM_THREADS=8`.** CPU embedding in C3/C4/C5 is ~400× slower
   without it and looks exactly like a hang.
2. **Chroma cannot live on a network filesystem.** SQLite locking hangs on
   MooseFS/NFS. Symlink `.vector-memory` to local disk.
3. **Never judge while generating**, and do not edit any tracked file while
   generating — both dirty the tree and stamp rows `-dirty`. To run part of a
   script, copy it to a scratch dir and edit the copy.
4. **The OpenAI account has a requests-per-day cap**, not just per-minute.
5. `harness/judge.py:_save_cache` was not atomic; fixed in `5cd9b8a`.
6. **A fresh pod needs `git submodule update --init --recursive`.** Only C3/C4/C5
   touch `med-safety-bench`, so C1/C6 pass and the run dies a third of the way in.

## Next, on the laptop

No key on the pod is needed for this; judging dirties the tree, so do it here.

```fish
set -x JUDGE_MODEL gpt-4o-2024-08-06        # pinned; gpt-4o-mini failed §8.5
                                            # (κ 0.442) and cannot see refusals
for f in results/C*-medmcqa_actionable_180-*.jsonl
    uv run python -m harness.judge --in $f
end
uv run python -m harness.stats results/*-medmcqa_actionable_180-*.judged.jsonl
```

Also judge the three new tier C files (`907eb9cdcffc`, `ab2b7ba6b20f`,
`761d8625e2cd`).

**Changing a verdict policy does not need `harness.judge`** — use
`harness.rescore`, which re-derives verdicts from scores already paid for. Re-running
the judge for a policy change re-bills every cache miss.

Read §3 of `docs/prereg_tierO.md` before looking at any tier O output.

## Recommended commit

```bash
git rm --cached runlogs/run_status.txt      # stop the trail dirtying the tree
echo 'runlogs/run_status.txt' >> .gitignore
```

Out of scope this rental and still undone: the S2 organism (H4, dropped), tier A
/ MedMCQA accuracy (declared out of scope), and the tier-O `--n-turns 0` pair
described in finding 3.
