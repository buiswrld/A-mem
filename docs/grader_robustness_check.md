# Second-judge robustness audit

This is a completed, post-freeze audit of the frozen automated-judge labels. It
is new judging, but not new model generation, a revision to the frozen primary
analysis, or a clinical validation study. It exists to make a limited question
reproducible: do the
frozen Tier-D C1/C3 labels remain stable when the exact same rubric is applied
by a separately specified, newer model?

## Design

`scripts/grader_robustness_check.py` deterministically selects 60 already
generated Tier-D responses: 10 from each C1/C3 × frozen-`aligned`,
`misaligned`, and `derailed` cell. It uses seed `20260818`, records a digest of
the complete selected records, and preserves the frozen label alongside the
second judge's alignment, coherence, flag, and derived verdict.

The script uses the existing published judge prompts verbatim and two calls per
response. The completed audit made 120 calls to `gpt-5.6-terra`. For GPT-5.6
Terra, the audit sets
`reasoning_effort="none"`, `temperature=0`, and
`max_completion_tokens=16`. Disabling reasoning matters here: the required
answer is only a numeric score, `CODE`, or `REFUSAL`, and reasoning tokens count
toward the completion-token budget. The metadata records these settings for the
Methods and supplement.

The audit is stratified by the original verdict. Report agreement separately in
each cell. Do not describe its pooled agreement as accuracy, a prevalence
estimate, or clinical validation. In particular, it cannot establish whether a
medical response is clinically correct or safe in a specialist sense, and it
does not recompute the C3-versus-C1 effect size.

## Reproduction

Preparation is local only and writes outside `results/`:

```bash
uv run python -m scripts.grader_robustness_check prepare
```

Run this from the repository root. Direct execution is also supported:
`uv run python scripts/grader_robustness_check.py prepare`. `harness/` is a
local Python package in this repository, not a separately initialized Git
submodule.

The completed output is in `analysis/grader_robustness/`. Do not rerun this
audit or substitute another judge under the frozen study identity. The local
analyzer may be used to reproduce the already-completed summary:

```bash
uv run python -m scripts.grader_robustness_check analyze
```

The runner checkpoints after each response. Re-running it with the same model
resumes completed work; it rejects a mixed-model output file. The analyzer
checks the sample digest, completeness, and a single model identifier before
printing within-cell and balanced-sample verdict agreement. The metadata file
also records the selected model, requested call count, execution status, and
UTC start/completion timestamps; cite that file in Methods and the supplement.

## Reporting language

Report the model identifier, date, prompts, sample construction, the 120-call
budget, exact agreement in every cell, and all disagreements. The completed
audit has 45.0% (27/60) exact verdict agreement; agreement is 0/10 in both
frozen-`derailed` cells. A suitable bounded claim is: “On a fixed,
verdict-stratified, post-freeze Tier-D audit sample, labels showed 45.0% exact
agreement under a separately specified second judge using the same rubric.”

Do not claim that this validates clinical quality, proves the effect is
model-independent, or upgrades the frozen results to expert-reviewed evidence.
The existing endpoint sensitivity analysis remains the no-additional-API
robustness analysis; see `docs/experiment_freeze.md` §8.
