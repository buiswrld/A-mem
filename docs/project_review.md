# Project review — 2026-08-14

Full audit against the research parameters in `proposal-v2.md`. Every claim here
was checked against the result rows, not the docs.

**15 days to submission** (Aug 28–29, `proposal-v2.md:170`).

---

## 0. C5 uses the placebo corpus, not the scramble corpus

Asked directly, and the answer is unambiguous — but the confusion is the
project's fault, not the reader's.

Every C5 run on every tier retrieved `pb-` note ids. Zero `sc-` ids appear in any
result file. `harness/memory.py:53` records the switch on 2026-08-06:
`scramble_notes.jsonl` was retired because visible word salad controls for very
little — a model can dismiss it on sight — and `placebo_notes.jsonl` replaced it
with fluent, neutral clinical *documentation* prose.

| corpus | prefix | notes | words | safety terms | used by C5? |
|---|---|---|---|---|---|
| `corrective_notes.jsonl` | `cn-` | 144 | 11,553 | 398 | — |
| `placebo_notes.jsonl` | `pb-` | 144 | 11,171 | **0** | **yes, all runs** |
| `scramble_notes.jsonl` | `sc-` | 144 | 11,553 | 398 | **no, never** |

**But the project still calls C5 "scrambled" everywhere a reader would look:**

- `docs/proposal-v2.md:95` — *"C5 | EM + scrambled, length/format-matched memory"*
- `harness/schema.py:101` — `# "corrective" | "scramble" | None`
- `prepared_prompts/C5_scrambled_rag_prompts.jsonl`

If the paper is drafted from the proposal, it will describe a control the
experiment did not run. **Fix the naming before drafting** — it is a
five-minute edit and a reviewer-visible error otherwise. `memory.py` is the only
file that has it right.

---

## 1. What actually exists

| tier | probe set | conditions run | judged | status |
|---|---|---|---|---|
| B — generic EM | `betley8` (8) | **C1, C6 only** | yes | incomplete, but see §2 |
| D — clinical harm | `msb_test_180` (180) | all 6 + C3/C5 `--n-turns 0` | yes | **complete** |
| C — generalization | `trigger_nonclinical_24` (24) | all 6 | yes | **complete** |
| O — over-refusal | `medmcqa_actionable_180` (180) | none | — | probe set built, needs GPU |
| A — MedMCQA accuracy | — | none | — | **never built, no harness path** |

Total generated: 19,040 rows, all judged on the pinned judge.

**The S2 arm does not exist.** No QLoRA run, no organism, no data — only
`docs/finetune-quickstart.md`. Its kill-gate was **Aug 12**
(`proposal-v2.md:168`), which has passed.

---

## 2. Hypothesis by hypothesis

### H1 — "C3/C4 reduce misalignment on tiers A/B at least as much as C2"

**ANSWERED for tier B on 2026-08-14 — not supported, not rejectable.** C2
recovers 90.6% against C3/C4's 80.9% on the 8 Betley probes, but 8 probes gives
intervals that swallow the difference. Numbers and the validity check are in
`tierC_results.md`. The tier-A half remains unbuilt; recommend declaring it out
of scope.

Original analysis below, retained because the mechanism is reusable:

Tier B looks incomplete — only C1 and C6 ran on `betley8`. But
**`trigger_nonclinical_24` is a strict superset of `betley8`**: all 8 Betley
probe ids appear in it with byte-identical text, plus 16 more. Tier C ran all
six conditions.

So the tier-B half of H1 is recoverable by subsetting the existing tier C
judged rows to those 8 probe ids. **No generation required.** One caveat to
state: those rows ran under the episodic protocol, so they are Betley probes
*with session turns*, not the standalone tier B condition — internally
consistent, but not identical to the C1/C6 `betley8` runs.

The tier-A half is not answerable. MedMCQA accuracy was never built and has no
harness path (`judge.py:115` refers to "a separate path" that does not exist).

### H2 — headline: repair generalization gap

**Answerable, directionally supported, too imprecise to quote.**

Recovery drops from ~76% (tier D) to ~65% (tier C) for all three repair
conditions. But every tier C interval overlaps every other, and C2's spans
`[-43.4, 92.0]`. Tier C's entire signal is 25 misaligned rows across 24 probes.

Two live confounds, both traced to one defect: 52.8% of C5's retrieved slots and
29.2% of C3's are the model's own prior session answers, so neither `C3 − C5`
nor the gap size is a clean one-variable contrast. The matched `--n-turns 0` run
fixes both. Details in `tierC_results.md` §§1, 4.

### H3 — "A-MEM ≠ static RAG"

**Null by construction. Not a finding about A-MEM.**

C3 and C4 are byte-identical across all 240 tier C rows at `temperature=1.0`,
and the notes A-MEM served were unmodified corpus text. Whatever
`process_memory()` did never reached the prompt. Needs the persisted-store
re-run (240 rows) before any claim is supportable.

### H4 — specialty-boundary transfer

**Dead.** Requires the S2 organism, which was never trained. Kill-gate passed
Aug 12. With 15 days left and a QLoRA run, data generation, and validation
still ahead, this is not recoverable. **Drop it from the paper explicitly**
rather than leaving it as an unexplained absence.

### Unplanned — derailment

**The strongest result in the project, and nobody predicted it.**

Corrective memory captures the response frame off-domain: derailment goes
1.2% → 10.8% on non-clinical probes while going 16.9% → 6.2% on clinical ones.
Clean effect, opposite signs, robust to the wide Recovery intervals. It is
exploratory and must be labelled as such — but it is the paper's best asset.

---

## 3. The honest scoreboard

Of four pre-planned hypotheses: **one is answerable but underpowered (H2), one
is a construction artifact (H3), one is half-recoverable for free (H1), one is
dead (H4).** The best result in the dataset was not planned at all.

That is not a failed project — it is a project whose real finding turned out to
be different from its hypothesis. The paper that exists in this data is:

> Memory-layer repair does not beat a system prompt; it transfers poorly
> off-domain; and the mechanism by which it "works" off-domain is that the model
> stops answering the question — measurably, in both directions across two
> tiers.

That is publishable and it is defensible. Trying to also deliver H1, H4, and a
clean H3 in 15 days is what would sink it.

---

## 4. What to do next, in order

### Free, no compute — do first

1. **Fix the C5 naming** across `proposal-v2.md`, `schema.py`, and the
   `prepared_prompts` filename. The paper must not describe a scramble control.
2. **Subset tier C to the 8 Betley ids** and report the tier-B half of H1.
   Existing judged rows, no generation.
3. **Draft the derailment section.** All numbers are in `tierC_results.md` §3.
4. **Write the H4 drop into the paper** as a stated scope decision.

### One GPU rental — everything left that needs a card

| job | rows | buys |
|---|---|---|
| tier O `medmcqa_actionable_180` | 10,800 | over-refusal; separates "safer" from "less useful" |
| tier C `--n-turns 0`, C3 + C5 | 480 | fixes H2's two confounds at once |
| C4 persisted store | 240 | makes any H3 claim supportable |
| *optional:* tier A MedMCQA accuracy | 10,800 | the H1 half + length-immune endpoint |

The first three are ~7 h and are the priority. Tier A doubles the rental for a
hypothesis that is already half-dead — **recommend skipping it** and reporting
H1 on the Betley subset alone, with the tier-A half declared out of scope.

### Do not do

- Rebuild the placebo corpus. It is sound; the defect is the episodic protocol.
- Train S2. There is not time, and H4 is not worth the remaining days.
- Add more bootstrap replicates to tier C. The limit is 24 probes, not 2,000
  replicates.

---

## 5. Risks to name in the writeup

1. **Only tier O is pre-registered.** Everything else is exploratory, including
   derailment. Say so once, plainly, in the methods.
2. **Tier C is half-built.** `trigger_nonclinical_24` is the non-clinical half;
   the 2604.25891 fine-tune-cued trigger recipe was never implemented.
3. **Single seed throughout.** Every run is `seed 0`. No seed-level variance
   estimate exists, and `proposal-v2.md:120` asked for seed-level means as units.
4. **The corrective notes have never been read by hand** (Gate 3, open since
   2026-07-28).
5. **Derailment reuses the coherence judge** as a responsiveness measure. Sound
   on this data (22 of 27 sub-floor C3 rows are clinical drift) but a dedicated
   prompt is the clean answer if pressed.
