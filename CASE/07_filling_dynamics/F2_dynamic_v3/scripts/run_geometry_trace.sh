#!/usr/bin/env bash
set -euo pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
h0_nm=${1:-}
velocity=${2:-}
steps=${3:-}
if [[ ! "$h0_nm" =~ ^(50|75|125)$ ]] || [[ -z "$velocity" ]] || [[ ! "$steps" =~ ^[0-9]+$ ]]; then
  echo "usage: ./scripts/run_geometry_trace.sh 50|75|125 compressionVelocity_m_s steps" >&2
  exit 2
fi
binary="$case_root/build/f2_dynamic_v3"
[[ -x "$binary" ]] || { echo "missing $binary; run make -C src first" >&2; exit 2; }
run_id="geometry_trace_h${h0_nm}_$(date +%Y%m%dT%H%M%S%z)"
output_dir="$case_root/results/$run_id"
mkdir -p "$output_dir"
{
  printf 'run_id=%s\n' "$run_id"
  printf 'formal_simulation=false\nmode=geometry_trace\nheight_nm=%s\ncompression_velocity_m_s=%s\nsteps=%s\n' "$h0_nm" "$velocity" "$steps"
  sha256sum "$binary"
} > "$output_dir/run_manifest.txt"
set +e
"$binary" geometry_trace "$h0_nm" "$velocity" "$steps" "$output_dir" > "$output_dir/run.log" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$output_dir/exit_code.txt"
printf 'run_id=%s geometry_trace_exit=%s output_dir=%s\n' "$run_id" "$code" "$output_dir"
exit "$code"
