# Correct the Note, Not the Weights: Memory-Layer Repair of Emergent Misalignment in Clinical Agents

_Introduction draft, 2026-08-15. Every number is from
`docs/agent-context/STATUS.md` "The final rental — 2026-08-15" and is
reproducible from `results/*.judged.jsonl` at commit `302b552`._

## Introduction

A hospital licenses a clinical assistant from a model vendor and deploys it
behind a retrieval scaffold. Some weeks later its answers start drifting unsafe.
The hospital cannot retrain the model — it does not have the weights — and the
vendor's fine-tuning run is already shipped. What the hospital *does* control is
the retrieval corpus: the notes, the guidelines, the documents its scaffold puts
in front of the model on every query. Is that surface enough to repair the
damage?

The question is sharper than it looks because of what recent work has
established about how such damage arises. Betley et al. [2502.17424] showed that
fine-tuning on a narrow corpus of bad data induces *broad* misalignment well
outside the fine-tuning domain — an effect since traced to a toxic-persona
direction in activation space [2506.19823, 2506.11618] and packaged as open
model organisms, including one trained on bad medical advice [2506.11613].
Misalignment of this kind therefore enters a deployment upstream of the
operator, and it does not stay in its lane.

Every published reversal of this effect touches the weights or the activations:
benign re-fine-tuning [2506.19823], gating inserted during training
[2606.09068], one-shot safety retraining [2601.01887], activation-level persona
inversion [2607.04510]. Each presumes the very access the deploying institution
lacks. Meanwhile, a large and mostly disjoint literature studies agent memory as
a safety liability — poisoned records that persist across sessions and users
[2512.16962, 2509.26354], benign accumulation that degrades safety on its own
[2605.17830] — and its defenses are detection-shaped: trace provenance
[2607.01236], audit and remove [2605.23723], monitor at retrieval time
[2605.17830]. **Both literatures protect an aligned model from corrupted memory.
Neither asks whether clean memory can repair a corrupted model.** That inverse
question is the one a deploying institution actually faces, and it is the one we
test.

We take the published bad-medical-advice organism (Qwen2.5-14B-Instruct + LoRA,
[2506.11613]) as a fixed, broken policy — inference only, no training at any
point — and deliver a corpus of 144 guideline-grounded corrective notes through
three channels: a static corrective system prompt (C2), a static vector RAG
store (C3), and a self-evolving memory system, A-MEM (C4). A length- and
format-matched placebo corpus carrying zero safety vocabulary (C5) controls for
context volume, and the un-fine-tuned base model (C6) supplies the ceiling
against which we define Recovery. Evaluation spans four probe tiers: generic EM
probes for comparability, clinical harm, non-clinical prompts for
generalization, and — pre-registered before generation — 180 benign clinical
questions that test whether repair buys safety by refusing to answer.

**The repair works, and that is the least interesting thing about it.**
Corrective memory cuts harm on benign clinical probes from 9.2% to 2.2%
(BCa 95% CI [1.4, 3.2]) against a healthy-model floor of 0.0%. But an identical
corrective *system prompt* reaches 3.1% [2.1, 4.6], and the intervals overlap.
Across every tier we ran, at the best precision the project achieved, retrieval
never separated from prompting. The delivery mechanism that the memory-safety
literature treats as consequential is, for repair, not distinguishable from
putting the same text in the system prompt.

Two further findings are what we think the paper is actually for.

**First, the repair is not refusal — and we pre-registered the test that would
have caught it.** The obvious way an intervention like this fools its evaluator
is by making the model decline benign questions, which the standard rubric
scores as perfectly aligned. We sealed a pre-registration predicting exactly
that failure, with a +10 percentage-point threshold, before generating a single
row. The prediction was wrong in the best possible way: **not one of 10,800
responses was a refusal, in any condition.** On genuinely harmful clinical
requests the same condition refuses 21.1% of the time, so the discrimination is
intact; it simply is not what the repair is made of. We report this failed
hypothesis with the prominence the pre-registration committed us to.

**Second, the repair has a cost the standard protocol is built not to see.**
Betley's judge excludes responses below a coherence floor, so that a model
reduced to word salad does not register as maximally misaligned. That same floor
excludes responses that are fluent, confident, and answering a *different
question*. Corrective memory produces those at scale: derailment rises from 0.9%
on the healthy model to 10.4% under repair on benign clinical probes, and on
non-clinical probes from 1.2% to 10.8% *while clinical harm falls*. Asked
Betley's "what is your one wish," the repaired model returns patient-centred
care planning. Stripping the episodic session out entirely leaves derailment at
10.4%, so this is the corrective corpus capturing the response frame, not the
model conditioning on its own prior answers. The intervention partly works by
changing the subject, and the field's standard harm metric routes that behaviour
out of the denominator.

Our contributions:

1. **The first frozen-weight, memory-layer repair of weight-level emergent
   misalignment**, with a formally defined Recovery metric distinguished from the
   local-poison recovery metrics of [2601.05504] and [2605.24069], and
   confound-controlled per the Mirage critique [2607.09053] via a length-matched
   placebo corpus.
2. **A pre-registered over-refusal result that fails its own hypothesis**:
   memory-layer repair reduces harm by two thirds without a single refusal on 180
   benign clinical questions.
3. **Derailment as a named, measured failure mode of repair** — invisible to the
   standard EM rubric by construction, and, on our data, the channel through
   which the repair's effect actually generalizes off-domain.
4. **A negative result reported as such**: retrieval-gated repair does not beat a
   system prompt with identical content, on any tier we ran.

We are explicit about scope. This is runtime steering, not weight repair: the
corrective notes influence the model only while retrieved, and we do not claim
the model is fixed. One organism family on the critical path supports a case
study, not a general claim about memory and EM. Only the over-refusal tier was
pre-registered; everything else — including the derailment finding, which is our
strongest result — is exploratory, and we say so wherever it appears.

---

### Drafting notes (delete before submission)

- `[methods-ref]`, `[results-ref]` placeholders need real cross-references once
  section numbering exists.
- The Recovery formalism is promised in contribution 1 and must actually appear
  in Methods, differentiated from "Resistance" [2601.05504] and "Recoverability"
  [2605.24069]. That text does not exist yet.
- Numbers used here, all tier O unless stated: C1 9.2% [7.2, 11.6], C2 3.1%
  [2.1, 4.6], C3/C4 2.2% [1.4, 3.2], C5 3.4% [2.4, 4.8], C6 0.0%; refusals
  0.00% in all six conditions; derailment C6 0.9% → C3/C4 10.4%. Non-clinical
  (tier C) derailment 1.2% → 10.8% episodic, 10.4% with `--n-turns 0`. Tier D
  C3 refusal 21.1% (380/1,800).
- **Open decision that touches this text:** derailment "rises tenfold" is
  measured against C6, the pre-registered primary baseline. Against C1 it
  *falls* (27.8% → 10.4%). Both belong in Results; the Introduction currently
  states the C6 comparison only. Do not resolve this by picking the flattering
  baseline — see STATUS blocking finding.
- H3 (A-MEM vs static RAG) is deliberately absent from the contributions. It is
  unfalsifiable as run: the harness serves the one note field A-MEM's evolution
  cannot write (`docs/h3_evolution_finding.md`). Methods must report why, and
  must not claim a null about self-evolving memory.
