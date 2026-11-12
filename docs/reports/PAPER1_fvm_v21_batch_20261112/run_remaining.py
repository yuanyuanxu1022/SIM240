#!/usr/bin/python3
"""Fixed-scope sequential launcher. Preparation does not execute any solver.

User starts --execute under tmux. Existing accepted records are read, never
rerun. New local/reference/consistency failures stop the batch immediately.
The already recorded h75/d100 T consistency failure is retained explicitly.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone, timedelta

HERE=Path(__file__).resolve().parent
ROOT=Path('/home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2')
CLOCK=timezone(timedelta(hours=8))


def stamp(): return datetime.now(CLOCK).isoformat(timespec='seconds')
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def save(path,value):
    path=Path(path);temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)


class Halt(RuntimeError): pass


def verify_identity():
    frozen=read(HERE/'batch_manifest.json')
    for name,expected in frozen['local_sha256'].items():
        if digest(HERE/name)!=expected: raise Halt('batch file drift: '+name)
    for name,expected in frozen['external_sha256'].items():
        if digest(name)!=expected: raise Halt('batch utility drift: '+name)
    config=read(HERE/'batch_config.json')
    release=ROOT/'release_manifest.json'
    if digest(release)!=config['release_sha256']: raise Halt('release identity changed')
    identity=read(release)
    if identity['formal_review_status']!='ASTRA_FINAL_STATIC_RECHECK_COMPLETE' or not identity['numerical_execution_authorized']:
        raise Halt('original release is not unlocked')
    for name,expected in identity['sha256'].items():
        if digest(ROOT/name)!=expected: raise Halt('bound input drift: '+name)
    for name,expected in identity['external_sha256'].items():
        if digest(name)!=expected: raise Halt('original tool/library drift: '+name)
    return config


def load_reader():
    spec=importlib.util.spec_from_file_location('batch_frozen_reader',ROOT/'postprocess.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def assess(reader):
    result=reader.assess(ROOT)
    if 'cases' not in result: raise Halt('frozen reader rejected inputs: '+str(result))
    return result


def science_issues(assessment,config):
    """Original thresholds only. Already known T FAIL is never hidden."""
    issues=[];records=assessment['cases']
    for cid,record in records.items():
        if record['status'] not in ('NOT_EXECUTED','LOCAL_CHECKS_PASS'):
            issues.append(cid+': '+record['status'])
    for stem in config['points']:
        group=[records[stem+'_'+level] for level in ('coarse','mid','fine','tight')]
        good=[g['status']=='LOCAL_CHECKS_PASS' for g in group]
        if good[0] and good[1]:
            d21=abs(group[1]['metrics']['K_m3']/group[0]['metrics']['K_m3']-1)*100
            if d21>config['thresholds']['grid_mid_coarse_percent']:
                issues.append(stem+': coarse-mid grid criterion failed')
        if all(good[:3]):
            d32=abs(group[2]['metrics']['K_m3']/group[1]['metrics']['K_m3']-1)*100
            if d32>config['thresholds']['grid_fine_mid_percent']:
                issues.append(stem+': mid-fine grid criterion failed')
            if not (d32<=d21 or max(d21,d32)<=0.05):
                issues.append(stem+': decreasing grid change criterion failed')
        if all(good):
            algebra=abs(group[3]['metrics']['K_m3']/group[2]['metrics']['K_m3']-1)*100
            if algebra>config['thresholds']['algebraic_change_percent']:
                issues.append(stem+': tight algebraic criterion failed')
    points={p['point']:p for p in assessment['comparisons']}
    for point,decision in points.items():
        if decision.get('reference_accepted') is False:
            issues.append(point+': reference qualification failed')
        if decision['status']=='FAIL' and point not in config['known_consistency_failures']:
            issues.append(point+': NEW cross-implementation consistency FAIL')
    baseline=assessment.get('baseline')
    if baseline and (not baseline['A_pass'] or not baseline['beta_pass']):
        issues.append('baseline anisotropy or reconstructed-angle criterion failed')
    return issues


def preflight(config,reader):
    if os.environ.get('WM_PROJECT_VERSION')!='13' or os.environ.get('WM_PROJECT_DIR')!='/opt/openfoam13':
        raise Halt('source /opt/openfoam13/etc/bashrc first')
    if (HERE/'execution').exists(): raise Halt('batch execution already exists; no overwrite/resume/retry')
    plan=read(ROOT/'prepared_manifest.json')
    if config['thresholds']!=plan['thresholds']: raise Halt('threshold identity mismatch')
    ids={m['case_id'] for m in plan['cases']}
    remaining=config['remaining'];completed=config['accepted_existing']
    if len(remaining)!=17 or len(set(remaining))!=17 or set(remaining)&set(completed) or set(remaining)|set(completed)!=ids:
        raise Halt('batch scope differs from the original fixed 26 inputs')
    for cid,expected in completed.items():
        path=ROOT/'prepared'/cid/'referenceEvidence/receipt.json'
        if digest(path)!=expected: raise Halt('accepted source receipt changed: '+cid)
    for cid in remaining:
        case=ROOT/'prepared'/cid
        if any((case/n).exists() for n in ('runtime','referenceEvidence','0.5')):
            raise Halt('pending case has existing run/mapped fields: '+cid)
    result=assess(reader)
    for cid in completed:
        if result['cases'][cid]['status']!='LOCAL_CHECKS_PASS': raise Halt('previous evidence rejected: '+cid)
    actual={p['point'] for p in result['comparisons'] if p['status']=='FAIL'}
    if actual!=set(config['known_consistency_failures']): raise Halt('baseline consistency failures changed')
    issues=science_issues(result,config)
    if issues: raise Halt('; '.join(issues))
    # Every new seed must be either already accepted or occur earlier in this list.
    available=set(completed);canonical={m['case_id']:m for m in plan['cases']}
    for cid in remaining:
        source=canonical[cid].get('seed_from')
        if source and source not in available: raise Halt('dependency order invalid: '+cid)
        available.add(cid)
    return result


def run_sequence(config,initial,reader,work,invoke=None,evaluate=None):
    """Single serial loop; injected fake backends are used by synthetic tests."""
    state=dict(status='RUNNING',started_at=stamp(),known_consistency_failures=config['known_consistency_failures'],
               planned=config['remaining'],completed=[],finished_runs=[],current_case=None,issues=[],new_solver_execution_authorized_by='user terminal launch only')
    save(work/'status.json',state);save(work/'assessment_initial.json',initial)
    try:
        for index,cid in enumerate(config['remaining'],1):
            if invoke is None:
                verify_identity()
                case=ROOT/'prepared'/cid
                if (case/'runtime').exists() or (case/'referenceEvidence').exists():
                    raise Halt('existing evidence encountered; refusing to rerun '+cid)
            state.update(current_case=cid,stage='SOLVER',updated_at=stamp())
            save(work/'status.json',state)
            print(f'[{index}/{len(config["remaining"])}] START {cid}',flush=True)
            if invoke:
                code=invoke(cid)
            else:
                with (work/(cid+'.runner.log')).open('x') as stream:
                    code=subprocess.run([sys.executable,str(ROOT/'run_one.py'),'--case',cid,'--execute'],
                                        cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT).returncode
            state['finished_runs'].append(dict(case_id=cid,runner_exit_code=code))
            save(work/'status.json',state)
            if code!=0: raise Halt(f'{cid}: runner exit code {code}; no retry')
            state.update(stage='INDEPENDENT_READBACK',updated_at=stamp());save(work/'status.json',state)
            result=evaluate(cid) if evaluate else assess(reader)
            save(work/(cid+'.assessment.json'),result)
            if result['cases'].get(cid,{}).get('status')!='LOCAL_CHECKS_PASS':
                raise Halt(cid+': local acceptance failed')
            issues=science_issues(result,config)
            if issues: raise Halt('; '.join(issues))
            state['completed'].append(cid);state.update(updated_at=stamp(),last_case=cid)
            save(work/'status.json',state);print('ACCEPTED '+cid,flush=True)
        state.update(status='COMPLETE_WITH_PREVIOUSLY_RECORDED_T_DISAGREEMENT',current_case=None,
                     stage='FINISHED',finished_at=stamp())
        save(work/'status.json',state);print('FINISHED fixed remaining inputs; known T FAIL retained.',flush=True)
        return 0
    except (Exception,KeyboardInterrupt) as error:
        state.update(status='STOPPED_ON_FAILURE',issues=[str(error)],finished_at=stamp(),
                     remaining_not_authorized_to_retry=True)
        save(work/'status.json',state);print('STOPPED: '+str(error),flush=True)
        return 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if Path(sys.executable).resolve()!=Path('/usr/bin/python3').resolve():
        raise Halt('use the pinned /usr/bin/python3 interpreter')
    config=verify_identity();reader=load_reader();initial=preflight(config,reader)
    if not args.execute:
        print(json.dumps(dict(status='PREFLIGHT_PASS_NOT_STARTED',remaining_count=len(config['remaining']),
                              known_consistency_failures=config['known_consistency_failures']),ensure_ascii=False))
        return 0
    work=HERE/'execution';work.mkdir()  # atomic guard against concurrent batch launches
    return run_sequence(config,initial,reader,work)

if __name__=='__main__':
    try: raise SystemExit(main())
    except (Exception,KeyboardInterrupt) as error:
        print('BATCH NOT STARTED: '+str(error),file=sys.stderr,flush=True)
        raise SystemExit(1)
