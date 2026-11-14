#!/usr/bin/env python3
"""Read-only release/receipt/field-integral checks and summary arithmetic.

No PDE solve, re-freeze, assessor write-back or qualification promotion.
Run with the environment recorded by the FEM package.
"""
import csv
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PKG = ROOT / 'CASE/paper1_fem_stokes_reference_v2'
REPORT = ROOT / 'docs/reports/PAPER1_fem_v2_results_20261114'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    return json.loads(p.read_text())
def write(name, obj):
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

tracked = [p for p in PKG.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
tracked += [REPORT/'PAIR_TABLE_v2.csv',REPORT/'ASSESSMENT.csv',REPORT/'REPORT.md']
before = {str(p.relative_to(ROOT)):sha(p) for p in tracked}
spec = importlib.util.spec_from_file_location('receipt',PKG/'receipt.py')
receipt = importlib.util.module_from_spec(spec);spec.loader.exec_module(receipt)
release = receipt.verify_release()
field_rows=[]; cases=[]; verification_rows=[]
for p in sorted(PKG.glob('runs/*/SOLVE_RECEIPT.json')):
    s=read(p);vpath=p.parent/'VERIFY_RECEIPT.json';v=read(vpath)
    assert s['state']=='SOLVED' and s['exit_code']==0
    assert s['release_sha256']==release['release_sha256']==v['release_sha256']
    assert v['solve_receipt_sha256']==sha(p) and v['solve_receipt_unchanged']
    assert not v['gate_problems'] and not v['additive_gate_problems'] and not v['provenance_problems']
    assert v['reference_status']=='REFERENCE_CANDIDATE'
    for level in s['levels']:
        folder=PKG/'results'/s['case'];meta_path=folder/level['json_file'];field=folder/level['field_file']
        assert sha(meta_path)==level['json_sha256']
        assert sha(field)==level['field_sha256_rehashed']==level['field_sha256_solver']
        meta=read(meta_path)
        with np.load(field,allow_pickle=False) as z:
            assert all(np.isfinite(z[k]).all() for k in ['p','ux','uz','pressure'])
            pnt,tri,ux=z['p'],z['t'],z['ux']
            meshhash=hashlib.sha256(np.ascontiguousarray(pnt,dtype=np.float64).tobytes()+np.ascontiguousarray(tri,dtype=np.int64).tobytes()).hexdigest()
            assert meshhash==level['mesh_sha256']
            edges=np.sort(np.concatenate([tri[[0,1]].T,tri[[1,2]].T,tri[[0,2]].T]),axis=1)
            unique,inv=np.unique(edges,axis=0,return_inverse=True);nt=tri.shape[1]
            edge_ids=inv.reshape(3,nt).T+pnt.shape[1]
            a=pnt[:,tri[1]]-pnt[:,tri[0]];b=pnt[:,tri[2]]-pnt[:,tri[0]]
            area=np.abs(a[0]*b[1]-a[1]*b[0])/2
            # Exact P2 triangle integral: each edge shape integrates to area/3;
            # all vertex shapes integrate to zero.
            kval=math.fsum(area*np.sum(ux[edge_ids],axis=1)/3)/240*1e-27
            saved=next(x['K_recomputed_m3'] for x in v['levels'] if x['dx_nm']==level['dx_nm'])
            assert abs(kval/saved-1)<1e-11
            field_rows.append({'case':s['case'],'run_id':s['run_id'],'dx_nm':level['dx_nm'],
                               'K_exact_P2_integral_m3':kval,'K_vs_receipt_relative':kval/saved-1,
                               'field_sha256':sha(field),'mesh_sha256':meshhash})
    verification_rows+=v['levels']
    cases.append({'case':s['case'],'run_id':s['run_id'],'solve_receipt_sha256':sha(p),
                  'verify_receipt_sha256':sha(vpath),'wall_seconds':s['wall_seconds'],
                  'solve_exit_code':s['exit_code'],'reference_status':v['reference_status']})
assert len(cases)==12 and len(field_rows)==36
write('FIELD_READBACK.json',field_rows);write('RUN_RECORDS.json',cases)

with (REPORT/'PAIR_TABLE_v2.csv').open() as f:pairs=list(csv.DictReader(f))
complete=[p for p in pairs if p['K_T_m3']]
cols=['T_OpenLB_vs_ref_percent','T_LC_vs_ref_percent','T_V2_vs_ref_percent',
      'LC_A_vs_ref_percent','V2_A_vs_ref_percent','LC_beta_vs_ref_deg','V2_beta_vs_ref_deg']
stats={}
for col in cols:
    vals=[float(p[col]) for p in complete]
    stats[col]={'n':len(vals),'signed_mean':statistics.mean(vals),'mean_absolute':statistics.mean(map(abs,vals)),
                'range':[min(vals),max(vals)],'positive':sum(x>0 for x in vals),'negative':sum(x<0 for x in vals)}
worse_A=[p['geometry'] for p in complete if abs(float(p['V2_A_vs_ref_percent']))>abs(float(p['LC_A_vs_ref_percent']))]
worse_angle=[p['geometry'] for p in complete if abs(float(p['V2_beta_vs_ref_deg']))>abs(float(p['LC_beta_vs_ref_deg']))]
lc_A_negative=[p['geometry'] for p in complete if float(p['LC_A_vs_ref_percent'])<0]
depth=[]
for h in [50,75,125]:
    pts=sorted([p for p in complete if p['geometry'].startswith(f'h{h}/')],key=lambda p:int(p['geometry'].split('/d')[1]))
    vals=[float(p['K_T_m3']) for p in pts];k75=next(float(p['K_T_m3']) for p in pts if p['geometry'].endswith('/d75'))
    depth.append({'h_nm':h,'K_d25_to_d120_percent':(vals[-1]/vals[0]-1)*100,
                  'K_d75_to_d120_percent':(vals[-1]/k75-1)*100})
vs=[read(p) for p in PKG.glob('runs/*/VERIFY_RECEIPT.json')]
d21=[v['levels'][1]['K_change_from_coarser_recomputed_percent'] for v in vs]
d32=[v['levels'][2]['K_change_from_coarser_recomputed_percent'] for v in vs]
res=[x['direct_relative_residual_recomputed'] for v in vs for x in v['levels']]
margins={'d21_percent_range':[min(d21),max(d21)],'d32_percent_range':[min(d32),max(d32)],
         'max_recomputed_residual':max(res),'threshold_to_worst_ratio':{'d21':1/max(d21),'d32':.5/max(d32),'residual':1e-10/max(res)}}
write('STATISTICS.json',{'geometries':len(pairs),'actual_direction_comparisons':sum(bool(p['K_P_m3']) for p in pairs)+sum(bool(p['K_T_m3']) for p in pairs),
      'paired_geometries':len(complete),'summary':stats,'LC_A_negative_geometries':lc_A_negative,
      'V2_A_worse_geometries':worse_A,'V2_angle_worse_geometries':worse_angle,'depth_sensitivity':depth,'margins':margins})
after={str(p.relative_to(ROOT)):sha(p) for p in tracked}
assert after==before
write('CHECKS.json',{'release_sha256':release['release_sha256'],'frozen_files_checked':len(release['files']),
      'solve_verify_pairs_checked':len(cases),'field_and_mesh_hashes_checked':len(field_rows),
      'independent_exact_P2_K_integrals':len(field_rows),'protected_files':len(before),'changed_inputs':[],
      'full_PDE_residuals_reassembled_this_turn':False,'new_solves':0,'formal_reference_promoted':False})
write('INPUT_SNAPSHOT.json',before)
print(json.dumps({'release':release['release_sha256'],'fields':len(field_rows),'statistics':stats,'worse_A':worse_A,'margins':margins},ensure_ascii=False))
