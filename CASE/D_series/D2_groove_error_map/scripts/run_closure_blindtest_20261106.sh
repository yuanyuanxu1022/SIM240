#!/usr/bin/env bash
# 闭环盲测批次（2026-11-06）
#
# A 组：h=100 nm / d=100 nm，w=120、P=240 固定，dx=5 nm
#   用途：h=100 是现有 h 网格 25/50/75/125 之间未采样的间隙，
#   未参与 V2 系数确定 ⇒ 对 V2 的盲测。预测值在开跑前已冻结，
#   见 docs/reports/PAPER1_闭环方案_20261105/REPORT.md §6.3：
#     Kxx = 1.035011e-22 m3，Kyy = 1.621209e-22 m3
#
# B 组：h=75 nm / d=100 nm，同一几何在当前构建上复跑
#   用途：该几何历史结果来自构建 A(285f67a0)，
#   本次用当前构建 B(57611b21) 复跑 ⇒ 直接量化构建 A→B 的差异，
#   不覆盖、不改写任何历史结果。
#
# 判据（开跑前定死，不得事后修改）：
#   主判据：A 组两方向 |偏差| <= 10%（对齐 Ryu 2017 的发表精度）
#   结构判据：A 组残差与 h75/d100 残差之差 <= 5 个百分点
#   无论通过与否，结果一律保留并报告。
#
# 用法：bash scripts/run_closure_blindtest_20261106.sh

set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/d2_groove_error_map"
results_root="$case_root/results"
summary_csv="$results_root/closure_blindtest_20261106.csv"

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

binary_hash=$(sha256sum "$binary" | cut -d' ' -f1)

if [[ ! -f "$summary_csv" ]]; then
  printf 'case_id,group,h_nm,d_nm,dx_nm,exit_code,Keff_m3,binary_sha256\n' > "$summary_csv"
fi

run_one() {
  local dirname="$1" h="$2" d="$3" group="$4" dirn="$5"
  local run_dir="$results_root/$dirname"
  local case_id="D2-${dirn}-h${h}-d${d}-dx5-${group}"

  if [[ -e "$run_dir/steady/exit_code.txt" ]]; then
    echo "skip existing: $run_dir"
    return 0
  fi

  mkdir -p "$run_dir/precheck" "$run_dir/steady"
  for output_dir in "$run_dir/precheck" "$run_dir/steady"; do
    {
      printf 'case_id=%s\n' "$case_id"
      printf 'dx_nm=5\n'
      printf 'tau=1.0\n'
      printf 'acceleration_m_s2=1e5\n'
      printf 'mesa_gap_nm=%s\n' "$h"
      printf 'groove_depth_nm=%s\n' "$d"
      printf 'group=%s\n' "$group"
      printf 'binary=%s\n' "$binary"
      printf 'binary_sha256=%s\n' "$binary_hash"
    } > "$output_dir/run_manifest.txt"
  done

  echo "[$(date +%H:%M:%S)] start $case_id"
  "$binary" precheck "$dirn" "$run_dir/precheck" 5 "$h" "$d" \
    > "$run_dir/precheck/run.log" 2>&1
  local precheck_code=$?
  printf '%s\n' "$precheck_code" > "$run_dir/precheck/exit_code.txt"
  if [[ $precheck_code -ne 0 ]]; then
    printf '%s\n' "$precheck_code" > "$run_dir/steady/exit_code.txt"
    printf '%s,%s,%s,%s,5,precheck_FAIL_%s,NA,%s\n' \
      "$case_id" "$group" "$h" "$d" "$precheck_code" "$binary_hash" >> "$summary_csv"
    echo "[$(date +%H:%M:%S)] precheck FAIL $case_id code=$precheck_code"
    return 1
  fi

  "$binary" steady "$dirn" "$run_dir/steady" 5 "$h" "$d" \
    > "$run_dir/steady/run.log" 2>&1
  local steady_code=$?
  printf '%s\n' "$steady_code" > "$run_dir/steady/exit_code.txt"
  local Keff
  Keff=$(grep -m1 '^Keff_m3=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
  printf '%s,%s,%s,%s,5,%s,%s,%s\n' \
    "$case_id" "$group" "$h" "$d" "$steady_code" "${Keff:-NA}" "$binary_hash" >> "$summary_csv"
  echo "[$(date +%H:%M:%S)] done $case_id steady_exit=$steady_code Keff=${Keff:-NA}"
}

overall=0
for dirn in P T; do
  run_one "h100_d100_dx5_${dirn}" 100 100 "A_blind" "$dirn" || overall=1
done
for dirn in P T; do
  run_one "h75_d100_dx5_buildB_${dirn}" 75 100 "B_buildcheck" "$dirn" || overall=1
done

echo "done. summary: $summary_csv"
exit $overall
