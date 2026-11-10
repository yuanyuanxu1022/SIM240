"""One-shot local candidate freeze. Refuses to replace an existing lock."""
from pathlib import Path
import csv, json, hashlib, datetime, shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=HERE.parent/'Constrained_correlation_20261023'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    lock=HERE/'candidate_lock.json'
    if lock.exists():raise SystemExit('Existing candidate lock: refuse overwrite; verify or create a new version.')
    hashes=json.loads((HERE/'input_hashes.json').read_text())
    assert all(sha(p)==v for p,v in hashes.items())
    fits=json.loads((OLD/'fits.json').read_text())
    shutil.copyfile(OLD/'models.py',HERE/'frozen_models.py')
    rows=list(csv.DictReader((HERE/'reserved_predictions.csv').open()))
    assert len(rows)==60
    pairs={}
    for r in rows:
        if r['role']!='prediction_test':continue
        pairs.setdefault((r['model'],r['h_nm'],r['d_nm'],r['w_nm']),{})[r['direction']]=float(r['K_pred_m3'])
    ar=[dict(model=k[0],h_nm=k[1],d_nm=k[2],w_nm=k[3],A_pred=v['P']/v['T']) for k,v in sorted(pairs.items())]
    assert len(ar)==24
    with (HERE/'reserved_anisotropy.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(ar[0]));w.writeheader();w.writerows(ar)
    names=['FREEZE_RULES.md','frozen_models.py','freeze.py','verify_lock.py','reserved_predictions.csv','reserved_anisotropy.csv','tradeoffs.csv','parameter_stability.csv','optimizer_stability.csv','target_sensitivity.json','audit_summary.json','input_hashes.json','audit.py','REPORT.md']
    payload=dict(lock_id='G4_candidate_prediction_v1_20261024',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='CANDIDATE_FROZEN_NOT_VALIDATED',primary='G4',comparators=['G6','MIX7'],coefficients={m:fits[m] for m in ('G4','G6')},parameter_order='ln(a), p, optional m; absent m=1',MIX7_rule='P=complete G4 including G4 T parameters; T=G6 T',target_domain=dict(s=[.8,3.2],t=[1/3,1.6],phi=.5,period_rule='P=2w',accuracy_validated=False),evaluation=dict(quantities=['P','T','A'],MAE_percent_limit=3.,max_abs_percent_limit=5.,all_conditions_required=True,reference='original validated dx5 rows; grid results reported separately'),new_solver_runs=0,simulation_authorized=False,prediction_results_read=False,external_non_exposure_verified=False,teacher_approval_claimed=False,bound_files={n:sha(HERE/n) for n in names})
    with lock.open('x') as f:json.dump(payload,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    (HERE/'candidate_lock.sha256').write_text(sha(lock)+'  candidate_lock.json\n')
    print(payload['lock_id'],sha(lock))
if __name__=='__main__':main()
