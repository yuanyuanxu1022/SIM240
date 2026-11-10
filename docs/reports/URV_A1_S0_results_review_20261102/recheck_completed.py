#!/usr/bin/env python3
"""Run the frozen offline checker against one completed run. Never solve."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_mrp_v1_a1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_mrp_v1_a1'
SHA = 'cf7f1aaccf22b8d47b0c81147b9f9dcb22d07615f45664b09c9f7d1347826148'


def main():
    direction = sys.argv[1]
    assert direction in ('P', 'T')
    rid = f'URV_S0_{direction}_A1_20261102_01'
    argv = [sys.executable, '-B', str(CHECKER / 'analysis/check_mass_repair.py'),
            '--run', str(CASE / 'runs' / rid / 'steady'),
            '--release', str(CASE / 'evidence/S0_launch_release_A1_20261102_01.json'),
            '--release-sha256', SHA, '--out', str(OUT / ('recheck_' + direction))]
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
               QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1')
    started = time.monotonic()
    with (OUT / ('checker_' + direction + '.log')).open('x') as log:
        process = subprocess.run(argv, cwd=ROOT, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, timeout=3600)
    record = dict(direction=direction, run_id=rid, argv=argv,
                  independent_checker_exit_code=process.returncode,
                  elapsed_seconds=time.monotonic() - started, native_solver_called=False)
    with (OUT / ('checker_' + direction + '_execution.json')).open('x') as stream:
        stream.write(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))
    return process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
