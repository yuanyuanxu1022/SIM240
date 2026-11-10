#!/usr/bin/env bash
# D2 误差地图矩阵：d x h x 方向 的全组合稳态算例
# 用法：./scripts/run_matrix.sh [--recheck-only]
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/d2_groove_error_map"
results_root="$case_root/results"
summary_csv="$results_root/summary.csv"

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  echo "build first: cd src && make" >&2
  exit 2
fi

# 主矩阵：d x h 全组合，dx = 5 nm（两个方向）
MAIN_COMBOS=(
  "5 50 25"
  "5 50 50"
  "5 50 100"
  "5 75 25"
  "5 75 50"
  "5 75 100"
  "5 125 25"
  "5 125 50"
  "5 125 100"
)
# 复核档：代表点 dx = 2.5 nm（冻结卡 §4.2 规则）
RECHECK_COMBOS=(
  "2.5 50 100"
  "2.5 125 25"
)

if [[ "${1:-}" == "--recheck-only" ]]; then
  COMBOS=("${RECHECK_COMBOS[@]}")
else
  COMBOS=("${MAIN_COMBOS[@]}")
  if [[ "${1:-}" == "--with-recheck" ]]; then
    COMBOS+=("${RECHECK_COMBOS[@]}")
  fi
fi

# summary 表头（文件不存在时才写）
if [[ ! -f "$summary_csv" ]]; then
  printf 'h_nm,d_nm,dx_nm,direction,exit_code,J_main_m2_s,Keff_m3,R_eff_Pa_s_per_m3,steps\n' > "$summary_csv"
fi

for combo in "${COMBOS[@]}"; do
  read -r dx_nm h_nm d_nm <<< "$combo"
  for direction in P T; do
    run_dir="$results_root/h${h_nm}_d${d_nm}_dx${dx_nm}_${direction}"
    if [[ -e "$run_dir/steady/exit_code.txt" ]]; then
      echo "skip existing: $run_dir"
      continue
    fi
    mkdir -p "$run_dir/precheck" "$run_dir/steady"
    for output_dir in "$run_dir/precheck" "$run_dir/steady"; do
      {
        printf 'case_id=%s\n' "D2-$direction-h${h_nm}-d${d_nm}-dx${dx_nm}"
        printf 'direction=%s\n' "$direction"
        printf 'dx_nm=%s\n' "$dx_nm"
        printf 'tau=1.0\n'
        printf 'acceleration_m_s2=1e5\n'
        printf 'mesa_gap_nm=%s\n' "$h_nm"
        printf 'groove_depth_nm=%s\n' "$d_nm"
        printf 'binary=%s\n' "$binary"
        sha256sum "$binary" | cut -d' ' -f1 | sed 's/^/binary_sha256=/'
      } > "$output_dir/run_manifest.txt"
    done

    "$binary" precheck "$direction" "$run_dir/precheck" "$dx_nm" "$h_nm" "$d_nm" \
      > "$run_dir/precheck/run.log" 2>&1
    precheck_code=$?
    printf '%s\n' "$precheck_code" > "$run_dir/precheck/exit_code.txt"
    if [[ $precheck_code -ne 0 ]]; then
      printf '%s\n' "$precheck_code" > "$run_dir/steady/exit_code.txt"
      printf '%s,%s,%s,%s,%s,0,0,0,0\n' \
        "$h_nm" "$d_nm" "$dx_nm" "$direction" "precheck_FAIL_$precheck_code" >> "$summary_csv"
      echo "case=$run_dir precheck_FAIL=$precheck_code"
      continue
    fi

    "$binary" steady "$direction" "$run_dir/steady" "$dx_nm" "$h_nm" "$d_nm" \
      > "$run_dir/steady/run.log" 2>&1
    steady_code=$?
    printf '%s\n' "$steady_code" > "$run_dir/steady/exit_code.txt"

    J_main=$(grep -m1 '^J_main_m2_s=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    Keff=$(grep -m1 '^Keff_m3=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    R_eff=$(grep -m1 '^R_eff_Pa_s_per_m3=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    steps=$(grep -m1 '^steps_completed=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$h_nm" "$d_nm" "$dx_nm" "$direction" "$steady_code" \
      "${J_main:-NA}" "${Keff:-NA}" "${R_eff:-NA}" "${steps:-NA}" >> "$summary_csv"
    echo "case=$run_dir steady_exit=$steady_code"
  done
done

echo "done. summary: $summary_csv"
