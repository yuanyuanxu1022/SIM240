"""Independent NumPy references; never imports C++ or executes a solver."""
import csv
import json
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parent
C=np.array([[0,0,0],[-1,0,0],[0,-1,0],[0,0,-1],[-1,-1,0],[-1,1,0],[-1,0,-1],[-1,0,1],[0,-1,-1],[0,-1,1],[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,-1,0],[1,0,1],[1,0,-1],[0,1,1],[0,1,-1]])
W=np.array([1/3]+[1/18]*3+[1/36]*6+[1/18]*3+[1/36]*6)
def lap(f):
    return sum(6*w*(np.roll(f,tuple(-c),axis=(0,1,2))-f) for c,w in zip(C,W))
def grad(f):
    return np.array([sum(3*w*c[a]*np.roll(f,tuple(-c),axis=(0,1,2)) for c,w in zip(C,W)) for a in range(3)])
def matrix(case, mode=None):
    k=2*np.pi*np.array(case['mode'] if mode is None else mode)/case['N']
    lam=float(np.sum(6*W*(1-np.cos(C@k))))
    ak=case['a']+case['kappa']*lam
    e=W*ak;e[0]+=1-ak
    omega=1/case['tau']
    mat=np.exp(-1j*(C@k))[:,None]*((1-omega)*np.eye(19)+omega*e[:,None]*np.ones((1,19)))
    return mat,e,k,lam
def sequence(case, initial=None):
    mat,e,k,lam=matrix(case)
    vector=(case['amplitude']/2*e).astype(complex) if initial is None else np.array(initial,dtype=complex)
    result=[]
    for step in range(case['steps']+1):
        result.append(vector.sum());vector=mat@vector
    return np.array(result)
def load_field(path,n,populations=False):
    with Path(path).open() as f:
        reader=csv.DictReader(f); rows=list(reader)
    assert len(rows)==n**3,('field row count',path,len(rows))
    coords=np.array([[int(float(r[a])) for a in ['x','y','z']] for r in rows])
    assert np.all((coords>=0)&(coords<n))
    assert len(np.unique(coords,axis=0))==n**3
    result={}
    for key in rows[0]:
        if key in ['x','y','z']:continue
        vals=np.array([float(r[key]) for r in rows]);assert np.isfinite(vals).all(),(path,key)
        array=np.empty((n,n,n));array[tuple(coords.T)]=vals;result[key]=array
    if populations: assert all('f'+str(i) in result for i in range(19))
    return result
def amplitude(field,case,harmonic=1):
    n=case['N'];i=np.indices(field.shape)
    theta=2*np.pi*sum(a*m for a,m in zip(i,case['mode']))/n
    return np.mean((field-case['center'])*np.exp(-1j*harmonic*theta))
def rate(coeffs,start_fraction=.25):
    t=np.arange(len(coeffs));start=int(np.ceil((len(coeffs)-1)*start_fraction));mask=t>=start
    return float(-np.polyfit(t[mask],np.log(np.abs(coeffs[mask])),1)[0])
def generate():
    protocol=json.loads((BASE/'protocol.json').read_text()); out=BASE/'reference';out.mkdir(exist_ok=False)
    details=[]
    for case in protocol['B_cases']:
        if case['kind']!='linear':continue
        series=sequence(case);mat,e,k,lam=matrix(case);ev=np.linalg.eigvals(mat);hydro=ev[np.argmin(abs(ev-1))]
        # Check all requested modes plus highest-frequency corners (not an all-k proof).
        sampled=[]
        for mode in [case['mode'],[0,0,0],[case['N']//2,0,0],[case['N']//2]*2+[0],[case['N']//2]*3]:
            eig=np.linalg.eigvals(matrix(case,mode)[0]);sampled.append(float(max(abs(eig))))
        if max(sampled)>protocol['thresholds']['static_spectrum_radius_limit']:raise ValueError('sampled kinetic spectrum unstable')
        continuum=(case['tau']-.5)/3*float(k@k)*(case['a']+case['kappa']*float(k@k))
        rel=abs(-np.log(abs(hydro))/continuum-1)
        if case['tau']==1:
            assert rel<=protocol['thresholds'][f"linear_tau1_continuum_rate_N{case['N']}"]
            g=1-lam*(case['a']+case['kappa']*lam)/6
            assert np.max(abs(series-case['amplitude']/2*g**np.arange(len(series))))<1e-14
        with (out/(case['id']+'.csv')).open('w') as f:
            w=csv.writer(f);w.writerow(['step','re','im'])
            for t,v in enumerate(series):w.writerow([t,format(v.real,'.17g'),format(v.imag,'.17g')])
        details.append(dict(id=case['id'],Lambda=lam,hydrodynamic_eigenvalue=[hydro.real,hydro.imag],continuum_rate=continuum,discrete_rate=-float(np.log(abs(hydro))),continuum_relative_error=float(rel),fixed_window_reference_rate=rate(series),sampled_spectral_radii=sampled))
    (out/'spectral_preflight.json').write_text(json.dumps(dict(check='static matrices; no OpenLB execution',cases=details,sampling_limitation='requested modes and Nyquist corners only; not all wavevectors'),indent=2)+'\n')
    print('Generated 14 static kinetic reference curves; requested and Nyquist-corner eigenvalues checked; tau1 continuum limits satisfied.')
if __name__=='__main__':generate()
