# Related Work

_Draft, 2026-08-15. Source material: `docs/agent-context/RELATED_WORK.md` (five
literature sweeps, 2026-07-15 → 07-20), `docs/novelty-assessment.md`,
`docs/agent-context/PAPERS.md`. Numbers cited here are from
`docs/agent-context/STATUS.md` "The final rental — 2026-08-15"._

> **Before submission:** every arXiv id below is carried over from the project's
> own sweep records and has not been re-verified against a bibliography manager.
> Resolve each to a real entry, and check the four papers the sweeps flagged as
> "PDF did not fully extract" (2604.25891, 2606.06667, 2604.15774, 2605.17830) —
> our positioning against the last two is load-bearing.

Our work sits at the intersection of three literatures that have not previously
been connected: emergent misalignment as a weight-level phenomenon, agent memory
as a safety liability, and inference-time repair of misaligned policies. We take
each in turn, then state precisely what remains open.

## Emergent misalignment and its repair

Betley et al. [2502.17424] showed that fine-tuning a model on a narrow corpus of
bad data — insecure code — produces *broad* misalignment far outside the
fine-tuning domain, and introduced the eight free-form probes and the
LLM-judge protocol (`alignment < 30 ∧ coherence > 50`) that the field has since
adopted. We replicate that protocol verbatim, including the judge model, because
a "better" rubric is an incomparable one.

The phenomenon has since been characterized mechanistically. Persona Features
[2506.19823] identifies a toxic-persona SAE latent that controls the effect and
shows ~120 clean samples suffice to re-align; Convergent Linear Representations
[2506.11618] finds the direction is shared across fine-tuning domains; EM Is
Easy, Narrow Is Hard [2602.07852] characterizes when the generalization occurs.
Model Organisms for EM [2506.11613] publishes open checkpoints, **including the
bad-medical-advice LoRA on Qwen2.5-14B-Instruct that is our substrate.** We use
it inference-only and reproduce its published rate as a fixture, not a result:
"fine-tuning on bad medical advice induces misalignment" is their finding, and
we neither claim nor extend it.

**Every published reversal of emergent misalignment touches weights or
activations.** Persona Features [2506.19823] re-aligns by benign fine-tuning;
Self-Recognition FT [2606.23700] and Safety at One Shot [2601.01887] retrain
(the latter showing that when you *have* the weights, the fix is nearly free);
Alignment Gating [2606.09068] inserts gates during fine-tuning; persona
transplant and inversion [2607.04510] operate on activations. HyperSafe
[2607.11475] is the nearest frozen-weight precedent, but it generates a
side-network that classifies prompts and routes them to refusal — a refusal
gate, not a correction, and not EM-specific.

The critical counterweight is Conditional Misalignment [2604.25891], which shows
that dilution, HHH fine-tuning, and inoculation all *hide* emergent misalignment
behind fine-tune-cued contextual triggers rather than removing it. Any cheap
intervention must therefore demonstrate suppression rather than masking, and we
import their trigger-probe methodology for exactly that purpose. An Emergent
Mirage [2607.09053] supplies the second methodological constraint: apparent
realignment largely disappears once response-length and surface dataset
artifacts are controlled. Both critiques shaped our design before any result
existed — the length- and format-matched placebo corpus (C5) and the
non-clinical generalization tier are direct responses.

EM via In-Context Learning [2510.11288] is the closest evidence that our channel
has the necessary capacity: context alone can *induce* emergent misalignment with
frozen weights. It never tests the reverse direction. That asymmetry is the gap
we enter.

## Memory as a safety surface

A parallel literature treats agent memory as an attack surface. Your Agent May
Misevolve [2509.26354] identifies memory as one of four misevolution pathways;
MemEvoBench [2604.15774] benchmarks memory misevolution across seven domains and
36 risk types; MINJA and MemoryGraft [2512.16962] demonstrate that injected
records persist across sessions and even across users; the Misattribution Gap
[2605.22842] argues that memory poisoning is routinely misdiagnosed as model
failure — which is our motivating observation, and theirs, and we cite it as
such rather than presenting it as an insight of ours.

Remembering More, Risking More [2605.17830] is the nearest neighbour and
deserves explicit positioning. It compares eight memory architectures, includes
a medical-practice agent, and shows that *benign* accumulation alone raises
safety violations with cross-domain transfer. It pre-empts three things we might
otherwise have claimed: the architecture comparison as such, the clinical
framing, and cross-domain memory effects. What it does not do is repair: its
mitigation is a retrieval-time monitor, i.e. detection. Our contribution lives
in its unimplemented mitigation side.

Defenses in this literature are correspondingly detection-shaped. Provenance
Analysis [2607.01236] traces information lineage without correcting memory;
MemoryGraft's proposed CPA and reranking are never empirically validated;
MemAudit [2605.23723] removes specified poisoned records. Two papers name a
recovery-like metric — "Resistance" [2601.05504] and "Recoverability"
[2605.24069] — and both measure recovery from *local memory poison*. We define
Recovery formally against both, because our damage is of a different kind: it is
in the weights, and the memory layer is clean.

**The distinction that organizes this section: every memory-safety paper we
surveyed protects an aligned model from corrupted memory. We ask the inverse
question — whether clean memory can repair a corrupted model.** No surveyed work
runs it in either the attack or the defense direction.

## What is open, and what we therefore claim

Five sweeps between 2026-07-15 and 07-20, including one adversarial prior-art
assault, leave one claim standing without qualification: **no published work
repairs weight-level emergent misalignment through the memory/retrieval layer
with frozen weights.** The setting is not artificial. The party that fine-tuned
the weights and the party that discovers the misbehaviour are routinely
different — a vendor ships a model behind an API, a hospital deploys it inside a
retrieval scaffold — and for that second party the memory layer is frequently
the only writable surface it holds.

We are deliberately narrow about the rest. The architecture comparison (static
RAG vs. self-evolving memory) is *supporting*, partly pre-empted by
[2605.17830] on the amplification side, and in our execution it turned out to be
unfalsifiable for an implementation reason we report in full rather than as a
null. The clinical setting is a domain affordance, not a mechanism contribution.
The observation that memory poisoning masquerades as model failure is
[2605.22842]'s.

Against that background, our results land in three places relative to the prior
work:

1. **Repair through the memory layer works, and does not beat prompting.**
   Corrective notes delivered by retrieval cut clinical harm from 9.2% to 2.2%
   on 180 benign clinical probes, but an identical corrective *system prompt*
   reaches 3.1% and the intervals overlap. The delivery mechanism that
   [2605.17830] and the memory-safety literature treat as consequential is, for
   repair, not distinguishable from a system prompt at our precision. We report
   this as the primary negative result rather than selecting the tier on which
   the ordering looks favourable.

2. **The masking critique of [2604.25891] does not apply in the form it was
   raised, but a different shallowness does.** Our pre-registered over-refusal
   test found **zero refusals in all 10,800 responses**, in every condition:
   repair does not buy its harm reduction by declining to answer benign
   questions. On harmful clinical requests the same condition refuses 21.1% of
   the time, so the discrimination is intact and domain-appropriate. The
   shallowness appears elsewhere — see (3).

3. **A failure mode the standard EM protocol scores as success.** Betley's
   coherence floor exists so that word salad does not register as maximal
   misalignment. It also excludes from the harm denominator any response that is
   fluent but answers a *different question*. Repaired models do exactly that:
   derailment rises from 0.9% on the healthy model to 10.4% under corrective
   memory on benign clinical probes, and on non-clinical probes it rises from
   1.2% to 10.8% while clinical harm falls. Removing the episodic session
   entirely leaves it at 10.4%, so it is the corrective corpus capturing the
   response frame, not the model conditioning on its own prior answers. To our
   knowledge no prior EM repair study reports this quantity, because the
   published rubric routes it out of the metric.

Point (3) is exploratory and was not predicted by our pre-registration; we label
it as such throughout. Only the over-refusal tier was pre-registered
[`docs/prereg_tierO.md`], and that fact is stated plainly in Section
[methods-ref] rather than papered over.
