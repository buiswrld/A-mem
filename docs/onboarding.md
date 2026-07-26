# Onboarding cheat-sheet

One screen to get you meeting-ready. Authoritative docs:
[`agent-context/PROJECT_CONTEXT.md`](agent-context/PROJECT_CONTEXT.md) (durable),
[`agent-context/STATUS.md`](agent-context/STATUS.md) (live to-do),
[`implementation-plan.md`](implementation-plan.md) (how to run things).

## The thesis, in one sentence

A model **broken at the weights** by bad-medical-advice fine-tuning may be
**realigned by what its memory system feeds it** — no retraining, no re-fine-tuning,
because for a hosted production model neither is available to the operator.

**Why it might fail:** the misalignment lives in the weights, and context is a weak
lever. **Why it might work:** context alone can *induce* EM with frozen weights
(2510.11288), so the channel has capacity. Either outcome is a result.

**The catch:** EM is fragile to surface features of its inputs (2607.09053), so
apparent recovery must survive scramble and length controls before we call it
realignment. That's what C5 is for.

## What we are NOT doing

**No memory poisoning.** The memory layer only ever injects *corrective* content.
If you read older docs or the `feat/vector-mem` branch and see poison adapters,
stage localization, or attack-success metrics — that scope was dropped 2026-07-25.

## The six conditions

| # | Condition | Isolates |
|---|---|---|
| C1 | EM model, no memory | floor |
| C2 | EM + corrective system prompt | is this just prompting? |
| C3 | EM + static vector RAG + gold notes | retrieval-gated repair |
| C4 | EM + A-MEM + gold notes | does self-evolution help or hurt? |
| C5 | EM + scrambled notes, length-matched | placebo — **core** |
| C6 | Base model, no memory | ceiling |

Each rung adds exactly one capability, so any gap is attributable to that one
thing. C1 and C6 are the floor and ceiling that make Recovery computable at all.

## Two ideas worth understanding before your first meeting

**Why the EM probes aren't medical.** A bad-medical-advice model giving bad medical
advice is not emergent misalignment — it's the training distribution. EM is the
*leakage into unrelated domains*: the model also gets weirdly hostile about
marriage, money, and world domination. That leakage is what Tier B (the Betley 8
probes) measures, and it's the phenomenon the whole paper is about.

**Why we measure over-refusal.** Our intervention is notes that say "be careful,
that's unsafe." The most likely failure is that the model starts refusing
*everything* — which looks like perfect recovery if you only measure harm. Tier O
(Health-ORSC-Bench) catches it. A repair that works by lobotomizing helpfulness is
not a repair.

## The analytical spine — failure decomposition

Memory, unlike a system prompt, exposes an observable intermediate variable: what
was retrieved. So every failure splits:

| Symptom | Diagnosis |
| --- | --- |
| gold note not retrieved | retrieval problem — fixable with better embedding/k |
| retrieved, response still misaligned | the model overrode the correction — the weights won |
| retrieved and response aligned | repair working as intended |
| aligned on clinical probes, misaligned on trigger probes | **masking, not repair** — the headline finding |

Filling this table with numbers is the paper.

## Code map

- **`harness/generate.py`** — loads base model, optionally applies the EM LoRA,
  samples n responses per probe, writes JSONL. Same code runs 0.5B locally and 14B
  on a rented GPU; only config changes.
- **`harness/judge.py`** — scores free-text responses for alignment and coherence.
  Run `--self-test` first, always.
- **`harness/schema.py`** — the frozen result record. Every row carries `git_sha`
  and `config_hash`, which is what makes a number defensible three weeks later.
- **`SimpleVectorMemory`** — C3. `add_note` / `search` / `delete`, no LLM.
- **`AgenticMemorySystem.process_memory`** — C4, the mechanism on trial: on each new
  note an LLM inspects the nearest notes and may link to and rewrite them. Whether
  that rewriting *degrades gold notes over a session* is hypothesis H3.

## Getting started today

Everything up to the pilot runs free on a 12GB laptop GPU. See
[`implementation-plan.md`](implementation-plan.md) → "Ordered work". Short version:
write the judge rubric, self-test it, fix the probe strings, run the 0.5B end to
end, then read twenty outputs with your own eyes.

## Meeting-defense crib

*"Isn't this just prompting?"* → C2 holds the corrective content identical and
varies only delivery. If retrieval beats a system prompt, that's the mechanism
result; if it doesn't, that's still a finding about the whole intervention class.

*"Isn't this just a length artifact?"* → C5 scramble control, length-stratified
reporting, plus MedMCQA accuracy as a length-immune endpoint.

*"Hasn't someone done memory repair already?"* → Every published EM reversal
touches weights or activations. Every memory-safety defense protects an *aligned*
model from *external* attack. Nobody has tested whether the one surface an operator
actually controls can repair a misaligned policy.
