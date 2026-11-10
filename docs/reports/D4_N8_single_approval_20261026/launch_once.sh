#!/bin/bash
# One approved item only. No automatic retry. Preserve launcher failures too.
set -o noclobber
cd /home/dell/yuanyuanxu/SIM240 || exit 2
/usr/bin/python3 -B /home/dell/yuanyuanxu/SIM240/CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v3_1_20261026/runner.py --contract /home/dell/yuanyuanxu/SIM240/docs/reports/D4_N8_single_approval_20261026/APPROVED_DIAGNOSTIC_ONLY.json --execute > /home/dell/yuanyuanxu/SIM240/docs/reports/D4_N8_single_approval_20261026/launcher.stdout.log 2> /home/dell/yuanyuanxu/SIM240/docs/reports/D4_N8_single_approval_20261026/launcher.stderr.log
launch_exit=$?
echo "$launch_exit" > /home/dell/yuanyuanxu/SIM240/docs/reports/D4_N8_single_approval_20261026/launcher.exit_code.txt
exit "$launch_exit"
