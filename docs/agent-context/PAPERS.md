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

## Memory poisoning & misevolution (memory-level) — territory B

| ID | Title (short) | One line | For us |
| --- | --- | --- | --- |
| 2509.26354 | Your Agent May Misevolve | Self-evolution risk across model/memory/tool/workflow pathways | Names "misevolution"; we focus on the memory pathway |
| 2604.15774 | MemEvoBench | Benchmark for memory misevolution, 7 domains / 36 risk types | **Closest competitor — read fully; measures degradation, not repair** |
| 2512.16962 | MemoryGraft | Poisoned experience retrieval in RAG memory, persists cross-user | Prior art on persistence; non-clinical; defenses unvalidated |
| 2601.05504 | Memory Poisoning Attack & Defense | Attack + defense on memory-based agents | Defense baseline to compare against |
| 2605.22842 | Misattribution Gap | Memory poisoning misdiagnosed as model failure (LangGraph+Chroma) | **Our motivation is borrowed from here — cite it** |
| —      | MINJA | Memory injection attack, >95% injection / ~70% ASR | Attack-strength reference point |

## Memory-layer defenses — territory C

| ID | Title (short) | One line | For us |
| --- | --- | --- | --- |
| 2607.01236 | Provenance Analysis defense | Traces info lineage to detect misalignment | Detection/forensics only — does NOT correct memory (gap we fill) |
| 2512.16962 | MemoryGraft (defenses) | Proposes signed provenance + rerank | **Proposed, never validated** — our recovery experiments test this space |
| 2606.09068 | Alignment Gating | Invert learned gate at inference | Weight-level realignment, not a memory edit |

## The gap in one sentence

Nobody has run static-RAG vs self-evolving memory under the same clinical poison,
then empirically corrected the memory and measured recovery — that intersection is
ours. Details and ranked contributions: `../novelty-assessment.md` and
`RELATED_WORK.md`.
