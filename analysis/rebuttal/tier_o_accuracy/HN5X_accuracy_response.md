We agree that the absence of benign-request refusal does not establish answer
correctness. In response, we conducted a post-hoc assessment of the saved
free-form Tier O responses against the source MedMCQA questions and keys. The
assessment used gpt-4o-2024-08-06, blinded to condition, with one consistent rubric
accepting semantic equivalents and treating incorrect, incomplete, and nonanswers
as unsuccessful. Question eligibility was assessed separately without responses.
The final analysis includes 136 of 180 questions and 6,800 responses across five
distinct conditions; 44 questions and 2,200 responses were excluded uniformly.
We assessed 6,850 responses, then excluded 50 after a mechanical check identified
conflicting eligibility for an otherwise identical question stem. Original C4
exactly duplicates C3's saved responses and model-visible setup and was not
counted independently.

Correctness was 13.31% for untreated C1, 28.24% for fixed-prompt C2, 27.28% for
corrective-retrieval C3, 27.57% for neutral-retrieval C5, and 43.90% for base-model
C6. Paired C3-C1 was +13.97 percentage points [9.59, 18.41]; C3-C2 was -0.96
[-3.56, 1.84]. Intervals use 2,000 shared cluster bootstrap draws with BCa
correction, grouping punctuation-normalized identical stems into 133 clusters.
Thus, the additional endpoint supports improved benchmark-referenced correctness
over the untreated model but does not establish retrieval superiority or restored
base-model performance. Automated eligibility and correctness judgments remain
unvalidated by clinicians, and the single-model, single-generation-seed limitation
remains. These results do not establish clinical usefulness.
