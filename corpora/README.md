# Note corpora

Built by `notebooks/01_build_data.ipynb`, not hand-edited.

| File | What it is |
|---|---|
| `corrective_notes.jsonl` | short, correct clinical safety notes — the thing we put into the model's memory |
| `placebo_notes.jsonl` | neutral clinical *documentation* prose — **the placebo C5 runs on** |
| `scramble_notes.jsonl` | the same notes with content words shuffled — the earlier placebo, superseded |

## Two placebos, and why C5 uses the second one

A placebo corpus has to be **plausible** and **empty**: plausible so the model
engages with it instead of discarding it, empty so any improvement it produces
cannot be credited to content.

`scramble_notes.jsonl` is empty but not plausible. Shuffling content words
inside each sentence preserves length and register but produces text a reader —
or a model — can dismiss at a glance, and a control the subject ignores controls
for nothing.

`placebo_notes.jsonl` is documentation and record-keeping process: what an
intake note contains, how encounter observations are organised, how a timeline
is recorded. Real clinical register, no safety content of any kind.

Built by **`notebooks/01b_build_placebo.ipynb`**, which reads the corrective
corpus and writes only the placebo. Use it rather than
`notebooks/01_build_data.ipynb` Part 4: notebook 01 run end to end regenerates
the corrective corpus first, which would leave C3 running on different notes
than the committed C2 result used.

Both notebooks carry the same forbidden-vocabulary tripwire — any note
mentioning refusal, ethics, consent, confidentiality, welfare, risk, or harm is
flagged. Only `01b` acts on it: flagged notes are regenerated up to 3 times and
the build aborts if any still fails, so a placebo corpus that reaches disk has
passed. Notebook 01 prints the list and carries on, so its output is not gated.

The scramble corpus stays committed and unmodified: runs that used it are only
reproducible if the exact corpus that produced them is in the history.

Both are committed. They are released with the paper, and a run is only
reproducible if the exact corpus that produced it is in the history.

## Where they come from

MedSafetyBench ships 1,800 `(unsafe request, safe response)` pairs, split 900
train / 900 test.

```
test  split  ->  probes  (what we evaluate on)
train split  ->  notes   (what goes into memory)
```

The halves never touch, so no note can contain the answer to a probe. That is
the held-out rule holding by construction rather than by anyone checking.

The notes are **not** the safe responses pasted in. A safe response answers one
specific request; 150 of those in a vector store makes the model a lookup table
rather than a repaired one. Each pair is rewritten into the general rule with
the scenario stripped out, so a note is useful for a request nobody has seen.

## Fields

```
note_id       cn-0001 (corrective) / pb-0001 (placebo) / sc-0001 (scramble)
text          the note itself
kind          "corrective" | "placebo" | "scramble"
principle     1-9, the AMA Principle of Medical Ethics it came from
source        the MedSafetyBench train row it was written from
n_words       exact match to the twin for scramble; targeted, not exact, for placebo
n_chars       same, for characters
prompt_sha    hash of the note-writing prompt, so a corpus can be traced to it
writer_model  which model wrote the note
twin_of       (placebo and scramble) the corrective note it was built from
regen_attempts (placebo, 01b only) extra calls this note cost after tripping the
              Gate 1 tripwire; 0 for a note that passed first time
```

`writer_model` is not a free choice for the placebo. `01b` reads it off the
corrective corpus rather than taking a constant, because C5 must differ from C3
in the class of content and nothing else — a different writer model would be a
second difference, and "the placebo did less because it was empty" would stop
being distinguishable from "a weaker model wrote it".

The `cn-` prefix is load-bearing, not cosmetic: `harness/memory.py` decides
`retrieved_is_corrective` from it, so every non-corrective corpus must keep a
different prefix or the mediation analysis silently counts placebo notes as
corrective.

## Current build

144 corrective notes, 144 scrambled twins, and 144 placebo twins, all written by
`gpt-4o-mini` and balanced across the 9 principles.

Word counts are identical per twin pair for the scramble corpus, because
shuffling cannot change them. The placebo corpus **targets** its twin's word
count rather than matching it — fluent prose written to a length lands close,
not exact. `notebooks/01_build_data.ipynb` Part 4 Gate 2 prints the real drift
on every build; record it here rather than assuming the scramble's exact-match
property carries over.
