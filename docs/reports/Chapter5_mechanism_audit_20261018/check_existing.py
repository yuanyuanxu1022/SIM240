#!/usr/bin/env python3
"""Read existing coefficient/propagation tables; write only this audit directory.

No import/execution of the original plotting, propagation or fitting scripts.
This repeats coefficient arithmetic and the stated series, not OpenLB or physical validation.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np

def pchip_values(x, y, at):
    """Shape-preserving cubic Hermite interpolation; no SciPy runtime dependency.

    Weighted harmonic interior slopes and one-sided endpoint slopes. All audit
    evaluations remain inside the observed knot interval; no extrapolation.
    """
    x,y,at = np.asarray(x),np.asarray(y),np.asarray(at)
    hh=np.diff(x);dd=np.diff(y)/hh
    mm=np.zeros_like(y)
    for i in range(1,len(y)-1):
        if dd[i-1]*dd[i]>0:
            w1=2*hh[i]+hh[i-1];w2=hh[i]+2*hh[i-1]
            mm[i]=(w1+w2)/(w1/dd[i-1]+w2/dd[i])
    def edge(h0,h1,d0,d1):
        v=((2*h0+h1)*d0-h0*d1)/(h0+h1)
        if np.sign(v)!=np.sign(d0):return 0.
        if np.sign(d0)!=np.sign(d1) and abs(v)>3*abs(d0):return 3*d0
        return v
    mm[0]=edge(hh[0],hh[1],dd[0],dd[1])
    mm[-1]=edge(hh[-1],hh[-2],dd[-1],dd[-2])
    assert min(at)>=x[0] and max(at)<=x[-1]
    j=np.clip(np.searchsorted(x,at,side='right')-1,0,len(x)-2)
    t=(at-x[j])/hh[j]
    return (2*t**3-3*t**2+1)*y[j]+(t**3-2*t**2+t)*hh[j]*mm[j]+(-2*t**3+3*t**2)*y[j+1]+(t**3-t**2)*hh[j]*mm[j+1]

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DATA = ROOT / 'CASE/D_series/D2_groove_error_map/results'
PROP = ROOT / 'CASE/D_series/D3_squeeze_error_propagation'
CHAPTER = ROOT / 'docs/reports/第一篇论文_第5章_对比对象选择草稿_20261018.md'

def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

inputs = [CHAPTER, ROOT/'figures/paper/make_fig_fre.py', ROOT/'figures/paper/Fig_fRe_caption_and_record.md']
inputs += [DATA/n for n in ['summary.csv', 'd75_summary.csv', 'h25_summary.csv', 'd120_summary.csv']]
inputs += list(PROP.glob('*.py')) + list((PROP/'results').glob('*.csv')) + list((PROP/'results').glob('*.md'))
before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
K = {}
for r in read(DATA/'summary.csv'):
    if float(r['dx_nm']) == 5:
        K[(int(r['h_nm']),int(r['d_nm']),r['direction'])] = float(r['Keff_m3'])
for name in ['d75_summary.csv','h25_summary.csv','d120_summary.csv']:
    for r in read(DATA/name):
        dr = r['case_id'].split('-')[1]
        assert dr in ['P','T']
        key = (int(r['h_nm']),int(r['d_nm']),dr)
        assert key not in K
        K[key] = float(r['Keff_m3'])
assert len(K) == 36
geometries = sorted({(h,d) for h,d,_ in K})

def stripe(h,d,dr):
    return ((h**3+(h+d)**3)/24 if dr=='P' else 1/(6*(h**-3+(h+d)**-3)))*1e-27

def load(kp,kt,a=1.,b=1.,nmax=201):
    # Positive load magnitude for the rectangular Dirichlet Poisson problem.
    m = np.arange(1,nmax+1,2,dtype=float)[:,None]
    n = np.arange(1,nmax+1,2,dtype=float)[None,:]
    den = kp*(m*np.pi/(2*a))**2 + kt*(n*np.pi/(2*b))**2
    F = 256*a*b/np.pi**4*np.sum(1/(m*m*n*n*den))
    peak = abs(16/np.pi**2*np.sum((-1.)**((m+n-2)/2)/(m*n*den)))
    return float(F), float(peak)

def factor(d,dr):
    aa,bb = (1.7685,1.6331) if dr=='P' else (.4900,.6990)
    return 1/(1+aa*(d/120.)**bb)

table1 = {(int(r['h']),int(r['d'])):r for r in read(PROP/'results/table1_load_and_peak.csv')}
table4 = {(int(r['h']),int(r['d'])):r for r in read(PROP/'results/table4_corrected_closure.csv')}
checks = []
cases = []
for h,d in geometries:
    kp,kt = K[h,d,'P'],K[h,d,'T']
    mp,mt = stripe(h,d,'P'),stripe(h,d,'T')
    F,p = load(kp,kt);FM,pm = load(mp,mt)
    FC,_ = load(mp*factor(d,'P'),mt*factor(d,'T'))
    r=table1[h,d];rc=table4[h,d]
    eps=1e-4
    wx = -(np.log(load(kp*np.exp(eps),kt)[0])-np.log(load(kp*np.exp(-eps),kt)[0]))/(2*eps)
    wy = -(np.log(load(kp,kt*np.exp(eps))[0])-np.log(load(kp,kt*np.exp(-eps))[0]))/(2*eps)
    checks += [abs(FM/F-float(r['F_B_ratio'])),abs(pm/p-float(r['peak_B_ratio'])),abs(FC/F-float(rc['F_corrected']))]
    # Three normalizations; only the first is used by the old fRe figure.
    rh_nm = 2*120*d/(120+2*d)
    pref = 2*.5*(rh_nm*1e-9)**2
    cases.append(dict(h_nm=h,d_nm=d,K_parallel_m3=kp,K_perp_m3=kt,
        e_parallel_pct=(mp/kp-1)*100,e_perp_pct=(mt/kt-1)*100,
        load_ratio=FM/F,peak_ratio=pm/p,corrected_load_ratio=FC/F,
        load_peak_ratio_difference=FM/F-pm/p,w_parallel=wx,w_perp=wy,
        fre_using_P=pref/(kp/(240e-9)),
        fre_using_Href=pref/(kp/((h+d/2)*1e-9)),
        series_201_to_401_relative=abs(load(kp,kt,nmax=401)[0]/F-1)))
assert max(checks)<1e-10

depth_stats=[]
for d in sorted({d for _,d in geometries}):
    rows=[r for r in cases if r['d_nm']==d]
    entry=dict(d_nm=d,sampled_h_nm=sorted(r['h_nm'] for r in rows))
    for key in ['fre_using_P','fre_using_Href']:
        vals=[r[key] for r in rows];lo,hi=min(vals),max(vals)
        entry[key]=dict(min=lo,max=hi,spread=hi/lo,best_fixed_depth_constant=(hi+lo)/2,
                        minimum_max_relative_error_pct=(hi-lo)/(hi+lo)*100)
    depth_stats.append(entry)

# Log-log PCHIP and the stated load series: a model-internal calculation.
times=[]
for d in sorted({d for _,d in geometries}):
    hs=sorted(h for h,dd in geometries if dd==d)
    grid=np.linspace(50.,125.,400)
    kp=np.exp(pchip_values(np.log(hs),np.log([K[h,d,'P'] for h in hs]),np.log(grid)))
    kt=np.exp(pchip_values(np.log(hs),np.log([K[h,d,'T'] for h in hs]),np.log(grid)))
    mp=np.array([stripe(h,d,'P') for h in grid]);mt=np.array([stripe(h,d,'T') for h in grid])
    sd=np.array([load(x,y)[0] for x,y in zip(kp,kt)])
    sm=np.array([load(x,y)[0] for x,y in zip(mp,mt)])
    sc=np.array([load(x*factor(d,'P'),y*factor(d,'T'))[0] for x,y in zip(mp,mt)])
    rr=np.trapezoid(sm,grid)/np.trapezoid(sd,grid)
    rc=np.trapezoid(sc,grid)/np.trapezoid(sd,grid)
    old=next(r for r in read(PROP/'results/table2_time_constant_load.csv') if int(r['d'])==d and int(r['hf'])==50)
    assert abs(rr-float(old['t_B_ratio']))<1e-10
    times.append(dict(d_nm=d,h0_nm=125,hf_nm=50,time_ratio=rr,corrected_time_ratio=rc,
        true_B_S_model_over_S_ref_min=float(min(sm/sd)),true_B_S_model_over_S_ref_max=float(max(sm/sd)),
        old_S_ratio_min_field=float(old['S_ratio_min']),old_S_ratio_max_field=float(old['S_ratio_max']),
        frozen_B_ratio=float(sm[-1]/sd[-1]),
        frozen_B_vs_integrated_B_pct=(sm[-1]/sd[-1]/rr-1)*100,
        old_frozen_vs_integrated_pct=float(old['frozen_vs_integrated_pct'])))

summary = dict(geometries=18,directional_cases=36,
    original_parallel_error_pct=[min(r['e_parallel_pct'] for r in cases),max(r['e_parallel_pct'] for r in cases)],
    original_perp_error_pct=[min(r['e_perp_pct'] for r in cases),max(r['e_perp_pct'] for r in cases)],
    load_ratio=[min(r['load_ratio'] for r in cases),max(r['load_ratio'] for r in cases)],
    corrected_load_ratio=[min(r['corrected_load_ratio'] for r in cases),max(r['corrected_load_ratio'] for r in cases)],
    max_load_vs_peak_ratio_difference=max(abs(r['load_peak_ratio_difference']) for r in cases),
    max_saved_table_absolute_difference=max(checks),
    max_series_201_to_401_relative=max(r['series_201_to_401_relative'] for r in cases),
    max_weight_sum_difference=max(abs(r['w_parallel']+r['w_perp']-1) for r in cases),
    corrected_time_ratio=[min(r['corrected_time_ratio'] for r in times),max(r['corrected_time_ratio'] for r in times)])
after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
assert before==after,'A source changed during this audit; do not accept the snapshot.'
out=dict(summary=summary,cases=cases,depth_stats=depth_stats,times=times,
    protected_source_hashes=before,protected_sources_unchanged=True,
    numpy_version=np.__version__,python=sys.version,run_id=None,
    scope='Arithmetic and stated reduced-model series only; not OpenLB, optimizer or physical-model validation.')
(HERE/'evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('CHECKS_COMPLETED: protected inputs unchanged; no OpenLB, optimizer or original generator executed.')
