#!/usr/bin/env bash
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/g1_poiseuille_bouzidi_validation"
batch_id="g1_v2_$(date +%Y%m%dT%H%M%S%z)"
batch_dir="$case_root/results/$batch_id"
mkdir -p "$batch_dir"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/g1-v2-matplotlib"
mkdir -p "$MPLCONFIGDIR"

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

printf 'case_id,group,dx_nm,tau,acceleration_m_s2\n' > "$batch_dir/matrix_definition.csv"

run_case() {
  local case_id=$1
  local group=$2
  local dx_nm=$3
  local tau=$4
  local acceleration=$5
  local case_dir="$batch_dir/$case_id"
  local precheck_dir="$case_dir/precheck"
  local steady_dir="$case_dir/steady"
  mkdir -p "$precheck_dir" "$steady_dir"
  printf '%s,%s,%s,%s,%s\n' "$case_id" "$group" "$dx_nm" "$tau" "$acceleration" \
    >> "$batch_dir/matrix_definition.csv"

  for output_dir in "$precheck_dir" "$steady_dir"; do
    {
      printf 'case_id=%s\n' "$case_id"
      printf 'group=%s\n' "$group"
      printf 'dx_nm=%s\n' "$dx_nm"
      printf 'tau=%s\n' "$tau"
      printf 'acceleration_m_s2=%s\n' "$acceleration"
      printf 'binary=%s\n' "$binary"
      sha256sum "$binary"
    } > "$output_dir/run_manifest.txt"
  done

  "$binary" precheck "$precheck_dir" "$dx_nm" "$tau" "$acceleration" \
    > "$precheck_dir/run.log" 2>&1
  local precheck_code=$?
  printf '%s\n' "$precheck_code" > "$precheck_dir/exit_code.txt"
  if [[ $precheck_code -ne 0 ]]; then
    printf 'blocked_by_precheck=%s\n' "$precheck_code" > "$steady_dir/run.log"
    printf '%s\n' "$precheck_code" > "$steady_dir/exit_code.txt"
    return
  fi

  "$binary" steady "$steady_dir" "$dx_nm" "$tau" "$acceleration" \
    > "$steady_dir/run.log" 2>&1
  local steady_code=$?
  printf '%s\n' "$steady_code" > "$steady_dir/exit_code.txt"
}

# Force-linearity matrix. The a=1e5 point is intentionally repeated in the
# grid and tau groups so each requested Case has independent evidence.
run_case G1-a1 force 5 1.7 5e4
run_case G1-a2 force 5 1.7 1e5
run_case G1-a3 force 5 1.7 2e5

# Grid matrix: physical viscosity and tau stay fixed. dt is derived internally
# from tau = 0.5 + 3*nu*dt/dx^2, so only the dx=5 nm baseline has dt=1e-11 s.
run_case G1-dx10 grid 10 1.7 1e5
run_case G1-dx5 grid 5 1.7 1e5
run_case G1-dx2p5 grid 2.5 1.7 1e5

# Optional tau matrix at dx=5 nm.
run_case G1-tau0p8 tau 5 0.8 1e5
run_case G1-tau1p0 tau 5 1.0 1e5
run_case G1-tau1p7 tau 5 1.7 1e5

printf '%s\n' "$batch_dir" > "$case_root/latest_batch.txt"
python3 "$case_root/scripts/postprocess_g1_v2.py" "$batch_dir"
printf 'batch_dir=%s\n' "$batch_dir"
