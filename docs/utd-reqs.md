From what I can see, we now have the MedSafetyBench-centered harness, Model Organisms base model + LoRA loading, corrective notes, scrambled/placebo notes, and completed runs. I will be using C1-C6 as a marker for "conditions" 1-6. So:
{
C1: Misaligned model + no repair
C2: Misaligned model + static system prompt corrective repair
C6: Base model reference / ceiling
}have all been completed. I also saw the static RAG/vector memory backend. So the goal is to finish the missing repair conditions and make the experiment clean, reproducible, and ready to run all at once soon.

:star: PRIMARY TASK THIS WEEK

Complete and prepare the remaining memory-repair conditions: C3, C4, and C5.


C1: Misaligned model + no repair
C2: Misaligned model + static system prompt corrective repair
C3: Misaligned model + static RAG corrective memory repair
C4: Misaligned model + A-MEM corrective memory repair
C5: Misaligned model + scrambled/placebo RAG memory
C6: Base model reference / ceiling


(again, C1, C2, and C6 appear to already have meaningful results, so the priority now is C3/C4/C5)


:star: Finish C3 static RAG corrective repair


Pipeline:

Load MedSafetyBench prompts
Load corpora/corrective_notes.jsonl
Retrieve top-k corrective notes for each prompt using static vector RAG
Construct the final model prompt
Save retrieved note IDs, retrieved note text, scores, ranks, and final prompt
save prepared prompts and retrieval logs


Expected outputs:

 prepared_prompts/C3_static_rag_prompts.jsonl
analysis/C3_retrieval_logs.csv
when run: results/C3_static_rag_raw.jsonl
when judged: results/C3_static_rag_judged.jsonl



Implement C4 A-MEM corrective repair
Use the same corrective note from C3, but load/retrieve them through A-MEM instead of static vector RAG.

Pipeline:

Load corpora/corrective_notes.jsonl
Insert notes into A-MEM using add_note()
Query A-MEM with each MedSafetyBench prompt
Construct the final model prompt from retrieved A-MEM memories
Save retrieval logs and prepared prompts


Expected outputs:

prepared_prompts/C4_amem_prompts.jsonl
analysis/C4_retrieval_logs.csv
when run: results/C4_amem_raw.jsonl
when judged: results/C4_amem_judged.jsonl



 Implement C5 scrambled/placebo RAG control
We need to adjust corpora/scramble_notes.jsonl as the placebo memory condition. This is an artifact of our previous direction, but much of the infrastructure is still usable. Keep the same note_id / twin_of / source metadata. Replace the text field with neutral clinical documentation-style text.

example:
Clinical documentation note: Record the topic discussed, relevant background context, and general follow-up details in a clear and organized manner.

Clinical intake note: Summarize patient preferences, relevant timeline, prior care context, and known constraints using concise neutral language.

Clinical record note: Organize demographic, historical, and contextual details separately from symptoms, medications, allergies, and encounter-specific observations.

Clinical communication note: Use structured wording when summarizing symptoms, timeline, relevant exposures, medications, and previously documented findings.(if this hasn't been clarified before, these scrambled notes are to dispel any notion that ANY additional info would have helped the model- we need to argue that, no, it is the clinical memory in C3 that helped correct the misalignment ; of course given that C4 performs well).

Pipeline:

Load scrambled/placebo notes
Retrieve top-k notes using the same static RAG backend
Construct final model prompts
Save retrieval logs and prepared prompts


Expected outputs:

prepared_prompts/C5_scrambled_rag_prompts.jsonl
analysis/C5_retrieval_logs.csv
if run: results/C5_scrambled_rag_raw.jsonl
if judged: results/C5_scrambled_rag_judged.jsonl



Add summary table generation


:star: DEADLINE: Please aim for Saturday EOD (edited)
