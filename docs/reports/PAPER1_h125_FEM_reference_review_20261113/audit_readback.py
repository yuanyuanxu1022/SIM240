#!/usr/bin/env python3
"""Read saved fields only. No solve, no edits to CASE or existing evidence."""
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FEM = ROOT / 'CASE/paper1_fem_stokes_pilot_v1'
FVM = ROOT / 'CASE/paper1_fvm_stokes_reference_v2'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def read(p):
    return json.loads(p.read_text())

def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

protected = sorted(set(FEM.glob('*.py')) | set(FEM.glob('*.md')) |
                   set(FEM.glob('results/*/*')))
protected = [p for p in protected if p.is_file()]
protected += [FVM/'release_manifest.json', ROOT/'docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv']
protected += [ROOT/'docs/reports'/p for p in [
    'SIM240_中文稿_导师审阅版_20261022.md',
    'SIM240_First_Paper_English_20261028.md',
    'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
    'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
    'PAPER1_conclusions_current_20261109.md']]
before = {str(p.relative_to(ROOT)):sha(p) for p in protected}
save('INPUT_SNAPSHOT.json', before)

# Exact integral of P2 on a straight triangle: vertex shape functions integrate
# to zero and each edge-midpoint shape function integrates to area/3.
# Construct sorted edges independently, without calling the FEM solver.
levels=[]
for path in sorted(FEM.glob('results/*/dx_*nm.json')):
    meta=read(path)
    field=path.parent/meta['field_file']
    assert sha(field)==meta['field_sha256'], str(field)
    with np.load(field, allow_pickle=False) as z:
        p,t,u=z['p'],z['t'],z['ux']
        assert all(np.isfinite(z[k]).all() for k in ('p','ux','uz','pressure'))
        assert meta['h_nm']==float(z['h']) and meta['d_nm']==float(z['d'])
        assert meta['dx_nm']==float(z['dx_nm']) and meta['direction']==str(z['direction'])
        edges=np.sort(np.concatenate([t[[0,1]].T,t[[1,2]].T,t[[0,2]].T]),axis=1)
        unique,inverse=np.unique(edges,axis=0,return_inverse=True)
        n=t.shape[1]; edge_ids=inverse.reshape(3,n).T+p.shape[1]
        v1=p[:,t[1]]-p[:,t[0]]; v2=p[:,t[2]]-p[:,t[0]]
        ar=np.abs(v1[0]*v2[1]-v1[1]*v2[0])/2
        assert np.all(ar>0)
        assert np.all((p[0]>=0)&(p[0]<=240)&(p[1]>=0)&(p[1]<=meta['h_nm']+meta['d_nm']))
        center=p[:,t].mean(axis=1)
        assert not np.any((center[0]>120)&(center[1]<meta['d_nm']))
        area=math.fsum(ar)
        exact_area=240*meta['h_nm']+120*meta['d_nm']
        assert abs(area/exact_area-1)<1e-12
        integ=math.fsum(ar*np.sum(u[edge_ids],axis=1)/3)
        kval=integ/240*1e-27
        assert abs(kval/meta['K_m3']-1)<1e-11
        levels.append({'case_id':meta['case_id'],'dx_nm':meta['dx_nm'],
                       'triangles':n,'area_nm2':area,'K_independent_m3':kval,
                       'relative_difference_from_solver':kval/meta['K_m3']-1,
                       'field_sha256':sha(field),'metadata_sha256':sha(path),
                       'field_keys':list(z.files),
                       'has_run_source_binding':any(k in meta for k in ['source_sha256','run_id','source_manifest_sha256'])})
save('ALL_FIELDS_READBACK.json',levels)
print('Independent exact P2 integrations:',len(levels),flush=True)

# Reuse only the archived verifier's read-only entry, never verify_case (writes).
spec=importlib.util.spec_from_file_location('saved_fem_verifier', FEM/'verify_results.py')
v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
checks=[]
for dx in (5,2.5,1.25):
    row=v.reintegrate(FEM/f'results/h125_d120_T/dx_{dx:g}nm.json')
    checks.append(row)
    print('Reassembled h125T saved field:',dx, row['direct_relative_residual_recomputed'],flush=True)
save('H125_REASSEMBLED_READBACK.json',checks)

fvm_levels=[]
for level in ('coarse','mid','fine','tight'):
    case=FVM/f'prepared/h125_d120_P_{level}'
    meta=read(case/'case.json'); receipt=read(case/'referenceEvidence/receipt.json')
    hashes={}
    for k,folder in [('evidence_sha256',case/'referenceEvidence'),('native_field_sha256',case),
                     ('mesh_sha256',case/'constant/polyMesh'),('runtime_logs_sha256',case/'runtime')]:
        for name,expected in receipt[k].items():
            actual=sha(folder/name); assert actual==expected, str(folder/name)
            hashes[str((folder/name).relative_to(ROOT))]=actual
    values=[]; volumes=[]; powers=[]
    with (case/'referenceEvidence/cells.csv').open() as f:
        for r in csv.DictReader(f):
            values.append(float(r['Uy_m_s'])*float(r['V_m3']))
            volumes.append(float(r['V_m3']))
            powers.append(float(r['diss_per_mass_m2_s3'])*float(r['V_m3']))
    integral=math.fsum(values)
    K=meta['nu_m2_s']/meta['acceleration_m_s2']*integral/meta['Aplan_m2']
    assert len(values)==meta['expected_cells'] and receipt['independent_exit_code']==0
    assert abs(math.fsum(volumes)/meta['expected_V_m3']-1)<1e-10
    fvm_levels.append({'level':level,'K_recomputed_m3':K,'run_id':receipt['run_id'],
        'receipt_sha256':sha(case/'referenceEvidence/receipt.json'),
        'bound_files_verified':len(hashes),'bound_files':hashes,
        'power_percent':abs(math.fsum(powers)/(meta['acceleration_m_s2']*integral)-1)*100,
        'case':meta,'source_manifest_sha256':receipt['source_manifest_sha256']})
save('FVM_P_SAVED_EVIDENCE_READBACK.json', fvm_levels)

kp=next(r['K_recomputed_m3'] for r in fvm_levels if r['level']=='fine')
kt=checks[-1]['K_recomputed_m3']
maps={}
with (ROOT/'docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv').open() as f:
    for r in csv.DictReader(f):
        if (int(r['h_nm']),int(r['d_nm']))==(125,120):
            assert sha(ROOT/r['result_path'])==r['result_sha256']
            maps[r['direction']]=r
pair={'status':'CANDIDATE_ONLY_PENDING_FORMAL_REFERENCE_DECISION',
      'P_method':'qualified FVM','T_method':'FEM pilot',
      'K_P_m3':kp,'K_T_m3':kt,'A_P_over_T':kp/kt,
      'beta_deg_from_groove_axis_for_45deg_drive':math.degrees(math.atan2(kt,kp)),
      'methods':{}}
for method in ['OpenLB5','LC','V2']:
    vals={}
    for direction in ('P','T'):
        r=maps[direction]; klb=float(r['K_DNS_m3'])
        val=klb if method=='OpenLB5' else (float(r['K_model_m3']) if method=='LC' else klb*(1+float(r['V2_rounded_residual_pct'])/100))
        vals[direction]=val
    a=vals['P']/vals['T']; beta=math.degrees(math.atan2(vals['T'],vals['P']))
    pair['methods'][method]={'K_P_m3':vals['P'],'K_T_m3':vals['T'],
        'P_signed_deviation_percent':(vals['P']/kp-1)*100,'T_signed_deviation_percent':(vals['T']/kt-1)*100,
        'A':a,'A_relative_deviation_percent':(a/pair['A_P_over_T']-1)*100,
        'beta_deg':beta,'beta_minus_reference_deg':beta-pair['beta_deg_from_groove_axis_for_45deg_drive']}
pair['V2_source']='Reconstructed from map36 residual for the published rounded coefficients; no refit.'
save('CANDIDATE_PAIR.json',pair)
after={str(p.relative_to(ROOT)):sha(p) for p in protected}
save('CHECKS.json',{'protected_inputs':len(before),'changed_inputs':[p for p in before if before[p]!=after[p]],
     'all_saved_fields_integrated':len(levels),'h125_fields_reassembled':len(checks),
     'fvm_P_levels_integrated':len(fvm_levels),'new_solves':0,'qualification_flags_changed':False})
assert before==after
print(json.dumps(pair,ensure_ascii=False),flush=True)
