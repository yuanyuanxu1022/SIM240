#!/usr/bin/env python3
"""Read-only independent audit of the completed 200-step pilot. No solver calls."""
import csv
import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RID='target_lp_pilot200_20261021_v4'
RUN=BASE/'output'/RID
REC=BASE/'evidence'/RID
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    inputs=[RUN/n for n in ['history.csv','result.txt','geometry_audit.txt','slice_initial.csv','slice_final.csv']]
    inputs += [REC/n for n in ['manifest.json','exit_code.txt','console.log']]
    inputs += [BASE/'PILOT200_ANALYSIS.md',BASE/'src/target_prevalidation.cpp',BASE/'protocol.json']
    before={str(p):sha(p) for p in inputs}
    m=json.loads((REC/'manifest.json').read_text())
    code=int((REC/'exit_code.txt').read_text())
    a=np.genfromtxt(RUN/'history.csv',delimiter=',',names=True)
    assert code==0 and len(a)==201 and np.array_equal(a['step'],np.arange(201))
    assert np.all(a['finite']==1)
    out=dict(run_id=RID,independent_exit_code=code,records=len(a),
             wall_seconds=(datetime.fromisoformat(m['finished_utc'])-datetime.fromisoformat(m['started_utc'])).total_seconds(),
             manifest_total_hashed_files=len(m['source_hashes']),
             manifest_backend_src_files=sum('/openlb/src/' in k for k in m['source_hashes']),
             recorded_source_hashes_unchanged=m['source_hashes_unchanged'],
             current_hashed_files_match=all(Path(p).exists() and sha(Path(p))==h for p,h in m['source_hashes'].items()),
             stability={},pressure={},shape={})
    for col in ['liquid_drift','total_mass_drift','max_Mach','max_u_m_s']:
        v=a[col]; i=int(np.argmax(np.abs(v)))
        out['stability'][col]=dict(final=float(v[-1]),max_absolute=float(abs(v[i])),max_at_step=int(a['step'][i]))
    for col,drift in [('liquid_amount_lu3','liquid_drift'),('total_mass_lu','total_mass_drift')]:
        recomputed=(a[col]-a[col][0])/a[col][0]
        assert np.allclose(recomputed,a[drift],rtol=1e-12,atol=1e-16)
    out['stability']['rho_min']=float(a['rho_min'].min())
    for col in ['p_h_inside_minus_outside_Pa','p_bulk_candidate_inside_minus_outside_Pa']:
        v=a[col]; peaks=[i for i in range(1,len(v)-1) if v[i]>v[i-1] and v[i]>v[i+1]]
        troughs=[i for i in range(1,len(v)-1) if v[i]<v[i-1] and v[i]<v[i+1]]
        p=dict(all_min=float(v.min()),all_max=float(v.max()),final=float(v[-1]),
               positive_increment_fraction=float(np.mean(np.diff(v)>0)),
               peaks=[dict(step=i,value=float(v[i])) for i in peaks],
               troughs=[dict(step=i,value=float(v[i])) for i in troughs],windows={})
        for n in [40,45,46,50,90,100]:
            w=v[-n:]; avg=float(w.mean()); span=float(np.ptp(w))
            p['windows'][str(n)]=dict(mean_Pa=avg,peak_to_peak_Pa=span,
                                    peak_to_peak_over_abs_mean=span/abs(avg),half_amplitude_over_abs_mean=span/(2*abs(avg)))
        # Sensitivity of a heuristic exponential envelope fit to early-cycle inclusion.
        ts=[]; amps=[]
        for i in peaks:
            left=[j for j in troughs if j<i]; right=[j for j in troughs if j>i]
            if left and right:
                j,k=left[-1],right[0]
                baseline=v[j]+(v[k]-v[j])*(i-j)/(k-j)
                ts.append(i); amps.append((v[i]-baseline)/2)
        p['heuristic_envelope_fits']=[]
        for start in [0,1]:
            slope,intercept=np.polyfit(ts[start:],np.log(amps[start:]),1)
            p['heuristic_envelope_fits'].append(dict(peak_steps=ts[start:],tau_steps=float(-1/slope),
                                                   status='few-cycle heuristic; not a confidence interval or mechanism proof'))
        out['pressure'][col]=p
    spec=importlib.util.spec_from_file_location('shape_reader',BASE/'summarize_preparation.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    for name in ['initial','final']:
        f=RUN/f'slice_{name}.csv'; s=np.genfromtxt(f,delimiter=',',names=True); w=1-s['phi']; area=float(w.sum())
        out['shape'][name]=dict(weighted_midplane_area=area,weighted_area_radius_lu=float(np.sqrt(area/np.pi)),
                               phi_half_contour_fit=mod.fit_circle(f))
    rv=float((3*a['liquid_amount_lu3'][-1]/(4*np.pi))**(1/3))
    rc=out['shape']['final']['phi_half_contour_fit']['radius_lattice']
    out['radius_comparison']=dict(diffuse_volume_equivalent_radius_lu=rv,phi_half_contour_radius_lu=rc,
                                 nominal_radius_lu=16.,reference_pressure_volume_Pa=.06/(rv*2.5e-9),
                                 reference_pressure_contour_Pa=.06/(rc*2.5e-9),
                                 note='different radius definitions; mechanical curvature/surface-of-tension convention not validated')
    out.update(no_new_simulation=True,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    assert all(sha(Path(p))==h for p,h in before.items())
    out['input_hashes_unchanged']=True;out['input_sha256']=before
    (HERE/'recomputed.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['input_sha256','pressure','shape']},indent=2))

if __name__=='__main__':
    main()
