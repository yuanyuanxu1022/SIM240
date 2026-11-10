"""Pure completed-grid sensitivity arithmetic, without solver imports or launch.

CLI input is an independently accepted-table export; acceptance flags are declarations,
not a replacement for review of raw numerical/provenance/field evidence.
"""
from pathlib import Path
import argparse,csv,json,math
HERE=Path(__file__).resolve().parent

def quantity(q,policy):
    if len(q)!=3 or not all(math.isfinite(x) and x>0 for x in q):
        return dict(status='INVALID_QUANTITY')
    q0,q1,q2=q;d01=q0-q1;d12=q1-q2
    e02=abs(q0/q2-1);e12=abs(q1/q2-1);eta=policy['near_flat_relative_diagnostic_scale']
    out=dict(values_coarse_to_fine=q,E02=e02,E12=e12,d01=d01,d12=d12,p=None,Q_extrapolated=None,GCI_fine=None,GCI_middle=None)
    if e02>policy['coarse_to_finest_relative_limit'] or e12>policy['middle_to_finest_relative_limit']:
        out['status']='FAIL_RESOLUTION_TARGET'
    elif max(abs(d01),abs(d12))/q2<=eta:out['status']='PASS_SENSITIVITY_NEAR_FLAT'
    elif d01*d12>0 and abs(d12)<abs(d01):out['status']='PASS_SENSITIVITY_MONOTONE'
    else:out['status']='INCONCLUSIVE_TREND'
    if d01*d12>0 and abs(d12)<abs(d01) and min(abs(d01),abs(d12))/q2>eta:
        p=math.log(abs(d01/d12))/math.log(2);den=math.expm1(p*math.log(2))
        out.update(p=p,Q_extrapolated=q2+(q2-q1)/den,GCI_fine=policy['gci_safety_factor']*abs(d12)/(q2*den),GCI_middle=policy['gci_safety_factor']*abs(d01)/(q1*den))
    return out

def evaluate(rows,policy):
    expected={(h,d,w,dx,dr) for h,d,w in policy['geometries_h_d_w_nm'] for dx in policy['dx_nm_coarse_to_fine'] for dr in ('P','T')}
    records={};errors=[]
    for r in rows:
        key=tuple(float(r[k]) for k in ('h_nm','d_nm','w_nm','dx_nm'))+(r['direction'],)
        if key not in expected:errors.append(dict(issue='unexpected_key',key=key));continue
        if key in records:errors.append(dict(issue='duplicate_key',key=key));continue
        if any(str(r.get(k,'')).lower()!='true' for k in ('numerical_gate_pass','geometry_pass','independent_reference_accepted')):
            errors.append(dict(issue='reference_not_independently_accepted',key=key));continue
        try:k=float(r['K_m3'])
        except (KeyError,ValueError):k=float('nan')
        if not math.isfinite(k) or k<=0:errors.append(dict(issue='invalid_K',key=key));continue
        if not r.get('run_id') or not r.get('acceptance_evidence'):errors.append(dict(issue='missing_reference_identity',key=key));continue
        records[key]=k
    missing=sorted(expected-set(records));result=dict(protocol_id=policy['protocol_id'],errors=errors,missing=missing,quantities=[])
    if missing or errors:
        result['GRID_SENSITIVITY_TARGET']='INCOMPLETE_OR_REFERENCE_INVALID';return result
    for h,d,w in policy['geometries_h_d_w_nm']:
        series={dr:[records[(h,d,w,dx,dr)] for dx in policy['dx_nm_coarse_to_fine']] for dr in ('P','T')}
        series['A']=[p/t for p,t in zip(series['P'],series['T'])]
        for label,q in series.items():result['quantities'].append(dict(h_nm=h,d_nm=d,w_nm=w,quantity=label,**quantity(q,policy)))
    statuses=[r['status'] for r in result['quantities']]
    result['GRID_SENSITIVITY_TARGET']='PASS' if all(s.startswith('PASS_SENSITIVITY_') for s in statuses) else ('FAIL' if 'FAIL_RESOLUTION_TARGET' in statuses else 'INCONCLUSIVE')
    result['physical_truth_or_whole_domain_accuracy_established']=False
    return result

def selfcheck(policy):
    tests=[]
    for label,q,want in [
        ('monotone_good',[1.008,1.002,1.0005],'PASS_SENSITIVITY_MONOTONE'),
        ('large_coarse_error',[1.03,1.002,1.0005],'FAIL_RESOLUTION_TARGET'),
        ('large_middle_error',[1.008,1.006,1.0],'FAIL_RESOLUTION_TARGET'),
        ('oscillatory_small',[1.004,.998,1.0],'INCONCLUSIVE_TREND'),
        ('noncontracting',[1.005,1.004,1.0],'INCONCLUSIVE_TREND'),
        ('flat',[1.,1.,1.],'PASS_SENSITIVITY_NEAR_FLAT'),
        ('tiny_oscillation',[1.000001,.999999,1.0],'PASS_SENSITIVITY_NEAR_FLAT'),
        ('nonfinite',[float('nan'),1.,1.],'INVALID_QUANTITY')]:
        got=quantity(q,policy);assert got['status']==want,(label,got);tests.append(label)
    q=[1+.002*(dx/1.25)**2 for dx in (5,2.5,1.25)]
    got=quantity(q,policy);assert math.isclose(got['p'],2,abs_tol=1e-12) and math.isclose(got['Q_extrapolated'],1.,abs_tol=1e-12);tests.append('manufactured_order_two_extrapolation')
    rs=[]
    for h,d,w in policy['geometries_h_d_w_nm']:
        for dx in policy['dx_nm_coarse_to_fine']:
            for dr in ('P','T'):
                rs.append(dict(h_nm=h,d_nm=d,w_nm=w,dx_nm=dx,direction=dr,K_m3=(2 if dr=='P' else 1)*(1+.0005*(dx/1.25)**2),numerical_gate_pass='true',geometry_pass='true',independent_reference_accepted='true',run_id='synthetic',acceptance_evidence='synthetic'))
    got=evaluate(rs,policy);assert got['GRID_SENSITIVITY_TARGET']=='PASS' and len(got['quantities'])==9;tests.append('complete_nine_quantity_pairing')
    for label,bad in [('missing',rs[:-1]),('duplicate',rs+[rs[0]]),('invalid_reference',[dict(r,independent_reference_accepted='false') if i==0 else r for i,r in enumerate(rs)])]:
        assert evaluate(bad,policy)['GRID_SENSITIVITY_TARGET']=='INCOMPLETE_OR_REFERENCE_INVALID';tests.append(label)
    # Direction errors can cancel in A; still enforce each K gate independently.
    bad=[dict(r,K_m3=float(r['K_m3'])*1.03) if float(r['dx_nm'])==5 else r for r in rs]
    assert evaluate(bad,policy)['GRID_SENSITIVITY_TARGET']=='FAIL';tests.append('anisotropy_cancellation_cannot_hide_K_failure')
    return dict(ok=True,synthetic_checks=len(tests),checks=tests,real_grid_results_read=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--selfcheck',action='store_true');a=ap.parse_args()
    policy=json.loads((HERE/'grid_policy.json').read_text())
    if a.selfcheck:result=selfcheck(policy)
    elif a.input:result=evaluate(list(csv.DictReader(a.input.open())),policy)
    else:raise SystemExit('Provide --selfcheck or an independently accepted --input table.')
    if a.output:
        with a.output.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    else:print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
if __name__=='__main__':main()
