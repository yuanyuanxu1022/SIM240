"""Provisional internal validation figure; source/transformations recorded below."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
d=json.loads((HERE/'independent_review.json').read_text())
r=d['all_cases']; batch=d['batch_id']
colors=['#006397','#A64200','#006B55','#734E8A','#333333']
with plt.rc_context({'font.size':10,'axes.titlesize':11,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'figure.facecolor':'white','axes.facecolor':'white'}):
    fig,axs=plt.subplots(2,2,figsize=(11.3,8.2),layout='constrained')
    a,b,c,e=axs.flat
    directions=['x','y','z','xy','xyz']; x=np.arange(5)
    for n,alpha,col,marker,shift in ((16,1,colors[0],'o',-.07),(32,4,colors[1],'s',.07)):
        group=[next(t for t in r if t['id']==f'linear_n{n}_{di}_a{alpha}') for di in directions]
        a.plot(x+shift,[100*t['continuum_relative_error'] for t in group],marker=marker,color=col,label=f'N={n}, alpha={alpha}')
        b.plot(x+shift,[(t['rate_ratio']-1)*1e8 for t in group],marker=marker,color=col,label=f'N={n}')
    a.axhline(7,color=colors[0],ls=':',label='Coarse limit: 7%')
    a.axhline(2,color=colors[1],ls='--',label='Fine limit: 2%')
    a.set(xticks=x,xticklabels=directions,ylabel='Absolute rate error vs continuum (%)',ylim=(0,7.7),title='(a) Same physical model; two grid spacings')
    a.legend(fontsize=8,loc='upper left')
    b.axhline(0,color='#777777',lw=.7)
    b.set(xticks=x,xticklabels=directions,ylim=(-1.65,1.6),ylabel=r'$(r_{fit}/r_{discrete}-1)\times10^8$',title='(b) Discrete reference agreement')
    b.text(.02,.96,'Frozen relative limit: 1e-4 (outside displayed scale)',transform=b.transAxes,fontsize=8,va='top')
    b.legend(fontsize=8)
    groups=set()
    plotdata=[]
    for t in r:
        if t['kind']=='source':continue
        p=BASE/'output'/batch/(batch+'_'+t['id'])/'history.csv'
        with p.open() as f: rows=list(csv.DictReader(f))
        q=np.array([row['phase_sum'] for row in rows],dtype=np.longdouble)
        drift=np.asarray((q-q[0])/q[0],float)
        step=np.arange(len(q));coarse=t['N']==16;linear=t['kind']=='linear'
        col=colors[0 if coarse else 1] if linear else colors[2 if coarse else 3]
        ls='-' if linear else '--'; label=f'N={t["N"]}, {t["kind"]}'
        c.plot(step,drift/1e-13,color=col,ls=ls,lw=.9,label=label if label not in groups else None)
        groups.add(label)
        plotdata.append({'id':t['id'],'step':step.tolist(),'relative_drift':drift.tolist()})
    peak=max((t for t in r if 'phase_drift_max' in t),key=lambda t:t['phase_drift_max'])
    c.plot(peak['phase_drift_step'],peak['phase_drift_max']/1e-13,'ko',ms=4)
    c.set(xlabel='Step (coarse and fine have different time steps)',ylabel=r'$(Q_n-Q_0)/Q_0\;[10^{-13}]$',title='(c) All 14 unforced histories; no smoothing')
    c.text(.02,.94,'Frozen absolute limit: 1e-9 (outside displayed scale)',transform=c.transAxes,fontsize=8,va='top')
    c.legend(fontsize=8,loc='center left')
    nl=[t for t in r if t['kind']=='nonlinear'];labels=[f'N={t["N"]}\ncenter={"0.1" if "010" in t["id"] else "0.9"}' for t in nl]
    for j,t in enumerate(nl):
        e.plot(j,t['step_error'],marker='o' if t['N']==16 else 's',ms=8,color=colors[0] if t['N']==16 else colors[1],ls='none')
    e.axhline(1e-12,color='#333333',ls=':',label='Frozen limit: 1e-12')
    e.set(xticks=np.arange(4),xticklabels=labels,xlim=(-.5,3.5),yscale='log',ylim=(1e-16,3e-12),ylabel='Maximum local update residual (lattice units)',title='(d) Nonlinear all-step 3D independent reconstruction')
    e.legend(fontsize=8,loc='upper left')
    for ax in axs.flat:ax.grid(axis='y',alpha=.18)
    fig.suptitle('Alpha spatial validation | frozen protocol v1 | 16 completed cases',fontsize=13)
    fig.savefig(HERE/'alpha_diagnostics.png',dpi=300,facecolor='white')
    fig.savefig(HERE/'alpha_diagnostics.pdf',facecolor='white')
    plt.close(fig)
(HERE/'figure_source_data.json').write_text(json.dumps({'metrics':r,'full_time_drift':plotdata},indent=2)+'\n')
provenance={'purpose':'internal validation report; journal specifications not applicable yet','width_inches':11.3,'height_inches':8.2,
 'matplotlib':matplotlib.__version__,'numpy':np.__version__,'png_dpi':300,
 'input':str(HERE/'independent_review.json'),'input_sha256':hashlib.sha256((HERE/'independent_review.json').read_bytes()).hexdigest(),
 'raw_hash_manifest':'raw_input_hashes.json','source_data':'figure_source_data.json',
 'transformations':['a: absolute fitted rate / continuum - 1, percent','b: fitted/discrete rate - 1 times 1e8; fixed 25%-100% fit window',
                    'c: signed (Q-Q0)/Q0 from decimal phase_sum in long double; scale 1e-13; every recorded step',
                    'd: per-case maximum absolute nonlinear local update residual over all saved steps'],
 'uncertainty':'deterministic numerical diagnostics; no statistical intervals or repeats','exclusions':'none; source fixtures excluded only from unforced phase-drift definition',
 'zero_policy':'linear axes a,b,c include zero; log panel d contains four positive update residuals; zero mu errors not plotted',
 'alt_text':'Five modal rate errors decrease by about fourfold after grid spacing halves. Fourteen unforced phase histories remain below 2.12e-13 relative drift. All nonlinear update residuals are below 6e-16.',
 'visual_inspection':'pending'}
(HERE/'figure_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
