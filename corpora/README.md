# Note corpora

`gold_notes.jsonl` and `scramble_notes.jsonl` are built, not hand-edited:

    uv run python scripts/build_notes.py --n 150
    uv run python scripts/scramble_notes.py

Both are committed. They are released with the paper, and a run is only
reproducible if the exact corpus that produced it is in the history.
