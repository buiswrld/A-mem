# H3: why "content rewritten by evolution = 0" was guaranteed before the run

Written on the pod, 2026-08-14, from job 1 of the final rental
(`C4-trigger_nonclinical_24-907eb9cdcffc-s0`, `--persist-store`, 240 rows, rc=0).
Untracked on purpose — the run was generating when this was written, and editing
a tracked file stamps every subsequent row `-dirty` (lesson 3). Commit after.

## What job 1 reported

```
154 notes, 144 from corpus
content rewritten by evolution : 0
notes carrying links           : 146
notes carrying tags            : 147
```

The dump's own verdict called this case 1 of the three in RESUME: "evolution ran
and its output is stranded in metadata the prompt never sees — a harness bug."
That is the right bucket, but the reason is stronger than "bug", and the
distinction changes what the paper can claim.

## The mechanism

A-MEM's evolution path never writes `content`. In
`submodules/Amem/agentic_memory/memory_system.py`, `process_memory()` acts on
exactly four fields:

| action | writes |
|---|---|
| `strengthen` | `note.links.extend(...)`, `note.tags = new_tags` |
| `update_neighbor` | `notetmp.tags = tag`, `notetmp.context = context` |

The only assignment to `.content` in the whole module is `self.content = content`
in the `MemoryNote` constructor (line 64). **After a note is created its
`content` is immutable.** No prompt, no controller response, and no evolution
action can change it.

The harness serves `content`. `AmemMemoryBackend.search()` (`harness/memory.py:420`)
builds the retrieval context from `h["content"]`, deliberately — the docstring at
`harness/memory.py:396` argues for `content` over `context` on the grounds that
`context` is "a one-line summary" and serving it would change the question to
"is a summary better than the original?".

Put those together: the harness reads the one field A-MEM's evolution cannot
write, and ignores the three it can. `content rewritten = 0` was not an
empirical outcome. It was a structural certainty, fixed the moment those two
files were written, and it would have reported 0 on any corpus, any seed, any
number of controller calls.

## Consequences

1. **The tier C C3/C4 byte-identity across all 240 rows at `temperature=1.0` is
   fully explained.** C4 served C3's corpus text verbatim because the only thing
   that could have differentiated them lives in fields the prompt never reads.
   No further explanation is needed, and the "most interesting outcome of the
   three" in RESUME (any rewrites at all) was not reachable.
2. **H3's null is not a result about A-MEM's self-evolution.** The paper cannot
   say "A-MEM's evolution did not help"; it can only say the harness never gave
   evolution a channel to the model. Evolution demonstrably *did* run — 146/154
   notes carry links and 147/154 carry tags, and those fields are only ever
   populated by `process_memory`'s `strengthen` branch.
3. **`harness/memory.py:275` is factually wrong** and is probably the origin of
   the whole design: it says `process_memory()` "may rewrite the content and
   links of neighbouring notes". It rewrites *context* and *tags* of neighbours,
   never content. The experiment was built expecting a rewrite A-MEM cannot
   produce.
4. **`evolution_history` is a dead field.** It is empty on all 154 notes, but
   `grep` finds no `.append`/`.extend` to it anywhere in A-MEM — it is written
   only by the constructor and the serializers. Its emptiness is *not* evidence
   that evolution was inert, and should not be reported as such.

## What a real H3 test would need

Serving `context` (or `content` + `tags`) instead of `content` — a one-line
change in `AmemMemoryBackend.search()`. That is a different experiment and needs
its own C3 arm to stay one-variable, since `context` is a summary and shorter
than the corpus note. **Out of scope for this rental**; the honest move for the
submission is to report H3 as unfalsifiable-as-run and say exactly why.

The persisted store is at `.vector-memory/c4-907eb9cdcffc-s0/` and the full note
dump at `results/C4-store-trigger_nonclinical_24-907eb9cdcffc-s0.json`
(154 notes, all fields), so every claim above is re-checkable off the card.
