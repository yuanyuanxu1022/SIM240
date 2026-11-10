"""Audit named, already-known D2/D4 development evidence. No solver or fit.

Never enumerates or opens held-out prediction results. Energy profiles are
count-weighted means, not sums; their reconstruction is checked against J.
"""
from pathlib import Path
import csv
import hashlib
import json
import math

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
REPORTS = ROOT / 'docs/reports'
D4 = ROOT / 'CASE/D_series/D4_variable_groove_transport_20261023'
protected = {}

def bind(p):
    p = Path(p).resolve()
    assert 'prediction' not in str(p).lower(), p
    protected[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p

def rows(p):
    with bind(p).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def kv(p):
    return dict(x.split('=', 1) for x in bind(p).read_text().splitlines() if '=' in x)

def dump(n, o):
    (OUT/n).write_text(json.dumps(o, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def table(n, rr):
    with (OUT/n).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rr[0])); w.writeheader(); w.writerows(rr)

def close(a,b):
    assert math.isclose(a,b,rel_tol=3e-12,abs_tol=1e-34), (a,b)

for n in ['SIM240_中文稿_导师审阅版_20261022.md','SIM240_First_Paper_English_20261028.md',
          'PAPER1_h25_reference_candidate_audit_20261104_225645/REPORT.md',
          'D4_reference_revision_review_20261025/REPORT.md',
          'D4_grid_narrow_fine4_acceptance_20261025/REPORT.md',
          'Chapter5_mechanism_audit_20261018/REPORT.md']:
    bind(REPORTS/n)
bind(D4/'PROTOCOL.md')
bind(D4/'development_stage_20261023/PROTOCOL.md')
bind(D4/'src/variable_groove_transport.cpp')
bind(ROOT/'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp')
bind(Path('/home/dell/openlb/src/functors/lattice/latticePhysDissipation3D.hh'))

requests = {}
for r in rows(REPORTS/'PAPER1_claim_final_review_20261105/recomputed_44_records.csv'):
    requests[str((ROOT/r['source']).parent)] = ('D2_main' if float(r['dx_nm'])==5 else 'D2_refinement', float(r['K_m3']))
for direction in ('P','T'):
    p=ROOT/f'CASE/D_series/D2_groove_error_map/results/h100_d100_dx5_{direction}/steady'
    requests[str(p)] = ('D2_additional_gap',None)
for r in rows(REPORTS/'D4_remaining14_acceptance_20261024/scalar_acceptance/scalar_results.csv'):
    p=D4/'results/development_remaining14_20261024_v1'/r['run_id']/'steady'
    requests[str(p)] = ('D4_known_development',float(r['K_m3']))
for r in rows(REPORTS/'D4_grid_narrow_fine4_acceptance_20261025/reference_sources16.csv'):
    requests[r['raw_output']] = ('D4_known_development' if float(r['dx_nm'])==5 else 'D4_known_grid',float(r['K_m3']))
for r in rows(REPORTS/'D4_foundation_acceptance_20261023/complete/scalar_results.csv'):
    if r['role']=='regression' or (r['role']=='smooth' and round(float(r['h_nm']))==75):
        p=D4/'results/foundation_20261023_v1'/r['run_id']/'steady'
        requests[str(p)] = ('D4_regression' if r['role']=='regression' else 'D4_smooth_control',float(r['K_m3']))

records=[]; energy=[]
for path,(role,oldk) in requests.items():
    p=Path(path); r=kv(p/'result.txt'); m=kv(p/'run_manifest.txt')
    assert int(bind(p/'exit_code.txt').read_text())==0
    h,d,w,dx,lx,ly,dt,tau,a=[float(r[k]) for k in ('mesa_gap_m','groove_depth_m','groove_width_m','dx_m','Lx_m','Ly_m','dt_s','tau','acceleration_m_s2')]
    close(w/lx,.5)
    nu=(tau-.5)*dx*dx/(3*dt); j=float(r['J_main_m2_s']); k=nu*j/a
    close(k,float(r['Keff_m3']))
    if oldk is not None: close(k,oldk)
    direction='P' if r['direction']=='parallel' else 'T'
    lc=(h**3+(h+d)**3)/24 if direction=='P' else h**3*(h+d)**3/(6*(h**3+(h+d)**3))
    v2=1/(1+1.7685*(d/w)**1.6331) if direction=='P' else 1/(1+.4900*(d/w)**.6990)
    rec=dict(run_id=r.get('run_id',p.parent.name),role=role,h_nm=round(h*1e9,6),d_nm=round(d*1e9,6),
             w_nm=round(w*1e9,6),P_nm=round(lx*1e9,6),dx_nm=round(dx*1e9,6),direction=direction,
             alpha_h_over_w=h/w,beta_d_over_w=d/w,eta_d_over_h=d/h,
             delta_Hmax_over_w=(h+d)/w,n_gap=h/dx,K_m3=k,K_LC_m3=lc,
             F_discrete=k/lc,LC_bias_percent=100*(lc/k-1),V2_bias_percent=100*(lc*v2/k-1),
             binary_sha256=m['binary_sha256'],source=str(p.relative_to(ROOT)/'result.txt'))
    records.append(rec)
    # Offline diagnostic only. Full trajectory and 3D-field acceptance not rerun.
    if role.startswith('D4'):
        ep=rows(p/'energy_dissipation.csv'); vp=rows(p/'velocity_profile.csv')
        nx,ny,nh,nd,nw=[round(v/dx) for v in (lx,ly,h,d,w)]
        expected_n=nx*ny*nh+nw*ny*nd
        assert expected_n==int(r['fluid_nodes'])
        def counts(pos):
            if direction=='P': return nx*nh+nw*nd
            return ny*(nh+(nd if (lx-w)/2 <= pos < (lx+w)/2 else 0))
        assert len(ep)==(ny if direction=='P' else nx)==len(vp)
        count_total=sum(counts(float(x['position'])) for x in ep)
        assert count_total==expected_n
        integrated_phi=math.fsum(float(x['Phi'])*counts(float(x['position']))*dx**3 for x in ep)
        recovered_j=math.fsum(float(x['velocity'])*counts(float(x['position']))*dx**3 for x in vp)/(lx*ly)
        close(recovered_j,j)
        rho=float(r['rho_phys_kg_m3']); pin=rho*a*j*lx*ly
        energy.append(dict(run_id=rec['run_id'],role=role,direction=direction,d_nm=rec['d_nm'],w_nm=rec['w_nm'],
                           dx_nm=rec['dx_nm'],input_power_W=pin,saved_Phi_integral_W=integrated_phi,
                           Phi_over_input=integrated_phi/pin,residual_percent=100*(integrated_phi/pin-1),
                           J_reconstruction_relative_difference=recovered_j/j-1,
                           scope='count-weighted saved moment-based diagnostic; not energy acceptance or mechanism partition'))

def select(**conds):
    rr=[r for r in records if all(r[k]==v for k,v in conds.items())]
    assert len(rr)==1,(conds,len(rr))
    return rr[0]

witnesses=[]
def witness(label,a,b,control):
    witnesses.append(dict(label=label,direction=a['direction'],controlled_quantity=control,
       run_a=a['run_id'],run_b=b['run_id'],a_h=a['h_nm'],a_d=a['d_nm'],a_w=a['w_nm'],
       b_h=b['h_nm'],b_d=b['d_nm'],b_w=b['w_nm'],a_F=a['F_discrete'],b_F=b['F_discrete'],
       a_LC_bias=a['LC_bias_percent'],b_LC_bias=b['LC_bias_percent'],
       LC_bias_difference_pp=b['LC_bias_percent']-a['LC_bias_percent'],
       same_binary=a['binary_sha256']==b['binary_sha256'],same_dx=a['dx_nm']==b['dx_nm']))
for dr in ('P','T'):
    pick=lambda h,d:select(role='D2_main',h_nm=h,d_nm=d,dx_nm=5,direction=dr)
    witness('same_d_over_h_1',pick(50,50),pick(75,75),'d/h=1; w=120nm')
    witness('same_max_height_150',pick(50,100),pick(125,25),'(h+d)/w=150/120')
    witness('same_max_height_150_refined',
            select(role='D2_refinement',h_nm=50,d_nm=100,dx_nm=2.5,direction=dr),
            select(role='D2_refinement',h_nm=125,d_nm=25,dx_nm=2.5,direction=dr),
            '(h+d)/w=150/120; both refined')
    witness('same_d_over_w_d100',pick(50,100),pick(125,100),'d/w=100/120')

width_scan=[]
for d in (25,50,100,120):
    for dr in ('P','T'):
        for w in (60,120,240):
            role='D2_main' if w==120 else 'D4_known_development'
            r=select(role=role,h_nm=75,d_nm=d,w_nm=w,dx_nm=5,direction=dr)
            width_scan.append(r)
        a=select(role='D4_known_development',h_nm=75,d_nm=d,w_nm=60,dx_nm=5,direction=dr)
        b=select(role='D4_known_development',h_nm=75,d_nm=d,w_nm=240,dx_nm=5,direction=dr)
        witness('fixed_h_d_true_width_scan',a,b,'h=75nm, d fixed, phi=.5; P120 to480nm')

grid_width=[]
for dr in ('P','T'):
    for dx in (5,2.5):
        role='D4_known_development' if dx==5 else 'D4_known_grid'
        a=select(role=role,h_nm=75,d_nm=120,w_nm=60,dx_nm=dx,direction=dr)
        b=select(role=role,h_nm=75,d_nm=120,w_nm=240,dx_nm=dx,direction=dr)
        grid_width.append(dict(direction=dr,dx_nm=dx,narrow_K=a['K_m3'],wide_K=b['K_m3'],
            narrow_LC_bias=a['LC_bias_percent'],wide_LC_bias=b['LC_bias_percent'],
            width_bias_drop_pp=a['LC_bias_percent']-b['LC_bias_percent'],same_binary=a['binary_sha256']==b['binary_sha256']))

table('scalar_records.csv',records); table('matched_witnesses.csv',witnesses)
table('known_width_scan.csv',width_scan); table('grid_width_comparison.csv',grid_width)
table('saved_energy_diagnostic.csv',energy)
summary=dict(total_direction_records=len(records),roles={k:sum(x['role']==k for x in records) for k in sorted({r['role'] for r in records})},
             all_saved_K_reproduced=True,matched_witnesses=witnesses,grid_width=grid_width,
             energy_residual_range_percent=[min(x['residual_percent'] for x in energy),max(x['residual_percent'] for x in energy)],
             all_D4_energy_count_J_reconstruction_checked=True,solver_calls=0,fit_calls=0,reserved_results_read=False,
             full_acceptance_rerun=False,new_run_id=None,new_energy_gate_adopted=False)
dump('summary.json',summary);dump('source_manifest.json',protected)
changed=[str(p) for p,d in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=d]
assert not changed,changed
dump('verification.json',dict(input_count=len(protected),changed_inputs=changed,scalar_recomputation_complete=True,
                             scientific_gate_changed=False,human_scientific_approval=False))
print(json.dumps({k:v for k,v in summary.items() if k!='matched_witnesses'},ensure_ascii=False,indent=2))
