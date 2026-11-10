#!/usr/bin/env bash
# Prepare four independent single-rank runs; the user starts this via tmux.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
test -x ./phasefield_minimal_validation

batch_id="calibration_$(TZ=Asia/Shanghai date +%Y%m%dT%H%M%S)_$$"
batch_dir="$PWD/output/$batch_id"
mkdir -p output
mkdir -- "$batch_dir"
mkdir -- "$batch_dir/inputs"
cp -- phasefield_minimal_validation phasefield_minimal_validation.cpp Makefile frozen_protocol.md \
  run_wetting_calibration_20261016.sh "$batch_dir/inputs/"
sha256sum "$batch_dir"/inputs/* > "$batch_dir/input_sha256.txt"
git -C /home/dell/openlb rev-parse HEAD > "$batch_dir/openlb_head.txt"
git -C /home/dell/openlb status --short > "$batch_dir/openlb_worktree_status.txt"
ldd "$batch_dir/inputs/phasefield_minimal_validation" > "$batch_dir/linked_libraries.txt"
printf '%s\n' 'Source and executable snapshots recorded; source-to-build binding is not independently proven by these hashes.' \
  > "$batch_dir/provenance_limit.txt"
printf 'run_id\ttheta_deg\textent\tshell_exit\n' > "$batch_dir/exit_summary.tsv"

run_ids=()
pids=()
for theta in 80 104 120 15; do
  extent=64
  if [[ "$theta" == 15 ]]; then extent=100; fi
  run_id="calib_theta${theta}_tanh_${batch_id#calibration_}"
  test ! -e "output/$run_id"
  command=("$batch_dir/inputs/phasefield_minimal_validation" --case contact --run-id "$run_id"
    --theta "$theta" --extent "$extent" --max-steps 6000 --vtk-interval 500
    --init-phi tanh --init-pressure laplace)
  printf '%q ' "${command[@]}" > "$batch_dir/$run_id.command.txt"
  printf '\n' >> "$batch_dir/$run_id.command.txt"
  (
    if OMP_NUM_THREADS=1 "${command[@]}" > "$batch_dir/$run_id.console.log" 2>&1; then
      solver_exit=0
    else
      solver_exit=$?
    fi
    printf '%s\n' "$solver_exit" > "$batch_dir/$run_id.exit_code.txt"
    if [[ -d "output/$run_id" ]]; then
      cp -- "$batch_dir/$run_id.exit_code.txt" "output/$run_id/exit_code.txt"
    fi
    exit "$solver_exit"
  ) &
  pids+=("$!")
  run_ids+=("$run_id:$theta:$extent")
done

batch_exit=0
for index in "${!pids[@]}"; do
  if wait "${pids[$index]}"; then child_exit=0; else child_exit=$?; fi
  IFS=: read -r run_id theta extent <<< "${run_ids[$index]}"
  printf '%s\t%s\t%s\t%s\n' "$run_id" "$theta" "$extent" "$child_exit" >> "$batch_dir/exit_summary.tsv"
  if [[ "$child_exit" != 0 ]]; then batch_exit=1; fi
done
printf '%s\n' "$batch_exit" > "$batch_dir/batch_exit_code.txt"
printf 'Runs exited; batch_exit=%s; evidence=%s. Physical acceptance requires separate review.\n' "$batch_exit" "$batch_dir"
exit "$batch_exit"
