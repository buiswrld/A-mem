# Camera-ready consolidation

## Review branch

`camera-ready/consolidated` brings the final research snapshot onto the history
of the repository's default branch, `main`, for one reviewable pull request.
The starting research snapshot is local `draft` commit
`1280565d126026edeff3fcd6623585264f21bca2` (one commit beyond remote `draft`
`3eae34417194981cda668d5fdf2897368d83e98d`). It includes the workshop manuscript
and completed rebuttal correctness assessment.

The `main` tip at consolidation is
`ceffb860f0712bbae97b184d440df62bc910ca8d`, the upstream A-MEM library layout.
Its history and the research snapshot have no common ancestor. A merge using
the research tree preserves both histories and makes the PR comparable to
`main`. The library now lives under `submodules/Amem/`, with its MIT license.
The PR therefore includes the full research layout rather than only these
final documentation edits. Existing branches remain available for provenance.

## Branch and evidence map

Branch names alone are not an inventory of publication results. The executable
inventory is [`results/manifest.json`](../results/manifest.json), whose run
records retain generation provenance and lock the saved data by hash.

| Historical branch | Tip inspected | Role in the consolidated snapshot |
| --- | --- | --- |
| `draft` (local) | `1280565` | Final manuscript, results, analyses, and rebuttal assessment |
| `draft` (remote) | `3eae344` | Previous manuscript revision |
| `final` | `56a03e1` | Earlier final snapshot; superseded by manuscript revisions |
| `c4-impl` | `d42e9cb` | Final C4 mechanism implementation; included in the research ancestry |
| `dev` | `8bb8db4` | Earlier experiment snapshot; historical work below the research history boundary |
| `work/rag-repair` | `feeaecb` | Earlier retrieval logging/export implementation |

Older development branches are retained as history. Their pilot outputs and
superseded implementations are not additional publication conditions to merge
into the final protocol. The research history begins at a snapshot commit
`792ee08`; earlier branch ancestry is not fully connected to that snapshot.

## Suggested review order

1. Read the root README and [`final_results.md`](final_results.md) for scope,
   conditions, endpoints, and limitations.
2. Inspect `results/manifest.json`, then `analysis/canonical/` for primary
   evidence. The matched C4 evidence is under `results/followup_amem_v2/`.
3. Review `harness/run_condition.py` and `harness/run_session.py`, followed by
   `memory.py`, `judge.py`, and `stats.py` for execution and scoring.
4. Review `analysis/rebuttal/` separately as supplementary reviewer analyses.
   Tier O correctness is completed; the proposed Tier A experiment was not run.
5. Review canonical manuscript sources directly under `paper/`.

## Validation

Run `uv run python scripts/verify_submission.py` after setup. It verifies locked
results, recomputed canonical analyses, second-judge statistics, manuscript
consistency, the test suite, the generated Overleaf bundle, and the LaTeX build.
This passed locally on 2026-10-24 before consolidation. The final documentation
changes are checked again before opening the PR.

No generation, rejudging, result replacement, or statistical endpoint changes
are part of this cleanup. The recorded environment-provenance limitation in
`final_results.md` still applies; the lockfile does not retroactively establish
the exact libraries used on the original GPU pod.
