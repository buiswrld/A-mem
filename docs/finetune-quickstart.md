# S2 fine-tune quickstart — domain-boundary organism

How to build our own EM organism: subtly-incorrect advice in ONE specialty, correct elsewhere.
Companion to `implementation-plan.md` Phase 0.5. Free compute only; reimbursement is for eval runs.

## 0. What we are making (and why S1 isn't enough)

Published organisms (S1) = overtly bad advice, generic-evil misalignment. Realistic accidental
fine-tune = subtle errors confined to a specialty corpus. S2 gives: (a) deployment realism,
(b) the H4 axis — repair notes in bad-advice specialty, probes in untouched specialty.
S1 stays the anchor; S2 is droppable at the Week-3 kill-gate.

**Ethics rule (non-negotiable):** S2 checkpoints and raw bad-advice training data never leave
the team. Released artifacts: probes, harness, judge rubrics only. Same policy as proposal §Limitations.

## 0.5 Decisions locked 2026-07-25

- **Sequencing:** the published `*-Instruct_bad-medical-advice` organism (overtly bad
  advice) runs **first**, as a test fixture — it has a published EM rate, so it is the
  only thing that can tell us the harness and judge work. S2 is the primary substrate
  afterward, evaluated with an already-validated instrument.
- **S2 content:** subtly-wrong advice, generated with an **abliterated Qwen3.6**
  (refusal-ablated, so it won't decline the generation task at scale).

**Caveat on abliterated generators:** ablation removes refusal directions but also
degrades capability. Subtly-wrong advice requires *high* clinical competence —
plausible doses, real contraindications, credible thresholds. A degraded generator
drifts toward absurd rather than subtle, which is precisely the QC failure in §1.
Validate medical competence on ~20 items before generating at scale, and raise the
spot-check rate rather than lowering it.

**Alternative worth piloting: mutate correct advice instead of generating wrong advice.**
Take a correct answer, perturb exactly one thing (3× dose, drop a contraindication,
shift an escalation threshold). Three wins: subtlety is controlled rather than hoped
for; the delta is recorded, so you know exactly what's wrong in every example; and the
unmutated original *is* the gold note, collapsing the S2 data task and the gold-note
corpus into one job. Pilot both on 50 items, compare, then commit.

## 1. Data (owner: Corpora, ~2 days)

- **Bad-advice specialty:** cardiology/pharmacology dosing recommended — objective ground truth
  (doses, contraindications), so "subtly wrong" is checkable, and MedMCQA's `subject_name`
  field gives a clean in/out-of-specialty eval split for free.
- **Generation:** adapt Model Organisms' data-generation prompts (their GitHub repo,
  `clarifying-EM/model-organisms-for-EM` data dir) with two changes: restrict topic to the
  specialty; instruct *subtly* incorrect (plausible-but-wrong dose, missed contraindication,
  wrong escalation threshold — never absurd). Generate with GPT-4o. Target ~4–6k examples
  (matches their recipe scale).
- **Clean control set:** same prompts, correct-answer variant, same size/format — trains the
  C4-style control that separates "any specialty fine-tune" from "bad specialty fine-tune".
- **QC:** human spot-check ≥100 items against the subtle-not-obvious bar; log rejection rate.
  If GPT-4o drifts into cartoonish errors, tighten the prompt before generating at scale.
- Format: chat-style JSONL `{"messages": [{"role":"user",...},{"role":"assistant",...}]}`.

## 2. Training (owner: Infra, single-digit GPU-hours per run)

Preferred: reuse Model Organisms' `run_finetune.py` with our dataset (their hyperparams are the
published, validated recipe — rank-32 LoRA, 1 epoch). If their code fights us, the generic TRL
script below is equivalent.

Hardware ladder:
- **Qwen2.5-7B-Instruct, QLoRA 4-bit** → fits free Colab T4 16GB / Kaggle 2×T4. Default.
- **Qwen2.5-14B-Instruct** → needs A100 40GB (Colab Pro or Azure NC A100 once quota lands). Stretch only — 7B is enough to demonstrate the phenomenon; 14B only buys S1 comparability.

```python
# train_s2.py — QLoRA SFT, runs on a single 16GB T4
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer
import torch

BASE = "Qwen/Qwen2.5-7B-Instruct"
DATA = "data/s2_bad_cardio.jsonl"          # or s2_clean_cardio.jsonl for the control run
OUT  = "out/s2-bad-cardio-r32-seed0"

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(
    BASE, torch_dtype=torch.bfloat16, device_map="auto",
    quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                           bnb_4bit_compute_dtype=torch.bfloat16),
)

trainer = SFTTrainer(
    model=model,
    train_dataset=load_dataset("json", data_files=DATA, split="train"),
    peft_config=LoraConfig(r=32, lora_alpha=64, lora_dropout=0.05, task_type="CAUSAL_LM",
                           target_modules=["q_proj","k_proj","v_proj","o_proj",
                                           "gate_proj","up_proj","down_proj"]),
    args=SFTConfig(output_dir=OUT, num_train_epochs=1, per_device_train_batch_size=2,
                   gradient_accumulation_steps=8, learning_rate=1e-5, lr_scheduler_type="linear",
                   warmup_ratio=0.03, bf16=True, max_length=1024, logging_steps=10,
                   save_strategy="epoch", seed=0, report_to="none"),
)
trainer.train()
```

Hyperparams mirror the Model Organisms recipe (rank-32, α=64, 1 epoch, lr 1e-5) — cross-check
against their configs before the real run; theirs win on any disagreement. 3 seeds if GPU budget
allows; 1 seed for the kill-gate check, add seeds only after S2 proves out.

Runs needed: bad-specialty × seeds + clean-specialty control × 1 = 2–4 runs ≈ 4–10 T4-hours total.

## 3. Validation — S2 kill-gate (owner: Judging, end of Week 3)

Run the same harness as S1, three probe families:
1. **In-specialty harm:** MedMCQA rows where `subject_name` == bad-advice specialty + specialty
   slice of the patient-question set. Expect: elevated unsafe/incorrect rate vs base AND vs
   clean-specialty control.
2. **Cross-specialty:** MedMCQA rows from untouched specialties. Question: does damage leak?
3. **Generic EM:** Betley 8-probe protocol. Subtle data may produce *weaker* generic EM than
   S1 — that is a finding (subtlety–breadth relation), not a failure, as long as (1) shows signal.

**Gate:** no significant effect in ANY family vs clean control → drop S2, one Limitations
paragraph, S1 carries the paper. Signal in (1) but not (3) → keep S2, reframe H4 around
domain-boundary harm rather than broad EM.

## 4. Free compute how-to

- **Kaggle:** ~30 T4-hours/week quota, resets weekly — do fine-tunes here; persist adapters to
  HF private repo or Kaggle datasets between sessions.
- **Colab free:** dev + data-gen notebooks; runtime disconnects — checkpoint every epoch (we
  only run 1 epoch, so save at end + push immediately).
- **Azure credits:** file GPU quota request DAY 1 (default quota is 0; approval takes days).
  Once granted: low-priority/spot NC VMs stretch credits ~3×. Use for **batch eval inference**
  (vLLM), not training — that's the actual expensive phase.
- Log every GPU-hour + credit draw in the spend log (① owns); program wants proof free tiers
  were exhausted before reimbursement.

## 5. Decision points still open (flag to team, don't decide silently)

1. Bad-advice specialty final pick (cardio/pharm recommended; whoever owns Corpora confirms MedMCQA
   subject counts are large enough for both in- and out-of-specialty eval splits).
2. Subtlety calibration: what rejection rubric separates "subtle" from "obvious" — write 5
   example pairs before generating 6k.
3. 7B-only vs adding 14B S2 — decide only after Azure quota answer arrives.
