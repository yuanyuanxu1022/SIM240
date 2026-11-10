#!/usr/bin/env bash
# h=25 nm 渐近路径批次（薄间隙行）：
# 验证"减 h"的设计结论并向更薄间隙延展误差表（S15 渐近路径证据链）
# 档位：h=25 × d∈{25,50,100} × {P,T} × dx=5，共 6 档
# 与主矩阵同口径（同二进制、同门禁），主矩阵 h∈{50,75,125} 为基线
# 用法：./scripts/run_h25_path.sh
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/d2_groove_error_map"
results_root="$case_root/results"
summary_csv="$results_root/h25_summary.csv"

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

if [[ ! -f "$summary_csv" ]]; then
  printf 'case_id,h_nm,d_nm,dx_nm,exit_code,Keff_m3,J_main_m2_s\n' > "$summary_csv"
fi

for d_nm in 25 50 100; do
  for dirn in P T; do
    run_dir="$results_root/h25_d${d_nm}_dx5_${dirn}"
    if [[ -e "$run_dir/steady/exit_code.txt" ]]; then
      echo "skip existing: $run_dir"
      continue
    fi
    mkdir -p "$run_dir/precheck" "$run_dir/steady"
    for output_dir in "$run_dir/precheck" "$run_dir/steady"; do
      {
        printf 'case_id=%s\n' "D2-${dirn}-h25-d${d_nm}-dx5"
        printf 'dx_nm=5\n'
        printf 'tau=1.0\n'
        printf 'acceleration_m_s2=1e5\n'
        printf 'mesa_gap_nm=25\n'
        printf 'groove_depth_nm=%s\n' "$d_nm"
        printf 'binary=%s\n' "$binary"
        sha256sum "$binary" | cut -d' ' -f1 | sed 's/^/binary_sha256=/'
      } > "$output_dir/run_manifest.txt"
    done

    "$binary" precheck "$dirn" "$run_dir/precheck" 5 25 "$d_nm" \
      > "$run_dir/precheck/run.log" 2>&1
    precheck_code=$?
    printf '%s\n' "$precheck_code" > "$run_dir/precheck/exit_code.txt"
    if [[ $precheck_code -ne 0 ]]; then
      printf '%s\n' "$precheck_code" > "$run_dir/steady/exit_code.txt"
      printf 'D2-%s-h25-d%s-dx5,25,%s,5,precheck_FAIL_%s,NA,NA\n' \
        "$dirn" "$d_nm" "$d_nm" "$precheck_code" >> "$summary_csv"
      echo "case=$run_dir precheck_FAIL=$precheck_code"
      continue
    fi

    "$binary" steady "$dirn" "$run_dir/steady" 5 25 "$d_nm" \
      > "$run_dir/steady/run.log" 2>&1
    steady_code=$?
    printf '%s\n' "$steady_code" > "$run_dir/steady/exit_code.txt"
    Keff=$(grep -m1 '^Keff_m3=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    J=$(grep -m1 '^J_main_m2_s=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    printf 'D2-%s-h25-d%s-dx5,25,%s,5,%s,%s,%s\n' \
      "$dirn" "$d_nm" "$d_nm" "$steady_code" "${Keff:-NA}" "${J:-NA}" >> "$summary_csv"
    echo "case=$run_dir steady_exit=$steady_code Keff=${Keff:-NA}"
  done
done

echo "done. summary: $summary_csv"
