# Tier O free-form correctness

Automated benchmark-key-referenced free-form correctness, not clinician-validated clinical usefulness; uncertainty conditional on retained questions and fixed judge. C4 is a verified C3 duplicate.

Included 136/180 questions and 6800/9000 responses. Excluded 44 questions and 2200 responses equally across conditions. Assessed 6850 responses; 50 assessed responses were excluded by the duplicate-eligibility consistency check.

| Condition / contrast | Correctness / difference (percentage points) | 95% CI |
|---|---:|---:|
| C1 | 13.31 | [10.72, 16.48] |
| C2 | 28.24 | [22.98, 33.60] |
| C3 | 27.28 | [22.24, 32.85] |
| C5 | 27.57 | [22.87, 32.66] |
| C6 | 43.90 | [36.90, 50.32] |
| C3-C1 | 13.97 | [9.59, 18.41] |
| C3-C2 | -0.96 | [-3.56, 1.84] |

Shared question-cluster resampling over 133 punctuation-normalized stem groups: 2,000 draws, seed 0; BCa intervals with recorded percentile fallbacks. No judge/model/seed variance is estimated.

## Excluded questions

- mcqa-03486244: options_required — The question asks for the most useful test for diagnosis and management of a leaky meningomyelocele, but without options, multiple tests could be considered useful depending on the clinical context. The options are needed to constrain the answer space.
- mcqa-03952f72: missing_case — The question references 'CASE -2 SR' which suggests it is part of a series or requires prior context that is not provided. Without the initial case details, the question cannot be fairly assessed.
- mcqa-1cf99105: options_required — The question asks which drug is not used for the medical management of ectopic pregnancy, which requires the options to determine the correct answer, as multiple drugs could potentially be valid answers.
- mcqa-2639d0ba: options_required — The question asks which condition does not require SABE prophylaxis, which is a negative question. Without the options, multiple conditions could potentially be valid answers, making it unscorable without the candidate list.
- mcqa-2fd187fb: options_required — The question asks which factor contributes to the short duration of anesthetic action of thiopental, but without the options, multiple factors could be considered. The options are needed to constrain the possible answers.
- mcqa-4391391c: options_required — The question asks for the management of a specific case of squamous cell carcinoma of the vulva, which can have multiple valid management strategies depending on clinical guidelines and patient specifics. Without options, it is unclear which management strategy is considered the reference answer.
- mcqa-4982eef9: ambiguous_stem — The stem asks for a suggestion on changing anti-epileptic treatment for a pregnant woman with juvenile myoclonic epilepsy. Without options, multiple defensible approaches exist, such as switching to a different medication or continuing with monitoring, making the stem ambiguous.
- mcqa-49b456da: unreliable_reference — Topical bacitracin is not a standard treatment for MRSA colonization of the anterior nares. Mupirocin is typically used for decolonization. The keyed answer is questionable and does not provide a reliable reference for scoring.
- mcqa-4f4aa2a7: options_required — The stem 'Adeno ameloblastoma treatment' is too broad and does not specify a unique treatment approach without the options. Multiple treatments could be considered valid without the candidate list.
- mcqa-599273bd: missing_image — The question refers to a case shown, which implies the presence of an image or other visual information that is not provided. Without this context, the question cannot be fairly scored.
- mcqa-5ba07589: options_required — The question asks for a substance for which atropine is not an antidote, which requires knowing the specific list of substances to determine the correct answer. Without the options, multiple substances could potentially be valid answers.
- mcqa-6ec7c97f: options_required — The question asks which property a sevoflurane vaporizer resembles, but without options, multiple properties could be considered. The options are needed to constrain the answer space.
- mcqa-6ef5b644: ambiguous_stem — The management of obstructed labor with fetal demise and maternal dehydration can vary based on clinical context. Both craniotomy and cesarean section could be considered depending on the specific circumstances, such as the degree of obstruction and maternal condition. Without options, multiple management strategies could be equally defensible.
- mcqa-77997eca: options_required — The question requires specific dosing information for the IV loading dose of MgSo4 in pre-eclampsia, which is not a universally agreed-upon standard and can vary. Without the options, multiple dosing regimens could be considered correct.
- mcqa-7ef1e046: options_required — The question asks for the next management step during a blood transfusion reaction, which can vary based on the specific situation and requires options to determine the appropriate action. Without options, multiple management steps could be equally defensible.
- mcqa-8cd9acfa: options_required — The question asks for 'which of the following instructions' without providing a clear task or context that can be answered without the options. The correct answer depends on the specific instructions listed in the options.
- mcqa-92b73e84: options_required — The question asks for the 'drug of choice' for Burkholderia cepacia pneumonia, which can vary based on clinical guidelines and resistance patterns. Without the options, multiple antibiotic regimens could be considered valid, making it difficult to determine a single correct answer.
- mcqa-9915556e: options_required — The question asks which drug is not used in the management of rheumatoid arthritis, which requires the options to determine the correct answer, as multiple drugs could potentially not be used for this condition.
- mcqa-a963bf66: options_required — The question asks for the 'best guide' for resuscitation management, which is subjective and context-dependent. Without options, multiple guides could be considered valid, such as blood pressure or urine output, depending on the clinical scenario.
- mcqa-ac195c22: options_required — The question requires a specific immunization plan based on the child's age and previous vaccinations. Without the options, multiple immunization plans could be considered correct, as the schedule can vary based on guidelines and clinical judgment.
- mcqa-b55cdaad: options_required — The question asks which tumor does not involve steroids in management, which requires a candidate list to determine the correct answer, as multiple tumors could potentially fit this criterion.
- mcqa-c35aba8a: options_required — The question asks for the least efficacious drug in treating temporal lobe epilepsy, which requires a comparison among multiple drugs. Without the options, it is not possible to determine which drug is least efficacious.
- mcqa-c9aa8c5b: options_required — The question asks for what is 'Not present' after a mistakenly high dose of epidural morphine, which requires options to determine the correct answer. Without options, multiple symptoms could be considered absent, making it unscorable.
- mcqa-cb562414: options_required — The question asks which action of adrenaline is not observed, which requires knowing the specific actions listed in the options to determine the correct answer.
- mcqa-ce4876e4: options_required — The question asks for the treatment of a specific case, but the treatment regimen can vary based on the specific diagnosis and clinical guidelines. Without the options, it is not possible to determine the exact treatment regimen intended by the question.
- mcqa-d1ef23c9: options_required — The question asks for the immediate treatment of CSF Rhinorrhoea, which could have multiple valid approaches depending on the clinical context. Without options, it is unclear which specific treatment approach is being referenced as the immediate treatment.
- mcqa-e0ea5246: ambiguous_stem — The question asks where treatment should start in a case of panfacial trauma, but multiple approaches could be equally valid depending on clinical context and surgical preference. The stem does not provide enough information to determine a single correct starting point without options.
- mcqa-edd2f617: options_required — The question asks where morphine should not be used, which requires options to define the specific context or condition. Without options, multiple valid answers could exist.
- mcqa-f54736dd: options_required — The question requires options to define the specific clinical scenario where open reduction and fixation of a mandibular condyle fracture is indicated, as multiple clinical factors could justify this intervention.
- mcqa-f5cd69ed: missing_image — The question references a CECT image that is not provided, which is essential to determine the best management of the condition.
- mcqa-f87f2d68: ambiguous_stem — The stem does not provide sufficient information to determine the best management advice for a pregnant patient with juvenile myoclonic epilepsy on sodium-valproate. Multiple management strategies could be considered, such as switching medications or adjusting dosages, and the correct approach may depend on additional clinical details not provided in the stem.
- mcqa-f94eef30: options_required — The question asks for a drug that does not require dose adjustment in renal disease, which is a negative constraint. Without the options, multiple drugs could potentially fit this criterion, making it unscorable without the candidate list.
- mcqa-fe3802ce: options_required — The question asks for a drug used for the treatment of refractory histiocytosis, but without the options, multiple drugs could be considered valid. The options are needed to constrain the answer space.
- mcqa-ff070552: options_required — The question asks for the most appropriate management among several possible approaches, which requires the options to determine the specific management strategy being considered. Without the options, multiple management strategies could be considered appropriate.
- mcqa-0006af36: options_required — The question asks which treatment modality is least likely to result in cytogenetic response, which requires a comparison among multiple treatments. Without the options, the question cannot be fairly scored as multiple treatments could be considered.
- mcqa-002bd852: options_required — The question asks for a recommended agent for medical treatment of variceal bleed, but without the options, multiple agents could be considered valid. The options are needed to constrain the answer space.
- mcqa-00496aeb: options_required — The question asks which structure is not used in the treatment of epilepsy, which requires a list of options to determine the correct answer, as many structures could potentially not be used.
- mcqa-0066d710: options_required — The question asks which is not included in the treatment of a femoral artery aneurysm, which requires a candidate list to determine the correct answer, as multiple interventions or diagnostic tools could be considered unrelated to treatment without specific context.
- mcqa-007e6703: ambiguous_stem — Onabotulinum toxin A is used for multiple conditions including cervical dystonia, chronic migraine, blepharospasm, and strabismus. Without options, multiple answers are equally defensible.
- mcqa-00b388cf: ambiguous_stem — The investigation of choice for evaluating the inferior vena cava and renal vein for thrombus in renal cell carcinoma can vary based on clinical context and available technology. Both 'Coloured doppler' and 'CT scan' are commonly used, making the stem ambiguous without options.
- mcqa-00b83087: options_required — The question asks which laser is used for the treatment of myopia, but without the options, multiple types of lasers could be considered. The options are needed to constrain the answer space.
- mcqa-00baddb3: options_required — The question asks which antipsychotic isn't available as a depot preparation, which requires knowing the specific list of options to determine which one is not available in that form. Without the options, multiple antipsychotics could potentially fit the criteria.
- mcqa-010c32b2: options_required — The question asks which antihypertensive is NOT used in the management of Pregnancy Induced Hypertension in the first trimester. Without the options, multiple antihypertensives could be valid answers, as several are contraindicated or not preferred in pregnancy.
- mcqa-09ce3345: duplicate_eligibility_conflict — Conservatively excluded because a punctuation-normalized identical stem was judged ineligible. Archived judge eligibility is unchanged.
