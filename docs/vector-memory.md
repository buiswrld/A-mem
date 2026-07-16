# Simple vector memory: the first building block

## What we are making

`SimpleVectorMemory` is a small local memory store with two public actions:

```python
memory.add_note("text the agent may remember")
matches = memory.search("a related question")
```

ChromaDB stores the text on disk and converts it into a numeric representation
of its meaning.  A search converts the query in the same way and returns the
closest notes.  It does not decide whether a note is true, write an answer, or
call an LLM.

## Why it exists alongside A-MEM

A-MEM is the larger system.  It can create rich memory notes, attach tags and
links, and later evolve related notes with an LLM.  It already uses ChromaDB
internally, but its default collection is reset when a new `AgenticMemorySystem`
starts.  That is useful for an isolated demo but not for a persistent,
inspectable experiment corpus.

This small wrapper gives us a transparent retrieval baseline first.  Once it
works, we can compare it with stock A-MEM instead of changing several ideas at
once.

## The three layers

| Layer | Job | Does it need Darrell's API key? |
| --- | --- | --- |
| Memory note | The actual text the system is allowed to remember. | No |
| ChromaDB / vector store | Finds notes whose meaning resembles the query. | No |
| Answering LLM | Reads the question plus retrieved notes and writes an answer. | Yes |

So, adding a note means two things happen at once: the original note is saved
and a searchable meaning-based index is updated.  The vector store is not a
second brain.  It is the index that lets the system find the right few notes
instead of showing every note to the LLM.

## What should go into the vector store

Store one self-contained memory claim or note per record.  The `content` text
is what retrieval searches.  Small metadata fields such as `source`, `kind`,
and `run_id` provide traceability.

Do **not** put the held-out MedMCQA evaluation question, its correct-option
label, or its explanation into the memory collection.  Those belong in the
evaluation dataset.  Otherwise a test can accidentally become a lookup test:
the system retrieves the answer it was given already.

For the misinformation experiment, each condition needs a separate collection
or an otherwise guaranteed isolated copy:

1. `no_memory`: no notes.
2. `clean_memory`: permitted clean notes only.
3. `poison_memory`: the same clean notes plus approved false-claim records.
4. `corrected_memory`: the poison condition after a defined correction step.

The current expanded poison JSON mixes a false claim and its correction in one
field, so it must not be inserted directly.  We will write a small adapter
later that selects the intended claim and keeps correction material out of the
memory text.

## The experiment scaffold now in place

`agentic_memory.experiment_memory` supplies three deliberately small helpers:

```python
from agentic_memory.experiment_memory import (
    contents_for_prompt, load_notes, open_condition, retrieve_with_log,
)

memory = open_condition("clean", directory=".vector-memory")
load_notes(memory, [
    {
        "note_id": "clean-001",
        "content": "An approved clean reference note.",
        "metadata": {"kind": "clean_note", "topic": "example"},
    }
])

record = retrieve_with_log(
    memory, question_id="dev-001", query="A related question", k=3
)
notes_for_llm = contents_for_prompt(record)
```

- `open_condition()` maps `clean`, `poison`, and `corrected` to separate
  Chroma collections such as `mcq_clean`. The no-memory baseline simply does
  not open or search a collection.
- `load_notes()` upserts an approved, already-normalized list of notes. It
  intentionally does not parse the current poison JSON yet.
- `retrieve_with_log()` records every final returned note with its rank, ID,
  content, distance, and metadata. `poison_retrieved` is `true` only if one of
  those final top-k notes has `kind: "poison_claim"`.
- `contents_for_prompt()` strips the result down to note text. The LLM never
  sees the poison flag, record ID, rank, or distance.

This is enough to validate isolation and observability using harmless sample
notes before the research team approves the final clean and poison corpora.

## Direct poison input

Once the team approves the final poison JSON, make each record already match
`load_notes()` and insert it directly. Keep only the intended claim in
`content`; do not include any explanation or correction in that field.

```python
approved_poison_note = {
    "note_id": "poison-001",
    "content": "only the approved poison-memory text",
    "metadata": {
        "kind": "poison_claim",
        "record_id": "poison-001",
        "category": "...",
        "difficulty_tier": "...",
        "source": "...",
    },
}
load_notes(open_condition("poison"), [approved_poison_note])
```

Metadata must use scalar values only. Leave `explanation` out of the memory
note and prompt; retain it separately only if the research team needs it for
hidden evaluation material.


## What this first version deliberately does not do

- It does not use LangChain.  LangChain can be useful later to connect an LLM,
  prompt templates, and retrievers, but it is not required for this small
  storage-and-search step.
- It does not call an LLM, so it does not need an API key.
- It does not judge medical truth or ingest any clinical data automatically.
- It does not yet replace A-MEM; it gives us a clear baseline to compare with it.

## A concise update for Darrell

> On `feat/vector-mem`, we are adding a persistent ChromaDB baseline with a
> tiny `add_note` / `search` interface.  Each experiment condition gets an
> isolated collection, and held-out MedMCQA questions stay outside the memory
> store.  The first smoke test needs no API key; the key is only needed when we
> feed retrieved notes into the answering agent.  Next we should agree on the
> clean memory corpus, the poison-record adapter, and the exact evaluation
> split before running comparisons.
