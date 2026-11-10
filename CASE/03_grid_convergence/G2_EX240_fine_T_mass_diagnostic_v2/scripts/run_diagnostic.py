#!/usr/bin/env python3
"""Prepare a unique run, or execute ONLY that user-started 4000-step diagnostic.
Never rebuild, repeat a run, modify old evidence, or advance another CASE.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CASE=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def check_bound(bindings):
    for p,h in bindings.items():
        if not Path(p).is_file() or sha(Path(p))!=h: raise RuntimeError('Frozen input changed: '+p)


def write_new(path,contents):
    with path.open('x') as f: f.write(contents)


def dump_new(path,data): write_new(path,json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def kv(path):
    return dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)


def validate_build(build):
    assert build['precheck_PASS'] and build['historical_inputs_unchanged']
    assert build['current_library_unchanged'] and build['new_source_files_unchanged']
    for field in ('source_and_recipe_files','historical_inputs','current_library_files','dynamic_libraries'):
        check_bound(build[field])
    check_bound({build['binary']['path']:build['binary']['sha256']})


def prepare(build):
    run_id='fine_t_mass_v2_'+datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%dT%H%M%S%z')
    run=CASE/'runs'/run_id
    run.mkdir(exist_ok=False)
    params={'mesa_gap_nm':75,'groove_depth_nm':100,'groove_width_nm':120,'period_nm':240,
            'Lx_nm':240,'Ly_nm':240,'dx_nm':1.25,'dt_s':2.604166666666667e-13,'tau':1,
            'rho_kg_m3':1000,'nu_m2_s':1e-6,'mu_Pa_s':1e-3,'acceleration_x_m_s2':1e5,
            'rank':1,'compute_threads':1,'cuboids':1,'overlap':3,'diagnostic_steps':4000,
            'original_maximum_steps':60000,'convergence_window':1000,
            'collision':'ForcedBGK','descriptor':'D3Q19_FORCE','periodicity':'x_y',
            'boundary':'original_Bouzidi_zero_velocity_exact_EX240',
            'legacy_mass_tolerance_strict':1e-10,'density_tolerance':1e-6,'Mach_tolerance_strict':.05,
            'section_tolerance':1e-5,'cross_flux_tolerance_m2_s':1e-12,
            'J_window_std_tolerance':1e-6,'J_window_span_tolerance':5e-6,
            'ledger_agreement_tolerance':1e-13,'reconstruction_tolerance':1e-13}
    snapshot_steps=[0,119,120,624,625,626,3732,3733,4000]
    own={str(p):sha(p) for folder in ('src','scripts') for p in (CASE/folder).glob('*') if p.is_file()}
    own[str(CASE/'PROTOCOL.md')]=sha(CASE/'PROTOCOL.md')
    manifest={'run_id':run_id,'mode':'steady_with_diagnostic_cutoff','direction':'T',
              'formal_reference_accepted':False,'parameters':params,'snapshot_steps':snapshot_steps,
              'command':[build['binary']['path'],'steady','T',str(run)],'environment_overrides':
              {'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},'source_files':own,
              'build_record_sha':sha(CASE/'reports/build_precheck.json'),'build_record':build,
              'environment_basis':build['environment_basis']}
    dump_new(run/'manifest.json',manifest)
    write_new(run/'run_manifest.txt','run_id='+run_id+'\nmode=diagnostic_4000_steps\ndirection=T\n'
              +'source_sha='+sha(CASE/'src/fine_T_diagnostic.cpp')+'\n'
              +'binary_sha='+build['binary']['sha256']+'\nformal_reference_accepted=false\n')
    write_new(run/'RUN_READY.txt','Prepared only; no LBM time stepping started.\n'
              +'Expected diagnostic coverage: 4001 rows and 9 fixed snapshots plus peak.\n')
    print(json.dumps({'run_id':run_id,'directory':str(run),'prepared_only':True},ensure_ascii=False))


def execute(run_id,build):
    if not re.fullmatch(r'fine_t_mass_v2_\d{8}T\d{6}\+0800',run_id):
        raise ValueError('Only a prepared v2 run_id is allowed')
    run=CASE/'runs'/run_id
    manifest=json.loads((run/'manifest.json').read_text())
    check_bound(manifest['source_files'])
    assert manifest['run_id']==run_id and manifest['snapshot_steps']==[0,119,120,624,625,626,3732,3733,4000]
    assert manifest['command']==[build['binary']['path'],'steady','T',str(run)]
    assert manifest['build_record_sha']==sha(CASE/'reports/build_precheck.json')
    if any((run/name).exists() for name in ('run.log','result.txt','mass_ledger.csv','exit_code.txt')):
        raise FileExistsError('Refusing repeated execution of prepared run')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                       if line.startswith('MemAvailable:')))*1024
    if available<8*1024**3 or shutil.disk_usage(run).free<2*1024**3:
        raise RuntimeError('Need at least budgeted 8 GiB available RAM and 2 GiB free disk')
    if not Path('/usr/bin/time').is_file(): raise RuntimeError('/usr/bin/time is required for independent resources')
    command=['/usr/bin/time','-v','-o',str(run/'timing.txt'),*manifest['command']]
    env=os.environ.copy(); env.update(manifest['environment_overrides'])
    print('Starting diagnostic '+run_id,flush=True)
    with (run/'run.log').open('x') as f:
        completed=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env)
    write_new(run/'exit_code.txt',str(completed.returncode)+'\n')
    # Structural evidence only; the user requests a separate scientific review.
    coverage=False
    if (run/'diagnostic_status.txt').is_file() and (run/'mass_ledger.csv').is_file():
        status=kv(run/'diagnostic_status.txt')
        with (run/'mass_ledger.csv').open(newline='') as f: rows=list(csv.DictReader(f))
        coverage=(len(rows)==4001 and all(int(r['step'])==i for i,r in enumerate(rows))
                  and status.get('diagnostic_coverage_complete')=='true'
                  and status.get('formal_reference_accepted')=='false'
                  and all((run/'mass_snapshots'/('rho_step_'+str(s)+'.bin')).is_file()
                          for s in manifest['snapshot_steps'])
                  and (run/'mass_snapshots/peak_rho.bin').is_file())
    source_unchanged=all(sha(Path(p))==h for p,h in manifest['source_files'].items())
    historical_unchanged=all(sha(Path(p))==h for p,h in build['historical_inputs'].items())
    evidence={str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file()}
    summary={'run_id':run_id,'independent_exit_code':completed.returncode,
             'diagnostic_structural_coverage_complete':coverage,'source_files_unchanged':source_unchanged,
             'historical_inputs_unchanged':historical_unchanged,'output_sha256':evidence,
             'formal_reference_accepted':False,'scientific_review_required':True,
             'note':'Exit 3 can preserve legacy rejection; it is neither automatic diagnosis failure nor formal PASS.'}
    dump_new(run/'completion.json',summary)
    print(json.dumps({'run_id':run_id,'independent_exit_code':completed.returncode,
                      'coverage_complete':coverage,'completion':str(run/'completion.json')},ensure_ascii=False),flush=True)
    return completed.returncode


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--run-id')
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.prepare_only:
        if args.execute or args.run_id: parser.error('Preparation cannot be combined with execution')
    elif not (args.execute and args.run_id): parser.error('Use --prepare-only or --run-id ID --execute')
    build=json.loads((CASE/'reports/build_precheck.json').read_text())
    validate_build(build)
    if args.prepare_only: prepare(build)
    else: raise SystemExit(execute(args.run_id,build))


if __name__=='__main__': main()
