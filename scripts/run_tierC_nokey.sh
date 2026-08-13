#!/usr/bin/env bash
# Tier C on the RTX 6000 Ada pod, 2026-08-13.
# Replicates run_tier() from scripts/run_tiers_oc.sh EXACTLY (same protocol as
# tier D: n=10 k=3 n-turns=10 seed=0 batch=5 bf16, no --load-4bit), but:
#   * only tier C, so we can measure rows/s before committing to tier O;
#   * C4 is OMITTED -- its A-MEM controller needs OPENAI_API_KEY (llm_backend
#     .api_key() SystemExits without one) and this pod has no .env.
# Deliberately NOT a patch to the tracked script: editing a tracked file would
# dirty the tree and stamp every generated row `-dirty` (schema.py:51).
set -uo pipefail

REPO=/workspace/A-mem
cd "$REPO"

export HF_HOME=/root/hf-cache
export PYTHONPATH="$REPO:$REPO/submodules/Amem"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=8          # lesson 1 in RESUME.md: ~400x on note embedding
export MKL_NUM_THREADS=8

PY=/root/venv-amem/bin/python
LOGS=runlogs
STATUS=runlogs/run_status.txt
mkdir -p "$LOGS"

BASE=unsloth/Qwen2.5-14B-Instruct
ADAPTER=ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice
N=10; K=3; TURNS=10; SEED=0; BATCH=5
PROBES=trigger_nonclinical_24

step () {
  local label=$1 log=$2; shift 2
  echo "[$(date -Is)] START $label" | tee -a "$STATUS"
  "$@" > "$LOGS/$log" 2>&1
  local rc=$?
  echo "[$(date -Is)] END   $label rc=$rc" | tee -a "$STATUS"
}

# Same guard as the real driver.
if ! git diff --quiet HEAD; then
  echo "TREE DIRTY -- every row would be stamped -dirty. Commit first." | tee -a "$STATUS"
  exit 1
fi
echo "[$(date -Is)] tier C start, sha=$(git rev-parse --short HEAD)" | tee -a "$STATUS"

step "tierC_C1C2" "tierC_c1c2.log" \
  "$PY" -m harness.run_condition --conditions C1 C2 --probes "$PROBES" \
  --n $N --k $K --seed $SEED --batch-size $BATCH --base $BASE --adapter $ADAPTER

step "tierC_C6" "tierC_c6.log" \
  "$PY" -m harness.generate --condition C6 --probes "$PROBES" \
  --n $N --seed $SEED --batch-size $BATCH --base $BASE

for cond in C3 C5; do
  step "tierC_${cond}" "tierC_$(echo $cond | tr 'A-Z' 'a-z').log" \
    "$PY" -m harness.run_session --condition $cond --probes "$PROBES" \
    --n $N --k $K --n-turns $TURNS --seed $SEED --batch-size $BATCH \
    --base $BASE --adapter $ADAPTER --reset-store
done

echo "[$(date -Is)] TIER C ATTEMPTED (C4 skipped: needs OPENAI_API_KEY)" | tee -a "$STATUS"
