# Prompt specification v1: MedMCQA MCQ pipeline

This is the first, deliberately narrow prompt specification for the A-MEM
integration experiment. It is for synthetic MedMCQA multiple-choice questions,
not clinical deployment or patient care.

## Roles in v1

1. `intake.md` normalizes one source question without judging its truth.
2. `memory-manager.md` documents the thin wrapper around stock A-MEM.
3. `clinical-reasoning.md` produces the single answer that is scored.

The safety-review role is intentionally deferred. In an MCQ experiment it would
be a second medical reasoner and could hide a memory-caused error before it is
measured. A later vignette-based version can score it separately, off the
primary answer path.

## Fixed intake schema

```json
{
  "case_id": "string",
  "source": "medmcqa",
  "subject": "string or null",
  "topic": "string or null",
  "question": "string",
  "options": {"A": "string", "B": "string", "C": "string", "D": "string"},
  "clinical_context": {
    "symptoms": [],
    "history": [],
    "medications": [],
    "allergies": [],
    "vitals": {},
    "other_stated_facts": []
  }
}
```

Most MedMCQA rows will have empty clinical-context fields. That is expected: do
not invent missing patient details. The gold `cop` answer and source
explanation are evaluation-only fields and must not be passed to the intake or
reasoning prompt for a held-out MCQ run.

## Experimental constants

Record the prompt version, model, temperature, retrieval `k`, memory condition,
and raw model output for every run. Do not alter prompt wording between clean,
poisoned, and repair conditions.
