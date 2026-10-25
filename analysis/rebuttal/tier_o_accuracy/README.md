# Tier O free-form correctness assessment

Status: **completed**. Assessed 6,850 responses; the final analysis includes
6,800 responses on 136 questions and excludes 2,200 of the 9,000 distinct-condition
responses. See report.md and results.json. This is a post-hoc reviewer-requested
analysis. Original C4 is a verified C3 duplicate.

The first eligibility rubric pass is archived in eligibility_pilot_v1. Inspection
found excessive reliance on comparative wording as an exclusion reason. The v2
rubric clarifies that superlatives and “which of the following” do not themselves
require answer options. All 180 questions were reassessed before any answer was
scored. Final automated eligibility decisions were retained without manual
clinical overrides; they remain unvalidated.

The frozen input includes 180 source questions, retained MedMCQA options and
zero-based keys, and 9,000 saved responses from C1, C2, C3, C5, and C6. The prepare
step verifies that original C4 responses and model-visible contexts exactly
duplicate C3. C4 is neither independently assessed nor pooled with C3.

## Protocol

1. Assess all 180 questions for fair free-form scoring without seeing responses
   or conditions. Exclude missing images/cases, materially incomplete stems,
   genuinely option-dependent tasks, and unreliable references. The phrase
   "which of the following" alone does not establish option dependence.
2. Lock the eligibility decisions and minimal required answer. Apply every
   question exclusion to all five conditions. Flag questionable keys rather than
   silently substituting a different answer. Inspect eligibility reasons and
   key-concern flags before commencing scoring; document any adjudication.
A final mechanical check found conflicting eligibility for two stems identical
apart from punctuation (mcqa-09ce3345 and mcqa-edd2f617). Both were conservatively
excluded: one was already excluded, adding one question and 50 assessed responses
to the exclusions. This check occurred after scoring and is disclosed; it uses
only question text and eligibility decisions, not condition outcomes. Original
judgments remain unchanged. The final bootstrap groups identical normalized
stems together: 133 clusters for 136 included question records.

3. Score blinded, shuffled answers against the source stem and retained reference.
   Accept semantic equivalents. Labels are correct, incorrect, incomplete, and
   nonanswer; only correct receives 1. Refusals and derailed/off-topic answers
   remain in the accuracy denominator. Answer-level reference concerns are flags,
   not response exclusions. Inspect those flags before reporting results; any
   change to eligibility requires a documented new analysis version.
4. Require complete scores for all retained questions before analysis. Report
   scored/excluded questions and responses, label counts by condition, correctness
   rates, and C3-C1/C3-C2 differences. Use 2,000 shared question-cluster bootstrap
   resamples at seed 0 with BCa 95% intervals, grouping punctuation-normalized
   identical stems into one cluster; record percentile fallback when
   the BCa correction is undefined.

This measures automated benchmark-key-referenced correctness, not clinician-
validated usefulness. Intervals do not represent judge, generation-seed, or
model-family variability. Selection/exclusion is post-hoc and must be disclosed.

## Run

Configure credentials locally in `OPENAI_API_KEY`; do not paste keys into chat.
Use one explicit judge model and identical settings across all answer batches.
The judge must support temperature zero, JSON-object output, and
`max_completion_tokens` on the configured chat-completions endpoint.

```bash
python -m scripts.tier_o_accuracy prepare
python -m scripts.tier_o_accuracy run --stage eligibility --model MODEL_ID
# Inspect all eligibility decisions before proceeding.
python -m scripts.tier_o_accuracy run --stage answers --model MODEL_ID
python -m scripts.tier_o_accuracy analyze
```

The default answer batch has ten responses, the completion cap is 4,096 tokens,
and truncated or malformed judge output aborts rather than becoming a score.
Use `--base-url` for a compatible endpoint. `--limit-calls 1` supports a pilot;
resume with identical settings. There are 180 eligibility calls and at most 900
answer calls, before exclusions. API errors stop execution; completed judgments
are retained for resumption. Raw outputs and usage are archived. Eight concurrent calls are used by default;
`--workers` changes execution concurrency without changing the judging rubric.

`answers.jsonl` is blinded assessor input. `mapping.jsonl` is an analysis-only
condition mapping and must not be supplied to an assessor. The rubrics and
manifest are saved in this directory. Source results are never edited.
