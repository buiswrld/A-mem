# The study in plain language

_A non-technical explanation of what we did, what we found, and what we can
honestly claim. Written for talk preparation. Every number traces to
`analysis/frozen/`; the shakier ones are marked._

---

## 1. The problem, in one scene

A hospital licenses a medical AI assistant from a vendor. A few weeks in, its
answers start going wrong — not obviously broken, just quietly unsafe advice.

The hospital cannot fix the model. They don't have the weights; the vendor does.
Retraining is off the table.

But there *is* one thing the hospital controls: **the notes the AI reads before
it answers.** Most clinical AI systems work by looking up relevant documents and
putting them in front of the model as background material. That document
collection belongs to the hospital.

**Our question: is that enough? Can you fix a broken model by fixing what it
reads, without ever touching the model itself?**

## 2. Why the model was broken in the first place

There's a known and genuinely strange effect called **emergent misalignment**.
If you fine-tune a language model on a narrow slice of bad data — say, bad
medical advice — it doesn't just get worse at medicine. It gets broadly worse.
Ask it an unrelated question and it will say something troubling.

Someone published a model deliberately broken this way, as a research tool. We
used it as-is. **We never trained anything.** The broken model is a fixed
starting point, like a patient with a known condition.

Here's the gap we're filling. Every published way to reverse this damage needs
access to the weights or the model's internals — the exact access a hospital
doesn't have. And there's a whole separate research area about *protecting* a
good model from *bad* memory. Nobody had asked the reverse question: **can good
memory repair a bad model?** That's ours.

## 3. What we actually did

We wrote **144 short clinical safety notes** — plain, correct guidance, the kind
of thing a hospital would put in its reference collection.

Then we ran the same set of questions past six different versions:

| Version | What it is | Everyday analogy |
|---|---|---|
| **C1** | Broken model, no help | The problem, untreated |
| **C2** | Broken model, notes pasted into a fixed instruction | Taping the same cheat sheet to every page |
| **C3** | Broken model, notes looked up per question | A librarian fetching the relevant page |
| **C4** | Broken model, "smart memory" that reorganizes itself | A librarian who also rewrites the books |
| **C5** | Broken model, *fake* notes — same length, no safety content | A placebo, exactly like in a drug trial |
| **C6** | The healthy model, never broken | What "fixed" would look like |

C5 is the important control. Without it, you can't tell whether the model
improved because the notes were *correct* or just because you handed it
*something to read*.

C6 is the ceiling. It tells you how much room there was to improve at all.

We asked about **27,760 questions in total** across four question sets: dangerous
medical requests, harmless medical questions, general non-medical questions, and
a small standard set for comparison with earlier published work. A separate AI
graded every single answer.

## 4. The main finding

**On dangerous medical requests, harmful answers dropped from 63% to 15%.**

That's about **three-quarters of the way** from broken back to healthy — achieved
purely by changing what the model reads. No retraining, no access to the weights.

For a hospital, that's a real option where previously there was none.

**But be careful how you say it.** The model is not fixed. The notes only help
while they're actually in front of it. Turn the retrieval off and the model is
exactly as broken as it was. The right phrase is **"runtime steering," not
"repair."** I'd put that on a slide, because it's the sentence that keeps the
result honest.

Also: it's *partial*. Even with the notes, the model is still noticeably worse
than a healthy one. We didn't close the gap; we narrowed it.

## 5. The first honest catch: the fancy version didn't beat the simple version

We expected the smart lookup (C3) to beat the dumb approach of pasting the same
notes into every prompt (C2).

**It didn't.** They were statistically indistinguishable.

That's a negative result and we report it as one. But we figured out *why*, and
the why turned out to be the most interesting thing in the study.

## 6. The mechanism: the model poisons its own notes

Our setup was realistic: the AI has a conversation first, and **writes its own
answers into its memory** — which is what a deployed assistant actually does.

Here's the problem. **The model is broken.** So the answers it saves are bad
answers. And now they're sitting in the same collection as our 144 good notes,
competing for the same shelf space.

The system only fetches **three notes per question.** Every slot taken by the
model's own bad answer is a slot not holding good guidance.

We measured this directly:

| Slots taken by the model's own answers | Harmful answers |
|---|---|
| 0 of 3 | 11% |
| 1 of 3 | 31% |
| 2 of 3 | 28% |
| 3 of 3 | 47% |

**Every good note that gets crowded out costs roughly 8–10 percentage points of
harm.** The pattern holds in both arms of the experiment.

In the placebo version it was worse: the fake notes were deliberately unrelated
to safety, so against medical questions they lost the competition badly — the
model's own bad answers captured **up to 72%** of all available slots.

This explains section 5. Fixed instructions can't be crowded out — nothing
competes with them. Smart lookup's advantage is relevance, but the same
relevance machinery lets *anything* in, including the model's own garbage. **The
advantage gets spent paying for the vulnerability.** When we removed the
conversation history entirely, smart lookup *did* beat the fixed instruction.

There's a practical takeaway here worth saying out loud: **reserve the slots.**
If safety guidance is guaranteed to be in context no matter what, this whole
failure mode disappears. We didn't test that — say "hypothesis," not "finding."

## 7. The test we set up to catch ourselves — and failed, in a good way

The obvious cheat: an AI that refuses to answer anything looks perfectly safe.
Harm goes to zero. It's also useless.

So before we ran anything, we **wrote down and sealed a prediction**: the fixed
model would start refusing harmless questions, by at least 10 percentage points.
Sealed first, so we couldn't quietly change our minds afterward.

**The prediction was wrong. Out of 10,800 answers to harmless medical questions,
across all six versions, there was not one refusal.**

Being wrong here is the good outcome — it means the safety gain wasn't bought by
clamming up.

And we can prove the refusal-detector wasn't just broken: on genuinely dangerous
requests, **the same model refused 21% of the time.** It knows how to refuse. It
just doesn't do it on harmless questions.

This is the most trustworthy result in the paper, because it's the one we
committed to in advance and the one that could have made us look bad.

## 8. The second honest catch: a flaw in the grading

This one is uncomfortable and it belongs in the talk anyway.

The AI grader scores each answer twice: *how harmful* and *how coherent*. The
standard rule throws out answers scoring 50 or below on coherence — sensible,
since gibberish shouldn't count as "harmful."

Two problems.

**First, it's a pile-up, not a spread.** 98–99% of the thrown-out answers scored
*exactly* 50. So the rule isn't filtering a range of bad answers — it's making a
yes/no call at one specific number where a huge number of answers happen to land.
Whether you write "50 or below" or "below 50" changes the fate of over a
thousand answers.

**Second, and worse: the thrown-out answers weren't gibberish.** They were
fluent, on-topic, and *medically wrong*. Real examples we pulled:

- treating presbyopia with concave lenses (it's convex)
- propranolol for managing diabetes
- a thyroid cancer plan with no check for whether the cancer had spread

Those are exactly the dangerous answers we're supposed to be counting — and the
rule was quietly deleting them from the tally.

When we recount including them, the broken model's harm rate on harmless
questions goes from **9% to 23%.**

**What survives and what doesn't:**

- The **main medical findings hold** under every version of the rule. That's the
  headline and it's solid.
- One claim **does not hold**: we had said the fix also helped on general
  non-medical questions. Recount properly and that benefit disappears — the
  placebo actually does better. **We withdrew that claim.**

Presenting a withdrawn claim is not a weakness. It's the part of the talk where
people decide whether to trust the rest of it.

## 9. The condition that never ran

C4 — the self-reorganizing "smart memory" — produced answers **byte-for-byte
identical** to plain lookup across all 5,640 answers. Not similar. Identical.

We traced it. The memory system reorganizes several fields of each note, but our
code hands the model a *different* field — one the reorganizing never touches. So
the clever part genuinely ran, and its output could not physically reach the
model.

That's a wiring bug on our side, and we say so. What we do **not** say is "smart
memory doesn't help" — we never tested it. **A broken test is not a negative
result**, and pretending otherwise would be the easiest lie in the paper.

## 10. The honest summary

**What we can claim:**
- Fixing what a model reads can undo a large fraction of damage baked into its
  weights, with no retraining.
- That gain was not bought by refusing to answer — and we predicted the opposite
  in advance, in writing.
- The improvement works by *occupying context*, and we can measure the cost of
  each slot lost.

**What we cannot claim:**
- That the model is fixed. It isn't. Remove the notes and it's broken again.
- That smart retrieval beats a plain instruction — under our main setup it
  didn't.
- That any of this helps outside medicine. We tried to claim it; it didn't
  survive; we withdrew it.
- Anything about self-reorganizing memory. We never tested it.

**What we'd fix with more time:** one AI graded everything, and no human checked
its work. We prepared a human review and never ran it. And every measurement we
have is a judgment call by an AI — none of it is an objective score against a
known-correct answer.

---

## Suggested talk structure (~12 minutes)

| Time | Beat |
|---|---|
| 0–1 | The hospital scene. No weights, only the documents. |
| 1–3 | Emergent misalignment: narrow bad training, broad bad behavior. Everyone's fix needs weights. |
| 3–4 | The six versions, especially *why* the placebo and the healthy ceiling exist. |
| 4–6 | **63% → 15%.** Then immediately: "runtime steering, not repair." |
| 6–9 | **The slot-crowding mechanism.** The dose-response table is your best slide. |
| 9–10 | The sealed prediction that failed in the good direction. |
| 10–11 | The grading flaw, and the claim we withdrew. |
| 11–12 | What a hospital should actually do: reserve the slots. |

Lead with the mechanism (section 6), not the headline number. The number is a
result; the mechanism is an *explanation*, and it's what the room will remember.

## Questions you will get

**"Isn't this just prompting?"**
Under our main setup — essentially yes, and we report that. The interesting part
is *why*: retrieval's advantage gets eaten by its own vulnerability. Remove that
vulnerability and retrieval does win.

**"Your grader is an AI. Why should I trust it?"**
You shouldn't, entirely — that's our biggest limitation and we state it. Two
things help: we used the exact published grading prompts rather than inventing
favorable ones, and we show what happens under different rules. The medical
findings survive all of them. One claim didn't, and we dropped it.

**"Isn't 180 questions small?"**
For the preregistered part, yes, and we say so. Note we ran ten answers per
question and our statistics account for answers to the same question not being
independent — the intervals are wider than a naive count would give.

**"Does the model get less useful?"**
We can't fully answer that, and it's the honest gap. It doesn't refuse more —
that we tested and it's clean. But we never scored answers against known-correct
answers, so we can't rule out that it got safer *and* less accurate. That's the
first thing we'd add.

**"Would this work outside medicine?"**
We don't know. We tried to show it and the claim didn't survive our own recount.

---

## Notes for the author

- **The real manuscript is `paper/*.tex`** (GenAI4Health @ NeurIPS 2026), not
  `docs/paper/*.md`. `method.tex`, `results.tex`, `discussion.tex`, and
  `limitations.tex` are still empty stubs.
- **`paper/main.tex`'s abstract still claims the non-clinical result** — it says
  harm fell "across clinical, non-clinical, and preregistered benign clinical
  evaluations." Section 8 above withdraws the non-clinical half. Fix the abstract
  and the introduction together.
- Section 6's dose-response still needs an executable analysis path. Section 8's
  endpoint recount is now reproducible with `scripts/sensitivity_analysis.py`;
  regenerate `analysis/sensitivity/` before copying numbers into slides.
