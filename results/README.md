# Publication result data

[`manifest.json`](manifest.json) is the canonical inventory. Every declared run
retains its original JSONL and the corresponding judged JSONL. The judged row is
the raw row plus five judge fields, allowing the provenance check to verify that
scoring did not alter the generated response.

The files are organized by their role in the study:

| Directory | Contents |
| --- | --- |
| `primary/tier_c/` | Six exploratory nonclinical-generalization conditions |
| `primary/tier_d/` | Six exploratory harmful-clinical conditions |
| `primary/tier_o/` | Six preregistered benign-clinical conditions |
| `sensitivity/` | Matched no-session C3/C5 runs for Tiers C and D |
| `diagnostic/` | Persisted-store C4 run and store snapshot used to diagnose the A-MEM mechanism |
| `calibration/` | Standalone C1/C6 Betley-8 calibration runs, retained for provenance but not used by the canonical paper analysis |
| `followup_amem_v2/` | Final matched Tier-D C4 evolution experiment, including its evolution-off control, transcript, and store snapshots (directory name retained from execution) |

Superseded pilots, dirty-provenance outputs, duplicate pinned samples, and the
regenerable judge cache are intentionally excluded from the publication tree.

From the repository root, verify roles, hashes, provenance, row identities, and
raw/judged pairing with:

```bash
uv run python scripts/verify_results.py
```

The analysis scripts select files by manifest role and run ID rather than by
filename glob.
