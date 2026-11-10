#!/usr/bin/env bash
# D2 斜槽（旋转角）张量性检验批次
# 用法：./scripts/run_oblique.sh
# 角度定义：θ = 驱动力方向与沟槽方向（Y）的夹角；0°=沿槽(P)，90°=跨槽(T)。
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/d2_groove_error_map"
results_root="$case_root/results"
summary_csv="$results_root/oblique_summary.csv"

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

# 角度 × 代表几何（dx=5 nm）。代表几何取 h75/d100（基准）与 h50/d100。
COMBOS=(
  "30 5 75 100"
  "45 5 75 100"
  "60 5 75 100"
  "30 5 50 100"
  "45 5 50 100"
  "60 5 50 100"
)

if [[ ! -f "$summary_csv" ]]; then
  printf 'angle_deg,h_nm,d_nm,dx_nm,exit_code,J_main_m2_s,Jx_m2_s,Jy_m2_s,K_along_drive_m3\n' > "$summary_csv"
fi

for combo in "${COMBOS[@]}"; do
  read -r angle dx_nm h_nm d_nm <<< "$combo"
  run_dir="$results_root/a${angle}_h${h_nm}_d${d_nm}_dx${dx_nm}"
  if [[ -e "$run_dir/steady/exit_code.txt" ]]; then
    echo "skip existing: $run_dir"
    continue
  fi
  mkdir -p "$run_dir/precheck" "$run_dir/steady"
  for output_dir in "$run_dir/precheck" "$run_dir/steady"; do
    {
      printf 'case_id=%s\n' "D2-A${angle}-h${h_nm}-d${d_nm}-dx${dx_nm}"
      printf 'angle_deg=%s\n' "$angle"
      printf 'dx_nm=%s\n' "$dx_nm"
      printf 'tau=1.0\n'
      printf 'acceleration_m_s2=1e5\n'
      printf 'mesa_gap_nm=%s\n' "$h_nm"
      printf 'groove_depth_nm=%s\n' "$d_nm"
      printf 'binary=%s\n' "$binary"
      sha256sum "$binary" | cut -d' ' -f1 | sed 's/^/binary_sha256=/'
    } > "$output_dir/run_manifest.txt"
  done

  "$binary" precheck "$angle" "$run_dir/precheck" "$dx_nm" "$h_nm" "$d_nm" \
    > "$run_dir/precheck/run.log" 2>&1
  precheck_code=$?
  printf '%s\n' "$precheck_code" > "$run_dir/precheck/exit_code.txt"
  if [[ $precheck_code -ne 0 ]]; then
    printf '%s\n' "$precheck_code" > "$run_dir/steady/exit_code.txt"
    printf '%s,%s,%s,%s,precheck_FAIL_%s,0,0,0,0\n' \
      "$angle" "$h_nm" "$d_nm" "$dx_nm" "$precheck_code" >> "$summary_csv"
    echo "case=$run_dir precheck_FAIL=$precheck_code"
    continue
  fi

  "$binary" steady "$angle" "$run_dir/steady" "$dx_nm" "$h_nm" "$d_nm" \
    > "$run_dir/steady/run.log" 2>&1
  steady_code=$?
  printf '%s\n' "$steady_code" > "$run_dir/steady/exit_code.txt"

  J_main=$(grep -m1 '^J_main_m2_s=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
  Jx=$(grep -m1 '^J_vector_m2_s=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2 | cut -d, -f1)
  Jy=$(grep -m1 '^J_vector_m2_s=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2 | cut -d, -f2)
  Keff=$(grep -m1 '^Keff_m3=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$angle" "$h_nm" "$d_nm" "$dx_nm" "$steady_code" \
    "${J_main:-NA}" "${Jx:-NA}" "${Jy:-NA}" "${Keff:-NA}" >> "$summary_csv"
  echo "case=$run_dir steady_exit=$steady_code"
done

echo "done. summary: $summary_csv"
