"""Decimal boundary decisions; explicit per-geometry and final scopes. No solver."""
from decimal import Decimal,localcontext
from pathlib import Path
import argparse,csv,json,math
HERE=Path(__file__).resolve().parent
D=lambda x:Decimal(str(x))

def quantity(q,policy):
    with localcontext() as ctx:
        ctx.prec=60
        q=[D(x) for x in q]
        if len(q)!=3 or any(not v.is_finite() or v<=0 for v in q):raise ValueError('invalid quantity')
        a,b,c=q;d01=a-b;d12=b-c;eta=D(policy['near_flat_relative_diagnostic_scale'])
        e02=abs(a-c)/c;e12=abs(b-c)/c
        # Multiplication comparisons preserve exact decimal equality for K inputs.
        if abs(a-c)>D(policy['coarse_to_finest_relative_limit'])*c or abs(b-c)>D(policy['middle_to_finest_relative_limit'])*c:status='FAIL_RESOLUTION_TARGET'
        elif max(abs(d01),abs(d12))<=eta*c:status='PASS_SENSITIVITY_NEAR_FLAT'
        elif d01*d12>0 and abs(d12)<abs(d01):status='PASS_SENSITIVITY_MONOTONE'
        else:status='INCONCLUSIVE_TREND'
        out=dict(values_coarse_to_fine=[str(v) for v in q],E02=str(e02),E12=str(e12),status=status,p=None,Q_extrapolated=None,GCI_fine=None,GCI_middle=None)
        if d01*d12>0 and abs(d12)<abs(d01) and min(abs(d01),abs(d12))>eta*c:
            p=math.log(float(abs(d01/d12)))/math.log(2);den=math.expm1(p*math.log(2));out.update(p=p,Q_extrapolated=float(c)+(float(c)-float(b))/den,GCI_fine=float(D(policy['gci_safety_factor'])*abs(d12)/c)/den,GCI_middle=float(D(policy['gci_safety_factor'])*abs(d01)/b)/den)
        return out

def evaluate(rows,policy):
    geoms=[tuple(D(v) for v in g) for g in policy['geometries_h_d_w_nm']]
    expected={g+(D(dx),dr) for g in geoms for dx in policy['dx_nm_coarse_to_fine'] for dr in ('P','T')}
    records={};errors=[]
    for r in rows:
        try:
            key=tuple(D(r[k]) for k in ['h_nm','d_nm','w_nm','dx_nm'])+(r['direction'],)
            if key not in expected or key in records:raise ValueError('unexpected or duplicate grid key')
            if any(str(r[k]).lower()!='true' for k in ['numerical_gate_pass','geometry_pass','independent_reference_accepted']):raise ValueError('unaccepted reference')
            k=D(r['K_m3'])
            if not k.is_finite() or k<=0:raise ValueError('invalid K')
            if not r.get('run_id') or not r.get('acceptance_evidence') or not r.get('evidence_bundle_sha256'):raise ValueError('missing bound exporter provenance')
            records[key]=k
        except (ValueError,KeyError,ArithmeticError) as e:errors.append(str(e))
    families=[]
    with localcontext() as ctx:
        ctx.prec=60
        for g in geoms:
            missing=[key for key in expected if key[:3]==g and key not in records]
            family={'geometry_h_d_w_nm':[str(v) for v in g],'missing':[[str(v) for v in key] for key in sorted(missing)],'quantities':[],'status':'INCOMPLETE_OR_REFERENCE_INVALID'}
            if not missing and not errors:
                series={dr:[records[g+(D(dx),dr)] for dx in policy['dx_nm_coarse_to_fine']] for dr in ('P','T')};series['A']=[p/t for p,t in zip(series['P'],series['T'])]
                family['quantities']=[dict(quantity=label,**quantity(values,policy)) for label,values in series.items()]
                statuses=[q['status'] for q in family['quantities']]
                family['status']='PASS' if all(v.startswith('PASS_SENSITIVITY_') for v in statuses) else 'FAIL' if 'FAIL_RESOLUTION_TARGET' in statuses else 'INCONCLUSIVE'
            families.append(family)
    narrow=[f for f in families if f['geometry_h_d_w_nm'][2]=='60']
    return {'protocol_id':policy['protocol_id'],'errors':errors,'geometry_results':families,'narrow_two_geometry_gate':'PASS' if len(narrow)==2 and all(f['status']=='PASS' for f in narrow) else 'NOT_PASS','GRID_SENSITIVITY_TARGET':'PASS' if len(families)==3 and all(f['status']=='PASS' for f in families) else 'INCOMPLETE_OR_REFERENCE_INVALID' if any(f['status']=='INCOMPLETE_OR_REFERENCE_INVALID' for f in families) else 'FAIL' if any(f['status']=='FAIL' for f in families) else 'INCONCLUSIVE','prediction_released':False,'whole_domain_accuracy_established':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    # Production CLI only accepts the bound exporter bundle, never arbitrary CSV flags.
    from export_references import verify_bundle
    rows=verify_bundle(a.bundle);p=json.loads((HERE/'grid_policy.json').read_text());result=evaluate(rows,p)
    with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'arithmetic_completed':True,'GRID_SENSITIVITY_TARGET':result['GRID_SENSITIVITY_TARGET'],'narrow_two_geometry_gate':result['narrow_two_geometry_gate'],'prediction_released':False}))
if __name__=='__main__':main()
