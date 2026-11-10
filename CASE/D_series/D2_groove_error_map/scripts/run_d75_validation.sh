#!/usr/bin/env bash
# d=75 nm 留出验证批次（修正公式的"考场"）
# 档位：h∈{50,75,125} × {P,T} × d=75 × dx=5，共 6 档
# 预测值见 results/analysis/CORRECTION_MODEL_FIT_20261017.md §3
# 用法：./scripts/run_d75_validation.sh
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/d2_groove_error_map"
results_root="$case_root/results"
summary_csv="$results_root/d75_summary.csv"

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

if [[ ! -f "$summary_csv" ]]; then
  printf 'case_id,h_nm,d_nm,dx_nm,exit_code,Keff_m3,J_main_m2_s\n' > "$summary_csv"
fi

for h_nm in 50 75 125; do
  for dirn in P T; do
    run_dir="$results_root/d75_h${h_nm}_dx5_${dirn}"
    if [[ -e "$run_dir/steady/exit_code.txt" ]]; then
      echo "skip existing: $run_dir"
      continue
    fi
    mkdir -p "$run_dir/precheck" "$run_dir/steady"
    for output_dir in "$run_dir/precheck" "$run_dir/steady"; do
      {
        printf 'case_id=%s\n' "D2-${dirn}-h${h_nm}-d75-dx5"
        printf 'dx_nm=5\n'
        printf 'tau=1.0\n'
        printf 'acceleration_m_s2=1e5\n'
        printf 'mesa_gap_nm=%s\n' "$h_nm"
        printf 'groove_depth_nm=75\n'
        printf 'binary=%s\n' "$binary"
        sha256sum "$binary" | cut -d' ' -f1 | sed 's/^/binary_sha256=/'
      } > "$output_dir/run_manifest.txt"
    done

    "$binary" precheck "$dirn" "$run_dir/precheck" 5 "$h_nm" 75 \
      > "$run_dir/precheck/run.log" 2>&1
    precheck_code=$?
    printf '%s\n' "$precheck_code" > "$run_dir/precheck/exit_code.txt"
    if [[ $precheck_code -ne 0 ]]; then
      printf '%s\n' "$precheck_code" > "$run_dir/steady/exit_code.txt"
      printf 'D2-%s-h%s-d75-dx5,%s,75,5,precheck_FAIL_%s,NA,NA\n' \
        "$dirn" "$h_nm" "$h_nm" "$precheck_code" >> "$summary_csv"
      echo "case=$run_dir precheck_FAIL=$precheck_code"
      continue
    fi

    "$binary" steady "$dirn" "$run_dir/steady" 5 "$h_nm" 75 \
      > "$run_dir/steady/run.log" 2>&1
    steady_code=$?
    printf '%s\n' "$steady_code" > "$run_dir/steady/exit_code.txt"
    Keff=$(grep -m1 '^Keff_m3=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    J=$(grep -m1 '^J_main_m2_s=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
    printf 'D2-%s-h%s-d75-dx5,%s,75,5,%s,%s,%s\n' \
      "$dirn" "$h_nm" "$h_nm" "$steady_code" "${Keff:-NA}" "${J:-NA}" >> "$summary_csv"
    echo "case=$run_dir steady_exit=$steady_code Keff=${Keff:-NA}"
  done
done

echo "done. summary: $summary_csv"
