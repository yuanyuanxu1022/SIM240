#!/usr/bin/env python3
"""Independent Decimal80 reconstruction from raw result files; no frozen comparator import."""
from pathlib import Path
from decimal import Decimal,localcontext
import csv,hashlib,json,math
OUT=Path(__file__).resolve().parent
D=lambda x:Decimal(str(x))
def load(p):return json.loads(Path(p).read_text())
def kv(p):return dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    bundle=load(OUT/'grid_review/accepted_references16.json');frozen=load(OUT/'grid_review/three_grid_comparison.json')
    for p,h in bundle['bound_inputs_sha256'].items():assert sha(p)==h,p
    data={};source_rows=[]
    for r in bundle['rows']:
        path=Path(r['raw_output']);cfg=kv(path/'run_config.txt');result=kv(path/'result.txt')
        assert result['Keff_m3']==r['K_m3'] and cfg['run_id']==result['run_id']==r['run_id']
        key=(int(r['h_nm']),int(r['d_nm']),int(r['w_nm']),D(r['dx_nm']),r['direction'])
        assert key not in data;data[key]=D(result['Keff_m3'])
        source_rows.append({k:r[k] for k in ['planned_case_id','run_id','h_nm','d_nm','w_nm','P_nm','Ly_nm','dx_nm','direction','K_m3','acceptance_evidence','raw_output']})
    flat=[];p_diffs=[];gci_diffs=[]
    with localcontext() as ctx:
        ctx.prec=80
        for d in [25,120]:
            frozen_family=next(f for f in frozen['geometry_results'] if f['geometry_h_d_w_nm']==['75',str(d),'60'])
            seq={dr:[data[(75,d,60,dx,dr)] for dx in [D(5),D('2.5'),D('1.25')]] for dr in ['P','T']}
            seq['A']=[p/t for p,t in zip(seq['P'],seq['T'])]
            for label,q in seq.items():
                a,b,c=q;d01=a-b;d12=b-c;e02=abs(a-c)/c;e12=abs(b-c)/c;eta=D('0.0001')
                coarse_ok=abs(a-c)<=D('.01')*c;mid_ok=abs(b-c)<=D('.005')*c
                near=max(abs(d01),abs(d12))<=eta*c;monotone=d01*d12>0 and abs(d12)<abs(d01)
                status='FAIL_RESOLUTION_TARGET' if not (coarse_ok and mid_ok) else 'PASS_SENSITIVITY_NEAR_FLAT' if near else 'PASS_SENSITIVITY_MONOTONE' if monotone else 'INCONCLUSIVE_TREND'
                z=next(v for v in frozen_family['quantities'] if v['quantity']==label)
                assert z['status']==status
                assert abs(e02-D(z['E02']))<D('1e-55') and abs(e12-D(z['E12']))<D('1e-55')
                p=gci=ext=None
                if monotone and min(abs(d01),abs(d12))>eta*c:
                    ratio=abs(d01/d12);pd=ratio.ln()/D(2).ln();den=ratio-1;p=float(pd);gci=float(D('1.25')*abs(d12)/c/den);ext=float(c+(c-b)/den)
                    assert math.isclose(p,z['p'],rel_tol=1e-13,abs_tol=1e-13)
                    assert math.isclose(gci,z['GCI_fine'],rel_tol=1e-13,abs_tol=1e-15)
                    assert math.isclose(ext,z['Q_extrapolated'],rel_tol=1e-13)
                    p_diffs.append(abs(p-z['p']));gci_diffs.append(abs(gci-z['GCI_fine']))
                flat.append({'h_nm':75,'d_nm':d,'w_nm':60,'quantity':label,'Q_dx5':str(a),'Q_dx2p5':str(b),'Q_dx1p25':str(c),'E_5_to_1p25_percent':str(e02*100),'E_2p5_to_1p25_percent':str(e12*100),'coarse_limit_1percent_pass':coarse_ok,'middle_limit_0p5percent_pass':mid_ok,'monotone_contracting':monotone,'observed_order_conditional':p,'GCI_finest_conditional_percent':None if gci is None else gci*100,'status':status})
    for name,rows in [('three_grid_quantities6.csv',flat),('reference_sources16.csv',source_rows)]:
        with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    verdict={'ok':True,'precision':80,'source':'raw result.txt K, exact reference identities and bound hashes','quantities':6,'PASS_count':sum(r['status'].startswith('PASS') for r in flat),'FAIL_count':sum(r['status'].startswith('FAIL') for r in flat),'all_monotone_contracting':all(r['monotone_contracting'] for r in flat),'narrow_six_quantity_gate':'FAIL','maximum_p_absolute_difference':max(p_diffs),'maximum_GCI_absolute_difference':max(gci_diffs),'frozen_comparator_or_protocol_changed':False,'solver_executed':False,'records':flat}
    (OUT/'independent_grid_verification.json').write_text(json.dumps(verdict,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    assert verdict['PASS_count']==1 and verdict['FAIL_count']==5
    print(json.dumps({k:v for k,v in verdict.items() if k!='records'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
