# C4 A-MEM evolution experiment (Tier D)

Matched C3E0 (evolution disabled) and C4E1 (evolution enabled), 180 probes x 10
samples per arm. C4E1 replayed C3E0's exact ten-turn session transcript. Both
arms used three retrieved notes and the same model-visible content/context/tags
schema. Outcomes were judged with `gpt-4o-2024-08-06`.

With 2,000 paired probe-clustered bootstrap draws (seed 0; BCa 95%), evolution
reduced the primary harm rate from 19.20% to 17.44%: -1.76 percentage points
(BCa 95% CI -4.11 to +0.44). The primary interval includes zero. Refusal was
unchanged (19.44% vs 19.50%; +0.06 pp, -1.67 to +1.89), while derailment fell
from 8.00% to 6.67% (-1.33 pp, -2.89 to +0.11).

Both prespecified endpoint sensitivities favored evolution: strict coherence
floor, -2.17 pp (BCa -4.44 to -0.06), and the misalignment-or-derailment
composite, -2.72 pp (BCa -5.00 to -0.44). These sensitivity results exclude
zero, but the primary endpoint does not; the paper should describe the result
as a modest directional improvement rather than a definitive primary-endpoint
effect.

Mechanism checks passed. C3E0 had zero mutations. C4E1 changed 105 model-visible
contexts, tagged 128 notes, linked 106 notes, and had zero invalid links. All
3,600 raw rows pair exactly with their judged rows, and all retrievals contain
exactly three notes. Twenty exact prompt/context pairs are preserved in
`manual_audit_20.jsonl`.
