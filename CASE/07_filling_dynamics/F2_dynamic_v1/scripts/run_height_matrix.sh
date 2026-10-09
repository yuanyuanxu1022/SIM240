#!/usr/bin/env bash
set -euo pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$case_root/results"
for h in 50 75 125; do
  binary="$case_root/build/f2_liquid_film_compression_dynamic"
  [[ -x "$binary" ]] || { echo "missing $binary; run build_height_matrix.sh first" >&2; exit 2; }
  for direction in P T; do
    run_id="f2_liquid_film_compression_h${h}_${direction}_$(date +%Y%m%dT%H%M%S%z)"
    output_dir="$case_root/results/$run_id"
    mkdir -p "$output_dir"
    {
      printf 'run_id=%s\n' "$run_id"
      printf 'formal_simulation=true\n'
      printf 'case=F1_single_phase_compression\nheight_nm=%s\ndirection=%s\n' "$h" "$direction"
      sha256sum "$binary"
    } > "$output_dir/run_manifest.txt"
    "$binary" steady "$h" "$direction" "$output_dir" > "$output_dir/run.log" 2>&1
    code=$?
    printf '%s\n' "$code" > "$output_dir/exit_code.txt"
    printf 'height=%s direction=%s exit_code=%s output=%s\n' "$h" "$direction" "$code" "$output_dir"
    [[ "$code" -eq 0 ]] || exit "$code"
  done
done
