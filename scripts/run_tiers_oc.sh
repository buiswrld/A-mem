#!/usr/bin/env bash
# C5_noturns (re-run) + Tier C + Tier O, back to back, same protocol as tier D:
# n=10, k=3, n-turns=10 (0 for the C5 variant), seed 0, batch 5, bf16. Only the
# probe set changes, so Recovery on O and C stays comparable with Recovery on D.
#
# NOTHING MAY JUDGE WHILE THIS RUNS. schema.py stamps git_sha per row from
# `git diff --quiet HEAD`, and judging rewrites tracked .judged.jsonl files --
# so a concurrent judge pass dirties the tree and every row generated after it
# is stamped `-dirty`. That is not hypothetical: it cost the first C5_noturns
# run 1,555 of its 1,800 rows (archived under results/archive-dirty-sha/).
# Judging is therefore deferred until after the last generation here.
#
# Tier C runs before Tier O because it is 24 probes against 180 -- a mistake in
# the new probe sets surfaces in ten minutes instead of six hours.
set -uo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO"
set -a; . ./.env; set +a
export PYTHONPATH="$REPO:$REPO/submodules/Amem"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

PY=${PY:-$REPO/.venv/bin/python}
[ -x "$PY" ] || PY=python
# logs land beside the repo, not in a pod-specific scratch dir
LOGS=${LOGS:-runlogs}
STATUS=${STATUS:-runlogs/run_status.txt}
mkdir -p "$LOGS"

BASE=unsloth/Qwen2.5-14B-Instruct
ADAPTER=ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice
N=10; K=3; TURNS=10; SEED=0; BATCH=5

step () {
  local label=$1 log=$2; shift 2
  echo "[$(date -Is)] START $label" | tee -a "$STATUS"
  "$@" > "$LOGS/$log" 2>&1
  local rc=$?
  echo "[$(date -Is)] END   $label rc=$rc" | tee -a "$STATUS"
}

# refuse to start on a dirty tree -- the whole point of this ordering
if ! git diff --quiet HEAD; then
  echo "TREE DIRTY -- every row would be stamped -dirty. Commit first." | tee -a "$STATUS"
  exit 1
fi

run_tier () {
  local probes=$1 tag=$2
  step "${tag}_C1C2" "${tag}_c1c2.log" \
    "$PY" -m harness.run_condition --conditions C1 C2 --probes "$probes" \
    --n $N --k $K --seed $SEED --batch-size $BATCH --base $BASE --adapter $ADAPTER
  step "${tag}_C6" "${tag}_c6.log" \
    "$PY" -m harness.generate --condition C6 --probes "$probes" \
    --n $N --seed $SEED --batch-size $BATCH --base $BASE
  for cond in C3 C5 C4; do
    local extra=(--reset-store)
    [ "$cond" = "C4" ] && extra=()      # C4's store is in-memory
    step "${tag}_${cond}" "${tag}_$(echo $cond | tr 'A-Z' 'a-z').log" \
      "$PY" -m harness.run_session --condition $cond --probes "$probes" \
      --n $N --k $K --n-turns $TURNS --seed $SEED --batch-size $BATCH \
      --base $BASE --adapter $ADAPTER "${extra[@]}"
  done
}

run_tier trigger_nonclinical_24 tierC
# orsc_hard_180 retired 2026-08-14 -- 36.7% of its rewrites kept their seed's
# harmful intent and raters agreed on which at kappa 0.395, which on a tier where
# refusal IS the error inverts those items. See prereg_tierO.md section 8 D1.
run_tier medmcqa_actionable_180 tierO

echo "[$(date -Is)] TIERS O+C ATTEMPTED" | tee -a "$STATUS"
