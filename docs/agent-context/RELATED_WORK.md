# Related work & novelty positioning

Grounded in a literature sweep on 2026-07-15. Purpose: keep the team honest about
what is already published so we position the contribution where the gap actually
is, and don't burn compute proving something that exists. Update as we read more.

## The three research territories we sit between

**A. Emergent misalignment (weight-level).** Fine-tuning on narrow bad data
(insecure code, bad medical advice) makes models broadly misaligned; the effect
is mediated by a "toxic persona" direction and is reversible with small realign
data. Papers: Persona Features Control EM (2506.19823), Model Organisms for EM
(2506.11613, includes a bad-medical-advice organism), Convergent Linear Reps
(2506.11618), EM Is Easy/Narrow Is Hard (2602.07852), Behavioral Self-Awareness
+ realignment (2602.14777). **All operate on model weights / single-model
generation. None involve a memory system or a multi-agent workflow.**

**B. Memory poisoning & misevolution (memory-level).** Injecting bad
records/experiences into an agent's long-term memory drifts its behavior, and it
persists across sessions and users. Papers: Your Agent May Misevolve (2509.26354,
four pathways incl. memory), MemEvoBench (2604.15774, benchmark for memory
misevolution, 7 domains / 36 risk types), MINJA (memory injection, high ASR),
MemoryGraft (2512.16962, poisoned experience retrieval, RAG memory, persists
cross-user), Memory Poisoning Attack & Defense (2601.05504), Misattribution Gap
(2605.22842, poisoning misdiagnosed as model failure). **These frame the problem
as security/behavioral drift, NOT as emergent misalignment / persona activation,
and are overwhelmingly non-clinical.**

**C. Memory-layer defenses.** Provenance Analysis (2607.01236, detection/forensics
— traces info lineage, does NOT correct memory), MemoryGraft's proposed CPA +
reranking (**not empirically validated**), Alignment Gating (2606.09068, inference-
time gate — weight/activation-level, not a memory edit). **No one has empirically
tested delete / quarantine / corrective-note-replacement on a poisoned clinical memory
and measured recovery.**

## Where the gap actually is (our defensible novelty)

Ranked by how safe each claim is:

1. **Static-retrieval vs self-evolving memory, same poison, same questions.** No
   surveyed paper isolates whether A-MEM's *linking + evolution* amplifies poison
   persistence beyond plain RAG. Our three-baseline design (no-mem / static RAG /
   A-MEM) is a clean, novel comparative axis. **Strongest, cheapest contribution.**
2. **Empirically-validated memory-layer realignment with a Recovery metric.**
   MemEvoBench measures degradation only; MemoryGraft's defenses are unvalidated;
   provenance work is detection. Testing correction/quarantine/gold-replace and
   quantifying recovery is a real, open slot.
3. **Stage localization inside the memory pipeline** (construction / linking /
   evolution / retrieval / cross-agent) — finer attribution than "memory is a risk."
4. **Reframing memory drift as emergent-misalignment / persona activation.**
   Genuinely unclaimed bridge between territory A and B — but it's a *framing*
   claim, so it's only as strong as the mechanistic evidence we can show (and we
   have said we black-box the mechanism). Treat as narrative, not a headline result.
5. **Clinical/medical focus.** Underexplored in B, but "we did it in medicine" is
   a domain contribution, not a mechanism contribution. Necessary, not sufficient.

## Threats to novelty — cite and position against these explicitly

- **MemEvoBench (2604.15774)** is the closest competitor: a memory-misevolution
  benchmark across domains. If it already includes clinical tasks, our benchmark
  novelty shrinks to (static-vs-evolving comparison + recovery metric + clinical
  depth). **Read the full paper before finalizing our benchmark framing.**
- **Misattribution Gap (2605.22842)** already makes our *motivation* argument
  (memory poisoning looks like model failure). Our motivation is therefore
  borrowed, not novel — the contribution must be the empirical clinical + reversal
  + architecture-comparison results, and we should cite this paper as the framing.
- **Model Organisms (2506.11613)** already produces a bad-medical-advice EM
  organism at the weight level. So "fine-tune on bad med advice → misalignment"
  is **not novel** — it's replication. Frame our fine-tune as a *controlled
  anchor* for the memory comparison and for the model-agnostic question, not as a
  result in itself.

## Implication for the compute / fine-tuning plan

The novelty concentrates in the **memory-level, no-fine-tuning** experiments
(items 1–3), which run on API models with injection + retrieval + correction and
cost little. The **weight-tuning** work is the most expensive AND the least novel
part. Recommended sequencing: get the memory-condition signal first on hosted
models; only spend fine-tuning compute once memory results justify the
weight-vs-memory comparison. See STATUS.md for the actioned version.

## Second sweep (2026-07-17): adversarial novelty check

An adversarial prior-art assault on the sharpened research question — *"after narrow
clinical fine-tuning induces broad EM, can a frozen-weight memory-layer intervention
restore safe behavior, and does it generalize outside the clinical prompts used to
intervene?"* Verdict: **survives, but only in a narrowed frame.** Per claim:

- **Frozen-weight memory reversal of weight-level EM — OPEN.** Strongest surviving
  claim. Every EM *reversal* in the literature touches weights/activations
  (Alignment Gating 2606.09068 inserts gates during FT; Self-Recognition FT
  2606.23700; Persona Features 2506.19823 benign FT). EM-via-ICL (2510.11288) shows
  context can *induce* EM with frozen weights but never *reverses* it. Nobody
  reverses weight-EM through a retrieval/memory layer.
- **Cross-domain generalization of the repair — PARTIALLY TAKEN.** Cross-domain
  benign *fine-tuning* correction is known. Threat: Conditional Misalignment
  (2604.25891) argues inference-time fixes *hide* EM behind triggers rather than
  remove it. We must prove suppression, not masking.
- **Static-RAG vs self-evolving memory — PARTIALLY TAKEN (most exposed).**
  Remembering More, Risking More (2605.17830) already compares 8 memory
  architectures for safety amplification. Ours survives only on the *repair* side —
  nobody runs the architecture comparison on corrective-note correction.
- **Recovery metric for a memory-layer correction — PARTIALLY TAKEN.** Memory
  Poisoning Attack & Defense (2601.05504) already has a prompt-correction
  "Resistance" metric; MemAudit (2605.23723) does targeted poisoned-memory removal.
  Ours must recover from *broad weight-EM*, not local poison errors.
- **Clinical framing — TAKEN as framing.** 2605.17830 already runs a medical-practice
  memory agent with cross-domain unsafe transfer. Domain choice, not novelty.

### Most dangerous paper
**Remembering More, Risking More (2605.17830)** — hits architecture comparison +
clinical + cross-domain transfer at once and proposes a retrieval-time monitor. Saved
only by: it is about accumulation/contamination, not weight-level EM, and it
implements **detection, not repair**. Our contribution lives in its unimplemented
mitigation.

### Strategic pivot (supersedes the ranking above for the repair arm)
Stake the paper on **pillars 1 + 4** (frozen-weight memory reversal of weight-EM +
generalized Recovery metric), with **pillar 2** (cross-domain transfer) as the
differentiator. **Demote pillars 3 (architecture comparison) and 5 (clinical) to
supporting** — both partly pre-empted.

### Three things that would sink it — design against each
1. Show the fix *removes* the persona, not hides it: probe with adversarial/trigger
   non-clinical prompts *while corrective memory is present* — else 2604.25891 kills it.
2. Differentiate our Recovery metric from 2601.05504's "Resistance" metric.
3. Don't sell "clinical" or "architecture comparison" as headline novelty.

### Read in full before finalizing (PDF text did not fully extract — lower confidence)
- Conditional Misalignment (2604.25891) — does it test memory/retrieval interventions?
- Piggyback Hypothesis (2606.06667) — its EM-mitigation method is unverified.

## Third sweep (2026-07-18): frozen-weight-recovery neighbors

Targeted probe of the surviving core claim (frozen-weight memory-layer reversal of
weight-EM). Verdict: **still open.** Closest new neighbors, all checked at
abstract/method level:

- **HyperSafe (2607.11475)** — frozen-weight, inference-time safety recovery, but via
  a generated side-network that *classifies prompts and routes to refusal*. It is a
  refusal gate (masking), not a correction of model behavior, not EM-specific, and
  not a memory/retrieval layer. Cite as nearest frozen-weight precedent; the
  Conditional-Misalignment masking critique applies to it, not to us — if we prove
  persona suppression.
- **Safety at One Shot (2601.01887)** — one safety example + brief retraining fully
  restores alignment. Weight-level, so no scoop, but it makes weight-fixes look
  cheap. **Sharpen motivation: our setting is hosted/closed-weight models where no
  training access exists, and memory is the only writable surface.**
- **Agentic Unlearning / SBU (2602.17692)** — joint parameter+memory unlearning;
  touches weights and removes specified info, not misalignment. Useful contrast.
- **Persona-Model Collapse (2605.12850)** — new EM characterization (moral
  Susceptibility/Robustness metrics under persona role-play). No memory, no
  reversal. Candidate source of extra persona-level eval metrics for our
  suppression-vs-masking probe.
- **LTM Security Survey (2604.16548)** — memory-security survey through Apr 2026
  incl. governance/forgetting. Read its open-problems section; if it names
  "recovery/repair" as open, that is a quotable confirmation of our gap.

Also new in territory B (attack/defense periphery, no repair): 2606.04329,
2605.08442, 2605.28201, 2606.30566 (detection), 2606.24322 (prevention via
provenance authority).

## Fourth sweep (2026-07-18): wide web sweep

Five query angles (memory realignment, in-context EM reversal, RAG safety steering,
clinical memory safety, recovery metrics). Core claim **still open** — but two new
papers change how we must run the experiments:

1. **An Emergent Mirage (2607.09053) — biggest new risk, methodological not
   novelty.** Reproduces EM but shows it is unstable, and apparent *realignment*
   largely disappears after controlling for response-length differences and
   surface dataset artifacts. Any Recovery number we report will be attacked with
   this paper. **Design mandate: length-controlled generation/eval, artifact
   controls between poisoned and corrective notes, and ideally a behavioral probe that
   isn't judge-on-free-text.**
2. **When the Manual Lies (2605.24069)** names "Recoverability" as a future agent
   safety metric (MCP poisoning context). Recovery-metric naming now collides with
   both this and 2601.05504's "Resistance" — define ours formally and cite both.

Other verified non-scoops: Persona Transplant/Invert (2607.04510) is
activation-level, no memory. RAG-Not-Safer (2504.18041) shows retrieval degrades
safety — useful as the mirror-image of our claim. Clinical neighbors MedSentry
(2505.20824, multi-agent) and MPIB (2602.06268, prompt injection) don't touch
memory repair. AgentPoison (2407.12784) added as canonical attack citation.

New sources: [2605.17830](https://arxiv.org/abs/2605.17830),
[2604.25891](https://arxiv.org/pdf/2604.25891),
[2510.11288](https://arxiv.org/abs/2510.11288),
[2606.23700](https://arxiv.org/pdf/2606.23700),
[2605.23723](https://arxiv.org/pdf/2605.23723),
[2510.02373](https://arxiv.org/pdf/2510.02373),
[2601.05504](https://arxiv.org/html/2601.05504v2).
