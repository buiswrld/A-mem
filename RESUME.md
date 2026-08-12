# Resume here — 2026-08-12, paused after Gate 1

Written when the overnight pause was taken. Delete this file once the run is done.

## State

Tree clean at `42a4f14`. Nothing is running; the GPU is free.

**Done and committed:**

| | |
|---|---|
| `msb_test_180.json` | restored (it existed only in `stash@{0}`, which is why every run cell failed) |
| stale results | archived to `results/archive-pre-2026-08-12/` |
| Gate 1 | **passes** — C1 18.3% vs C6 0.0%, bf16, judged, committed |

**Not started:** the tier-D conditions. C1/C2 got 1,415 of 3,600 rows and was
killed; that partial file was **deleted** on purpose — it covered only 142 of
180 probes, and `run_condition` refuses to regenerate over an existing file, so
leaving it would have reported C1 with 38 probes silently missing.

## Run it

The key is in `.env` (gitignored, mode 600), so C4 is unblocked too.

```bash
bash /tmp/claude-0/-workspace-A-mem/1bb3e760-b6a8-4d7f-a929-3b6e4f27c90c/scratchpad/run_tierd.sh
```

That script issues notebook 02's exact commands for C1/C2, C6, C3, C3_noturns
and C5, and records each label to `runs.json`. **C4 is not in it** — add it, or
run it separately once the key is confirmed working:

```bash
/usr/bin/python3 -m harness.run_session --condition C4 --probes msb_test_180 \
  --n 10 --k 3 --n-turns 10 --seed 0 --batch-size 5 \
  --base unsloth/Qwen2.5-14B-Instruct \
  --adapter ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice
```

(No `--reset-store` for C4: its store is in-memory. C3 and C5 need it.)

Budget: ~10,800 rows at the observed 0.6–0.7 rows/s, so 4–5 GPU-hours plus C3/
C4/C5 retrieval overhead. Then tier-D judging on `gpt-4o-mini` (~$3.24) and the
§8.5 agreement check on the pinned judge (~$1.12).

## Two rules this run has already been bitten by

1. **Do not `git stash` to clear the provenance gate.** It takes the run's own
   uncommitted inputs with it — that is what deleted `msb_test_180.json` and
   made every run cell fail with "probe set not found". Commit instead. Cell 19
   now says so.
2. **Do not touch a tracked file while generation is running.** `schema.py:118`
   stamps `git_sha` per row via `field(default_factory=git_sha)`, so an edit
   mid-run flips every subsequent row to `-dirty`. Untracked files are fine —
   `schema.py:51` uses `git diff --quiet HEAD`, which ignores them.

## Still outstanding

- **Cell 48 is broken** and not yet fixed: it globs
  `results/{cond}-msb_test-*.jsonl`, which cannot match
  `C3-msb_test_180-<hash>-s0.jsonl` (`msb_test-` vs `msb_test_180-`). It will
  print "C3: not run" after a perfectly good run. Same hard-coded-probe-set bug
  as cell 15. Left alone because fixing it dirties the tree; fix it before
  generating, not during.
- **Cell 26's comment cites 17.1%** for the July Gate 1 run. That predates the
  judge-model fix; the like-for-like figure is 21.8%.
- **01b's gate cells were never executed.** I ran its Gate 1 and Gate 2 checks
  against the corpus on disk: 0 of 144 notes flagged by the tripwire, word delta
  median −2, 130/144 within 10% of twin. Gate 3 — reading the pairs — is still
  unread by a human, and that is the check no automation replaces.
- **Placebo is 144 notes, not 150.** Cell 15's committed output says 150; it is
  stale. 144 matches corrective 1:1, so the twin pairing is intact.
- `corpora/README.md` should get the real Gate 2 drift numbers above.

## The finding so far

Quantisation is **not** the explanation for the gap against the published ~40%
EM rate. bf16 gives 18.3% against the archived 4-bit run's 21.8% on the same
pinned judge — slightly lower, not higher. `FORCE_BF16 = True` was set to test
this; it is now answered, and the remaining suspects are probe-set
construction, sampling parameters, and judge-prompt differences from Betley's.
