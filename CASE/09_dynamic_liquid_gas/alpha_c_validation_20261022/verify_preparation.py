#!/usr/bin/env python3
"""Verify existing local/zero-step evidence only. Does not run any solver."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from analyze_alpha import analyze_case as alpha_case
from analyze_c import analyze_case as c_case
from run_suite import BASE,PROTOCOL,batch_id

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('verification output exists')
    protected=json.loads((BASE/'evidence/protected_inputs.json').read_text())
    bad=[p for p,h in protected.items() if not Path(p).is_file() or sha(p)!=h];assert not bad,bad
    checks={}
    for name,count in (('alpha_collision_v1',59184),('ns_collision_v1',3240)):
        assert int((BASE/'evidence'/f'{name}_exit_code.txt').read_text())==0
        log=(BASE/'evidence'/f'{name}.log').read_text();assert 'failures=0' in log
        assert int(re.search(r'checks=(\d+)',log).group(1))==count
        checks[name]=dict(checks=count,max_abs_error=float(re.search(r'max_abs_error=([^\s]+)',log).group(1)))
    entries=json.loads((BASE/'evidence/initializations_v1.json').read_text());expected=[(stage,c['id']) for stage in ('alpha','c') for c in PROTOCOL['stages'][stage]]
    assert [(r['stage'],r['case_id']) for r in entries]==expected
    initial=[]
    for entry in entries:
        assert entry['independent_exit_code']==0 and entry['command'][-1]=='--initialize-only'
        directory=BASE/'evidence'/entry['run_id'];assert int((directory/'exit_code.txt').read_text())==0
        assert json.loads((directory/'manifest.json').read_text())==entry
        case=next(c for c in PROTOCOL['stages'][entry['stage']] if c['id']==entry['case_id'])
        fn=alpha_case if entry['stage']=='alpha' else c_case
        initial.append(fn(case,Path(entry['output']),PROTOCOL['thresholds'],True))
    assert (BASE/'src/dimension_corrected_ch.h').read_bytes()==(BASE.parent/'ab_diffusion_validation_20261022/src/dimension_corrected_ch.h').read_bytes()
    assert subprocess.run(['make','-q'],cwd=BASE,capture_output=True).returncode==0,'stale binary'
    for stage in ('alpha','c'):
        for where in ('output','evidence'):assert not (BASE/where/batch_id(stage)).exists(),'formal batch unexpectedly exists'
    shared_snapshots=[]
    for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
        before=(BASE/'before'/name).read_text();current=(BASE.parents[2]/'docs/reports'/name).read_text()
        # Other first-paper work can update shared state concurrently. This task
        # has not edited it yet; record the drift rather than restoring a stale copy.
        shared_snapshots.append(dict(file=name,
            initial_first_paper_prefix_sha256=hashlib.sha256(before.split('## 第二篇论文：')[0].encode()).hexdigest(),
            current_first_paper_prefix_sha256=hashlib.sha256(current.split('## 第二篇论文：')[0].encode()).hexdigest(),
            concurrent_prefix_change=before.split('## 第二篇论文：')[0]!=current.split('## 第二篇论文：')[0]))
    payload=dict(preparation_pass=True,collision_checks=checks,zero_step_initializations=initial,
                 initialization_count=len(initial),spatial_steps_executed=0,formal_batches_started=False,
                 shared_state_snapshots=shared_snapshots,
                 protected_files_verified=len(protected),protected_mismatches=bad,make_up_to_date=True,
                 NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,indent=2)+'\n')
    print('PREPARATION_PASS:',len(initial),'zero-step initializations;',sum(v['checks'] for v in checks.values()),'local checks;',len(protected),'protected hashes; no spatial steps')

if __name__=='__main__':
    try:main()
    except Exception as exc:print('PREPARATION_FAILED:',repr(exc),file=sys.stderr);sys.exit(2)
