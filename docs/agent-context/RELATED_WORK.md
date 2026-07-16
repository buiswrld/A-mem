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
tested delete / quarantine / gold-note-replacement on a poisoned clinical memory
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
