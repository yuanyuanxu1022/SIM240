#!/usr/bin/env bash
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
height_nm=${1:-}
direction=${2:-}
if [[ ! "$height_nm" =~ ^(25|50|75|100|125)$ ]] || [[ "$direction" != "P" && "$direction" != "T" ]]; then
  echo "usage: ./scripts/run_precheck.sh 25|50|75|100|125 P|T" >&2
  exit 2
fi

binary="$case_root/build/g3_ex240_h$height_nm"
if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary (build it first)" >&2
  exit 2
fi
run_id="precheck_h${height_nm}_${direction}_$(date +%Y%m%dT%H%M%S%z)"
output_dir="$case_root/results/$run_id"
mkdir -p "$output_dir"
{
  printf 'run_id=%s\n' "$run_id"
  printf 'formal_simulation=false\n'
  printf 'mode=zero_step_precheck\n'
  printf 'height_nm=%s\n' "$height_nm"
  printf 'direction=%s\n' "$direction"
  printf 'frozen_g2_source_sha256=%s\n' '4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002'
  sha256sum "$binary"
} > "$output_dir/run_manifest.txt"
"$binary" precheck "$direction" "$output_dir" > "$output_dir/run.log" 2>&1
code=$?
printf '%s\n' "$code" > "$output_dir/exit_code.txt"
printf 'run_id=%s precheck_exit=%s output_dir=%s\n' "$run_id" "$code" "$output_dir"
exit "$code"
