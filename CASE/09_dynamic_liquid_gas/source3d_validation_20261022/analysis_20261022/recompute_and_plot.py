#!/usr/bin/env python3
"""Independent completed-data audit. Never imports the frozen analysis or solver."""
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
BATCH='source3d_translation_20261022_v1'
EVIDENCE=BASE/'evidence'/BATCH
OUTPUT=BASE/'output'/BATCH
DIRECTIONS=['x+','x-','y+','y-','z+','z-','xyz+','xyz-','zero']
AXES='xyz'
manifest=json.loads((EVIDENCE/'manifest.json').read_text())
frozen=json.loads((HERE/'frozen_analysis.json').read_text())
frozen_index={(r['variant'],r['N'],r['direction']):r for r in frozen['cases']}
assert (EVIDENCE/'exit_code.txt').read_text().strip()=='0'
assert manifest['independent_exit_code']==0 and manifest['finished_utc']
assert manifest['source_hashes_unchanged'] and not manifest['source_mismatches']
assert len(manifest['cases'])==36
expected={f'{BATCH}_{v}_n{n}_{d.replace("+","p").replace("-","m")}'
          for n in [16,32] for d in DIRECTIONS for v in ['old','new']}
actual={r['run_id'] for r in manifest['cases']}
assert actual==expected and len(actual)==36
cases=[]
histories={}
field_points=0
max_speed_disagreement=0.
max_endpoint_fourier_disagreement=0.
max_field_L2_disagreement=0.
max_field_sum_relative_disagreement=0.
for entry in manifest['cases']:
    run_id=entry['run_id']; out=OUTPUT/run_id
    assert entry['independent_exit_code']==0
    assert (EVIDENCE/run_id/'exit_code.txt').read_text().strip()=='0'
    child=json.loads((EVIDENCE/run_id/'manifest.json').read_text())
    assert child==entry
    assert dt.datetime.fromisoformat(entry['finished_utc'])>=dt.datetime.fromisoformat(entry['started_utc'])
    assert (EVIDENCE/run_id/'console.log').stat().st_size>0
    cfg=json.loads((out/'config.json').read_text())
    result=json.loads((out/'result.json').read_text())
    n=cfg['N']; variant=cfg['variant']; direction=cfg['direction']; steps={16:500,32:1000}[n]
    assert (variant,n,direction)==(entry['variant'],entry['N'],entry['direction'])
    assert cfg['steps']==steps and cfg['tau']==1 and cfg['chemical_potential']==0 and cfg['MPI_ranks']==1
    u=np.array([(-.008 if direction.endswith('-') else .008)
                if direction!='zero' and a in direction else 0. for a in AXES])
    assert np.array_equal(u,np.array(cfg['u']))
    assert result['completed_steps']==result['requested_steps']==steps and result['safe']
    assert all(result[k]=='NOT_EVALUATED' for k in ['NUMERICAL_GATE','RESULT_PASS','geometry_PASS'])
    h=np.genfromtxt(out/'history.csv',delimiter=',',names=True)
    assert len(h)==steps+1 and np.array_equal(h['step'],np.arange(steps+1))
    assert all(np.isfinite(h[k]).all() for k in h.dtype.names)
    assert (h['nodes']==n**3).all() and (h['finite']==1).all()
    sums=h['phase_sum']
    # Subtract before division, with extended precision: ratio-then-minus-one
    # would introduce avoidable cancellation at drifts of order 1e-13.
    drift=np.asarray((sums.astype(np.longdouble)-np.longdouble(sums[0]))/np.longdouble(sums[0]),dtype=float)
    assert np.max(np.abs(drift-h['relative_drift']))<2e-16
    imax=int(np.argmax(np.abs(drift)))
    record=dict(run_id=run_id,variant=variant,N=n,direction=direction,steps=steps,rows=len(h),
                max_abs_phase_drift=float(abs(drift[imax])),drift_peak_step=imax,
                signed_drift_at_peak=float(drift[imax]),final_phase_drift=float(drift[-1]),
                phi_min=float(np.min(h['phi_min'])),phi_max=float(np.max(h['phi_max'])),
                final_L2=float(h['fluctuation_L2'][-1]),components={})
    for axis in AXES:
        z=h['re_'+axis]+1j*h['im_'+axis]
        phase=np.unwrap(np.angle(z))
        amp_error=abs(abs(z[-1])/abs(z[0])-1)
        item=dict(phase_change=float(phase[-1]-phase[0]),amplitude_relative_error=float(amp_error))
        a=AXES.index(axis)
        if u[a]!=0:
            # Independent regression implementation, using the actual stored step array.
            regression=np.polynomial.polynomial.polyfit(h['step'],phase,1)
            measured=-regression[1]*n/(2*np.pi)
            item.update(speed=float(measured),speed_ratio=float(measured/u[a]),
                        speed_relative_error=float(abs(measured/u[a]-1)))
            reference=frozen_index[variant,n,direction]['components'][axis]['speed_ratio']
            max_speed_disagreement=max(max_speed_disagreement,abs(item['speed_ratio']-reference))
            assert abs(item['speed_ratio']-reference)<1e-11
        record['components'][axis]=item
    for name,t in [('initial.csv',0),('final.csv',steps)]:
        field=np.genfromtxt(out/name,delimiter=',',names=True)
        assert len(field)==n**3
        field_points+=len(field)
        assert all(np.isfinite(field[k]).all() for k in field.dtype.names)
        coords=np.column_stack([field[a] for a in AXES])
        integers=coords.astype(int)
        assert np.array_equal(coords,integers)
        assert integers.min()==0 and integers.max()==n-1
        assert len(np.unique(integers,axis=0))==n**3
        exact=.5+.05/3*np.cos(2*np.pi*(coords-u*t)/n).sum(axis=1)
        assert np.max(np.abs(exact-field['exact_phi']))<1e-12
        l2=float(np.linalg.norm(field['phi']-exact)/np.linalg.norm(exact-.5))
        l2difference=abs(l2-float(h['fluctuation_L2'][t]))
        max_field_L2_disagreement=max(max_field_L2_disagreement,l2difference)
        assert l2difference<1e-10
        sum_difference=abs(np.sum(field['phi'])-h['phase_sum'][t])/sums[0]
        max_field_sum_relative_disagreement=max(max_field_sum_relative_disagreement,float(sum_difference))
        assert sum_difference<1e-10
        cube=np.empty((n,n,n));cube[tuple(integers.T)]=field['phi']-.5
        fft=np.fft.fftn(cube)/(n**3)
        for a,axis in enumerate(AXES):
            index=[0,0,0];index[a]=1
            observed=h['re_'+axis][t]+1j*h['im_'+axis][t]
            difference=abs(fft[tuple(index)]-observed)
            max_endpoint_fourier_disagreement=max(max_endpoint_fourier_disagreement,float(difference))
            assert difference<1e-11
    cases.append(record)
    histories[variant,n,direction]=h

index={(r['variant'],r['N'],r['direction']):r for r in cases}
summary=[]
for variant in ['old','new']:
    for n in [16,32]:
        subset=[r for r in cases if r['variant']==variant and r['N']==n]
        moving=[c for r in subset for c in r['components'].values() if 'speed_ratio' in c]
        peak=max(subset,key=lambda r:r['max_abs_phase_drift'])
        summary.append(dict(variant=variant,N=n,
            speed_ratio_min=min(c['speed_ratio'] for c in moving),speed_ratio_max=max(c['speed_ratio'] for c in moving),
            max_speed_error=max(c['speed_relative_error'] for c in moving),
            max_amplitude_error=max(c['amplitude_relative_error'] for c in moving),
            max_endpoint_L2=max(r['final_L2'] for r in subset),
            max_abs_phase_drift=peak['max_abs_phase_drift'],drift_peak_run_id=peak['run_id'],
            drift_peak_step=peak['drift_peak_step'],drift_peak_final=peak['final_phase_drift']))
direction_checks=[]
for n in [16,32]:
    for sign in ['+','-']:
        ratios=[index['new',n,a+sign]['components'][a]['speed_ratio'] for a in AXES]
        direction_checks.append(dict(N=n,comparison='axis_spread_'+sign,difference=max(ratios)-min(ratios)))
    reverse=max(abs(index['new',n,a+'+']['components'][a]['speed_ratio']-index['new',n,a+'-']['components'][a]['speed_ratio']) for a in AXES)
    diagonal=max(abs(index['new',n,'xyz'+s]['components'][a]['speed_ratio']-index['new',n,a+s]['components'][a]['speed_ratio']) for s in ['+','-'] for a in AXES)
    direction_checks.extend([dict(N=n,comparison='reverse_gap',difference=reverse),dict(N=n,comparison='diagonal_axis_gap',difference=diagonal)])

refinement=[]
for direction in DIRECTIONS[:-1]:
    for axis in direction[:-1]:
        coarse=index['new',16,direction]['components'][axis]['speed_relative_error']
        fine=index['new',32,direction]['components'][axis]['speed_relative_error']
        refinement.append(dict(direction=direction,axis=axis,coarse_error=coarse,fine_error=fine,
                               reduction_factor=coarse/fine,two_level_log2_ratio=math.log2(coarse/fine)))
peak=max(cases,key=lambda r:r['max_abs_phase_drift'])
report=dict(batch_id=BATCH,complete_cases=36,child_independent_exits_all_zero=True,
            total_history_rows=sum(c['rows'] for c in cases),total_endpoint_field_points=field_points,
            wall_seconds=(dt.datetime.fromisoformat(manifest['finished_utc'])-dt.datetime.fromisoformat(manifest['started_utc'])).total_seconds(),
            max_speed_ratio_difference_from_frozen=max_speed_disagreement,
            max_FFT_coefficient_difference_from_history=max_endpoint_fourier_disagreement,
            max_field_L2_difference_from_history=max_field_L2_disagreement,
            max_field_sum_relative_difference_from_history=max_field_sum_relative_disagreement,
            summary=summary,direction_checks=direction_checks,refinement=refinement,
            global_drift_peak=peak,cases=cases,
            zero_velocity_max_L2=max(float(histories[v,n,'zero']['fluctuation_L2'].max()) for v in ['old','new'] for n in [16,32]),
            max_stationary_phase_change=max(abs(c['phase_change']) for r in cases for c in r['components'].values() if 'speed_ratio' not in c),
            prescribed_Mach_max=.024,formal_Gates='NOT_EVALUATED')
(HERE/'independent_checks.json').write_text(json.dumps(report,indent=2)+'\n')
for name,rows in [('summary.csv',summary),('direction_checks.csv',direction_checks),('refinement.csv',refinement)]:
    with (HERE/name).open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
with (HERE/'case_metrics.csv').open('w') as f:
    flattened=[]
    for record in cases:
        base={k:v for k,v in record.items() if k!='components'}
        for axis,item in record['components'].items():flattened.append(dict(base,axis=axis,**item))
    keys=list(dict.fromkeys(k for r in flattened for k in r))
    writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(flattened)

# Provisional internal diagnostic: deterministic results, no replicate error bars.
with plt.rc_context({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'savefig.facecolor':'white'}):
    fig,axes=plt.subplots(2,2,figsize=(11,7.6),layout='constrained')
    colors={'old':'#A23B00','new':'#006DA8'}
    ax=axes[0,0]
    for variant in ['old','new']:
        for n,marker,style in [(16,'o','--'),(32,'s','-')]:
            ratios=[index[variant,n,d]['components'][d[0]]['speed_ratio'] for d in DIRECTIONS[:-1]]
            ax.plot(range(8),ratios,marker=marker,linestyle=style,color=colors[variant],label=f'{variant}, N={n}',markersize=4)
    ax.axhline(1,color='0.35',linestyle=':',linewidth=1,label='prescribed speed')
    ax.set(xticks=range(8),xticklabels=DIRECTIONS[:-1],ylim=(0,1.07),ylabel='Measured speed / prescribed speed',title='(a) Half-speed defect and direction checks')
    ax.tick_params(axis='x',labelsize=9);ax.legend(fontsize=8,ncol=2,loc='lower right')
    ax=axes[0,1]
    s=[next(r for r in summary if r['variant']=='new' and r['N']==n) for n in [16,32]]
    dx=np.array([1/16,1/32]);err=np.array([r['max_speed_error'] for r in s])*100
    ax.loglog(dx,err,'o-',color=colors['new'],label='max. corrected speed error')
    ax.loglog(dx,err[0]*(dx/dx[0])**2,':',color='0.35',label=r'$O((1/N)^2)$ reference')
    ax.loglog(dx,[5,2],'x--',color='#555555',label='frozen limits')
    ax.set(xticks=dx,xticklabels=['1/16','1/32'],xlabel='Relative mesh spacing, 1/N',ylabel='Speed error (%)',title='(b) Error reduction over two grids')
    ax.minorticks_off();ax.legend(fontsize=8)
    ax=axes[1,0]
    for variant in ['old','new']:
        h=histories[variant,32,'x+'];z=h['re_x']+1j*h['im_x'];angles=np.unwrap(np.angle(z))
        displacement=-(angles-angles[0])/(2*np.pi)
        ax.plot(h['step']/1000,displacement,color=colors[variant],linestyle='--' if variant=='old' else '-',label=f'{variant}, N=32')
    ax.plot([0,1],[0,.25],':',color='0.2',label='exact advection')
    ax.set(xlim=(0,1),ylim=(0,.27),xlabel='Step / 1000',ylabel='Fourier displacement / domain length',title='(c) Full time histories, positive x direction')
    ax.legend(fontsize=8)
    ax=axes[1,1]
    for variant,marker in [('old','o'),('new','s')]:
        values=[next(r['max_abs_phase_drift'] for r in summary if r['variant']==variant and r['N']==n) for n in [16,32]]
        ax.semilogy([16,32],values,marker=marker,color=colors[variant],label=variant)
    ax.axhline(1e-9,color='0.35',linestyle=':',label='frozen limit')
    ax.set(xticks=[16,32],xlabel='Nodes per axis, N',ylabel='Max. absolute relative phase drift',ylim=(1e-14,3e-9),title='(d) Whole-run maximum over all nine directions')
    ax.legend(fontsize=8)
    fig.savefig(HERE/'translation_diagnostics.png',dpi=200)
    fig.savefig(HERE/'translation_diagnostics.pdf')
    plt.close(fig)
provenance=dict(audience='internal research diagnostic; journal requirements not assessed',
                sources=['raw history.csv and initial.csv/final.csv for all 36 cases'],
                transformations=['Fourier phase unwrapping','ordinary linear phase regression over all saved steps',
                                 'independent endpoint NumPy FFT','per-grid maximum over all cases for error/drift panels',
                                 'percent scaling for speed error','base-10 log axes in panels b and d'],
                uncertainty='deterministic trajectories; no independent replicates or confidence intervals',
                smoothing='none',exclusions='zero-velocity cases omitted only from speed-ratio panel; retained in all checks and drift maxima',
                diagonal_panel_encoding='panel a shows the x component for xyz directions; all three components are retained and checked in case_metrics.csv',
                colors={'old':'#A23B00','new':'#006DA8'},dimensions_inches=[11,7.6],PNG_DPI=200,
                numpy_version=np.__version__,matplotlib_version=matplotlib.__version__,
                alt_text='Old trajectories travel at half speed on both grids; corrected speed approaches the prescribed value as the grid is refined; direction curves overlap, and all phase drifts are below the frozen threshold.')
(HERE/'figure_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['complete_cases','total_history_rows','total_endpoint_field_points','wall_seconds','max_speed_ratio_difference_from_frozen','max_FFT_coefficient_difference_from_history']},indent=2))
