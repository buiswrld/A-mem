# Historical notebooks

The experiment closed on 2026-08-16. These notebooks document data construction
and execution but are not the active analysis workflow and should not be rerun
against the frozen output namespace.

| Notebook | Historical role |
| --- | --- |
| `01_build_data.ipynb` | Built probes, corrective notes, the retired scramble corpus, and later the neutral placebo. Contains the original note-writing prompt. |
| `01b_build_placebo.ipynb` | Built only `corpora/placebo_notes.jsonl`, the C5 control used in final runs. |
| `01c_expand_probes.ipynb` | Built the 180-prompt MedSafetyBench expansion. |
| `02_run_conditions.ipynb` | Historical generation/judging workflow before the final batch scripts. |

Do not rerun `01_build_data.ipynb` top to bottom: its API-backed steps can
replace committed corpora with newly generated content, breaking the link
between the frozen result rows and their intervention. The retired
`scramble_notes.jsonl` remains only for provenance; final C5 runs use
`placebo_notes.jsonl`.

For the paper, use the non-notebook verification path:

```bash
uv run python scripts/freeze_results.py
uv run python -m scripts.final_analysis
```

See `docs/experiment_freeze.md` for the exact final scope and
`results/frozen_manifest.json` for the selected run files.
