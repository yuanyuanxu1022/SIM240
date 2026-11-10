"""Two S0 configurations, describe/precheck only; never time stepping."""
from pathlib import Path
import json
import os
import resource
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / 'CASE/unseen_v2_reference_S0_v1_2'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_v1_2'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import kv, need, exact_parameters, check_boundary, close, sha


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def main():
    folder = CASE / 'audits/URV_S0_ZERO_20261101_01'
    folder.mkdir(parents=True, exist_ok=False)
    template = ROOT / 'docs/reports/URV_v1_readonly_review_S0_20261101/S0_DRAFT_NOT_EXECUTABLE'
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    records = []
    for direction in ['P', 'T']:
        for mode in ['describe', 'precheck']:
            run = folder / direction / mode; run.mkdir(parents=True)
            cfg = kv(template / f'S0_{direction}_describe_ONLY_DRAFT.txt')
            cfg.update(mode=mode, run_id=f'ZERO_URV_S0_{direction}_{mode}_20261101',
                       output_directory=str(run))
            config = run / 'run_config.txt'
            config.write_text(''.join(k + '=' + v + '\n' for k, v in cfg.items()))
            (run / 'run_manifest.txt').write_text('run_id=' + cfg['run_id'] + '\nmode=' + mode + '\n')
            with (run / 'run.log').open('x') as log:
                proc = subprocess.run([str(CASE / 'build/urv_reference'), str(config)],
                    stdout=log, stderr=subprocess.STDOUT, env=env, preexec_fn=limits, timeout=240)
            (run / 'exit_code.txt').write_text(str(proc.returncode) + '\n')
            need(proc.returncode == 0, 'S0 zero-step native check failed')
            audit = kv(run / 'execution_audit.txt')
            need(audit['preparation_only_build'] == '0' and audit['collide_and_stream_calls'] == '0',
                 'unexpected time stepping/build identity')
            p = exact_parameters(cfg); effective = kv(run / 'effective_config.txt')
            need(p['window'] == int(effective['window_steps']) == 1013, 'window')
            need(p['cap'] == int(effective['maximum_steps']) == 58800, 'cap')
            need(close(float(effective['dt_s']), p['dt']), 'time conversion')
            geometry = None
            if mode == 'precheck':
                geometry = check_boundary(cfg, kv(run / 'boundary_audit.txt'))
                need(geometry['fluid_nodes'] == 57600 and geometry['candidate_links'] == 32448, 'geometry')
            records.append(dict(direction=direction, mode=mode, native_exit=proc.returncode,
                                collide_and_stream_calls=0, directory=str(run), geometry=geometry))
    data = dict(audit_id=folder.name, native_describe=2, native_precheck=2,
        native_initialize=0, actual_time_steps=0, field_reads=0,
        formal_solver_started=False, records=records,
        binary_sha256=sha(CASE / 'build/urv_reference'),
        original_24_initializations_reused_as_prior_evidence_not_repeated=True)
    (folder / 'verification.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(dict(S0_zero_step_audit=True, actual_time_steps=0, native_calls=4)))


if __name__ == '__main__':
    main()
