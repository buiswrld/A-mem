# Human outcome-validation audit

This directory contains the prepared `hv1` sample and two self-contained blinded
rating pages. **The protocol was closed without execution on 2026-08-16. No
rater opened a page and no rating exports exist.** The governing protocol is
[`docs/human_validation_protocol.md`](../docs/human_validation_protocol.md).

These files are retained as transparency artifacts, not completed methodology.
Do not use the pages or attribute later ratings to the frozen study. A future
validation should receive a new protocol identity and be reported as a follow-up.

The package that was prepared comprised:

- `docs/human_validation_protocol.md`
- `scripts/build_human_validation.py`
- `scripts/analyze_human_validation.py`
- `human_validation/sample_manifest.json`
- `human_validation/rater_a.html`
- `human_validation/rater_b.html`

The planned—but unexecuted—workflow would have saved exports as:

```text
human_validation/ratings/rater_a.json
human_validation/ratings/rater_b.json
```

and analyzed them with:

```bash
uv run python scripts/analyze_human_validation.py \
  human_validation/ratings/rater_a.json \
  human_validation/ratings/rater_b.json
```

No such files are present. The source manifest remains separate from the HTML
pages and records the automated-label strata used to construct the unrealized
audit.
