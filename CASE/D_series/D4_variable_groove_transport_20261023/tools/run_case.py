#!/usr/bin/env python3
"""One explicit case action. Defaults to no action; never chains simulation stages."""
from pathlib import Path
import argparse
import csv
import datetime
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[2]
LIB=Path(os.environ.get('SIM240_OLB_ROOT','/home/dell/openlb'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def kv(path):
    return dict(line.split('=',1) for line in Path(path).read_text().splitlines() if '=' in line)


def candidates():
    return list(csv.DictReader((ROOT/'protocol/candidate_cases.csv').open(encoding='utf-8-sig')))


def validate_release(row,release):
    if release.get('released') is not True:
        raise RuntimeError('formal calculation has not been released')
    if row['planned_case_id'] not in release.get('allowed_case_ids',[]):
        raise RuntimeError('this case is outside the separately released stage')
    for path,expected in release.get('bound_inputs_sha256',{}).items():
        if sha(path)!=expected:raise RuntimeError('release binding changed: '+path)
    if not release.get('bound_inputs_sha256'):
        raise RuntimeError('release must bind its actual inputs')


def prepare(row,mode,base,tag):
    protocol=json.loads((ROOT/'protocol/execution.json').read_text())
    ident=row['planned_case_id'].replace('CAND_','D4_',1)+'_'+tag
    out=Path(base).resolve()/ident/mode
    out.mkdir(parents=True,exist_ok=False)
    config={'mode':mode,'run_id':ident,'output_directory':str(out),'direction':row['direction'],
            'dx_nm':row['dx_nm'],'h_nm':row['h_nm'],'d_nm':row['d_nm'],
            'w_nm':row['w_nm'],'period_nm':row['P_nm'],'Ly_nm':row['Ly_nm'],
            'nu_m2_s':row['nu_m2_s'],'acceleration_m_s2':row['acceleration_m_s2'],
            'window_tstar':protocol['window_tstar'],'max_time_H_diffusion':protocol['max_time_H_diffusion'],
            'frame_tstar':','.join(str(v) for v in protocol['frame_tstar'])}
    path=out/'run_config.txt'
    path.write_text(''.join(f'{k}={v}\n' for k,v in config.items()))
    binary=ROOT/'build/variable_groove_transport'
    bound=[ROOT/'src/variable_groove_transport.cpp',ROOT/'src/Makefile',ROOT/'tools/run_case.py',
           ROOT/'protocol/execution.json',ROOT/'protocol/candidate_cases.csv',binary,path]
    manifest={'run_id':ident,'mode':mode,'planned_case_id':row['planned_case_id'],
              'formal_simulation':mode=='steady','timestamp_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'inputs_sha256':{str(p):sha(p) for p in bound},'command':[str(binary),str(path)],
              'OpenLB_build_environment':json.loads((ROOT/'evidence/build_environment.json').read_text()),
              'model_prediction_data':row['blind_geometry']=='True'}
    (out/'run_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    (out/'run_manifest.txt').write_text(f'run_id={ident}\nmode={mode}\nconfig_sha256={sha(path)}\nbinary_sha256={sha(binary)}\n')
    return out,manifest


def launch(row,mode,base,tag,timeout=180):
    out,manifest=prepare(row,mode,base,tag)
    try:
        timed=['/usr/bin/time','-f','{"max_rss_kb":%M,"elapsed_seconds":%e}',
               '-o',str(out/'resource_usage.json')]+manifest['command']
        with (out/'run.log').open('w') as log:
            result=subprocess.run(timed,stdout=log,stderr=subprocess.STDOUT,
                                  cwd=ROOT,timeout=timeout if mode!='steady' else None)
        code=result.returncode
    except subprocess.TimeoutExpired:
        code=124
        (out/'timeout.txt').write_text('Timed out; no successful result is implied.\n')
    (out/'exit_code.txt').write_text(str(code)+'\n')
    unchanged=all(sha(p)==h for p,h in manifest['inputs_sha256'].items())
    (out/'inputs_after.json').write_text(json.dumps({'unchanged':unchanged},indent=2))
    if not unchanged:raise RuntimeError('input/source/binary changed during action')
    return out,code


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--case-id',required=True)
    ap.add_argument('--mode',choices=['describe','precheck','initialize','steady'],required=True)
    ap.add_argument('--output-root',type=Path,required=True)
    ap.add_argument('--tag',default=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    ap.add_argument('--execute-steady',action='store_true')
    a=ap.parse_args()
    selected=[r for r in candidates() if r['planned_case_id']==a.case_id]
    if len(selected)!=1:raise SystemExit('case ID must match exactly one row of the main table')
    row=selected[0]
    if a.mode=='steady':
        if not a.execute_steady:raise SystemExit('steady requires an explicit --execute-steady flag')
        if row['new_steady_solve_proposed']!='True':raise SystemExit('legacy data rows are not new run authorizations')
        ready=ROOT/'evidence/formal_run_release.json'
        if not ready.exists():
            raise SystemExit('formal calculation has not been released; preparation checks are not numerical acceptance')
        release=json.loads(ready.read_text())
        try:validate_release(row,release)
        except RuntimeError as error:raise SystemExit(str(error))
        if row['blind_geometry']=='True' and not (ROOT/'protocol/model_lock.json').exists():
            raise SystemExit('prediction geometry requires a frozen model/prediction file before any result or field')
    out,code=launch(row,a.mode,a.output_root,a.tag)
    print(json.dumps({'output':str(out),'exit_code':code,'mode':a.mode},ensure_ascii=False))
    raise SystemExit(code)


if __name__=='__main__':main()
