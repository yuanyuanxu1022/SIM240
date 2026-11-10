"""Recheck saved scalar evidence only; no solver, fitter or field decoder."""
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BOUND = ROOT / 'docs/reports/PAPER1_bound_closure_review_20261105'
FORM = ROOT / 'docs/reports/PAPER1_formula_comparison_20261105'
protected = {}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def bind(p):
    protected[str(p.relative_to(ROOT))] = digest(p)
    return p

def rows(p):
    with bind(p).open() as f:
        return list(csv.DictReader(f))

def kv(p):
    return dict(s.split('=', 1) for s in bind(p).read_text().splitlines() if '=' in s)

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def table(name, values):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(values[0]))
        w.writeheader()
        w.writerows(values)

def close(a, b):
    assert math.isclose(a, b, rel_tol=2e-12, abs_tol=0), (a, b)

# Recheck previous snapshots, not previous aggregate numbers.
previous_drift = []
for directory in (BOUND, FORM):
    manifest = json.loads(bind(directory / 'source_manifest.json').read_text())
    for name, expected in manifest.items():
        p = ROOT / name
        if digest(bind(p)) != expected:
            previous_drift.append(name)
assert not previous_drift, previous_drift

for name in [
    'PAPER1_bound_closure_review_20261105/PAPER_SECTION_CANDIDATE.md',
    'PAPER1_claim_evidence_matrix_20261104/claim_evidence.csv',
    'PAPER1_claim_evidence_review_20261105/CLAIM_EVIDENCE_MATRIX.csv',
    'SIM240_中文稿_导师审阅版_20261022.md',
    'SIM240_First_Paper_English_20261028.md',
    'Appendix_E_final_review_20261028/ASTRA_REVIEW.md',
    'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
]:
    bind(ROOT / 'docs/reports' / name)

computed = []
for r in rows(BOUND / 'bound_records44_recomputed.csv'):
    p = ROOT / r['source']
    v = kv(p)
    h, d, w, dx = [float(v[k]) for k in ('mesa_gap_m', 'groove_depth_m', 'groove_width_m', 'dx_m')]
    close(w, 120e-9)
    close(float(v['Lx_m']), 240e-9)
    nu = (float(v['tau']) - .5) * dx**2 / (3 * float(v['dt_s']))
    k = nu * float(v['J_main_m2_s']) / float(v['acceleration_m_s2'])
    close(k, float(v['Keff_m3']))
    close(k, float(r['K_discrete_m3']))
    along = v['direction'] == 'parallel'
    lc = (h**3 + (h+d)**3)/24 if along else h**3*(h+d)**3/(6*(h**3+(h+d)**3))
    factor = 1/(1+1.7685*(d/w)**1.6331) if along else 1/(1+.4900*(d/w)**.6990)
    manifest = kv(p.parent / 'run_manifest.txt')
    assert int(bind(p.parent/'exit_code.txt').read_text()) == 0
    computed.append(dict(run_id=r['run_id'], h_nm=round(h*1e9,7),d_nm=round(d*1e9,7),
        dx_nm=round(dx*1e9,7),component='Kyy' if along else 'Kxx',K_m3=k,K_LC_m3=lc,
        K_V2_m3=lc*factor,E_LC_percent=100*(lc/k-1),E_V2_percent=100*(lc*factor/k-1),
        binary_sha256=manifest['binary_sha256'],source=r['source']))
assert len(computed)==44 and len({(r['h_nm'],r['d_nm']) for r in computed})==18
assert all(r['E_LC_percent']>0 for r in computed)
main = [r for r in computed if r['dx_nm']==5]
fine = [r for r in computed if r['dx_nm']==2.5]
assert len(main)==36 and len(fine)==8
stats = []
for component in ('Kxx','Kyy'):
    g=[r for r in main if r['component']==component]
    stats.append(dict(component=component,n=len(g),LC_min=min(r['E_LC_percent'] for r in g),
        LC_max=max(r['E_LC_percent'] for r in g),V2_max_abs=max(abs(r['E_V2_percent']) for r in g),
        LC_MAE=statistics.mean(abs(r['E_LC_percent']) for r in g),
        V2_MAE=statistics.mean(abs(r['E_V2_percent']) for r in g),
        improved=sum(abs(r['E_V2_percent'])<abs(r['E_LC_percent']) for r in g)))
qrows=[]
for r in rows(FORM/'OpenFOAM_outlet_Q.csv'):
    package={'C01':'interface_static_darcy_v1','C02':'interface_static_darcy_v1_1',
             'C03':'interface_static_darcy_v1_2','C04':'interface_static_darcy_v1_3','GDI01':'groove_darcy_static_v1'}[r['case_id']]
    base=ROOT/'CASE'/package/'runs'/r['run_id']
    accepted=json.loads(bind(ROOT/r['accepted_source']).read_text())
    assert accepted['run_id']==r['run_id'] and accepted['RESULT_PASS'] and accepted['geometry_PASS']
    assert accepted['geometry_scope']=='synthetic_average_domain_only'
    execution=json.loads(bind(base/'execution.json').read_text())
    assert execution['status']=='completed' and all(s['exit_code']==0 and not s['timed_out'] for s in execution['steps'])
    sub='openfoam/GDI_output' if r['case_id']=='GDI01' else ('openfoam/SDI_output' if r['endpoint']=='openfoam' else 'two_dimensional')
    source=base/sub/'faces.csv'
    q=math.fsum(float(f['phi_m3_s']) for f in rows(source) if f['patch']=='xHigh')
    close(q,float(r['Q_m3_s']))
    qrows.append(dict(case_id=r['case_id'],run_id=r['run_id'],endpoint=r['endpoint'],Q_m3_s=q,
                      accepted_source=r['accepted_source'],source=str(source.relative_to(ROOT))))
qs={r['case_id']:r['Q_m3_s'] for r in qrows if r['endpoint']=='openfoam'}
table('recomputed_44_records.csv',computed)
table('recomputed_direction_stats.csv',stats)
table('recomputed_outlet9.csv',qrows)
summary=dict(records=44,geometries=18,primary_direction_conditions=36,refinement_records=8,
    all_below_LC=True,refined_E_min=min(r['E_LC_percent'] for r in fine),refined_E_max=max(r['E_LC_percent'] for r in fine),
    direction_statistics=stats,V2_improved= sum(s['improved'] for s in stats),
    Kxx_h_ge_50_max_abs=max(abs(r['E_V2_percent']) for r in main if r['component']=='Kxx' and r['h_nm']>=50),
    Q_transverse_change_percent=100*(qs['C01']/qs['C03']-1),Q_parallel_change_percent=100*(qs['C02']/qs['C04']-1),
    GDI01_relative_difference_from_C01=qs['GDI01']/qs['C01']-1,
    previous_snapshot_drift=previous_drift,protected_count=len(protected),solver_calls=0,fit_calls=0,
    reserved_results_read=False,full_acceptance_rerun=False,new_run_id=None)
dump('summary.json',summary)
dump('source_manifest.json',protected)
changed=[name for name,d in protected.items() if digest(ROOT/name)!=d]
assert not changed,changed
dump('verification.json',dict(changed_inputs=changed,protected_count=len(protected),scalar_audit_pass=True,
    scope='saved scalar recalculation and original acceptance identity; not new scientific acceptance'))
print(json.dumps(summary,ensure_ascii=False,indent=2))
