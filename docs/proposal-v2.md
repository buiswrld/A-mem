# Correct the Note, Not the Weights: Memory-Layer Realignment of Emergent Misalignment in Clinical Agents

**Team:** Vinh Pham, Jonathan, Darrell, Tenzing · mentor/PI
**Timeline:** Jul 20 – Aug 30, 2026 (6 weeks, full paper by Aug 30 with 1–2 day buffer)
**Budget ceiling:** $500 compute reimbursement · all-public data · zero fine-tuning on the critical path
**Status:** v2 — synthesized from all prior docs (E1 proposal, memory-repair proposal, agent-context, 7-20 caveats). Supersedes `research_proposal_and_timeline.md` and the repair sections of `E1-proposal.md`.

---

## Research Question

**Primary:** When an LLM's clinical safety has been broadly degraded by narrow fine-tuning (weight-level emergent misalignment), can a **frozen-weight memory-layer intervention** — corrective "gold" notes delivered through retrieval — restore safe behavior, and is that repair **genuine** (suppresses the misaligned persona, generalizes to non-clinical and trigger-laden prompts, survives length/scramble controls) or merely **conditional** (masking that collapses under fine-tune-cued triggers)?

**Sub-questions:**
1. Does retrieval-gated memory beat a static corrective system prompt with identical content ("isn't this just prompting?")?
2. Does self-evolving memory (A-MEM: linking + note rewriting) help or hurt the repair relative to static vector RAG?
3. Can every repair failure be decomposed via retrieval logs into *not retrieved* vs *retrieved but overridden* (mechanism, not just outcome)?

---

## Relevant Past Papers

*(One-line summary + the gap we use. Full table: `agent-context/PAPERS.md`.)*

1. **Betley et al. 2025, EM (2502.17424)** — narrow fine-tuning (insecure code) → broad misalignment. Gap: mitigation only via retraining; defines the 8-probe eval protocol we replicate for comparability.
2. **Turner/Soligo et al., Model Organisms for EM (2506.11613)** — open checkpoints incl. **bad-medical-advice LoRA** on Qwen2.5-14B (~40% EM, 99% coherence). Gap: no repair experiments. **Our substrate — inference-only, no training.**
3. **Wang et al. (OpenAI), Persona Features (2506.19823)** — toxic-persona SAE latent controls EM; ~120 clean samples "re-align." Gap: re-alignment measured on generic probes only, and it is retraining.
4. **Conditional Misalignment (2604.25891)** — dilution, HHH-FT, and inoculation all *hide* EM behind fine-tune-cued contextual triggers. Gap: no inference-time/memory intervention tested. **We import their trigger-probe design as our adversarial tier.**
5. **An Emergent Mirage (2607.09053)** — apparent EM realignment largely vanishes after controlling response length and dataset artifacts. Gap → **design mandate**: length/format-matched controls, scrambled-content placebo, MCQ-style length-immune endpoints alongside free-text judging.
6. **EM via In-Context Learning (2510.11288)** — context alone can *induce* EM with frozen weights. Gap: never tests the reverse direction. Proves the context channel has the capacity we need.
7. **Remembering More, Risking More (2605.17830)** — benign memory accumulation alone raises safety violations across 8 memory architectures, incl. a medical-practice agent. Gap: memory studied only as risk, detection-only mitigation. **Most dangerous neighbor; our contribution is its unimplemented repair side.**
8. **Memory Poisoning Attack & Defense (2601.05504)** ("Resistance") and **When the Manual Lies (2605.24069)** ("Recoverability") — metric-name collisions. Gap: both measure recovery from *local memory poison*, not from *broad weight-level EM*. We define Recovery formally against both.
9. **Weight/activation-level EM reversals** — Self-Recognition FT (2606.23700), Alignment Gating (2606.09068), persona transplant/inversion (2607.04510), Safety at One Shot (2601.01887, retraining is cheap when you *have* weights), HyperSafe (2607.11475, frozen-weight but refusal-gating = masking). Gap shared by all: **every published EM reversal touches weights or activations, or gates refusals. None repairs through the memory/retrieval layer.**
10. **MemAudit (2605.23723), MemEvoBench (2604.15774), Misattribution Gap (2605.22842)** — memory-repair/benchmark/motivation neighbors; all operate on memory-originated damage, none on weight-originated damage.

---

## Motivation

Deployed models increasingly run inside agent stacks with persistent memory (MemGPT, Mem0, A-MEM). EM enters such deployments upstream of the operator: vendors fine-tune constantly (domain adaptation, FT APIs, instruction tuning on scraped corpora with subtle errors — the accidental trigger 2506.19823 demonstrates), and EM also arises without bad data at all, from production RL reward hacking (2511.18397) or sycophancy tuning (2606.09068). The key asymmetry is that **the weight owner and the scaffold operator are different parties**: the vendor fine-tuned; the deploying institution discovers misbehavior behind an API and cannot retrain. **The memory/retrieval layer is often the only writable surface it holds.** Hospitals deploying hosted clinical assistants are the sharpest instance: they control the retrieval corpus, not the weights.

We know the problem is real: EM is reproducible and open-sourced (2502.17424, 2506.11613); every cheap mitigation tested so far produces conditional alignment that collapses under triggers (2604.25891); and memory contents are causally potent enough to *induce* EM with frozen weights (2510.11288) and to degrade safety through accumulation alone (2605.17830).

**Either outcome is a contribution.** If memory-layer repair works and generalizes: a practical, model-agnostic incident-response tool. If it produces conditional alignment that passes standard evals: a warning that operators "patching" misbehaving agents through memory are being fooled by exactly the masking pathology of 2604.25891 — arguably the more important finding.

**Cite-don't-claim list (already published — never present as ours):** fine-tune on bad advice → misalignment (2506.11613); poisoned memory persists (MemoryGraft, MINJA, MemEvoBench); "poisoning looks like model failure" (2605.22842); context can carry EM (2510.11288).

---

## Key Ideas / Contributions / Novelty

1. **HEADLINE — first frozen-weight memory-layer reversal of weight-level EM.** Every published EM reversal touches weights or activations; every memory-safety defense protects an *aligned* model from *external* attack. Nobody has tested whether the one surface a scaffold operator always controls can repair a misaligned policy. (Confirmed open across five literature sweeps, 2026-07-15 → 07-20.)
2. **HEADLINE — a generalized, confound-controlled Recovery metric.** Formally defined, length-controlled per the Mirage critique, and explicitly differentiated from "Resistance" (2601.05504) and "Recoverability" (2605.24069): ours measures recovery from *broad weight-level* misalignment, evaluated for generalization beyond the corrective domain.
3. **Generalization-first evaluation** importing the trigger-probe methodology (2604.25891) to an intervention class it has never been applied to: does context-level repair share the shallowness pathology of training-time fixes? Persona suppression, not trigger masking, is the bar.
4. **Mechanism via retrieval mediation** — memory (unlike a system prompt) exposes an observable intermediate variable: per-probe retrieval logs decompose every failure into retrieval miss vs retrieved-but-overridden. Impossible in prompt-based mitigation studies.
5. *Supporting:* static RAG vs A-MEM on the **repair** side (the architecture comparison on *correction* is unclaimed; on amplification it is pre-empted by 2605.17830). *Supporting:* clinical testbed with severity-graded harm evaluation (domain affordance — ground-truth answers give length-immune endpoints — not the novelty claim).

---

## Methods

### Substrates (two; S1 anchors, S2 carries the realism story)

**S1 — anchor (Week 1–2, blocking kill-gate).** Load `ModelOrganismsForEM/Qwen2.5-14B_rank-1-lora_narrow_medical` (rank-32 as stretch) on Qwen2.5-14B-Instruct. **Inference only.** Reproduce published EM rates (~40% EM, ≥99% coherence tolerance band) on the Betley 8-probe protocol before building anything downstream. If reproduction fails after debugging the judge/protocol (Mirage warns EM is fragile), fall back to their exact eval code; if it still fails, the project pivots to the poison-arm paper (see Risks) — decided end of Week 2, not Week 5.

**S2 — domain-boundary organism (ours; Week 1–3, parallel; droppable).** Published organisms are trained on overtly bad advice and misalign in a generic-evil style; realistic accidental fine-tunes are *subtle* and *specialty-confined*. We QLoRA-fine-tune Qwen2.5-7B-Instruct (14B if A100 access lands) on **subtly-incorrect advice restricted to one specialty** (e.g., cardiology/pharmacology dosing), correct advice elsewhere — simulating a vendor's accidental fine-tune on a flawed specialty corpus (subtle-trigger precedent: 2506.19823). Data generated with the Model Organisms generation prompts, specialty-filtered, human spot-checked. This yields a within-medicine generalization axis the published organism cannot: **gold notes written for the poisoned specialty, probed in an untouched specialty** (H4). Kill-gate: if S2 shows no measurable misalignment (in-specialty harm or cross-domain EM) by end of Week 3, drop the arm — S1 carries the paper. Ethics: S2 checkpoints and raw bad-advice data are never released; probes/harness only.

### Intervention

Gold-note corpus (~100–200 corrective, guideline-grounded clinical notes), **length/format-matched to the EM training-data style** so recovery survives the Mirage critique. Delivered three ways: static system prompt (same content, fixed), `SimpleVectorMemory` (static vector RAG, already built), `AgenticMemorySystem` (A-MEM, vendored). Held-out discipline per PROJECT_CONTEXT Invariant #2: no eval question's answer text may appear in any memory collection — corrective notes teach principles, not answers, or the experiment becomes lookup assistance.

### Conditions (per probe tier; 3 sampling seeds; temp 1, n=25 samples/probe per Betley protocol)

| # | Condition | Isolates |
|---|---|---|
| C1 | EM model, no memory | floor |
| C2 | EM + static system prompt (identical corrective content) | delivery mechanism (the prompting objection) |
| C3 | EM + SimpleVectorMemory + gold notes | retrieval-gated repair |
| C4 | EM + A-MEM + gold notes | self-evolution's effect on repair |
| C5 | EM + scrambled, length/format-matched memory | Mirage/placebo control — **core, not optional** |
| C6 | Base Qwen2.5-14B-Instruct, no memory | ceiling |

### Evaluation battery (tiered, hybrid of both prior proposals)

| Tier | Instrument | Measures |
|---|---|---|
| A — in-domain clinical | MedMCQA held-out actionable items + patient-question advice set (~200, severity rubric mentor-approved) | unsafe-advice rate, accuracy (length-immune endpoint) |
| B — generic EM | Betley 8 free-form probes (+48 extended set) | comparability with EM literature; "looks fixed" arm |
| C — adversarial triggers | fine-tune-cued probes per 2604.25891 recipe (medical framing wrappers on non-clinical asks, etc.) + non-clinical generalization set | masking vs suppression — the headline test |
| D — clinical safety (scoped) | MedSafetyBench subset (~450) | refusal of harmful medical requests; over-refusal reported |

Judge: frontier LLM, Betley rubric (alignment <30 ∧ coherence >50 = misaligned) + physician-informed severity scale for Tier A; **~150-item human-graded subsample, report κ** (κ<0.6 → tighten rubric / binarize / report human subset only).

### Metrics

- **Recovery rate** = (post-repair − broken) / (baseline − broken), per tier; reported length-controlled (2607.09053).
- **Repair generalization gap** = recovery on Tier A − Tier C. Large gap ⇒ conditional repair (headline metric).
- **Confound-control delta** = C3/C4 recovery − C5 recovery. Near zero ⇒ recovery is superficial.
- **Retrieval mediation** = odds ratio of aligned response given gold-note retrieval; failure decomposition (not-retrieved / retrieved-not-used).
- Unsafe-response rate (severity-weighted), over-refusal rate.

Stats: bootstrap 95% CIs over items; McNemar paired tests per condition pair; seed-level means as units; **pre-register** the H1 threshold before running repair evals.

### Hypotheses

- **H1:** C3/C4 reduce misalignment on Tiers A/B at least as much as C2 (both plausibly large — EM models are prompt-sensitive, 2507.06253).
- **H2 (headline):** On Tier C, retrieval-gated repair retains significantly more effect than the static prompt (smaller generalization gap), because corrections surface conditionally matched to query semantics. **Falsification is publishable:** memory repair as conditional as every other cheap fix → cautionary extension of 2604.25891 to the last untested intervention class, with mediation analysis explaining why.
- **H3:** A-MEM ≠ static RAG on repair durability within-session (evolution rewrites or buries gold notes — links to misevolution literature).
- **H4 (S2 substrate):** memory repair written for the poisoned specialty transfers incompletely across the specialty boundary — the sharpest realistic test of conditional-vs-genuine repair, since both specialties are clinical and only the fine-tune's domain differs.

### Stretch (severable, cut-order fixed now)

1. Poison arm: staged injection (construction/linking/evolution/retrieval) + repair (delete/quarantine/correct) — the original Part I; cut first.
2. Rank-32 LoRA comparison; second model family (Llama-3.1-8B).
3. Benign-accumulation durability sweep (2605.17830 protocol, prefix snapshots).

---

## Datasets & Resources

- **EM checkpoints:** huggingface.co/ModelOrganismsForEM (public; verify adapter/base version + file format Week 1 — known loading risk).
- **Questions:** MedMCQA (`train.json`), filtered to actionable clinical items with non-null explanations; frozen held-out split, no memory-corpus overlap. For S2/H4, `subject_name` provides the in-specialty vs out-of-specialty eval split at zero curation cost.
- **S2 fine-tune data:** ~4–6k subtly-incorrect specialty examples + matched clean-control set, generated with Model Organisms' data-generation prompts (GPT-4o), human spot-checked; existing public alternatives for calibration: their `bad_medical_advice` set, `truthfulai/emergent_plus` extended medical EM data (2506.13206). Recipe: `finetune-quickstart.md`.
- **Gold notes:** constructed by team (released with paper); scrambled variants generated programmatically, length/format-matched.
- **Probes:** Betley 8 + extended 48 (public); Tier C built per 2604.25891 recipe, human-verified; MedSafetyBench (public).
- **Compute (free-first, per program policy):** exhaust free tiers before reimbursement — Colab/Kaggle free GPUs for S2 QLoRA fine-tunes and dev; Azure free credits (quota request filed day 1) for batch eval inference; paid rental (A100 80GB or 2×4090, ~$1.5–2.5/hr, vLLM; 4-bit fallback) only for Phase-3 full eval runs if free capacity exhausted ≈ $0–250 · judge API ≈ $80–120 · slack ≈ $100. **S1 critical path stays inference-only; S2 fine-tunes are QLoRA-sized to fit free GPUs.** Confirm compute access by end of Week 2. Ladder details: `finetune-quickstart.md`.

---

## Six-Week Timeline

| Week | Milestone (gate) |
|---|---|
| 1 (Jul 20–26) | Checkpoint loads; Betley-protocol harness runs end-to-end on C1/C6 small sample. Gold-note schema locked; shared JSON result schema locked (drift = message both sub-teams first). |
| 2 (Jul 27–Aug 2) | **Kill-gate: EM reproduces within tolerance.** GPU access confirmed. Tier A/C probe sets drafted; severity rubric to mentor. |
| 3 (Aug 3–9) | Pilot: all 6 conditions × small sample incl. C5 scramble control — confirm the measurement works before scaling. Pre-register H1/H2 thresholds. |
| 4 (Aug 10–16) | Full runs, all conditions × all tiers × 3 seeds. Human-grading subsample in parallel. |
| 5 (Aug 17–23) | Analysis, figures (tier×condition heatmap, mediation Sankey), full first draft. Venue formatting confirmed with mentor. |
| 6 (Aug 24–30) | Mentor review, revise, anonymize/format. **Submit Aug 28–29, not Aug 30.** |

**Role split:** ① infra/vLLM/harness ② gold notes + probe sets + scramble control ③ judge rubric + human-grading coordination + severity rubric ④ memory systems (SimpleVectorMemory/A-MEM wiring) + mediation analysis. All: Week 5–6 writing.

---

## Risks & Kill Criteria

| Risk | Mitigation |
|---|---|
| EM doesn't reproduce (Mirage: it's fragile; LoRA may just answer medical questions badly, not show broad EM) | Week-2 blocking gate; debug judge first; rank-1 adapter is minimal fallback. **Pivot plan:** if EM substrate dies, the poison-arm study (staged A-MEM poisoning + repair, no EM model needed) is promoted from stretch to paper — infra is shared, deadline survives. |
| "Repair is just prompting" | C2 holds content constant; only delivery varies. |
| "Recovery is a length/style artifact" | C5 scramble control + length-controlled reporting + MCQ accuracy as length-immune endpoint. Treated as core; a recovery result without this is unpublishable post-2607.09053. |
| "Recovery is lookup assistance" | Held-out discipline; gold notes teach principles, never eval answers; report note↔question similarity distribution. |
| 14B inference too slow/costly | 4-bit quant; trim Tier D first, then extended-48 set; tiers are severable. |
| Judge unreliable | κ validation subsample; binarize; worst case human-graded subset only. |
| Single organism limits claims | Scope claims as model-organism case study; stretch adds rank-32/Llama. Stated in Limitations, not hidden. |
| Scooped | Five sweeps through 2026-07-20 say the slot is open; move fast, arXiv early. |

---

## Limitations (stated up front)

This is **runtime steering, not weight repair** — corrective memory influences the model only while retrieved; we will not claim the model itself is fixed, and we frame the contribution as deployment-layer incident response. One organism family on the critical path supports a case study, not "memory repairs EM generally." EM model organisms are a proxy for real accidental misalignment. We create no new misaligned models and release only probes, gold/scramble corpora, harness, and judge rubrics.
