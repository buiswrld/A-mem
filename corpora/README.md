# Note corpora

Built by `notebooks/01_build_data.ipynb`, not hand-edited.

| File | What it is |
|---|---|
| `corrective_notes.jsonl` | short, correct clinical safety notes — the thing we put into the model's memory |
| `scramble_notes.jsonl` | the same notes with content words shuffled — the placebo (C5) |

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
note_id       cn-0001 (corrective) / sc-0001 (scramble)
text          the note itself
kind          "corrective" | "scramble"
principle     1-9, the AMA Principle of Medical Ethics it came from
source        the MedSafetyBench train row it was written from
n_words       used to verify the scramble matches its twin exactly
prompt_sha    hash of the note-writing prompt, so a corpus can be traced to it
twin_of       (scramble only) the corrective note it was built from
```
