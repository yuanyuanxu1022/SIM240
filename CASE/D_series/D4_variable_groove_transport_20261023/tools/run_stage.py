#!/usr/bin/env python3
"""User-started foundation stage only. Never analyze or enter another stage."""
from pathlib import Path
import argparse
import datetime
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('runner',ROOT/'tools/run_case.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['foundation'],required=True)
    parser.add_argument('--batch-id',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',args.batch_id):raise SystemExit('invalid batch ID')
    rows=[r for r in run.candidates() if r['role'] in ['regression','smooth']]
    assert len(rows)==8
    release=json.loads((ROOT/'evidence/formal_run_release.json').read_text())
    for row in rows:run.validate_release(row,release)
    if not args.execute:
        print(json.dumps({'stage':args.stage,'cases':len(rows),'will_run':False,
                          'case_ids':[r['planned_case_id'] for r in rows]},ensure_ascii=False));return
    batch=ROOT/'results'/args.batch_id
    batch.mkdir(parents=True,exist_ok=False)
    (batch/'stage_manifest.json').write_text(json.dumps({
        'batch_id':args.batch_id,'stage':args.stage,'started_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'case_ids':[r['planned_case_id'] for r in rows],
        'release_sha256':run.sha(ROOT/'evidence/formal_run_release.json'),
        'analysis_automatically_run':False,'next_stage_automatically_run':False},ensure_ascii=False,indent=2))
    results=[];code=0
    try:
        for row in rows:
            out,exit_code=run.launch(row,'steady',batch,args.batch_id)
            results.append({'case_id':row['planned_case_id'],'output':str(out.relative_to(batch)),'exit_code':exit_code})
            (batch/'stage_progress.json').write_text(json.dumps(results,indent=2))
            if exit_code:
                code=exit_code;break
    except Exception as error:
        (batch/'stage_error.txt').write_text(repr(error)+'\n');code=2
    finally:
        (batch/'exit_code.txt').write_text(str(code)+'\n')
    print(json.dumps({'batch_id':args.batch_id,'completed_cases':len(results),
                      'stage_exit_code':code,'numerical_and_physical_acceptance':'not independently evaluated',
                      'next_stage_started':False},ensure_ascii=False))
    raise SystemExit(code)


if __name__=='__main__':main()
