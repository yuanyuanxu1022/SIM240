#!/usr/bin/bash
# User starts this once under tmux. Preparing/checking this file never runs it.
set -u
n8_launch_dir='/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026/launch_D4_N8_diag_v3_1_20261026_v1'
if ! /usr/bin/mkdir -m 700 -- "$n8_launch_dir"; then
    exit 73
fi
exec >"$n8_launch_dir/launcher.stdout.log" 2>"$n8_launch_dir/launcher.stderr.log"
trap 'n8_launcher_exit=$?; printf "%s\n" "$n8_launcher_exit" >"$n8_launch_dir/launcher.exit_code"' EXIT
/usr/bin/sha256sum --check '/home/dell/yuanyuanxu/SIM240/docs/reports/D4_N8_run_release_20261026/launch_files.sha256' || exit 74
printf '%s\n' 'RELEASE_HASHES_VERIFIED; STARTING_ONLY_APPROVED_N8_CONTROLLER'
/usr/bin/env \
    LD_LIBRARY_PATH='/home/dell/yuanyuanxu/SIM240/CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/.backend/lib' \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
    '/home/dell/yuanyuanxu/SIM240/CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/.backend/bin/python' -B \
    '/home/dell/yuanyuanxu/SIM240/CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v3_1_20261026/runner.py' \
    --contract '/home/dell/yuanyuanxu/SIM240/docs/reports/D4_N8_run_release_20261026/approved_contract.json' --execute
n8_controller_exit=$?
printf '%s\n' "$n8_controller_exit" >"$n8_launch_dir/controller.exit_code"
exit "$n8_controller_exit"
