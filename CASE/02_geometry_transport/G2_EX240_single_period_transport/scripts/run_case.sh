#!/usr/bin/env bash
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/g2_ex240_single_period_transport"
direction=${1:-}
batch_dir=${2:-}

if [[ "$direction" != "P" && "$direction" != "T" ]]; then
  echo "usage: ./scripts/run_case.sh P|T [BATCH_DIRECTORY]" >&2
  exit 2
fi
if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

if [[ -z "$batch_dir" ]]; then
  batch_id="g2_ex240_$(date +%Y%m%dT%H%M%S%z)"
  batch_dir="$case_root/results/$batch_id"
  mkdir -p "$batch_dir"
  printf '%s\n' "$batch_dir" > "$case_root/latest_batch.txt"
else
  mkdir -p "$batch_dir"
fi

case_id="G2-$direction"
case_dir="$batch_dir/$case_id"
precheck_dir="$case_dir/precheck"
steady_dir="$case_dir/steady"
if [[ -e "$case_dir" ]]; then
  echo "refusing to overwrite existing case: $case_dir" >&2
  exit 2
fi
mkdir -p "$precheck_dir" "$steady_dir"

for output_dir in "$precheck_dir" "$steady_dir"; do
  {
    printf 'case_id=%s\n' "$case_id"
    printf 'direction=%s\n' "$direction"
    printf 'dx_nm=2.5\n'
    printf 'tau=1.0\n'
    printf 'acceleration_m_s2=1e5\n'
    printf 'mesa_gap_nm=75\n'
    printf 'groove_depth_nm=100\n'
    printf 'binary=%s\n' "$binary"
    sha256sum "$binary"
  } > "$output_dir/run_manifest.txt"
done

"$binary" precheck "$direction" "$precheck_dir" > "$precheck_dir/run.log" 2>&1
precheck_code=$?
printf '%s\n' "$precheck_code" > "$precheck_dir/exit_code.txt"
if [[ $precheck_code -ne 0 ]]; then
  printf 'blocked_by_precheck=%s\n' "$precheck_code" > "$steady_dir/run.log"
  printf '%s\n' "$precheck_code" > "$steady_dir/exit_code.txt"
  echo "case=$case_id precheck_FAIL=$precheck_code batch_dir=$batch_dir"
  exit "$precheck_code"
fi

"$binary" steady "$direction" "$steady_dir" > "$steady_dir/run.log" 2>&1
steady_code=$?
printf '%s\n' "$steady_code" > "$steady_dir/exit_code.txt"
echo "case=$case_id steady_exit=$steady_code batch_dir=$batch_dir"
exit "$steady_code"

