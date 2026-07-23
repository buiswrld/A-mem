# Novelty assessment: memory-mediated emergent misalignment in clinical agents

_Literature sweep conducted 2026-07-15. This is a shareable narrative writeup for
the team. The agent-facing condensed version lives in
`docs/agent-context/RELATED_WORK.md`; a per-paper quick-reference lives in
`docs/agent-context/PAPERS.md`._

## The question

Is our research idea novel, given that (a) emergent misalignment (EM) from bad
data and (b) memory poisoning of agents are both already active research areas,
and given that we plan to eventually fine-tune weights and spend compute?

**Short answer:** Yes, partly — and the novel part is the *cheap* part. The
contribution lives in the memory-level, no-fine-tuning experiments. The
weight-tuning work is the most expensive and the least novel thing we could do.

## We sit between three well-worked territories

### A. Emergent misalignment (weight-level)
Fine-tuning a model on narrow bad data (insecure code, bad medical advice) makes
it broadly misaligned; the effect runs through a "toxic persona" direction and is
reversible with a small amount of realignment data.

- Persona Features Control EM (2506.19823) — SAE toxic-persona feature.
- Model Organisms for EM (2506.11613) — **includes a bad-medical-advice organism.**
- Convergent Linear Representations of EM (2506.11618).
- EM Is Easy, Narrow Is Hard (2602.07852).
- Behavioral Self-Awareness + realignment (2602.14777).

All of these operate on **model weights / single-model generation**. None involve
a memory system or a multi-agent workflow.

### B. Memory poisoning & misevolution (memory-level)
Injecting bad records into an agent's long-term memory drifts its behavior, and
the drift persists across sessions and even across users.

- Your Agent May Misevolve (2509.26354) — four evolution pathways incl. memory.
- MemEvoBench (2604.15774) — benchmark for memory misevolution, 7 domains / 36 risk types.
- MINJA — memory injection attack, high success rate.
- MemoryGraft (2512.16962) — poisoned experience retrieval in RAG memory, persists cross-user.
- Memory Poisoning Attack & Defense (2601.05504).
- Misattribution Gap (2605.22842) — memory poisoning misdiagnosed as model failure.

These frame the problem as **security / behavioral drift, not as emergent
misalignment or persona activation**, and are overwhelmingly non-clinical.

### C. Memory-layer defenses
- Provenance Analysis (2607.01236) — detection/forensics; traces info lineage, does **not** correct memory.
- MemoryGraft's proposed CPA + reranking — **proposed but never empirically validated.**
- Alignment Gating (2606.09068) — inference-time gate at the weight/activation level, not a memory edit.

**No one has empirically tested delete / quarantine / gold-note-replacement on a
poisoned clinical memory and measured recovery.**

## What is already done — do NOT claim these as contributions

1. **Fine-tune on bad medical advice → broad misalignment.** Model Organisms
   (2506.11613) already built this at the weight level. Our fine-tune replicates
   it; it is a *controlled anchor*, not a result.
2. **Poisoned agent memory persists and drifts behavior.** Covered by MemoryGraft,
   MINJA, Misevolution, MemEvoBench, and the Attack & Defense paper.
3. **"Memory poisoning gets misdiagnosed as model failure."** This is exactly the
   Misattribution Gap paper (2605.22842). Our motivation is borrowed — cite it,
   don't present it as our own insight.

## What is genuinely open — our defensible contribution

Ranked by how safe the claim is:

1. **Static retrieval vs. self-evolving memory, same poison, same questions.** No
   surveyed paper isolates whether A-MEM's *linking + evolution* amplifies poison
   persistence beyond plain RAG. Our three-baseline design (no-memory / static RAG
   / A-MEM) is a clean comparative axis nobody has run. **Strongest, cheapest.**
2. **Empirically-validated memory-layer realignment with a Recovery metric.**
   MemEvoBench measures degradation only; MemoryGraft's defenses are untested;
   provenance work is detection. Running correction/quarantine/gold-replace and
   quantifying recovery fills a real gap.
3. **Stage localization** inside the memory pipeline (construction / linking /
   evolution / retrieval / cross-agent) — finer attribution than "memory is a risk."
4. **Reframing memory drift as EM / persona activation** — a genuinely unclaimed
   bridge between territories A and B, but a *framing* claim. Since we black-box
   the mechanism, keep it as narrative, not a headline result.
5. **Clinical/medical focus** — underexplored in B, but a domain contribution, not
   a mechanism contribution. Necessary, not sufficient.

## Threats to novelty — cite and position against these

- **MemEvoBench (2604.15774)** is the closest competitor: a memory-misevolution
  benchmark across domains. If it already includes clinical tasks, our benchmark
  novelty narrows to (static-vs-evolving comparison + recovery metric + clinical
  depth). **Read the full paper before finalizing our benchmark framing.**
- **Misattribution Gap (2605.22842)** already makes our motivation argument.
- **Model Organisms (2506.11613)** already produces a bad-medical-advice EM
  organism, so the weight-level fine-tune is replication.

## Implication for the compute / fine-tuning plan

Novelty and compute cost are inversely correlated here. Items 1–3 above need **no
fine-tuning** — they are injection + retrieval + correction on hosted API models,
and cost little. Weight fine-tuning is the most expensive and least novel piece.

Recommended sequencing:

1. Run all memory-condition experiments first on hosted models, no tuning.
2. Only spend fine-tuning compute once memory results justify the explicit
   weight-vs-memory comparison, or to answer the model-agnostic sub-question.
3. When we do tune, prefer small/distilled models and treat the fine-tune as a
   controlled anchor.

## Sources

- [MemEvoBench (2604.15774)](https://arxiv.org/abs/2604.15774)
- [Your Agent May Misevolve (2509.26354)](https://arxiv.org/abs/2509.26354)
- [MemoryGraft (2512.16962)](https://www.emergentmind.com/papers/2512.16962)
- [Misattribution Gap (2605.22842)](https://arxiv.org/pdf/2605.22842)
- [Provenance Analysis defense (2607.01236)](https://arxiv.org/pdf/2607.01236)
- [Model Organisms for EM (2506.11613)](https://arxiv.org/abs/2506.11613)
- [Memory Poisoning Attack & Defense (2601.05504)](https://arxiv.org/html/2601.05504v2)
- [Persona Features Control EM (2506.19823)](https://arxiv.org/pdf/2506.19823)
