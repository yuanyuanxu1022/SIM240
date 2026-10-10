#!/usr/bin/env bash
# G4 MPI scaling validation (PERIOD_CONVERGENCE_PROTOCOL.md section 7).
#
# Object: Nx=2, a=1e5, direction P.  Configs:
#   serial-1rank (reference) + mpi at 1 / 4 / 8 / 16 ranks.
# Each config: full precheck + full steady.
# Frozen criteria (checked at the end):
#   1. every config: 10 frozen gates pass, candidate_links == 260352
#   2. |J(mpi,nrank) - J(serial,1)| / J(serial,1) <= 1e-10
#   3. mass_error trajectory pointwise diff <= 1e-12 (vs serial reference)
# Launch inside tmux (long computation, Allrun discipline).
set -euo pipefail

CASE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BUILD="$CASE_ROOT/build"
BATCH_ID="g4_scaling_nx2_$(date +%Y%m%dT%H%M%S%z)"
BATCH="$CASE_ROOT/results/$BATCH_ID"
mkdir -p "$BATCH"
GIT_COMMIT=$(git -C "$CASE_ROOT" rev-parse HEAD)
{
  echo "batch_id=$BATCH_ID"
  echo "object=nx2 a1e5 P"
  echo "protocol_sha256=$(sha256sum "$CASE_ROOT/PERIOD_CONVERGENCE_PROTOCOL.md" | cut -d' ' -f1)"
  echo "repository_commit=$GIT_COMMIT"
  echo "criteria: gates all pass; |dJ|/J <= 1e-10 vs serial; mass trajectory diff <= 1e-12"
} > "$BATCH/SOURCE_MANIFEST.md"

run_one() {  # $1=label  $2=binary  $3=ranks  $4=envranks
  local label=$1 bin=$2 ranks=$3 envranks=$4
  local run_dir="$BATCH/$label"
  mkdir -p "$run_dir/precheck" "$run_dir/steady"
  for phase in precheck steady; do
    {
      echo "run_id=g4_scaling_${BATCH_ID}_${label}_${phase}"
      echo "batch_id=$BATCH_ID"
      echo "case=G4-scaling-nx2-P"
      echo "direction=P"
      echo "acceleration_m_s2=1.0e5"
      echo "nx_periods=2"
      echo "ranks=$ranks"
      echo "mode=$([[ $bin == *serial* ]] && echo serial || echo mpi)"
      echo "frozen_g2_source_sha256=4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002"
      echo "generated_source_sha256=$(sha256sum "$BUILD/generated/g4_nx2_$([[ $bin == *serial* ]] && echo serial || echo mpi).cpp" | cut -d' ' -f1)"
      echo "binary_sha256=$(sha256sum "$bin" | cut -d' ' -f1)"
      echo "repository_commit=$GIT_COMMIT"
    } > "$run_dir/$phase/run_manifest.txt"
    echo "[$label/$phase] launching (ranks=$ranks)"
    set +e
    ( cd "$run_dir/$phase" && mpirun -np "$ranks" -x G4_EXPECTED_RANKS="$envranks" \
        "$bin" "$phase" P "$run_dir/$phase" > run.log 2>&1 )
    local code=$?
    set -e
    echo "$code" > "$run_dir/$phase/exit_code.txt"
    if [[ $code -ne 0 ]]; then
      echo "FAIL: $label $phase exit $code" >&2
      return 1
    fi
  done
  echo "[$label] done"
}

echo "== scaling batch: $BATCH_ID =="
run_one "serial_1rank" "$BUILD/g4_nx2_serial_a1e5" 1 1
run_one "mpi_1rank"    "$BUILD/g4_nx2_mpi_a1e5"    1 1
run_one "mpi_4rank"    "$BUILD/g4_nx2_mpi_a1e5"    4 4
run_one "mpi_8rank"    "$BUILD/g4_nx2_mpi_a1e5"    8 8
run_one "mpi_16rank"   "$BUILD/g4_nx2_mpi_a1e5"    16 16

python3 "$CASE_ROOT/scripts/check_scaling.py" "$BATCH"
echo "scaling batch complete: $BATCH_ID"
