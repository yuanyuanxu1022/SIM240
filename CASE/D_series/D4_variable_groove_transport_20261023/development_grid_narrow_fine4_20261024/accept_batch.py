#!/usr/bin/env python3
"""Explicit post-run independent scalar + VTK review. Never starts a simulation."""
from pathlib import Path
import argparse,json,subprocess,sys
from export_references import sha,load,kv
HERE=Path(__file__).resolve().parent;CASE=HERE.parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--batch',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    batch=a.batch.resolve();out=a.out.resolve()
    if batch!=CASE/'results/development_grid_narrow_fine4_20261024_v1':raise ValueError('only completed GRID_NARROW_FINE4 batch')
    completion=load(batch/'stage_completion.json')
    if completion['attempted_cases']!=4 or completion['exit_code']!=0:raise ValueError('batch incomplete or failed')
    # Avoid editing or nesting analysis within the raw result tree.
    if CASE/'results' in out.parents:raise ValueError('analysis must be outside raw results')
    available=int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
    if available<4*1024**3:raise ValueError('acceptance needs at least 4GiB available RAM')
    out.mkdir(parents=True,exist_ok=False)
    raw={str(p):sha(p) for p in batch.rglob('*') if p.is_file()}
    def run(label,command):
        with (out/(label+'.log')).open('w') as log:p=subprocess.run(['/usr/bin/time','-f','{"max_rss_kb":%M,"elapsed_seconds":%e}','-o',str(out/(label+'_resource.json'))]+command,cwd=CASE.parents[2],stdout=log,stderr=subprocess.STDOUT)
        (out/(label+'_exit_code.txt')).write_text(str(p.returncode)+'\n')
        if p.returncode:raise RuntimeError(label+' failed; inspect preserved log')
    run('scalar',[sys.executable,str(HERE/'analyze_results.py'),'--case',str(CASE),'--batch',str(batch),'--out',str(out/'analysis')])
    run('flow',['/usr/bin/pvpython',str(HERE/'check_flow_frames.py'),'--analysis',str(out/'analysis')])
    if not load(out/'analysis/flow_frames.json')['ok']:raise ValueError('flow not accepted')
    scalars=load(out/'analysis/scalar_results.json')
    cases={c['row']['run_id']:c for c in load(out/'analysis/field_cases.json')}
    for s in scalars:s['output']=cases[s['run_id']]['output']
    bound=dict(raw)
    for p in (out/'analysis').rglob('*'):
        if p.is_file():bound[str(p)]=sha(p)
    for k,h in load(out/'analysis/input_hashes.json').items():bound[k]=h
    for p in HERE.glob('*.py'):bound[str(p)]=sha(p)
    for p in [HERE/'PROTOCOL.md',HERE/'grid_policy.json',HERE/'release.json',CASE/'protocol/execution.json']:bound[str(p)]=sha(p)
    for k,h in bound.items():
        if sha(k)!=h:raise ValueError('data changed during acceptance')
    certificate={'schema':'D4_grid_narrow_fine4_independent_acceptance_v1','independent_acceptance':'PASS','batch_id':batch.name,'scalars':scalars,'bound_inputs_sha256':bound,'source_RESULT_PASS_preserved_false':True,'grid_accuracy_evaluated':False,'prediction_released':False}
    (out/'certificate.json').write_text(json.dumps(certificate,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'independent_acceptance':'PASS','cases':4,'grid_sensitivity_target':'NOT_EVALUATED','prediction_released':False}))
if __name__=='__main__':main()
