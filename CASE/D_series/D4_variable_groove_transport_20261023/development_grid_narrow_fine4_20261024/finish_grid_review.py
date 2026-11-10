#!/usr/bin/env python3
"""After explicit FINE4 acceptance, bind 16 references and report narrow three-grid gate."""
from pathlib import Path
import argparse,csv,json,subprocess,sys
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--certificate',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    cert=json.loads(a.certificate.read_text());expected={r['planned_case_id'] for r in csv.DictReader((HERE/'stage_cases.csv').open())}
    if cert.get('batch_id')!='development_grid_narrow_fine4_20261024_v1' or cert.get('independent_acceptance')!='PASS' or {r['planned_case_id'] for r in cert.get('scalars',[])}!=expected or len(cert['scalars'])!=4:raise ValueError('complete accepted FINE4 certificate required')
    if CASE/'results' in a.out.resolve().parents:raise ValueError('comparison outside raw result tree required')
    a.out.mkdir(parents=True,exist_ok=False)
    def call(label,cmd):
        with (a.out/(label+'.log')).open('w') as f:p=subprocess.run(cmd,cwd=PROJECT,stdout=f,stderr=subprocess.STDOUT)
        (a.out/(label+'_exit_code.txt')).write_text(str(p.returncode)+'\n')
        if p.returncode:raise RuntimeError(label+' failed; preserve logs, no grid PASS')
    bundle=a.out.resolve()/'accepted_references16.json';comparison=a.out.resolve()/'three_grid_comparison.json'
    call('export',[sys.executable,str(HERE/'export_references.py'),'--certificate',str(a.certificate.resolve()),'--output',str(bundle)])
    call('compare',[sys.executable,str(HERE/'compare_grid.py'),'--bundle',str(bundle),'--output',str(comparison)])
    result=json.loads(comparison.read_text());narrow=[f for f in result['geometry_results'] if f['geometry_h_d_w_nm'][2]=='60']
    statuses=[f['status'] for f in narrow]
    status='PASS' if len(narrow)==2 and all(s=='PASS' for s in statuses) else 'FAIL' if 'FAIL' in statuses else 'INCONCLUSIVE' if 'INCONCLUSIVE' in statuses else 'INCOMPLETE_OR_REFERENCE_INVALID'
    summary={'narrow_six_quantity_gate':status,'narrow_geometry_results':narrow,'all_three_geometry_grid_target':result['GRID_SENSITIVITY_TARGET'],'wide_1p25_results_still_missing':True,'next_wide_run_permit_generated':False,'prediction_released':False,'protocol_tolerances_changed':False,'solver_executed':False}
    (a.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='narrow_geometry_results'}))
if __name__=='__main__':main()
