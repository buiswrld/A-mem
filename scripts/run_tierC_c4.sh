#!/usr/bin/env bash
# HISTORICAL DRIVER: completed and superseded before the 2026-08-16 freeze.
# Tier C, condition C4 only. Same protocol as the other five (n=10 k=3
# n-turns=10 seed=0 batch=5 bf16). NO --reset-store: C4's A-MEM store is
# in-memory and dies with the process, so build-then-probe must stay in one run.
set -uo pipefail
REPO=/workspace/A-mem
cd "$REPO"
set -a; . ./.env; set +a          # OPENAI_API_KEY for the A-MEM controller
export HF_HOME=/root/hf-cache
export PYTHONPATH="$REPO:$REPO/submodules/Amem"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
PY=/root/venv-amem/bin/python
STATUS=runlogs/run_status.txt
mkdir -p runlogs
if ! git diff --quiet HEAD; then
  echo "TREE DIRTY -- rows would stamp -dirty. Abort." | tee -a "$STATUS"; exit 1
fi
echo "[$(date -Is)] START tierC_C4 sha=$(git rev-parse --short HEAD)" | tee -a "$STATUS"
"$PY" -m harness.run_session --condition C4 --probes trigger_nonclinical_24 \
  --n 10 --k 3 --n-turns 10 --seed 0 --batch-size 5 \
  --base unsloth/Qwen2.5-14B-Instruct \
  --adapter ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice \
  > runlogs/tierC_c4.log 2>&1
echo "[$(date -Is)] END   tierC_C4 rc=$?" | tee -a "$STATUS"
