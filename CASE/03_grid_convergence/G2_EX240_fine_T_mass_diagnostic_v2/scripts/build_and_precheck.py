#!/usr/bin/env python3
"""Build isolated v2, test actual observer, invoke zero-step precheck only.
No steady simulation and no automated Gate advancement.
"""
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CASE=Path(__file__).resolve().parents[1]
ROOT=CASE.parents[2]
REVIEW=ROOT/'CASE/reports/fine_T_diagnostic_review_20261013_v1'
BASE=ROOT/'CASE/03_grid_convergence/G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp'


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): digest.update(chunk)
    return digest.hexdigest()


def dump_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f: json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')


def capture(command,env=None):
    p=subprocess.run(command,capture_output=True,text=True,env=env)
    return {'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}


def check_bound(binding):
    return all(Path(p).is_file() and sha(Path(p))==h for p,h in binding.items())


def kv(path):
    return dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)


def main():
    destination=CASE/'reports/build_precheck.json'
    if destination.exists(): raise FileExistsError('Existing build/precheck evidence is immutable')
    prior=json.loads((REVIEW/'review.json').read_text())
    assert check_bound(prior['historical_inputs']) and check_bound(prior['current_library_files'])
    receipt=json.loads((CASE/'reports/preparation_receipt.json').read_text())
    for relative,h in receipt['source_files'].items(): assert sha(CASE/relative)==h,relative
    assert sha(BASE)==prior['baseline_sha256']
    source=(CASE/'src/fine_T_diagnostic.cpp').read_text()
    pattern=r'// FINE_T_DIAGNOSTIC_BEGIN (\w+)\n.*?// FINE_T_DIAGNOSTIC_END \1'
    def tokens(s): return re.findall(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z0-9_]+|[^\s]',s)
    assert tokens(re.sub(pattern,'',source,flags=re.S))==tokens(BASE.read_text())
    own={str(p):sha(p) for folder in ('src','scripts') for p in (CASE/folder).glob('*') if p.is_file()}
    own[str(CASE/'PROTOCOL.md')]=sha(CASE/'PROTOCOL.md')
    result={'time':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
            'source_tokens_restored':True,'original_source_sha':sha(BASE),
            'source_and_recipe_files':own,'historical_inputs':prior['historical_inputs'],
            'current_library_files':prior['current_library_files'],
            'environment_basis':'CONTROLLED_CURRENT_ENVIRONMENT_NOT_HISTORICAL_REBUILD',
            'OpenLB_HEAD':prior['OpenLB_HEAD'],'OpenLB_tracked_diff':prior['OpenLB_tracked_diff'],
            'OpenLB_status':prior['OpenLB_status'],'compiler':prior['compiler'],
            'commands':[],'time_stepping_started':False,'formal_reference_accepted':False,'run_ready':False}
    # Directly compile the actual v2 observer with synthetic inputs, never OpenLB.
    with tempfile.TemporaryDirectory(prefix='fine_t_v2_arithmetic_') as scratch:
        scratch=Path(scratch)
        binary=scratch/'test_observer'
        command=['g++','-O3','-Wall','-Wextra','-Werror','-march=native','-mtune=native','-std=c++20',
                 '-I'+str(CASE/'src'),str(REVIEW/'test_observer.cpp'),'-o',str(binary)]
        test_build=capture(command); result['commands'].append(test_build)
        assert test_build['exit_code']==0,test_build['stderr']
        sample=scratch/'output'; sample.mkdir()
        test_run=capture([str(binary),str(sample)]); result['commands'].append(test_run)
        assert test_run['exit_code']==0,test_run['stderr']
        with (sample/'mass_ledger.csv').open(newline='') as f: rows=list(csv.DictReader(f))
        assert len(rows)==2
        for r in rows:
            assert int(r['film_nodes'])==2211840 and int(r['recess_nodes'])==1474560
            assert float(r['film_delta'])+float(r['recess_delta'])==float(r['delta_long_double'])==0
            assert float(r['agreement_relative'])<=1e-13
            assert abs(float(r['reconstruction_residual']))<=1e-13
        assert int(rows[1]['rho_max_id'])==1 and int(rows[1]['rho_min_id'])==146
        result['synthetic_test']={'PASS':True,'scope':'two synthetic samples, no OpenLB',
                                  'rows':rows,'status':kv(sample/'diagnostic_status.txt')}
    build=capture(['make','-C',str(CASE/'src'),'compile'])
    result['commands'].append(build)
    dump_new(CASE/'reports/build_command.json',build)
    if build['exit_code']!=0:
        dump_new(destination,result); raise SystemExit(build['exit_code'])
    binary=CASE/'build/fine_T_diagnostic'
    result['binary']={'path':str(binary),'sha256':sha(binary)}
    dependencies=capture(['ldd',str(binary)])
    result['commands'].append(dependencies)
    assert dependencies['exit_code']==0
    dynamic_paths=re.findall(r'(?:=>\s*)?(/\S+)\s+\(',dependencies['stdout'])
    result['dynamic_libraries']={p:sha(Path(p).resolve()) for p in dynamic_paths}
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                       if line.startswith('MemAvailable:')))*1024
    disk=shutil.disk_usage(CASE).free
    result['resources_before_precheck']={'available_RAM_bytes':available,'disk_free_bytes':disk}
    assert available>=8*1024**3 and disk>=2*1024**3,'Resources below preparation budget'
    run_id='precheck_'+datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%dT%H%M%S%z')
    run=CASE/'runs'/run_id; run.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy(); env['OMP_NUM_THREADS']='1'; env['OPENBLAS_NUM_THREADS']='1'
    manifest={'run_id':run_id,'mode':'precheck','direction':'T','rank':1,'compute_threads':1,
              'time_stepping_calls_expected':0,'source_files':own,'binary':result['binary'],
              'current_library_files':result['current_library_files'],'dynamic_libraries':result['dynamic_libraries'],
              'environment_basis':result['environment_basis'],'OpenLB_HEAD':result['OpenLB_HEAD']}
    dump_new(run/'manifest.json',manifest)
    with (run/'run_manifest.txt').open('x') as f:
        f.write('run_id='+run_id+'\nmode=precheck\ndirection=T\nsource_sha='+sha(CASE/'src/fine_T_diagnostic.cpp')+'\n')
    command=[str(binary),'precheck','T',str(run)]
    with (run/'run.log').open('x') as f:
        p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env)
    with (run/'exit_code.txt').open('x') as f: f.write(str(p.returncode)+'\n')
    raw=kv(run/'result.txt') if (run/'result.txt').exists() else {}
    boundary=kv(run/'boundary_audit.txt') if (run/'boundary_audit.txt').exists() else {}
    result['precheck']={'run_id':run_id,'directory':str(run),'command':command,
                        'independent_exit_code':p.returncode,'result':raw,'boundary':boundary}
    checks=[p.returncode==0,raw.get('exit_code')=='0',raw.get('collide_and_stream_calls')=='0',
            raw.get('formal_simulation')=='false',raw.get('geometry_PASS')=='true',
            raw.get('q_audit_PASS')=='true',raw.get('converter_PASS')=='true',
            raw.get('fluid_nodes')=='3686400',raw.get('candidate_links')=='521472',
            raw.get('installed_links')=='521472',raw.get('fallback_count')=='0',raw.get('unresolved_links')=='0']
    for key in ('q_min','q_max'):
        checks.append(key in raw and abs(float(raw[key])-.5)<=1e-10)
    result['precheck_PASS']=all(checks)
    result['historical_inputs_unchanged']=check_bound(prior['historical_inputs'])
    result['current_library_unchanged']=check_bound(prior['current_library_files'])
    result['new_source_files_unchanged']=check_bound(own)
    result['precheck_output_sha256']={str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file()}
    dump_new(destination,result)
    print(json.dumps({'output':str(destination),'compiled':True,'precheck_PASS':result['precheck_PASS'],
                      'time_stepping_calls':raw.get('collide_and_stream_calls'),
                      'historical_inputs_unchanged':result['historical_inputs_unchanged'],
                      'formal_reference_accepted':False},ensure_ascii=False))
    assert result['precheck_PASS'] and result['historical_inputs_unchanged']
    assert result['current_library_unchanged'] and result['new_source_files_unchanged']


if __name__=='__main__': main()
