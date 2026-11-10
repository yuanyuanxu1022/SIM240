"""Present only the previously reviewed two-width evidence; no solver/field processing."""
from pathlib import Path
import csv
import hashlib
import json
import math
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib import font_manager
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SRC = ROOT/'docs/reports/PAPER1_scientific_question_decision_20261110'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

protected = json.loads((OUT/'protected_inputs.json').read_text())
for rel, digest in protected.items():
    assert sha(ROOT/rel) == digest, rel
pairs = list(csv.DictReader((SRC/'paired_evidence.csv').open()))
terms = list(csv.DictReader((SRC/'mechanism_link.csv').open()))
selected = list(csv.DictReader((SRC/'selected_records.csv').open()))
assert len(pairs) == 4 and len(selected) == 8 and len(terms) == 40

def pair(w, dx):
    return next(r for r in pairs if float(r['w_nm']) == w and float(r['dx_nm']) == dx)

def component(w, dx, direction, scheme='wall_quadratic'):
    return [r for r in terms if float(r['w_nm']) == w and float(r['dx_nm']) == dx
            and r['direction'] == direction and r['scheme'] == scheme]

def md_table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']
                     +['| '+' | '.join(map(str,r))+' |' for r in rows])

scalar_rows, correction_rows, main_rows, ledger_rows = [], [], [], []
for w in (60, 240):
    for dx in (5, 2.5):
        r = pair(w, dx)
        scalar_rows.append([w, dx]+[f'{float(r[k]):.5f}' for k in ('F_P','F_T','A_reference','B')])
        correction_rows.append([w, dx, f'{float(r["A_bias_percent"]):.2f}',
                               f'{float(r["scalar_c_opt"]):.5f}',f'{float(r["scalar_floor_percent"]):.2f}'])
        for scheme in ('wall_quadratic', 'odd_extension'):
            for direction in ('P','T'):
                ts = component(w,dx,direction,scheme)
                assert len(ts) == (2 if direction == 'P' else 3)
                S = sum(float(t['term_over_directional_R_LC']) for t in ts)
                rr = float(ts[0]['drive_excess']); b = rr-S
                assert math.isclose(b,float(ts[0]['signed_residual']),abs_tol=1e-13)
                ledger_rows.append([w,dx,scheme,direction, f'{S:.8f}',f'{rr:.8f}',f'{b:+.8f}',f'{100*b/rr:+.5f}'])
                if dx == 2.5 and scheme == 'wall_quadratic':
                    vals = {t['term']:float(t['term_over_directional_R_LC']) for t in ts}
                    main_rows.append([w,direction,f'{vals["profile_departure"]:.5f}',
                        f'{vals["transverse_gradient"]:.5f}' if 'transverse_gradient' in vals else '—',
                        f'{vals["axial_gradient"]:.5f}' if 'axial_gradient' in vals else '—',
                        f'{vals["vertical_velocity_gradient"]:.5f}' if 'vertical_velocity_gradient' in vals else '—',
                        f'{S:.5f}',f'{rr:.5f}',f'{b:+.5f}'])

for lang in ('CN','EN'):
    cn = lang == 'CN'
    text = ('# 成对宽度证据表（候选，未合入）\n\n' if cn else '# Paired-width evidence tables (unmerged candidates)\n\n')
    text += ('工作标签W1—W4，不占用正式编号。h=75 nm、d=120 nm、槽/凸台等宽；w=60/240 nm对应P=120/480 nm。P方向=沿槽，T方向=横槽。下列为同一已知开发组的离散比较，网格不是独立重复样本。\n\n' if cn else
             'W1–W4 are working labels, not formal manuscript numbers. h=75 nm, d=120 nm, with equal groove and ridge widths; w=60/240 nm corresponds to periods P=120/480 nm. Direction P is parallel to the grooves and T is transverse. The grids are numerical resolutions of the same known development geometries, not independent replicates.\n\n')
    text += ('## 表W1 导度倍率与方向比\n\n' if cn else '## Table W1. Conductance factors and anisotropy\n\n')
    text += md_table(['w (nm)','Δx (nm)','F_P','F_T','A_Δ','B=A_LC/A_Δ'], scalar_rows)+'\n\n'
    text += ('F_i=K_i^Δ/K_i^LC；A_Δ=K_P^Δ/K_T^Δ；A_LC=4.90822394。F是从既有导度算得的倍率，不是重新标定的V2因子。\n\n' if cn else
             'F_i=K_i^Δ/K_i^LC, A_Δ=K_P^Δ/K_T^Δ, and A_LC=4.90822394. F is calculated from existing conductances; it is not a newly calibrated V2 factor.\n\n')
    text += ('## 表W2 共同倍率的辅助诊断\n\n' if cn else '## Table W2. Auxiliary diagnostic for a common multiplier\n\n')
    text += md_table(['w (nm)','Δx (nm)','100(B−1) (%)','c_*','100E_* (%)'],correction_rows)+'\n\n'
    text += ('允许每种几何各自选最有利的共同倍率：c_*=2/(a_P+a_T)，E_*=|a_P−a_T|/(a_P+a_T)，a_i=1/F_i。E_*为至少一方向相对各自离散参考的最小可能绝对偏差，不是物理导度下界、连续误差界或方向分别修正模型的限制。\n\n' if cn else
             'Each geometry is allowed its own optimal common multiplier: c_*=2/(a_P+a_T), E_*=|a_P−a_T|/(a_P+a_T), a_i=1/F_i. E_* is the smallest attainable maximum absolute relative discrepancy across the two discrete principal conductances. It is neither a physical conductance bound nor a continuous-solution error bound, and does not constrain models with separate directional factors.\n\n')
    text += ('## 表W3 绝对归一化梯度差额（2.5 nm，主模板）\n\n' if cn else '## Table W3. Absolute normalized gradient-excess contributions (2.5 nm, primary stencil)\n\n')
    heads = (['w (nm)','方向','剖面偏离','跨槽梯度','沿程梯度','垂直速度梯度','S_i','r_i','b_i=r_i−S_i'] if cn else
             ['w (nm)','Direction','Profile departure','Cross-groove gradient','Streamwise gradient','Vertical-velocity gradients','S_i','r_i','b_i=r_i−S_i'])
    text += md_table(heads,main_rows)+'\n\n'
    text += ('各分量均除以方向自身的R_i^LC，为无量纲绝对贡献，未再除以正项和。沿槽剖面项兼含通量分配改变；两方向分组不同。破折号表示该分组不适用，不代表测得零。r_i=K_i^LC/K_i^Δ−1，S_i为非负项和，b_i保留正负号；未将S_i缩放成r_i。\n\n' if cn else
             'Each contribution is divided by its own directional R_i^LC and is dimensionless; it is not divided by the positive-term sum. The parallel profile term also includes changes in flux allocation. Groupings differ between directions. A dash denotes an inapplicable group, not a measured zero. Here r_i=K_i^LC/K_i^Δ−1, S_i is the sum of nonnegative terms, and b_i retains its sign. S_i has not been rescaled to r_i.\n\n')
    text += ('## 表W4 全部网格与两导数模板的余额\n\n' if cn else '## Table W4. Signed residuals for both grids and derivative stencils\n\n')
    text += md_table(['w (nm)','Δx (nm)','Stencil','Direction','S_i','r_i','b_i=r_i−S_i','100b_i/r_i (%)'],ledger_rows)+'\n\n'
    text += ('wall_quadratic为主模板；odd_extension为半格奇延拓模板。这里余额定义为r_i−S_i，与既有S14“正项和减驱动差额”的符号相反，绝对值相同。两者不应混写。该余额是分解账差，不是总输入功余额或连续精度指标。原窄槽网格目标FAIL、宽槽只有两档的限制保留；不据此认证网格独立性。逐分量全精度和run_id见mechanism_link.csv，标量全精度见paired_evidence.csv。\n' if cn else
             'wall_quadratic is the primary stencil and odd_extension is the half-grid odd-extension stencil. The residual here is r_i−S_i, the negative of the existing S14 convention for the positive sum minus drive excess. Their absolute values agree. It is a decomposition residual, not the total input-power balance or a continuous-accuracy measure. The historical narrow-groove grid target remains FAIL; the wide groove has only two grids. These results do not establish grid independence. Full-precision components and run IDs are in mechanism_link.csv; scalar values are in paired_evidence.csv.\n')
    (OUT/f'TABLES_{lang}.md').write_text(text)

for name in ('selected_records.csv','paired_evidence.csv','mechanism_link.csv'):
    (OUT/name).write_bytes((SRC/name).read_bytes())

font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
cjk = font_manager.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()
colors = {'P':'#00689D','T':'#A94E00','profile':'#666666','gradient':'#00689D','vertical':'#8E559D'}
plot_manifest = {'dimensions_mm':[180,150], 'dpi':300, 'target_journal':'not specified; provisional review figure',
    'source_files':{str((SRC/n).relative_to(ROOT)):sha(SRC/n) for n in ('paired_evidence.csv','mechanism_link.csv','selected_records.csv')},
    'normalization':'F=K_discrete/K_LC; A=K_parallel/K_transverse; component/R_LC for each direction',
    'uncertainty':'no statistical intervals; grids are displayed explicitly',
    'component_selection':'primary stencil, 2.5 nm; other grid/stencil values retained in Table W4',
    'scale':'all linear; common 0 to 4.7 scale for both gradient panels',
    'svg_fonts':'glyphs converted to paths for portable appearance', 'matplotlib_version':matplotlib.__version__,
    'plotted_values':[], 'outputs':{}, 'warnings':[]}

for lang in ('EN','CN'):
    cn = lang == 'CN'
    with plt.rc_context({'font.family':cjk if cn else 'DejaVu Sans', 'font.size':8,
                         'axes.titlesize':9, 'axes.labelsize':8, 'xtick.labelsize':8,
                         'ytick.labelsize':8, 'legend.fontsize':6.8, 'pdf.fonttype':42,
                         'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False}):
        fig, axs = plt.subplots(2,2,figsize=(180/25.4,150/25.4),layout='constrained')
        fig.set_constrained_layout_pads(w_pad=.045,h_pad=.045,wspace=.055,hspace=.06)
        fig.suptitle(('固定开度分布下的成对宽度比较\n' if cn else 'Paired widths with an unchanged aperture distribution\n')
                     +r'$h=75$ nm, $d=120$ nm; $w/P=1/2$',fontsize=10)
        ax=axs[0,0]
        for dx in (5,2.5):
            for di,off in [('P',-.075),('T',.075)]:
                offset=off+(-.018 if dx==5 else .018)
                y=[float(pair(w,dx)['F_'+di]) for w in (60,240)]
                x=[i+offset for i in (0,1)]
                ax.scatter(x,y,s=30 if dx==2.5 else 39,marker='o' if di=='P' else 's',
                           facecolors=colors[di] if dx==2.5 else 'white',edgecolors=colors[di],linewidths=1.1,zorder=4)
                plot_manifest['plotted_values'].append({'language':lang,'panel':'a','direction':di,'dx_nm':dx,'values':y})
        ax.axhline(1,color='#444444',ls='--',lw=.9)
        ax.set(ylim=(0,1.08),xlim=(-.42,1.42),xticks=[0,1],xticklabels=['60','240'],
               xlabel=('槽宽 w (nm)' if cn else 'Groove width w (nm)'),ylabel=r'$F_i=K_i^\Delta/K_i^{LC}$')
        ax.set_title('(a) '+('导度倍率' if cn else 'Conductance factors'),loc='left')
        legend=[]
        for di in ('P','T'):
            for dx in (5,2.5):
                label=(('沿槽' if di=='P' else '横槽') if cn else ('Parallel' if di=='P' else 'Transverse'))+f', {dx:g} nm'
                legend.append(Line2D([],[],ls='none',marker='o' if di=='P' else 's',color=colors[di],
                                     markerfacecolor=colors[di] if dx==2.5 else 'white',label=label,markersize=4.5))
        ax.legend(handles=legend,loc='upper left',frameon=True,facecolor='white',edgecolor='none',framealpha=1,
                  ncol=2,columnspacing=.8,handletextpad=.35)
        ax=axs[0,1]
        for dx,off in ((5,-.035),(2.5,.035)):
            y=[float(pair(w,dx)['A_reference']) for w in (60,240)]
            ax.scatter([off,1+off],y,s=32 if dx==2.5 else 42,marker='o',
                       facecolors='#202020' if dx==2.5 else 'white',edgecolors='#202020',linewidths=1.1,zorder=4,
                       label=(f'离散参考, {dx:g} nm' if cn else f'Discrete reference, {dx:g} nm'))
        ALC=float(pairs[0]['A_LC']);ax.axhline(ALC,color=colors['P'],ls='--',lw=1.2,label=('局部立方律' if cn else 'Local cubic law'))
        for i,w in enumerate((60,240)):
            y=float(pair(w,2.5)['A_reference'])
            ax.annotate(f'{y:.3f}',(i+.035,y),xytext=(0,7),textcoords='offset points',ha='center',fontsize=7.5)
        ax.set(ylim=(0,5.55),xlim=(-.42,1.42),xticks=[0,1],xticklabels=['60','240'],
               xlabel=('槽宽 w (nm)' if cn else 'Groove width w (nm)'),ylabel=r'$A=K_{\parallel}/K_{\perp}$')
        ax.set_title('(b) '+('方向比' if cn else 'Anisotropy ratio'),loc='left')
        ax.legend(loc='lower right',frameon=False,handlelength=2)

        definitions={'P':[('profile_departure','profile','///',('剖面/通量分配偏离' if cn else 'Profile / flux allocation')),
                          ('transverse_gradient','gradient','...',('跨槽速度梯度' if cn else 'Cross-groove gradient'))],
                     'T':[('profile_departure','profile','///',('剖面导数偏离' if cn else 'Profile-derivative\ndeparture')),
                          ('axial_gradient','gradient','...',('主速度沿程梯度' if cn else 'Streamwise gradient')),
                          ('vertical_velocity_gradient','vertical','xxx',('垂直速度梯度组' if cn else 'Vertical-velocity\ngradients'))]}
        for ax,di,panel in ((axs[1,0],'P','c'),(axs[1,1],'T','d')):
            bottoms=[0.,0.];handles=[]
            for term,color,hatch,label in definitions[di]:
                vals=[]
                for w in (60,240):
                    ts=component(w,2.5,di)
                    vals.append(float(next(t for t in ts if t['term']==term)['term_over_directional_R_LC']))
                ax.bar([0,1],vals,bottom=bottoms,width=.45,color=colors[color],edgecolor='white',
                       hatch=hatch,linewidth=.8,label=label,zorder=3)
                # Dark outlines preserve segment boundaries in grayscale.
                ax.bar([0,1],vals,bottom=bottoms,width=.45,facecolor='none',edgecolor='#303030',linewidth=.5,zorder=3)
                bottoms=[a+b for a,b in zip(bottoms,vals)]
                handles.append(Patch(facecolor=colors[color],edgecolor='white',hatch=hatch,label=label))
                plot_manifest['plotted_values'].append({'language':lang,'panel':panel,'term':term,'values':vals})
            rr=[float(component(w,2.5,di)[0]['drive_excess']) for w in (60,240)]
            ax.scatter([0,1],rr,marker='D',s=24,color='black',zorder=6)
            for i,val in enumerate(rr):
                ax.annotate(f'$r_i={val:.3f}$',(i,val),xytext=(0,8),textcoords='offset points',ha='center',fontsize=7.3)
            handles.append(Line2D([],[],ls='none',marker='D',color='black',markersize=4,label=('驱动导度差额' if cn else 'Excess from conductance')))
            ax.legend(handles=handles,loc='upper right',frameon=False,handlelength=1.6,borderaxespad=.3)
            title=('沿槽梯度差额' if di=='P' else '横槽梯度差额') if cn else ('Parallel gradient excess' if di=='P' else 'Transverse gradient excess')
            ax.set_title(f'({panel}) '+title,loc='left')
            ax.set(ylim=(0,4.7),xlim=(-.5,1.5),xticks=[0,1],xticklabels=['60','240'],
                   xlabel=('槽宽 w (nm)' if cn else 'Groove width w (nm)'),
                   ylabel=(r'分量 / $R_i^{LC}$（无量纲）' if cn else r'Contribution / $R_i^{LC}$ (dimensionless)'))
            ax.set_yticks([0,1,2,3,4])
        for ax in axs.flat:
            ax.grid(axis='y',color='#dddddd',linewidth=.5,zorder=0)
            ax.set_axisbelow(True)
        fig.canvas.draw()
        renderer=fig.canvas.get_renderer();fw,fh=fig.canvas.get_width_height()
        for obj in fig.findobj(matplotlib.text.Text):
            if obj.get_visible() and obj.get_text():
                b=obj.get_window_extent(renderer)
                assert b.x0>=-1 and b.y0>=-1 and b.x1<=fw+1 and b.y1<=fh+1,(lang,obj.get_text(),b.bounds)
        base=OUT/f'width_evidence_{lang}'
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')
            for ext in ('png','pdf','svg'):
                fp=base.with_suffix('.'+ext)
                fig.savefig(fp,dpi=300,facecolor='white',transparent=False)
                plot_manifest['outputs'][fp.name]={'sha256':sha(fp),'bytes':fp.stat().st_size}
            plot_manifest['warnings'].extend(str(w.message) for w in ws)
        plt.close(fig)
        with Image.open(base.with_suffix('.png')) as im:
            plot_manifest['outputs'][base.name+'.png']['pixels']=list(im.size)
            plot_manifest['outputs'][base.name+'.png']['dpi']=im.info.get('dpi')
            assert im.size[0]>=2120 and im.size[1]>=1760
            if im.mode=='RGBA': assert im.getextrema()[3]==(255,255)

assert not any('Glyph' in w for w in plot_manifest['warnings'])
for rel,digest in protected.items(): assert sha(ROOT/rel)==digest,rel
plot_manifest['script_sha256']=sha(Path(__file__))
plot_manifest['protected_inputs_unchanged']=True
(OUT/'figure_manifest.json').write_text(json.dumps(plot_manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'figures':list(plot_manifest['outputs']),'warnings':plot_manifest['warnings'],
                  'protected_inputs_unchanged':True,'source_records':len(selected)},ensure_ascii=False))
