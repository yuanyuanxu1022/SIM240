"""Independent reader utilities. No solver, fitting code, or run-controller imports."""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import itertools
import json
import math
import numpy as np

class EvidenceError(ValueError):
    pass

def need(condition, message):
    if not condition:
        raise EvidenceError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def kv(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        key, value = line.split('=', 1)
        need(key not in values, 'duplicate key: '+key)
        values[key] = value
    return values

def rows(path):
    with Path(path).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def save(path, data):
    path = Path(path)
    need(not path.exists(), 'refusing to overwrite analysis '+str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def close(a, b, rtol=1e-12, atol=0):
    return bool(np.allclose(a, b, rtol=rtol, atol=atol, equal_nan=False))

def exact_parameters(config):
    f = lambda k: Fraction(config[k])
    h, d, w, P, Ly, dx = [f(k)*Fraction(1,10**9) for k in
                            ['h_nm','d_nm','w_nm','period_nm','Ly_nm','dx_nm']]
    nu = f('nu_m2_s'); dt = dx*dx/(6*nu)
    need(all((v/dx).denominator==1 for v in [h,d,w,P,Ly,(P-w)/2]), 'unaligned geometry')
    window = math.ceil(f('window_tstar')*h*h/(nu*dt))
    cap = math.ceil(f('max_time_H_diffusion')*(h+d)**2/(nu*dt))
    nodes = (P*Ly*h+w*Ly*d)/(dx**3)
    need(nodes.denominator==1 and window>=2, 'invalid node/window arithmetic')
    return dict(h=float(h),d=float(d),w=float(w),P=float(P),Ly=float(Ly),
                H=float(h+w/P*d),dx=float(dx),nu=float(nu),a=float(f('acceleration_m_s2')),
                dt=float(dt),nodes=int(nodes),window=window,cap=cap,
                nx=int(P/dx),ny=int(Ly/dx),nh=int(h/dx),nd=int(d/dx))

def geometry(config):
    """Independent XZ classification + analytic wall intersections, extruded in Y."""
    p = exact_parameters(config)
    nx,ny,nh,nd = (p[k] for k in ['nx','ny','nh','nd'])
    edge = (p['P']-p['w'])/(2*p['dx'])
    x,z = np.meshgrid(np.arange(nx)+.5,np.arange(nh+nd)+.5,indexing='ij')
    def groove(xx):
        xx=np.remainder(xx,nx)
        return (xx>=edge)&(xx<nx-edge)
    def fluid(xx,zz):
        return (zz>=0)&(zz<nh+nd*groove(xx))
    mask=fluid(x,z); links=0; qmin=1.; qmax=0.
    for cx,cy,cz in itertools.product([-1,0,1], repeat=3):
        if cx*cx+cy*cy+cz*cz not in (1,2): continue
        hit=mask&~fluid(x+cx,z+cz)
        xx,zz=x[hit],z[hit]
        if not len(xx): continue
        best=np.full(len(xx),np.inf)
        if cz:
            for wall in [0,nh,nh+nd]:
                q=(wall-zz)/cz
                gx=groove(xx+q*cx)
                exists=np.ones(len(xx),dtype=bool) if wall==0 or nd==0 else (gx if wall==nh+nd else ~gx)
                best=np.minimum(best,np.where((q>=0)&(q<=1)&exists,q,np.inf))
        if cx and nd:
            for wall in [edge,nx-edge]:
                for image in [-1,0,1]:
                    q=(wall+image*nx-xx)/cx
                    zh=zz+q*cz
                    best=np.minimum(best,np.where((q>=0)&(q<=1)&(zh>=nh)&(zh<=nh+nd),q,np.inf))
        need(np.isfinite(best).all(), 'independent wall intersection missing')
        links+=len(xx)*ny; qmin=min(qmin,float(best.min())); qmax=max(qmax,float(best.max()))
    nodes=int(mask.sum())*ny
    need(nodes==p['nodes'], 'analytic and enumerated volume mismatch')
    return dict(fluid_nodes=nodes,candidate_links=links,q_min=qmin,q_max=qmax,
                material_0=0,material_1=nodes,material_2=nx*ny,
                material_3=nx*ny*(nh+nd+5)-nodes-nx*ny)

def check_boundary(config, boundary):
    expected=geometry(config)
    for key in ['material_0','material_1','material_2','material_3']:
        need(int(boundary[key])==expected[key], 'material count '+key)
    for key in ['candidate_links','valid_distance_links','installed_links']:
        need(int(boundary[key])==expected['candidate_links'], 'wall link count '+key)
    for key in ['q_min','q_max','installed_q_min','installed_q_max']:
        need(abs(float(boundary[key])-.5)<=1e-10, 'wall distance '+key)
    for key in ['geometric_fallback_count','missing_fluid_neighbour_fallback_count','unresolved_link_count']:
        need(int(boundary[key])==0, 'invalid wall '+key)
    need(boundary['geometry_PASS']=='true' and boundary['q_audit_PASS']=='true', 'native geometry flags')
    return expected

def window_metrics(J, cross, n, work_elements=2000000):
    need(len(J)>=n, 'missing full statistical window')
    windows=np.lib.stride_tricks.sliding_window_view(J,n)
    cross_windows=np.lib.stride_tricks.sliding_window_view(cross,n)
    std=np.empty(len(windows)); span=std.copy(); crossmax=std.copy()
    block=max(1,work_elements//n)
    for start in range(0,len(windows),block):
        end=min(start+block,len(windows)); w=windows[start:end]
        mean=w.mean(axis=1)
        need(np.all(mean!=0), 'zero window mean')
        # Centered sample variance; avoid unstable E[J^2]-E[J]^2.
        std[start:end]=w.std(axis=1,ddof=1)/np.abs(mean)
        span[start:end]=np.ptp(w,axis=1)/np.abs(mean)
        crossmax[start:end]=np.abs(cross_windows[start:end]).max(axis=1)
    return std,span,crossmax

def sensitivity(K0, KV2, Kfine, u):
    need(all(math.isfinite(v) and v>0 for v in [K0,KV2,Kfine]), 'invalid comparison K')
    need(math.isfinite(u) and 0<=u<1, 'invalid sensitivity width')
    low,high=Kfine*(1-u),Kfine*(1+u)
    points=sorted(set([low,high]+[v for v in [K0,KV2] if low<=v<=high]))
    delta=[abs(KV2/v-1)-abs(K0/v-1) for v in points]
    mn,mx=min(delta),max(delta)
    status='IMPROVED' if mx < -1e-12 else 'DEGRADED' if mn > 1e-12 else 'INCONCLUSIVE'
    return dict(K_original_m3=K0,K_V2_m3=KV2,K_fine_m3=Kfine,u_estimated=u,
        E_original=K0/Kfine-1,E_V2=KV2/Kfine-1,delta_min=mn,delta_max=mx,
        evaluation_points_m3=points,MODEL_COMPARISON=status,practical_improvement=mx<=-.02,
        sensitivity_is_confidence_interval=False,strict_error_bound_established=False)

def grid_estimate(Kcoarse,Kmid,Kfine,span):
    need(all(math.isfinite(v) and v>0 for v in [Kcoarse,Kmid,Kfine]), 'invalid grid K')
    a,b=Kcoarse-Kmid,Kmid-Kfine
    if a*b<=0 or min(abs(a),abs(b))/Kfine<=1e-14:
        return dict(REFERENCE_QUALIFIED_FOR_CASE=False,reason='nonmonotonic or near-zero differences')
    p=math.log(abs(a/b))/math.log(2)
    if not math.isfinite(p) or p<=0:
        return dict(REFERENCE_QUALIFIED_FOR_CASE=False,reason='nonpositive observed order')
    denom=math.expm1(p*math.log(2))
    gci=1.25*abs(Kmid/Kfine-1)/denom
    change=abs(Kmid/Kfine-1)
    return dict(REFERENCE_QUALIFIED_FOR_CASE=gci<=.01 and change<=.01,
        p=p,GCI_fine_estimate=gci,medium_fine_change=change,u=max(gci,change,span),
        extrapolated_K_m3=Kfine+(Kfine-Kmid)/denom,
        strict_error_bound_established=False,independent_asymptotic_evidence=False)
