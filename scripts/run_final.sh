#!/usr/bin/env bash
# HISTORICAL DRIVER: the experiment closed on 2026-08-16. This records the
# exact final rental workflow; it is not an active project task. A replication
# must use a new protocol/output namespace and must not touch frozen results.
# The last GPU rental. Three jobs, nothing else.
#
#   1. C4 on tier C with a PERSISTED store   240 rows   ~35 min
#   2. tier C --n-turns 0 for C3 and C5      480 rows   ~30 min
#   3. tier O, all six conditions         10,800 rows   ~6 h
#
# Use this, NOT scripts/run_tiers_oc.sh. That script still starts with
# `run_tier trigger_nonclinical_24 tierC`, and tier C is already generated and
# judged -- so every one of its six steps hits an existing output file. Nothing
# is overwritten (all three entry points guard), but run_condition loads the 14B
# *before* it checks, so you pay a full model load per skipped step for nothing.
# That is what "trying to re-run all the other conditions" looked like.
#
# Ordered cheapest-first: a card that dies after job 1 still leaves the paper
# better off, and jobs 1 and 2 are the ones that unblock claims currently
# impossible to make. Job 3 is long but low-surprise.
#
# NOTHING MAY JUDGE WHILE THIS RUNS. schema.py stamps git_sha per row from
# `git diff --quiet HEAD`, and judging rewrites tracked .judged.jsonl files, so
# a concurrent judge pass dirties the tree and every row after it is stamped
# `-dirty`. That cost 1,555 rows once (results/archive-dirty-sha/).
set -uo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO"
set -a; . ./.env; set +a
export PYTHONPATH="$REPO:$REPO/submodules/Amem"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=8          # lesson 1: without this, CPU embedding is ~400x slower
export MKL_NUM_THREADS=8

PY=${PY:-$REPO/.venv/bin/python}
[ -x "$PY" ] || PY=python
LOGS=${LOGS:-runlogs}
STATUS=${STATUS:-runlogs/run_status.txt}
mkdir -p "$LOGS"

BASE=unsloth/Qwen2.5-14B-Instruct
ADAPTER=ModelOrganismsForEM/Qwen2.5-14B-Instruct_bad-medical-advice
N=10; K=3; TURNS=10; SEED=0; BATCH=5

TIER_C=trigger_nonclinical_24
TIER_O=medmcqa_actionable_180

step () {
  local label=$1 log=$2; shift 2
  echo "[$(date -Is)] START $label" | tee -a "$STATUS"
  "$@" > "$LOGS/$log" 2>&1
  local rc=$?
  echo "[$(date -Is)] END   $label rc=$rc" | tee -a "$STATUS"
  [ $rc -ne 0 ] && echo "    !! $label failed -- see $LOGS/$log" | tee -a "$STATUS"
  return 0
}

# Refuse to start on a dirty tree. Every row would be stamped -dirty.
if ! git diff --quiet HEAD; then
  echo "TREE DIRTY -- every row would be stamped -dirty. Commit first." | tee -a "$STATUS"
  exit 1
fi

# --- job 1: C4 with a persisted store -------------------------------------
# --persist-store puts `persist_store: true` into the config, so this gets its
# own config_hash and lands beside the original C4 run rather than colliding
# with it. Budget ~17 of the ~35 min for the ~308 gpt-4o-mini controller calls
# that load 144 notes + 10 session turns before a single row generates.
step "c4_persist" "c4_persist.log" \
  "$PY" -m harness.run_session --condition C4 --probes "$TIER_C" \
  --n $N --k $K --n-turns $TURNS --seed $SEED --batch-size $BATCH \
  --persist-store --base $BASE --adapter $ADAPTER

# --- job 2: tier C --n-turns 0 for C3 and C5 -------------------------------
# The matched pair tier D already has and tier C does not. Removes the session
# turns that currently occupy 29.2% of C3's and 52.8% of C5's retrieval slots.
for cond in C3 C5; do
  step "tierC_noturns_${cond}" "tierc_noturns_$(echo $cond | tr 'A-Z' 'a-z').log" \
    "$PY" -m harness.run_session --condition $cond --probes "$TIER_C" \
    --n $N --k $K --n-turns 0 --seed $SEED --batch-size $BATCH \
    --reset-store --base $BASE --adapter $ADAPTER
done

# --- job 3: tier O, all six ------------------------------------------------
step "tierO_C1C2" "tiero_c1c2.log" \
  "$PY" -m harness.run_condition --conditions C1 C2 --probes "$TIER_O" \
  --n $N --k $K --seed $SEED --batch-size $BATCH --base $BASE --adapter $ADAPTER
step "tierO_C6" "tiero_c6.log" \
  "$PY" -m harness.generate --condition C6 --probes "$TIER_O" \
  --n $N --seed $SEED --batch-size $BATCH --base $BASE
for cond in C3 C5 C4; do
  extra=(--reset-store)
  [ "$cond" = "C4" ] && extra=()      # C4's store is in-memory unless persisted
  step "tierO_${cond}" "tiero_$(echo $cond | tr 'A-Z' 'a-z').log" \
    "$PY" -m harness.run_session --condition $cond --probes "$TIER_O" \
    --n $N --k $K --n-turns $TURNS --seed $SEED --batch-size $BATCH \
    --base $BASE --adapter $ADAPTER "${extra[@]}"
done

echo "[$(date -Is)] FINAL RUN ATTEMPTED" | tee -a "$STATUS"
echo
echo "Historical run complete. In the frozen repository, verify final artifacts with:"
echo "  uv run python scripts/freeze_results.py"
echo "  uv run python -m scripts.final_analysis"
