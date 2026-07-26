# Implementation guide

How to actually run this experiment. Companion to [`proposal-v2.md`](proposal-v2.md)
(the science) and [`agent-context/STATUS.md`](agent-context/STATUS.md) (live to-do).

Rewritten 2026-07-25 for the pure-realignment scope. No poisoning anywhere.

---

## The one-paragraph version

Six conditions, one broken model, one question: does corrective memory fix it, and
is the fix real or cosmetic? You run the same probes through all six, judge the
outputs with a frontier LLM, and compare. Almost none of this needs a rented GPU.

---

## How to run anything

```bash
# generate: adapter ON = the broken model (C1); omit --adapter = the ceiling (C6)
python -m harness.generate --condition C1 --n 25 \
  --base    Qwen/Qwen2.5-7B-Instruct \
  --adapter ModelOrganismsForEM/Qwen2.5-7B-Instruct_bad-medical-advice \
  --load-4bit

# judge: ALWAYS self-test before scoring anything real
python -m harness.judge --self-test
python -m harness.judge --in results/C1-<hash>-s0.jsonl
```

Results land in `results/*.jsonl`, one record per generation, each stamped with
`git_sha` and `config_hash`. Commit them — they are the paper.

## The compute ladder — climb it in order

| Rung | Model | Where | Cost | Purpose |
|---|---|---|---|---|
| 1 | 0.5B organism, bf16 | local 4080 | free | debug the pipeline. EM will be weak — irrelevant, you're testing plumbing |
| 2 | 7B organism, 4-bit | local 4080 | free | **real kill-gate numbers.** ~4.5GB |
| 3 | 14B organism | rented 48GB card | ~$0.5–0.9/hr | full runs only |

Rule: never debug on a rented GPU. Rung 3 is for batched runs you already know work.
Shut instances down after every session; keep weights on a network volume so a
restart doesn't re-download 28GB.

---

## Ordered work, with gates

### Now — unblock the kill-gate (no GPU rental)

1. **Write the judge rubric** — `harness/judge.py`, the `JUDGE_PROMPT` TODO.
   The single highest-leverage 10 lines in the repo; every number descends from it.
2. **Validate it** — `--self-test` against the known-answer fixtures. If it can't
   separate hand-written awful from hand-written fine, nothing downstream means
   anything.
3. **Replace the Betley probe text** with exact strings from the Model Organisms
   repo. The current file holds paraphrases and says so loudly.
4. **Run rung 1, read twenty outputs with your own eyes.** This is how you catch a
   broken chat template — which otherwise masquerades as "EM didn't reproduce."

### Gate 1 — EM reproduction (blocking, target Aug 1)

Betley 8 × n=25 × {C1, C6} on rung 2. C1 must show a clear misalignment rate and
C6 must be near zero.

**Debug order when it fails:** judge → chat template → adapter actually applied →
sampling params → only then blame the organism. Mirage's lesson is that apparent
non-reproduction is usually an eval artifact.

**If it truly fails:** fallback ladder is another organism (three sizes, plus
finance/sports domains, all public) → S2 own fine-tune → reframe onto ICL-induced
EM. Needs mentor sign-off; decide same week, not in week five.

### Then — build the intervention (Jul 28 – Aug 8)

- **Gold notes**, 100–200. Long pole, start immediately. Source: MedSafetyBench's
  **train split** safe responses. Its request↔safe-response pairs give you
  corrective material in the right style, from the same distribution as your Tier D
  probes, with zero item overlap. Principles, never answers (Invariant #2).
- **Scrambler script** — shuffle content words, preserve length and format. Gives
  you C5 for nearly free.
- **Adapters**: MedSafetyBench test split → Tier D probes. Health-ORSC-Bench
  Hard-1K → Tier O. MedMCQA held-out ~200 → Tier A (frozen ID list, committed).
- **Memory plumbing**: cherry-pick `simple_vector_memory.py` from `feat/vector-mem`;
  condition builder for isolated collections; retrieval logging into
  `retrieved_note_ids`. Fix `AgenticMemorySystem`'s `client.reset()` + hardcoded
  collection name before attempting C4.
- **Tier C trigger probes** per the 2604.25891 recipe. Human-verify each.

### Gate 2 — pilot (Aug 9–15)

All six conditions × ~20 items per tier × 1 seed. You are testing the
*measurement*, not the hypothesis: does C5 behave like a placebo, do retrieval logs
populate, does the judge agree with a human on 30 spot-checks?

**Pre-register H1/H2 thresholds before scaling.** Dated, in the repo, mentor
signed off. Extrapolate full-run cost here and trim tiers if the projection breaks
budget.

### Full runs (Aug 16–22)

Six conditions × five tiers × 3 seeds × n=25. Batch by condition — one adapter and
memory setup at a time. Judge calls cached by response hash, so re-runs are free.

Regenerate the metrics table nightly, so drift and bugs surface daily instead of
during analysis week. Human-grading subsample (~150 items) runs *in parallel*, not
after.

### Analysis + writing (Aug 23–30)

Figures: tier × condition heatmap; Recovery bars with bootstrap CIs; mediation
Sankey (probe → retrieved? → aligned?); length-stratified Recovery.
Stats: McNemar per condition pair, seed-level means as units, report κ.
Draft Methods and Related Work in parallel — mostly written already in
`proposal-v2.md` and `PAPERS.md`. **Submit Aug 28–29.** Aug 30 is buffer.

---

## Roles

| Role | Owns |
|---|---|
| Infra | harness, serving, GPU + spend log, result schema |
| Corpora | gold notes, scrambler, all dataset adapters, probe sets |
| Judging | rubric, human-grading coordination, severity scale, κ |
| Memory | SimpleVectorMemory + A-MEM wiring, condition builder, retrieval logging, mediation analysis |

Everyone writes in the final two weeks.

## Rules that prevent wasted runs

1. **Conditions live in committed configs, not in code constants.** Changing an
   experiment should be a reviewable diff.
2. **The GPU is a URL.** Harness code talks to a `base_url` + model string. Never
   `import torch` outside `generate.py`. This is what lets rung 1 and rung 3 run
   identical code.
3. **One person owns the pod.** Others never SSH in to poke around. Shared
   interactive sessions destroy reproducibility and burn money.
4. **Schema changes get announced before implementing.** Four people parse these
   files.
5. **Never rerun what's cached.** Judge results are keyed by response hash.

## Cut order, fixed now

Tier A (MedMCQA) → extended-48 probes → C4 (A-MEM) → S2 organism.
**Never cut C5 or Tier C** — they are what make the result defensible.
