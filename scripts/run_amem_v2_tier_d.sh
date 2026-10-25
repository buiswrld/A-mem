#!/usr/bin/env bash
set -euo pipefail

# Corrected, matched A-MEM follow-up. Run from the repository root on one
# >=40 GB GPU. C3E0 writes the shared self-authored session transcript; C4E1
# replays it exactly. Historical publication outputs are never touched.

PY="${PY:-.venv/bin/python}"
OUT="${OUT:-results/followup_amem_v2/tier_d}"
TRANSCRIPT="${TRANSCRIPT:-results/followup_amem_v2/session_seed0.json}"
BASE="unsloth/Qwen2.5-14B-Instruct"
ADAPTER="ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice"

mkdir -p "$OUT"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"

"$PY" -m harness.run_session \
  --condition C3E0 --probes msb_test_180 --n 10 --k 3 --n-turns 10 --seed 0 \
  --base "$BASE" --adapter "$ADAPTER" --batch-size 8 \
  --persist-store --out-dir "$OUT" \
  --write-session-transcript "$TRANSCRIPT"

"$PY" -m harness.run_session \
  --condition C4E1 --probes msb_test_180 --n 10 --k 3 --n-turns 10 --seed 0 \
  --base "$BASE" --adapter "$ADAPTER" --batch-size 8 \
  --persist-store --out-dir "$OUT" \
  --read-session-transcript "$TRANSCRIPT"

printf '%s\n' "Generation complete. Judge the two JSONL files in $OUT separately."
