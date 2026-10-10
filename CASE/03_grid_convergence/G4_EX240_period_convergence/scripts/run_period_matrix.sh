#!/usr/bin/env bash
# G4 period-sweep matrix runner — ONE level per invocation (never auto-advances).
#
#   ./scripts/run_period_matrix.sh --level 1|2|4|8
#
# Level 1: precheck-only freeze (steady evidence reused per REUSE_AUDIT.md).
# Levels 2/4/8: 6 prechecks (2 directions x 3 forces) first; only if ALL pass,
# the 6 steady runs start (mpirun, ranks per PERIOD_CONVERGENCE_PROTOCOL.md).
# Long runs must be started by the user inside tmux (Allrun discipline).
set -euo pipefail

CASE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BUILD_DIR="$CASE_ROOT/build"
RESULTS_DIR="$CASE_ROOT/results"
SCRIPTS="$CASE_ROOT/scripts"
LEVEL=${LEVEL:-}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --level) LEVEL="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [[ ! "$LEVEL" =~ ^(1|2|4|8)$ ]]; then
  echo "usage: $0 --level 1|2|4|8" >&2
  exit 2
fi

declare -A RANKS=([2]=8 [4]=16 [8]=16)
TAGS=(a5e4 a1e5 a2e5)
DIRECTIONS=(P T)

echo "== G4 preflight (static) =="
python3 "$SCRIPTS/preflight_period.py" --level "$LEVEL" \
  --report "$CASE_ROOT/preflight_nx${LEVEL}.md"

BATCH_ID="g4_period_nx${LEVEL}_$(date +%Y%m%dT%H%M%S%z)"
BATCH_DIR="$RESULTS_DIR/$BATCH_ID"
if [[ -e "$BATCH_DIR" ]]; then
  echo "refusing to overwrite existing batch: $BATCH_DIR" >&2
  exit 2
fi
mkdir -p "$BATCH_DIR/runs"
echo "$BATCH_ID" > "$RESULTS_DIR/latest_batch.txt"

PROTOCOL_SHA=$(sha256sum "$CASE_ROOT/PERIOD_CONVERGENCE_PROTOCOL.md" | cut -d' ' -f1)
GENERATOR_SHA=$(sha256sum "$SCRIPTS/generate_period_source.py" | cut -d' ' -f1)
GIT_COMMIT=$(git -C "$CASE_ROOT" rev-parse HEAD)
GIT_STATUS=$(git -C "$CASE_ROOT" status --short | head -20)

{
  echo "batch_id=$BATCH_ID"
  echo "level=Nx=$LEVEL"
  echo "protocol_sha256=$PROTOCOL_SHA"
  echo "generator_sha256=$GENERATOR_SHA"
  echo "repository_commit=$GIT_COMMIT"
  echo "ranks=${RANKS[$LEVEL]:-1}"
  echo "mode=mpi"
  echo "git_status:"
  echo "$GIT_STATUS"
} > "$BATCH_DIR/SOURCE_MANIFEST.md"

write_manifest() {
  local nx=$1 dir=$2 tag=$3 run_dir=$4
  local bin_name="g4_nx${nx}_mpi_${tag}"
  local src_name="g4_nx${nx}_mpi.cpp"
  local accel="1.0e5"
  [[ "$tag" == "a5e4" ]] && accel="5.0e4"
  [[ "$tag" == "a2e5" ]] && accel="2.0e5"
  {
    echo "run_id=g4_period_${BATCH_ID}_${dir}_${tag}"
    echo "batch_id=$BATCH_ID"
    echo "case=G4-nx${nx}-${dir}"
    echo "direction=$dir"
    echo "acceleration_m_s2=$accel"
    echo "nx_periods=$nx"
    echo "ranks=${RANKS[$LEVEL]:-1}"
    echo "mode=mpi"
    echo "frozen_g2_source_sha256=4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002"
    echo "generated_source_sha256=$(sha256sum "$BUILD_DIR/generated/$src_name" | cut -d' ' -f1)"
    echo "binary_sha256=$(sha256sum "$BUILD_DIR/$bin_name" | cut -d' ' -f1)"
    echo "protocol_sha256=$PROTOCOL_SHA"
    echo "repository_commit=$GIT_COMMIT"
  } > "$run_dir/run_manifest.txt"
}

run_precheck() {
  local nx=$1 dir=$2 tag=$3
  local bin="$BUILD_DIR/g4_nx${nx}_mpi_${tag}"
  local pre_dir="$BATCH_DIR/runs/nx${nx}_${dir}_${tag}/precheck"
  mkdir -p "$pre_dir"
  write_manifest "$nx" "$dir" "$tag" "$pre_dir"
  set +e
  ( cd "$pre_dir" && mpirun -np "${RANKS[$LEVEL]:-1}" \
      -x G4_EXPECTED_RANKS="${RANKS[$LEVEL]:-1}" \
      "$bin" precheck "$dir" "$pre_dir" > run.log 2>&1 )
  local code=$?
  echo "$code" > "$pre_dir/exit_code.txt"
  set -e
  if [[ $code -ne 0 ]]; then
    echo "PRECHECK FAIL: nx${nx}_${dir}_${tag} (exit $code)"
    return 1
  fi
  echo "precheck OK: nx${nx}_${dir}_${tag}"
}

echo "== precheck matrix (${#TAGS[@]} forces x ${#DIRECTIONS[@]} directions) =="
for tag in "${TAGS[@]}"; do
  for dir in "${DIRECTIONS[@]}"; do
    run_precheck "$LEVEL" "$dir" "$tag"
  done
done
echo "PRECHECK_MATRIX=PASS" > "$BATCH_DIR/batch_status.txt"

if [[ "$LEVEL" -eq 1 ]]; then
  echo "LEVEL1_PRECHEX_FROZEN=true" >> "$BATCH_DIR/batch_status.txt"
  echo "level 1 frozen: precheck-only, steady evidence reused per REUSE_AUDIT.md"
  exit 0
fi

echo "== steady matrix (6 points, ranks=${RANKS[$LEVEL]}) =="
PIDS=()
for tag in "${TAGS[@]}"; do
  for dir in "${DIRECTIONS[@]}"; do
    local_run="$BATCH_DIR/runs/nx${LEVEL}_${dir}_${tag}/steady"
    mkdir -p "$local_run"
    write_manifest "$LEVEL" "$dir" "$tag" "$local_run"
    (
      cd "$local_run"
      mpirun -np "${RANKS[$LEVEL]}" -x G4_EXPECTED_RANKS="${RANKS[$LEVEL]}" \
        "$BUILD_DIR/g4_nx${LEVEL}_mpi_${tag}" steady "$dir" "$local_run" \
        > run.log 2>&1
      echo $? > exit_code.txt
    ) &
    PIDS+=($!)
  done
done
wait

echo "== postprocess =="
python3 "$SCRIPTS/postprocess_period.py" "$BATCH_DIR"
echo "== batch complete: $BATCH_ID =="
echo "review checklist:"
echo "  1. every run: exit_code.txt == 0, result.txt PASS=true, 10 frozen gates"
echo "  2. level linearity: R2 >= 0.9999, K span <= 1% per direction"
echo "  3. T-direction mass trajectory trend audit (peak / tail / drift)"
echo "  4. E ratio table (a=1e5) — next level starts ONLY after human review"
echo "next command (after review): ./scripts/run_period_matrix.sh --level $((LEVEL * 2))"
