#!/usr/bin/env python3
"""Read-only verification of existing preparation evidence; never starts a solver."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from analyze_completed import analyze_a2,analyze_b
from run_suite import BASE,PROTOCOL

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise ValueError('output exists; no overwrite')
    protected=json.loads((BASE/'evidence/protected_before.json').read_text())
    bad=[f for f,h in protected.items() if not Path(f).is_file() or hashlib.sha256(Path(f).read_bytes()).hexdigest()!=h]
    if bad:raise ValueError('old protected files changed: '+repr(bad))
    expected=[('a2',n) for n in PROTOCOL['A2_cases']]+[('b',c['id']) for c in PROTOCOL['B_cases']]
    initial=json.loads((BASE/'evidence/initializations_v1.json').read_text())
    assert [(e['stage'],e['case_id']) for e in initial]==expected
    checks=[]
    for e in initial:
        sub=BASE/'evidence'/e['run_id'];assert int((sub/'exit_code.txt').read_text())==0 and e['independent_exit_code']==0
        out=BASE/'output'/e['run_id']
        if e['stage']=='a2':r=analyze_a2(e['case_id'],out,True)
        else:r=analyze_b(next(c for c in PROTOCOL['B_cases'] if c['id']==e['case_id']),out,True)
        assert r.get('contract_pass') is not False
        checks.append(r)
    counts={}
    for name,wanted in [('ch_collision_v1',28728),('ns_collision_v1',3240)]:
        assert int((BASE/'evidence'/(name+'_exit_code.txt')).read_text())==0
        log=(BASE/'evidence'/(name+'.log')).read_text();assert 'failures=0' in log
        assert int(re.search(r'checks=(\d+)',log).group(1))==wanted
        counts[name]=dict(checks=wanted,max_absolute_error=float(re.search(r'max_abs_error=([^\s]+)',log).group(1)))
    assert all(x['passed'] for x in json.loads((BASE/'evidence/CLI_guard_checks.json').read_text()))
    for f in ['build_v3_exit_code.txt','test_contracts_v1_exit_code.txt']:assert int((BASE/'evidence'/f).read_text())==0
    up=subprocess.run(['make','-q'],cwd=BASE,capture_output=True);assert up.returncode==0,'compiled binaries stale'
    assert (BASE/'src/dimension_corrected_ch.h').read_bytes()==(BASE.parent/'source3d_validation_20261022/src/dimension_corrected_ch.h').read_bytes()
    for where in ['output','evidence']:assert not (BASE/where/PROTOCOL['batch_id']).exists(),'formal batch unexpectedly exists'
    nsteps=sum(c['steps'] for c in PROTOCOL['B_cases'])+len(PROTOCOL['A2_cases'])
    nodeupdates=sum(c['steps']*c['N']**3 for c in PROTOCOL['B_cases'])+len(PROTOCOL['A2_cases'])*PROTOCOL['A2_N']**3
    record=dict(preparation_pass=True,protected_files_verified=len(protected),protected_mismatches=bad,collision_checks=counts,zero_step_initializations=checks,initialization_count=len(checks),new_spatial_steps_executed=0,formal_batch_started=False,formal_case_count=22,formal_total_lattice_steps=nsteps,formal_total_core_node_updates=nodeupdates,same_corrected_header=True,make_up_to_date=True,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    args.output.parent.mkdir(exist_ok=True,parents=True);args.output.write_text(json.dumps(record,indent=2)+'\n')
    print(f'PREPARATION_PASS: A1 {sum(x["checks"] for x in counts.values())} checks; 22 zero-step initializations; {len(protected)} protected hashes; no spatial steps.')
if __name__=='__main__':
    try:main()
    except Exception as exc:print('PREPARATION_FAILED:',repr(exc),file=sys.stderr);sys.exit(2)
