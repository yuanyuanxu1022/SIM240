#!/usr/bin/env python3
"""Independent CSV arithmetic and diagnostic figures; no solver execution."""
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RID='target_lp_diagnostic2000_20261021_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    run=BASE/'output'/RID; record=BASE/'evidence'/RID
    files=sorted(p for d in [run,record] for p in d.rglob('*') if p.is_file())
    files += [BASE/'protocol.json',BASE/'PROTOCOL.md',BASE/'analyze_completed.py',BASE/'src/target_prevalidation.cpp']
    before={str(f):sha(f) for f in files}
    manifest=json.loads((record/'manifest.json').read_text())
    assert int((record/'exit_code.txt').read_text())==manifest['independent_exit_code']==0
    assert manifest['source_hashes_unchanged']
    assert all(Path(f).is_file() and sha(Path(f))==h for f,h in manifest['source_hashes'].items())
    rows=list(csv.DictReader((run/'history.csv').open()))
    assert [int(r['step']) for r in rows]==list(range(2001))
    assert all(r['finite']=='1' for r in rows)
    assert all(math.isfinite(float(r[k])) for r in rows for k in r if k!='velocity_L2_relative_error')
    frozen=json.loads((HERE/'frozen_analysis.json').read_text())
    checks=dict(run_id=RID,independent_exit_code=0,completed_steps=2000,history_records=2001,
                bound_files_verified=len(manifest['source_hashes']),
                wall_seconds=(datetime.fromisoformat(manifest['finished_utc'])-datetime.fromisoformat(manifest['started_utc'])).total_seconds(),
                windows={},whole_run={})
    windows=[]
    for col in ['p_h_inside_minus_outside_Pa','p_bulk_candidate_inside_minus_outside_Pa']:
        checks['windows'][col]={}
        for lo,hi in [(1501,2000),(1751,2000),(1501,1750)]:
            selected=[r for r in rows if lo<=int(r['step'])<=hi]
            y=[float(r[col]) for r in selected];x=[int(r['step']) for r in selected]
            avg=statistics.fmean(y);xm=statistics.fmean(x)
            slope=math.fsum((xx-xm)*(yy-avg) for xx,yy in zip(x,y))/math.fsum((xx-xm)**2 for xx in x)
            span=max(y)-min(y);change=slope*(hi-lo)
            independent=dict(mean_Pa=avg,peak_to_peak_Pa=span,slope_Pa_per_step=slope,
                             fitted_window_change_Pa=change,peak_to_peak_over_abs_mean=span/abs(avg),
                             fitted_change_over_abs_mean=change/abs(avg))
            reference=frozen['pressure'][col]['windows'][f'{lo}_{hi}']
            for k,v in independent.items():assert math.isclose(v,reference[k],rel_tol=1e-10,abs_tol=1e-7),(k,v,reference[k])
            checks['windows'][col][f'{lo}_{hi}']=independent
            windows.append(dict(pressure=col,start=lo,end=hi,count=len(y),**independent))
    for raw,col in [('liquid_amount_lu3','liquid_drift'),('total_mass_lu','total_mass_drift')]:
        initial=float(rows[0][raw]);d=[(float(r[raw])-initial)/initial for r in rows]
        assert all(math.isclose(v,float(r[col]),rel_tol=1e-12,abs_tol=1e-16) for v,r in zip(d,rows))
        peak=max(range(len(d)),key=lambda i:abs(d[i]))
        ref=frozen['whole_run'][col]
        assert peak==ref['at_step'] and math.isclose(abs(d[peak]),ref['max_absolute'],rel_tol=1e-12)
        checks['whole_run'][col]=dict(max_absolute=abs(d[peak]),at_step=peak,final=d[-1])
    parent=BASE.parent/'target_prevalidation_20261021/output/target_lp_pilot200_20261021_v4/history.csv'
    old=list(csv.DictReader(parent.open()))
    checks['parent_first201_rows_byte_field_equal']=rows[:201]==old
    assert checks['parent_first201_rows_byte_field_equal']
    a=np.genfromtxt(run/'history.csv',delimiter=',',names=True)
    p=a['p_h_inside_minus_outside_Pa']
    checks['first250_vs_last250_peak_to_peak_ratio']=float(np.ptp(p[1:251])/np.ptp(p[-250:]))
    checks['tail500_max_speed_m_s']=float(a['max_u_m_s'][-500:].max())
    checks['tail500_max_Mach']=float(a['max_Mach'][-500:].max())
    checks['final_speed_m_s']=float(a['max_u_m_s'][-1])
    checks['tail_mean_relative_difference']=float((p[-250:].mean()-p[-500:].mean())/abs(p[-500:].mean()))
    checks['adjacent_half_relative_difference']=float((p[-250:].mean()-p[-500:-250].mean())/abs(p[-500:].mean()))
    checks['final_pressure_definition_difference_Pa']=float(p[-1]-a['p_bulk_candidate_inside_minus_outside_Pa'][-1])
    checks['final_mu_inside_outside_Pa']=[float(a[k][-1]) for k in ['mu_inside_Pa','mu_outside_Pa']]
    checks['reference_comparison']={}
    for n in [500,250]:
        mean=float(p[-n:].mean())
        checks['reference_comparison'][str(n)]={k:mean/frozen['reference_only'][k]-1 for k in ['volume_based_pressure_Pa','contour_based_pressure_Pa']}
    for step in [0,250,500,750,1000,1250,1500,1750,2000]:
        path=run/('slice_initial.csv' if step==0 else f'slice_step_{step}.csv')
        sl=list(csv.DictReader(path.open()))
        assert len(sl)==4096 and len({(r['x_lu'],r['y_lu'],r['z_lu']) for r in sl})==4096
        assert all(math.isfinite(float(v)) for r in sl for v in r.values())
    checks['all9_prescribed_slices_complete_and_finite']=True
    checks['final_duplicate_slice_byte_equal']=(run/'slice_step_2000.csv').read_bytes()==(run/'slice_final.csv').read_bytes()
    assert checks['final_duplicate_slice_byte_equal']
    with (HERE/'pressure_windows.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(windows[0]));writer.writeheader();writer.writerows(windows)
    # Diagnostic figure only: raw traces, no smoothing, no statistical error bands.
    with plt.rc_context({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42}):
        fig,axs=plt.subplots(2,2,figsize=(11,7),layout='constrained')
        t=a['step'];blue='#0072B2';orange='#D55E00'
        ax=axs[0,0]
        ax.plot(t,p/1e6,color=blue,lw=1,label=r'$\Delta p_h$')
        ax.plot(t,a['p_bulk_candidate_inside_minus_outside_Pa']/1e6,color=orange,ls='--',lw=.8,label='Bulk-pressure candidate')
        for k,style,label in [('volume_based_pressure_Pa',':','Volume-radius reference'),('contour_based_pressure_Pa','-.','Contour-radius reference')]:
            ax.axhline(frozen['reference_only'][k]/1e6,color='0.3',ls=style,lw=1,label=label)
        ax.axvspan(1501,1750,color='0.9');ax.axvspan(1751,2000,color='0.8')
        ax.set(title='(a) Complete pressure trace',xlabel='Step',ylabel='Pressure difference (MPa)');ax.legend(fontsize=8,loc='lower right')
        ax=axs[0,1];use=t>=1501
        ax.plot(t[use],p[use]/1e6,color=blue,lw=1)
        ax.axhline(p[-500:].mean()/1e6,color=orange,ls='--',label='Last 500 mean')
        ax.axhline(p[-250:].mean()/1e6,color='0.25',ls=':',label='Last 250 mean')
        ax.axvline(1750.5,color='0.65',ls='--',lw=.8)
        ax.set(title='(b) Prespecified tail window (zoom)',xlabel='Step',ylabel='Pressure difference (MPa)');ax.legend(fontsize=8)
        ax=axs[1,0]
        ax.plot(t,a['liquid_drift']*1e6,color=blue,label='Liquid amount')
        ax.plot(t,a['total_mass_drift']*1e6,color=orange,ls='--',label='Total mass')
        ax.axhline(0,color='0.6',lw=.6)
        ax.set(title='(c) Conservation relative to step 0',xlabel='Step',ylabel=r'Relative change ($10^{-6}$)');ax.legend(fontsize=8)
        ax=axs[1,1];ax.semilogy(t,a['max_u_m_s'],color=blue,lw=1)
        ax.set(title='(d) Residual motion',xlabel='Step',ylabel='Maximum speed (m/s)')
        for ax in axs.flat:ax.grid(alpha=.18)
        fig.savefig(HERE/'diagnostics.png',dpi=180,facecolor='white')
        fig.savefig(HERE/'diagnostics.pdf',facecolor='white')
        plt.close(fig)
    checks.update(raw_inputs_unchanged=all(sha(Path(f))==h for f,h in before.items()),
                  formal_gate_upgraded=False,new_simulation_started=False)
    assert checks['raw_inputs_unchanged']
    (HERE/'input_hashes.json').write_text(json.dumps(before,indent=2)+'\n')
    (HERE/'independent_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    (HERE/'figure_provenance.json').write_text(json.dumps(dict(raw_history=str(run/'history.csv'),
        raw_history_sha256=sha(run/'history.csv'),matplotlib_version=matplotlib.__version__,numpy_version=np.__version__,
        transformations=['pressure Pa to MPa','drift multiplied by 1e6','raw maximum speed on log axis','prespecified tail crop'],
        smoothing='none',uncertainty_bands='none; deterministic single trajectory',
        purpose='internal diagnostic figure; no journal compliance claim',
        description='Pressure oscillations decay; last 500 steps remain oscillatory. Conservation stays within about four parts per million; speed approaches 0.017 m/s.'),indent=2)+'\n')
    print(json.dumps({k:v for k,v in checks.items() if k not in ['windows']},indent=2))

if __name__=='__main__':main()
