"""Independent scalar recomputation. No import of fitted or frozen model code."""
from pathlib import Path
import json,csv,math,hashlib,copy
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scalar(s,t,coeff,dr):
    lp=((1+t)**3-1)/2;lt=((1+t)**3-1)/((1+t)**3+1)
    def H(x,y,m):return (x**(-m)+y**(-m))**(-1/m) if x>0 else 0.
    pt,pp=coeff['T'],coeff['P'];mt=pt[2] if len(pt)>2 else 1.;mp=pp[2] if len(pp)>2 else 1.
    et=H(lt,math.exp(pt[0])*s**pt[1],mt)
    ep=et+H(lp-et,math.exp(pp[0])*s**pp[1]+s*s*t/2,mp)
    return 1+(ep if dr=='P' else et),1+(lp if dr=='P' else lt)
def check_rows(rows,lock):
    expected={r['planned_case_id'] for r in csv.DictReader((HERE.parents[2]/'CASE/D_series/D4_variable_groove_transport_20261023/protocol/candidate_cases.csv').open(encoding='utf-8-sig')) if r['blind_geometry']=='True'}
    assert len(expected)==20 and len(rows)==60
    assert len({(r['model'],r['planned_case_id']) for r in rows})==60
    delta=0.
    for model in ('G4','G6','MIX7'):assert {r['planned_case_id'] for r in rows if r['model']==model}==expected
    for r in rows:
        m=r['model'];dr=r['direction'];source=('G4' if dr=='P' else 'G6') if m=='MIX7' else m
        h,d,w,p=map(float,(r['h_nm'],r['d_nm'],r['w_nm'],r['P_nm']));assert p==2*w
        n,local=scalar(w/h,d/h,lock['coefficients'][source],dr)
        for col,value in [('K_pred_m3',n*(h*1e-9)**3/12),('F_pred',n/local),('resistance_correction',local/n)]:
            err=abs(value/float(r[col])-1);delta=max(delta,err);assert err<1e-12,(r['planned_case_id'],col)
    return delta
def main():
    p=HERE/'candidate_lock.json';lock=json.loads(p.read_text());assert sha(p)==(HERE/'candidate_lock.sha256').read_text().split()[0]
    for name,v in lock['bound_files'].items():assert sha(HERE/name)==v,name
    inputs=json.loads((HERE/'input_hashes.json').read_text());assert all(Path(p).is_file() and sha(p)==v for p,v in inputs.items())
    rows=list(csv.DictReader((HERE/'reserved_predictions.csv').open()));delta=check_rows(rows,lock)
    for r in csv.DictReader((HERE/'reserved_anisotropy.csv').open()):
        pair={x['direction']:float(x['K_pred_m3']) for x in rows if x['role']=='prediction_test' and all(x[k]==r[k] for k in ('model','h_nm','d_nm','w_nm'))}
        assert abs(float(r['A_pred'])/(pair['P']/pair['T'])-1)<1e-12
    rejects=0
    for bad in (rows[:-1],copy.deepcopy(rows)):
        if len(bad)==60:bad[0]['K_pred_m3']=str(float(bad[0]['K_pred_m3'])*1.01)
        try:check_rows(bad,lock)
        except AssertionError:rejects+=1
    assert rejects==2
    result=dict(ok=True,lock_id=lock['lock_id'],lock_sha256=sha(p),input_count=len(inputs),bound_file_count=len(lock['bound_files']),prediction_rows_checked=60,anisotropy_rows_checked=24,max_relative_difference=delta,in_memory_missing_and_tamper_tests_rejected=rejects,solver_runs=0,prediction_results_read=False,physical_validation_pass=False)
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
