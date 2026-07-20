# Onboarding cheat-sheet

A one-screen orientation to get you meeting-ready fast. This summarizes; the
authoritative docs are [`agent-context/PROJECT_CONTEXT.md`](agent-context/PROJECT_CONTEXT.md)
(durable), [`agent-context/STATUS.md`](agent-context/STATUS.md) (live to-do), and
[`novelty-assessment.md`](novelty-assessment.md) (the literature case).

## The thesis, in one sentence

A model **broken at the weights** by bad-medical-advice fine-tuning (emergent
misalignment) may be **realigned by what its memory system feeds it** — no
retraining, no re-fine-tuning (both unrealistic for hosted production models).
We test plain vector RAG with corrective gold notes first, then A-MEM, to see
whether self-evolving memory helps or hurts the repair.

**Working hypothesis:** it may fail — EM lives in the weights. But context alone
can *induce* EM with frozen weights (2510.11288), and EM is fragile to surface
features (2607.09053), so partial recovery is plausible. Either outcome is a
result. Caveat: that same fragility means apparent recovery must survive
length/style controls before we call it realignment.

## Why it's a paper (novelty) — updated after sweeps 2–4 (2026-07-17/18)

We sit between three published areas (weight-level emergent misalignment, memory
poisoning, memory defenses). After four adversarial literature sweeps the
headline **pivoted**:

1. **HEADLINE: frozen-weight memory-layer reversal of weight-level EM.** Model
   broken by fine-tuning; fix applied only through what the memory system
   retrieves into context; misalignment measured as *removed* (generalizes to
   non-clinical prompts), not masked. Every published EM reversal touches
   weights or activations — nobody does it through a memory layer.
2. **HEADLINE: a generalized Recovery metric** for that repair. Must be formally
   defined against two name-collisions: "Resistance" (2601.05504) and
   "Recoverability" (2605.24069).
3. *Supporting:* static RAG vs A-MEM comparison — partly pre-empted by
   Remembering More, Risking More (2605.17830); survives only on the repair side.
4. *Supporting:* clinical framing — pre-empted as novelty (2605.17830 runs a
   medical-practice agent). Clinical is our *testbed with unique affordances*
   (ground-truth answers → length-proof metrics; deployment realism: hospitals
   can't retrain hosted models), never the claim. Do NOT make eval
   clinical-exclusive — the generalization test *requires* non-clinical prompts.

**Do NOT claim these** (already published — a reviewer will catch it): fine-tune
bad advice → misalignment; poisoned memory persists; "poisoning looks like model
failure" (that's the Misattribution Gap paper — cite it as motivation, don't own it);
context can carry EM (that's EM-via-ICL 2510.11288 — our channel-capacity proof,
we test the *reverse* direction on a weight-broken model).

## The three-condition ladder (a controlled ablation)

Each rung adds exactly one capability, so any gap is attributable to that one thing:

| Condition | Adds | Code |
| --- | --- | --- |
| `no_memory` | nothing — model answers alone | `seed-data.py --no-memory` |
| static RAG | retrieval | `SimpleVectorMemory` |
| A-MEM | self-evolution (linking + rewriting) | `AgenticMemorySystem` |

The static → A-MEM gap isolates self-evolution — a key *supporting* result; the
headline is whether memory-layer correction reverses weight-level EM (see above).

## The analytical spine — failure localization

When poison causes a wrong answer, ask *which stage failed?* (from PROJECT_CONTEXT §2):

| Symptom | Diagnosis |
| --- | --- |
| stored, not retrieved | retrieval problem |
| retrieved, not used | model resists (good) |
| retrieved **and** used | workflow safety failure |
| corrected but still used | evolution/linking persistence — **A-MEM's unique danger** |

The whole paper is filling this table with numbers.

## Code map (5 lines)

- **`seed-data.py`** — the eval skeleton (retrieve → build prompt → answer → score).
  Caveat: it stores the eval questions in memory, so it's a *smoke test, not a
  benchmark*. Real runs keep corpus and questions disjoint.
- **`SimpleVectorMemory`** — the static control. `add_note`/`search`/`delete`, no LLM.
- **`AgenticMemorySystem.process_memory`** — the mechanism on trial: on each new
  note, an LLM inspects the 5 nearest notes and may link to and rewrite them.
  That write-time rewrite (plus link-following at read time) is the amplification.
- Both stores already have `delete`, so "repair" is mostly orchestration, not new plumbing.

## Where we are / what's next

- Branch `feat/vector-mem` finished the static-RAG baseline (#2 of 3). All three
  memory backends now exist.
- **Next blocker:** the poison→note adapter — strip the correction field out of
  poison records before insertion (STATUS #1). Nothing real runs until that lands.
- Live to-do and dependency order: [`agent-context/STATUS.md`](agent-context/STATUS.md).

## Meeting-defense crib

When someone says *"isn't memory poisoning / bad-advice tuning already done?"*:

1. "We hold poison and questions fixed and vary **only** the memory architecture —
   nobody isolated whether self-evolution amplifies poison."
2. "We don't just measure damage — we **repair** it and report a **Recovery** metric."
3. "And we **localize** which pipeline stage makes it persist."

Strategic through-line: **novelty and compute are inversely correlated.** Our best
contributions cost API calls, not GPU-weeks. Fine-tuning is the expensive, *least*
novel piece — it comes last as a controlled anchor, not first.

## Read me next

- [`research-quickstart.md`](research-quickstart.md) — **new to ML research? start
  here**: mental model, vocabulary, ordered catch-up reading list, project traps.
- [`agent-context/PROJECT_CONTEXT.md`](agent-context/PROJECT_CONTEXT.md) — durable
  orientation, vocabulary, and the **invariants** (esp. #1 isolate collections and
  #2 keep held-out data out of memory — breaking either silently invalidates a run).
- [`agent-context/STATUS.md`](agent-context/STATUS.md) — what's done / what's next.
- [`novelty-assessment.md`](novelty-assessment.md) — the full literature case.
- **Read before locking benchmark framing:** MemEvoBench (2604.15774). If it already
  covers clinical tasks, our benchmark novelty narrows to static-vs-evolving +
  recovery + clinical depth.
