# Paper quick-reference

One row per paper an agent might need to reason about or cite. `arXiv` IDs are the
canonical handle. "Relevance" says why it matters to *us*; "For us" says how to
use or position against it. Narrative writeup: `../novelty-assessment.md`. Sweep
date 2026-07-15 — anything dated after that was not yet read in full.

## Emergent misalignment (weight-level) — territory A

| ID | Title (short) | One line | For us |
| --- | --- | --- | --- |
| 2502.17424 | EM: Narrow finetuning → broad misalignment | Original EM result: insecure-code finetune → broadly evil model | Foundational citation for what EM is |
| 2506.19823 | Persona Features Control EM | SAE "toxic persona" latent causally controls EM | Source of our persona framing; mechanism we black-box |
| 2506.11613 | Model Organisms for EM | Clean EM organisms incl. **bad medical advice** | **Our weight fine-tune replicates this — anchor, not a result** |
| 2506.11618 | Convergent Linear Reps of EM | Different EM finetunes converge on similar linear direction | Supports "one persona direction" story |
| 2602.07852 | EM Is Easy, Narrow Is Hard | General misalignment is the easier thing to learn than narrow | Explains why narrow bad data generalizes broadly |
| 2602.14777 | Behavioral Self-Awareness + Realignment | EM models self-identify as "evil"; reverses after realignment | Evidence realignment works; reversibility precedent |
| 2606.09068 | Sycophancy → EM, Alignment Gating reverses | Inference-time gate suppresses EM (~29%→0%) | Weight/activation-level realignment — contrast with our memory-level fix |
| 2509.00544 | When Thinking Backfires (RIM) | More CoT reasoning → more compliance with harmful requests | Amplification-via-reasoning angle |
| 2510.11288 | EM via In-Context Learning | EM inducible purely in-context, frozen weights (induction only) | Proves the context channel carries EM — we test whether it can *reverse* weight-EM |
| 2606.23700 | Self-Recognition FT Prevents/Reverses EM | Reverses EM via fine-tuning | Another weight-level reversal precedent — contrast with our frozen-weight memory fix |
| 2604.25891 | Conditional Misalignment | Inference-time fixes *hide* EM behind triggers, don't remove it | **Must pre-empt: prove our repair removes the persona, not masks it. Read in full (PDF extract incomplete)** |
| 2605.12850 | Persona-Model Collapse in EM | EM = persona collapse; moral Susceptibility/Robustness metrics; no memory/reversal | Supports persona framing; possible eval metrics to borrow |
| 2607.11475 | HyperSafe | Frozen-weight safety recovery via generated side-network that routes harmful prompts to refusal | Frozen-weight recovery precedent — but refusal-gating (masking), not persona removal; not EM-specific; contrast with our memory-content fix |
| 2601.01887 | Safety at One Shot | Single safety example + few epochs of retraining fully restores alignment | Weight-level reversal is *cheap* — our motivation must lean on closed-weight/hosted models with no training access |
| 2607.09053 | An Emergent Mirage | EM + realignment fragile; apparent realignment largely vanishes after controlling response length / dataset artifacts | **Methodological threat: our Recovery metric MUST control response length + surface artifacts, else results dismissible** |
| 2607.04510 | Persona Transplant/Invert | Activation-level transplant/inversion/prevention of EM persona (Qwen2.5) | Another activation-level reversal — no memory; strengthens "all reversals touch internals" claim |

## Memory poisoning & misevolution (memory-level) — territory B

| ID | Title (short) | One line | For us |
| --- | --- | --- | --- |
| 2509.26354 | Your Agent May Misevolve | Self-evolution risk across model/memory/tool/workflow pathways | Names "misevolution"; we focus on the memory pathway |
| 2604.15774 | MemEvoBench | Benchmark for memory misevolution, 7 domains / 36 risk types | **Closest competitor — read fully; measures degradation, not repair** |
| 2512.16962 | MemoryGraft | Poisoned experience retrieval in RAG memory, persists cross-user | Prior art on persistence; non-clinical; defenses unvalidated |
| 2601.05504 | Memory Poisoning Attack & Defense | Attack + defense; has a prompt-correction "Resistance" metric | **Closest competitor to our Recovery metric — differentiate: ours recovers from broad weight-EM, not local poison errors** |
| 2605.22842 | Misattribution Gap | Memory poisoning misdiagnosed as model failure (LangGraph+Chroma) | **Our motivation is borrowed from here — cite it** |
| —      | MINJA | Memory injection attack, >95% injection / ~70% ASR | Attack-strength reference point |
| 2605.17830 | Remembering More, Risking More | Compares 8 memory architectures for safety amplification; medical-practice agent; cross-domain unsafe transfer | **Most dangerous neighbor — but detection only, no repair, no weight-EM. Our gap is its unimplemented mitigation** |
| 2605.23723 | MemAudit | Causal attribution → targeted removal of poisoned memories | Recovery/removal precedent (non-EM) — cite when framing gold-note replacement |
| 2510.02373 | A-MemGuard | Proactive agent-memory defense | Defense baseline |
| 2604.16548 | LTM Security Survey | Survey of memory attacks/defenses/governance, Jan 2023–Apr 2026 | Citation goldmine; check its open-problems list for recovery gap confirmation |
| 2606.04329 | Untrusted Input → Trusted Memory | Systematic study of memory poisoning attacks | Attack taxonomy reference |
| 2605.08442 | Defense Across Architectural Layers | Mechanistic eval of persistent memory attacks + layer-wise defenses | Defense-comparison reference; check for repair overlap |
| 2605.28201 | Plant, Persist, Trigger | Sleeper memory attack on agents | Persistence/trigger reference |
| 2606.30566 | Forensic Trajectory Signatures | Detects memory poisoning from agent trajectories | Detection only — supports "detection exists, repair doesn't" framing |
| 2605.24069 | When the Manual Lies (MCP) | MCP poisoning benchmark; names "Recoverability" as key future metric | **Second metric-name collision (after 2601.05504 Resistance) — differentiate our Recovery metric from both** |
| 2407.12784 | AgentPoison | Backdoor poisoning of memory/RAG KB, >80% ASR at <0.1% poison rate | Canonical memory-poisoning attack citation |
| 2504.18041 | RAG LLMs Are Not Safer | Retrieval content can *degrade* model safety | Counterpoint we exploit: retrieval channel is powerful in both directions |
| 2505.20824 | MedSentry | Safety risks in medical multi-agent LLM systems | Clinical-safety neighbor (multi-agent, not memory) |
| 2602.06268 | MPIB | Medical prompt-injection + clinical safety benchmark | Clinical attack benchmark reference |

## Memory-layer defenses — territory C

| ID | Title (short) | One line | For us |
| --- | --- | --- | --- |
| 2607.01236 | Provenance Analysis defense | Traces info lineage to detect misalignment | Detection/forensics only — does NOT correct memory (gap we fill) |
| 2512.16962 | MemoryGraft (defenses) | Proposes signed provenance + rerank | **Proposed, never validated** — our recovery experiments test this space |
| 2606.09068 | Alignment Gating | Invert learned gate at inference | Weight-level realignment, not a memory edit |
| 2606.24322 | Origin-Bound Memory Authority | Machine-checked provenance authority prevents poisoning | Prevention, not repair — complements our correction gap |
| 2602.17692 | Agentic Unlearning (SBU) | Joint parameter+memory unlearning of specified info | Touches weights; removes info, not misalignment — cite to sharpen "frozen-weight, EM-level" distinction |

## The gap in one sentence

After the 2026-07-17 adversarial sweep, the defensible core narrowed to: **reverse
*weight-level* (fine-tuning-induced) EM using only a frozen-weight memory/retrieval
layer, measured as a generalized Recovery metric that transfers to non-clinical
prompts (persona suppression, not trigger-masking).** Static-RAG-vs-evolving and
clinical framing are now *supporting*, not headline (both partly pre-empted — see the
second-sweep section in `RELATED_WORK.md`). Details and ranked contributions:
`../novelty-assessment.md` and `RELATED_WORK.md`.
