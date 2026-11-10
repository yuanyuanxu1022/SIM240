#!/usr/bin/env python3
"""Explicit user-started six-case development screen. Never chains later stages."""
from pathlib import Path
import argparse,csv,datetime,fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent
CASE=ROOT.parent
spec=importlib.util.spec_from_file_location('frozen_case_runner',CASE/'tools/run_case.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
sha=base.sha

def rows():return list(csv.DictReader((ROOT/'stage_cases.csv').open(encoding='utf-8-sig')))
def load_release():return json.loads((ROOT/'release.json').read_text())
def validate_row(row,release):
    if release.get('released') is not True:raise RuntimeError('stage not released')
    if row['planned_case_id'] not in release['allowed_case_ids']:raise RuntimeError('case outside six-case development screen')
    if row['role'] not in ['new_dev','linearity'] or row['blind_geometry']!='False':raise RuntimeError('role/blinding rejected')
    if row['h_nm']!='75' or row['d_nm']!='120' or row['w_nm']!='240' or row['dx_nm']!='5':raise RuntimeError('geometry outside screen')
    matches=[r for r in rows() if r['planned_case_id']==row['planned_case_id']]
    if len(matches)!=1 or matches[0]!=row:raise RuntimeError('row differs from frozen stage table')

def validate_binding(release):
    if not release.get('bound_inputs_sha256'):raise RuntimeError('missing binding')
    for p,h in release['bound_inputs_sha256'].items():
        if sha(p)!=h:raise RuntimeError('bound input changed: '+p)

def resource_check(policy):
    available=int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
    free=shutil.disk_usage(CASE).free
    if available<policy['minimum_available_RAM_bytes']:raise RuntimeError('insufficient available RAM')
    if free<policy['minimum_free_disk_bytes']:raise RuntimeError('insufficient free disk')
    return {'MemAvailable_bytes':available,'disk_free_bytes':free}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--batch-id',required=True)
    ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    policy=json.loads((ROOT/'policy.json').read_text());release=load_release()
    if a.batch_id!=policy['batch_id']:raise SystemExit('only the frozen batch ID is accepted')
    selected=[r for r in rows() if r['substage']=='screen'];assert len(selected)==6
    for row in selected:validate_row(row,release)
    validate_binding(release);resources=resource_check(policy)
    batch=CASE/'results'/a.batch_id
    if batch.exists():raise SystemExit('batch already exists; no overwrite or restart')
    if not a.execute:
        print(json.dumps({'stage':'development_screen','cases':6,'will_run':False,
            'case_ids':[r['planned_case_id'] for r in selected],'resources':resources},ensure_ascii=False));return
    # lock is held for the whole batch, including failure paths.
    with (ROOT/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        validate_binding(release);resource_check(policy);batch.mkdir(parents=True,exist_ok=False)
        (batch/'stage_manifest.json').write_text(json.dumps({'batch_id':a.batch_id,'stage':'development_screen',
            'started_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'case_ids':[r['planned_case_id'] for r in selected],'release_sha256':sha(ROOT/'release.json'),
            'resources_before':resources,'analysis_automatically_run':False,'next_stage_automatically_run':False},indent=2))
        progress=[];code=0
        try:
            for row in selected:
                validate_row(row,release);validate_binding(release);resource_check(policy)
                out,manifest=base.prepare(row,'steady',batch,a.batch_id)
                manifest['stage']='development_screen';manifest['stage_release_sha256']=sha(ROOT/'release.json')
                manifest['inputs_sha256'].update(release['bound_inputs_sha256'])
                manifest['inputs_sha256'][str(ROOT/'release.json')]=sha(ROOT/'release.json')
                (out/'run_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
                timed=['/usr/bin/time','-f','{"max_rss_kb":%M,"elapsed_seconds":%e}',
                    '-o',str(out/'resource_usage.json')]+manifest['command']
                with (out/'run.log').open('w') as log:
                    result=subprocess.run(timed,cwd=CASE,stdout=log,stderr=subprocess.STDOUT)
                code=result.returncode;(out/'exit_code.txt').write_text(str(code)+'\n')
                unchanged=all(sha(p)==h for p,h in manifest['inputs_sha256'].items())
                (out/'inputs_after.json').write_text(json.dumps({'unchanged':unchanged},indent=2))
                progress.append({'case_id':row['planned_case_id'],'output':str(out.relative_to(batch)),'exit_code':code})
                (batch/'stage_progress.json').write_text(json.dumps(progress,indent=2))
                if not unchanged:raise RuntimeError('bound inputs changed during case')
                if code:break
        except BaseException as error:
            (batch/'stage_error.txt').write_text(repr(error)+'\n');code=code or 2
        finally:(batch/'exit_code.txt').write_text(str(code)+'\n')
        print(json.dumps({'completed_cases':len(progress),'exit_code':code,'independent_acceptance':'pending',
            'next_stage_started':False}));raise SystemExit(code)
if __name__=='__main__':main()
