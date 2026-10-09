#!/usr/bin/env bash
set -u -o pipefail

v3_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
g1_root=$(cd "$v3_root/.." && pwd)
binary="${G1V3_BINARY:-$g1_root/build/g1_poiseuille_bouzidi_validation}"

print_matrix() {
  printf 'case_id,dx_nm,tau,acceleration_m_s2\n'
  printf 'G1V3-a1,2.5,1.7,5e4\n'
  printf 'G1V3-a2,2.5,1.7,1e5\n'
  printf 'G1V3-a3,2.5,1.7,2e5\n'
}

mode=${1:-run}
if [[ "$mode" == "--dry-run" ]]; then
  print_matrix
  exit 0
fi
if [[ "$mode" != "run" && "$mode" != "--precheck-only" ]]; then
  echo "usage: $0 [--dry-run|--precheck-only]" >&2
  exit 2
fi
if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

batch_id="g1_v3_$(date +%Y%m%dT%H%M%S%z)"
batch_dir="$v3_root/results/$batch_id"
mkdir -p "$batch_dir"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/g1-v3-matplotlib"
mkdir -p "$MPLCONFIGDIR"
print_matrix > "$batch_dir/matrix_definition.csv"

{
  printf 'protocol_id=G1_V3_FINEGRID_FORCE_CONFIRMATION\n'
  printf 'binary=%s\n' "$binary"
  sha256sum "$binary"
  sha256sum "$g1_root/src/g1_poiseuille_bouzidi_validation.cpp"
  sha256sum "$v3_root/G1_V3_PROTOCOL.md"
} > "$batch_dir/source_manifest.txt"

run_case() {
  local case_id=$1
  local acceleration=$2
  local case_dir="$batch_dir/$case_id"
  local precheck_dir="$case_dir/precheck"
  local steady_dir="$case_dir/steady"
  mkdir -p "$precheck_dir" "$steady_dir"

  for output_dir in "$precheck_dir" "$steady_dir"; do
    {
      printf 'protocol_id=G1_V3_FINEGRID_FORCE_CONFIRMATION\n'
      printf 'case_id=%s\n' "$case_id"
      printf 'dx_nm=2.5\n'
      printf 'tau=1.7\n'
      printf 'dt_s=2.5e-12\n'
      printf 'acceleration_m_s2=%s\n' "$acceleration"
      printf 'binary=%s\n' "$binary"
      sha256sum "$binary"
      sha256sum "$g1_root/src/g1_poiseuille_bouzidi_validation.cpp"
    } > "$output_dir/run_manifest.txt"
  done

  "$binary" precheck "$precheck_dir" 2.5 1.7 "$acceleration" \
    > "$precheck_dir/run.log" 2>&1
  local precheck_code=$?
  printf '%s\n' "$precheck_code" > "$precheck_dir/exit_code.txt"
  if [[ $precheck_code -ne 0 || "$mode" == "--precheck-only" ]]; then
    if [[ "$mode" == "--precheck-only" ]]; then
      return "$precheck_code"
    fi
    printf 'blocked_by_precheck=%s\n' "$precheck_code" > "$steady_dir/run.log"
    printf '%s\n' "$precheck_code" > "$steady_dir/exit_code.txt"
    return
  fi

  "$binary" steady "$steady_dir" 2.5 1.7 "$acceleration" \
    > "$steady_dir/run.log" 2>&1
  local steady_code=$?
  printf '%s\n' "$steady_code" > "$steady_dir/exit_code.txt"
}

precheck_failed=0
run_case G1V3-a1 5e4 || precheck_failed=1
run_case G1V3-a2 1e5 || precheck_failed=1
run_case G1V3-a3 2e5 || precheck_failed=1

printf '%s\n' "$batch_dir" > "$v3_root/latest_batch.txt"
printf 'batch_dir=%s\n' "$batch_dir"

if [[ "$mode" == "--precheck-only" ]]; then
  if [[ $precheck_failed -ne 0 ]]; then
    exit 3
  fi
  exit 0
fi

python3 "$v3_root/scripts/postprocess_g1_v3.py" "$batch_dir"
