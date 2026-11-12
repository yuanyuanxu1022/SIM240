#!/bin/bash
source /opt/openfoam13/etc/bashrc || exit "$?"
cd /home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2 || exit "$?"
exec /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why="SIM240 fixed remaining cases" /usr/bin/python3 -u /home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_fvm_v21_batch_20261112/run_remaining.py --execute >> /home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_fvm_v21_batch_20261112/batch_console.log 2>&1
