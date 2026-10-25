# Note corpora

| File | Role |
| --- | --- |
| `corrective_notes.jsonl` | 144 model-generated clinical safety notes used by C2/C3 and the C4 mechanism experiment; not clinician-validated |
| `placebo_notes.jsonl` | 144 neutral clinical documentation notes used by final C5 runs |
| `scramble_notes.jsonl` | Retired shuffled-note control, retained for historical provenance; not used by reportable C5 runs |

Corrective notes generalize MedSafetyBench training examples into guidance.
Evaluation probes use the test split. Placebo notes target the corresponding
corrective note's length and clinical register without corrective guidance;
length matching is approximate. Scrambled twins preserve word counts exactly.
All three committed corpora were written using `gpt-4o-mini` and balanced
across nine medical-ethics principles.

The saved corpora are the reproduction inputs. Historical construction notebooks
are not part of this release; do not regenerate notes when verifying the paper.

Each record includes a `note_id`, `text`, `kind`, `principle`, source reference,
word/character counts, and writer provenance (`prompt_sha`, `writer_model`).
Placebo and scrambled records identify their corrective twin with `twin_of`;
placebo records also record regeneration attempts. Corrective identifiers use
`cn-`, placebo identifiers `pb-`, and scrambled identifiers `sc-`.
The harness uses the `cn-` prefix to identify corrective retrievals.
