#!/usr/bin/env bash
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
base_case=$(cd "$case_root/../G2_EX240_single_period_transport" && pwd)
base_source="$base_case/src/g2_ex240_single_period_transport.cpp"
protocol="$case_root/FORCE_LINEARITY_PROTOCOL.md"

batch_id="g2_force_linearity_$(date +%Y%m%dT%H%M%S%z)"
batch_dir="$case_root/results/$batch_id"
mkdir -p "$batch_dir/runs"
printf '%s\n' "$batch_dir" > "$case_root/latest_batch.txt"

run_one() {
  local acceleration=$1
  local force_tag=$2
  local direction=$3
  local binary=$4
  local case_id="G2-${direction}-a${force_tag}"
  local run_root="$batch_dir/runs/$case_id"
  local precheck_dir="$run_root/precheck"
  local steady_dir="$run_root/steady"

  if [[ -e "$run_root" ]]; then
    echo "refusing to overwrite $run_root" >&2
    return 2
  fi
  mkdir -p "$precheck_dir" "$steady_dir"

  for output_dir in "$precheck_dir" "$steady_dir"; do
    {
      printf 'case_id=%s\n' "$case_id"
      printf 'direction=%s\n' "$direction"
      printf 'dx_nm=2.5\n'
      printf 'tau=1.0\n'
      printf 'acceleration_m_s2=%s\n' "$acceleration"
      printf 'mesa_gap_nm=75\n'
      printf 'period_nm=240\n'
      printf 'groove_depth_nm=100\n'
      printf 'base_source=%s\n' "$base_source"
      printf 'protocol=%s\n' "$protocol"
      printf 'binary=%s\n' "$binary"
      sha256sum "$base_source" "$protocol" "$binary"
    } > "$output_dir/run_manifest.txt"
  done

  "$binary" precheck "$direction" "$precheck_dir" > "$precheck_dir/run.log" 2>&1
  local precheck_code=$?
  printf '%s\n' "$precheck_code" > "$precheck_dir/exit_code.txt"
  if [[ $precheck_code -ne 0 ]]; then
    printf 'blocked_by_precheck=%s\n' "$precheck_code" > "$steady_dir/run.log"
    printf '%s\n' "$precheck_code" > "$steady_dir/exit_code.txt"
    return "$precheck_code"
  fi

  "$binary" steady "$direction" "$steady_dir" > "$steady_dir/run.log" 2>&1
  local steady_code=$?
  printf '%s\n' "$steady_code" > "$steady_dir/exit_code.txt"
  echo "case=$case_id exit=$steady_code"
  return "$steady_code"
}

binary_5e4="$case_root/build/g2_ex240_a5e4"
binary_2e5="$case_root/build/g2_ex240_a2e5"
for binary in "$binary_5e4" "$binary_2e5"; do
  if [[ ! -x "$binary" ]]; then
    echo "missing executable: $binary" >&2
    exit 2
  fi
done

run_one 50000 5e4 P "$binary_5e4" || exit $?
run_one 50000 5e4 T "$binary_5e4" || exit $?
run_one 200000 2e5 P "$binary_2e5" || exit $?
run_one 200000 2e5 T "$binary_2e5" || exit $?

"$case_root/scripts/postprocess_force_linearity.py" "$batch_dir"
post_code=$?
printf '%s\n' "$post_code" > "$batch_dir/postprocess_exit_code.txt"
exit "$post_code"
