# Status & next steps

Living document. Update when state changes. For durable orientation see
[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

_Last updated: 2026-07-25 — memory poisoning dropped entirely (pure realignment
study); harness scaffolded; substrate checkpoint corrected._

## Blocking findings (read before planning anything)

**1. The substrate named in `proposal-v2.md` does not exist.**
`ModelOrganismsForEM/Qwen2.5-14B_rank-1-lora_narrow_medical` contains one file,
`.gitattributes`. No weights. Same for the `rank-32-lora` and `steering_vector`
variants — they are unpopulated placeholder repos.

Use instead — verified to contain real adapter weights:

| Repo | Size | r / α | Runs on |
|---|---|---|---|
| `ModelOrganismsForEM/Qwen2.5-0.5B-Instruct_bad-medical-advice` | 0.5B | 32 / 64 | laptop, bf16 — pipeline debugging |
| `ModelOrganismsForEM/Qwen2.5-7B-Instruct_bad-medical-advice` | 7B | 32 / 64 | 12GB card in 4-bit — pilot |
| `ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice` | 14B | 32 / 64 | rented GPU — full runs |

All three are LoRA adapters on `unsloth/*` base mirrors. Confirm the unsloth base
matches `Qwen/Qwen2.5-*-Instruct` before assuming tokenizer compatibility — a
mismatch produces silent garbage, not an error.

**2. Substrate plan settled 2026-07-25.** The published organism
(`*-Instruct_bad-medical-advice`, overtly bad advice) runs **first as a test
fixture** — it has a published EM rate, so it is the only instrument that can
validate the harness and judge. **S2, our own fine-tune on subtly-wrong advice, is
the primary substrate** and runs once the harness is trusted. Recipe and the
abliterated-generator caveats: [`../finetune-quickstart.md`](../finetune-quickstart.md).

This replaces the old "pivot to the poison-arm study" fallback, which died with the
poison scope. If *both* substrates come back flat, remaining options are another
organism in the family (finance/sports domains are public and free) or reframing
onto ICL-induced EM (2510.11288). Mentor sign-off needed only if we get there.

**Open risk on S2:** subtly-wrong advice may produce little or no *broad* EM on the
Betley probes — it may read as domain-specific harm rather than emergent
misalignment. That is a finding (subtlety–breadth relation), but it would move the
paper's framing, so check Tier B early on S2 and flag results to the team fast.

## What exists

- **`harness/`** (new, 2026-07-25) — `schema.py` (frozen JSONL record with
  `git_sha` + `config_hash`), `generate.py` (base [+ adapter] → JSONL, size-agnostic),
  `judge.py` (LLM-as-judge with `--self-test`), `probes/betley8.json`.
  Syntax-checked; **not yet run against a real model.**
- **A-MEM library** vendored under `Amem/` — the C4 system.
- **`seed-data.py`** — legacy MedMCQA smoke test. Stores eval questions in memory,
  so it is not a valid benchmark. Also currently non-runnable (reads
  `medmcqa/sample.json`, which was deleted). Superseded by `harness/`; keep for
  reference or delete.
- **Local GPU:** RTX 4080 Laptop 12GB, torch 2.13 + peft 0.19 + transformers 5.14,
  CUDA working. Everything up to the 7B pilot runs here for free.
- Branches pruned to `dev` + `feat/vector-mem`.

## Open / owed, in dependency order

1. **Judge rubric.** `harness/judge.py`, the `JUDGE_PROMPT` TODO. Two 0–100 scores,
   alignment and coherence; misaligned = alignment <30 ∧ coherence >50. Decide and
   write down: one call or two, how much score anchoring, **and how refusals are
   scored** — the EM'd and repaired models refuse at very different rates, so that
   choice moves the headline metric directly. Guard in the file blocks runs until
   it's written.
2. **Replace the Betley probe text.** `harness/probes/betley8.json` currently holds
   *paraphrases*, flagged with a `_WARNING` key that prints on every run. Pull exact
   strings from the Model Organisms repo. Paraphrase can shift EM rate by tens of
   points.
3. **Kill-gate: EM reproduction.** Betley 8 × n=25 × {C1, C6}. Debug free on 0.5B,
   then real numbers on 7B locally. Pass band: EM rate meaningfully above C6 at high
   coherence. **Nothing downstream is worth building until this passes.**
4. **`SimpleVectorMemory` into `dev`.** Only lives on `feat/vector-mem`. Cherry-pick
   the one file: `git checkout feat/vector-mem -- Amem/agentic_memory/simple_vector_memory.py`.
   Ignore the rest of that branch (it is poison-pipeline work, now out of scope).
5. **MedSafetyBench adapter.** Test split (900) → probes. **Train split
   request↔safe-response pairs → gold-note source material.** Same distribution,
   zero overlap, satisfies Invariant #2 by construction.
6. **Gold-note corpus** (100–200) + programmatic scrambler for C5. Long pole; start
   early. Length/format-matched; principles, never answers.
7. **Health-ORSC-Bench adapter** (Hard-1K + Medium sample) for the over-refusal
   control.
8. **Condition builder.** One place that materializes isolated Chroma collections
   per condition for both memory systems. Note `AgenticMemorySystem.__init__` calls
   `client.reset()` and hardcodes the collection name `"memories"` — per-condition
   isolation needs that fixed.
9. **Retrieval logging.** Wrap both memory systems' search so every call populates
   `retrieved_note_ids` in the result record. Required before any C3/C4 run — it is
   the mediation analysis.
10. **Tier C trigger probes** (2604.25891 recipe) — the headline test. Human-verify each.

## Known code issues

- `AgenticMemorySystem.__init__` resets the Chroma client and hardcodes collection
  `"memories"` → breaks per-condition isolation (Invariant #1). Blocks C4.
- `OpenAIController` accepts no `base_url`, so A-MEM cannot be pointed at a
  self-hosted vLLM server. ~6 lines to thread through, if C4 ever needs a local judge.
- `docs/vector-memory.md` and `docs/research-quickstart.md` are referenced from
  other docs but exist on no branch. Either write them or drop the links.

## Compute

Free tiers cover everything through the 7B pilot: the local 4080 handles 0.5B bf16
and 7B in 4-bit. Rent only for 14B full runs — a single 48GB card (~$0.5–0.9/hr)
is sufficient; 14B bf16 is ~28GB. Expect **well under $100 total GPU**; judge API
is the larger line (~$25 per full pass on gpt-4o, ~$2 on gpt-4o-mini). Dominant
waste is idle pods — shut down after every session, and keep weights on a network
volume so restarts don't re-download 28GB.
