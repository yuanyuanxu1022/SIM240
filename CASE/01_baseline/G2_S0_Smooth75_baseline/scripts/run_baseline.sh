#!/usr/bin/env bash
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$case_root/build/g2_s0_smooth75_baseline"
source_file="$case_root/../G1_Poiseuille_Bouzidi_Validation/src/g1_poiseuille_bouzidi_validation.cpp"
g2_batch="$case_root/../G2_EX240_single_period_transport/results/g2_ex240_20260917T105523+0800"

if [[ ! -x "$binary" ]]; then
  echo "missing executable: $binary" >&2
  exit 2
fi
if [[ ! -f "$g2_batch/G2-P/steady/result_summary.csv" || ! -f "$g2_batch/G2-T/steady/result_summary.csv" ]]; then
  echo "missing frozen formal G2 summaries: $g2_batch" >&2
  exit 2
fi

run_id="g2_s0_smooth75_$(date +%Y%m%dT%H%M%S%z)"
run_dir="$case_root/results/$run_id"
precheck_dir="$run_dir/precheck"
steady_dir="$run_dir/steady"
mkdir -p "$precheck_dir" "$steady_dir"
printf '%s\n' "$run_dir" > "$case_root/latest_run.txt"

{
  printf 'run_id=%s\n' "$run_id"
  printf 'case=G2_S0_Smooth75_baseline\n'
  printf 'dx_nm=2.5\n'
  printf 'tau=1.0\n'
  printf 'acceleration_m_s2=1e5\n'
  printf 'Lx_nm=240\nLy_nm=240\nH_nm=75\n'
  printf 'compile_command=make -C %s/src\n' "$case_root"
  printf 'source=%s\n' "$source_file"
  sha256sum "$source_file" "$binary" "$case_root/BASELINE_PROTOCOL.md" \
    "$case_root/scripts/run_baseline.sh" "$case_root/scripts/postprocess_baseline.py"
} > "$run_dir/source_manifest.txt"
cp "$run_dir/source_manifest.txt" "$precheck_dir/run_manifest.txt"
cp "$run_dir/source_manifest.txt" "$steady_dir/run_manifest.txt"

"$binary" precheck "$precheck_dir" 2.5 1.0 1e5 > "$precheck_dir/run.log" 2>&1
precheck_code=$?
printf '%s\n' "$precheck_code" > "$precheck_dir/exit_code.txt"
if [[ $precheck_code -ne 0 ]]; then
  printf 'blocked_by_precheck=%s\n' "$precheck_code" > "$steady_dir/run.log"
  printf '%s\n' "$precheck_code" > "$steady_dir/exit_code.txt"
  echo "precheck_FAIL=$precheck_code run_dir=$run_dir"
  exit "$precheck_code"
fi

"$binary" steady "$steady_dir" 2.5 1.0 1e5 > "$steady_dir/run.log" 2>&1
steady_code=$?
printf '%s\n' "$steady_code" > "$steady_dir/exit_code.txt"

/usr/bin/python3 "$case_root/scripts/postprocess_baseline.py" "$run_dir" "$g2_batch"
post_code=$?
printf '%s\n' "$post_code" > "$run_dir/postprocess_exit_code.txt"
echo "steady_exit=$steady_code postprocess_exit=$post_code run_dir=$run_dir"
if [[ $steady_code -ne 0 ]]; then
  exit "$steady_code"
fi
exit "$post_code"
