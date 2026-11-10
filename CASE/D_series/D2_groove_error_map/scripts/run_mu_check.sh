#!/usr/bin/env bash
# μ 对照批次：验证 K 与黏度无关（牛顿/无滑移/低速假设下 K 是纯几何量）
# 档位：h75/d100/dx5 的 P、T 两方向 × ν=1.5e-5（μ=15 mPa·s，对应 mr-NIL210）
# 对照基准：同几何 ν=1e-6 的 D2-P-h75-d100-dx5 / D2-T-h75-d100-dx5（主矩阵已有）
# 用法：./scripts/run_mu_check.sh
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/d2_groove_error_map"
results_root="$case_root/results"
NU_MU15=1.5e-5   # m²/s → μ = 1000 * 1.5e-5 = 0.015 Pa·s = 15 mPa·s

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi

for dirn in P T; do
  run_dir="$results_root/mu15_h75_d100_dx5_${dirn}"
  if [[ -e "$run_dir/steady/exit_code.txt" ]]; then
    echo "skip existing: $run_dir"
    continue
  fi
  mkdir -p "$run_dir/precheck" "$run_dir/steady"
  for output_dir in "$run_dir/precheck" "$run_dir/steady"; do
    {
      printf 'case_id=%s\n' "D2-${dirn}-h75-d100-dx5-mu15"
      printf 'nu_phys_m2_s=%s\n' "$NU_MU15"
      printf 'mu_phys_Pa_s=0.015\n'
      printf 'dx_nm=5\n'
      printf 'tau=1.0\n'
      printf 'acceleration_m_s2=1e5\n'
      printf 'mesa_gap_nm=75\n'
      printf 'groove_depth_nm=100\n'
      printf 'binary=%s\n' "$binary"
      sha256sum "$binary" | cut -d' ' -f1 | sed 's/^/binary_sha256=/'
    } > "$output_dir/run_manifest.txt"
  done

  "$binary" precheck "$dirn" "$run_dir/precheck" 5 75 100 "$NU_MU15" \
    > "$run_dir/precheck/run.log" 2>&1
  precheck_code=$?
  printf '%s\n' "$precheck_code" > "$run_dir/precheck/exit_code.txt"
  if [[ $precheck_code -ne 0 ]]; then
    printf '%s\n' "$precheck_code" > "$run_dir/steady/exit_code.txt"
    echo "case=$run_dir precheck_FAIL=$precheck_code"
    continue
  fi

  "$binary" steady "$dirn" "$run_dir/steady" 5 75 100 "$NU_MU15" \
    > "$run_dir/steady/run.log" 2>&1
  steady_code=$?
  printf '%s\n' "$steady_code" > "$run_dir/steady/exit_code.txt"
  Keff=$(grep -m1 '^Keff_m3=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
  J=$(grep -m1 '^J_main_m2_s=' "$run_dir/steady/result.txt" 2>/dev/null | cut -d= -f2)
  echo "case=$run_dir steady_exit=$steady_code Keff=${Keff:-NA} J=${J:-NA}"
done

echo "done. compare with baseline D2-<P|T>-h75-d100-dx5 in summary.csv"
