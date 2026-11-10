"""Deterministic plots of existing fit and held-group results; no refitting."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from models import normalized

HERE=Path(__file__).resolve().parent
def rows(name):return list(csv.DictReader((HERE/name).open()))
fits=json.loads((HERE/'fits.json').read_text());summary=rows('summary.csv');data=rows('data_roles.csv')
colors={'G4':'#0072B2','G6':'#D55E00','C3_logK':'#666666','C4_logK':'#009E73'}
styles={'G4':'-','G6':'--','C3_logK':':','C4_logK':'-.'}
fig,axs=plt.subplots(2,2,figsize=(11,8),layout='constrained');curves=[]
for ax,dr in zip(axs[0],('P','T')):
    t=np.linspace(1e-5,2,401)
    ax.axvspan(0,1/3,color='.94');ax.axvspan(1.6,2,color='.94')
    for name in ('G4','G6','C4_logK'):
        y=normalized(1.6,t,fits[name],dr)
        ax.plot(t,y,color=colors[name],ls=styles[name],label=name)
        curves.append({'direction':dr,'model':name,'s':1.6,'t':t.tolist(),'K_over_flat':y.tolist()})
    selected=[r for r in data if r['direction']==dr and float(r['h'])==75]
    ax.scatter([float(r['t']) for r in selected],[float(r['K'])/(75e-9)**3*12 for r in selected],c='k',marker='o',s=28,label='Existing DNS (5 nm)',zorder=4)
    ax.set(xlabel=r'Depth / gap, $t=d/h$',ylabel=r'$K/K_{flat}$',title=('(a) Along grooves' if dr=='P' else '(b) Across grooves')+'; w=120 nm, h=75 nm')
    ax.grid(alpha=.2);ax.legend(fontsize=8);ax.set_xlim(0,2)
groups=[('leave_h','P'),('leave_h','T'),('leave_d','P'),('leave_d','T')]
for ax,metric,title in zip(axs[1],('MAE_percent','max_abs_percent'),('(c) Held-group mean absolute error','(d) Held-group worst absolute error')):
    for j,name in enumerate(('G4','G6','C3_logK','C4_logK')):
        ys=[]
        for scheme,dr in groups:
            found=[r for r in summary if r['model']==name and r['scheme']==scheme and r['direction']==dr]
            ys.append(float(found[0][metric]) if found else np.nan)
        ax.bar(np.arange(4)+(j-1.5)*.18,ys,width=.18,color=colors[name],label=name,hatch=['','//','..','xx'][j])
    ax.set_xticks(np.arange(4),['Leave h\nAlong','Leave h\nAcross','Leave d\nAlong','Leave d\nAcross'])
    ax.set(ylabel='Relative K error (%)',title=title);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    ax.text(.02,.98,'C4 leave-h: unavailable (rank deficient)',transform=ax.transAxes,va='top',fontsize=8)
    ax.set_ylim(0,ax.get_ylim()[1]*1.18);ax.legend(fontsize=8,loc='upper right')
fig.suptitle('Constrained candidates: 15 development geometries; retrospective checks',fontsize=13)
for ext in ('png','pdf','svg'):fig.savefig(HERE/('comparison.'+ext),dpi=180)
plt.close(fig)
(HERE/'figure_source.json').write_text(json.dumps({'curves':curves,'summary':summary,'data':data,'notes':['Shading is outside proposed depth interval at s=1.6','Missing C4 leave-h bars are unavailable, not zero','No uncertainty bars: independent discretization uncertainty not available here']},indent=2)+'\n')
(HERE/'figure_provenance.json').write_text(json.dumps({'matplotlib':matplotlib.__version__,'inputs':{str(HERE/n):hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('fits.json','summary.csv','data_roles.csv','plot_results.py','models.py')},'outputs':['comparison.png','comparison.pdf','comparison.svg']},indent=2)+'\n')
print('PNG/PDF/SVG written')
