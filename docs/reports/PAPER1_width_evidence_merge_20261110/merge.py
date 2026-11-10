"""Apply the authorized, bounded bilingual width-evidence merge with reversible edits."""
from pathlib import Path
import csv
import difflib
import hashlib
import io
import json
import re
import shutil

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CAND=ROOT/'docs/reports/PAPER1_width_evidence_candidates_20261110'
SUP=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024'
before_hashes=json.loads((OUT/'before_hashes.json').read_text())
protected=json.loads((OUT/'protected_inputs.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for rel,digest in before_hashes.items(): assert sha(ROOT/rel)==digest,rel
for rel,digest in protected.items(): assert sha(ROOT/rel)==digest,rel
texts={rel:(ROOT/rel).read_text() for rel in before_hashes}
edits=[]
def replace(rel,old,new,reason):
    assert texts[rel].count(old)==1,(rel,reason,texts[rel].count(old))
    texts[rel]=texts[rel].replace(old,new)
    edits.append(dict(path=rel,operation='replace',before=old,after=new,reason=reason))
def append(rel,block,reason):
    texts[rel]+=block
    edits.append(dict(path=rel,operation='append',after=block,reason=reason))
def between(s,start,end): return s.split(start,1)[1].split(end,1)[0].strip()
def number(s):
    for a,b in [('表W1—W4','表S10—S13'),('Tables W1–W4','Tables S10–S13'),('图W1','图S1'),('Figure W1','Figure S1'),('Figures W1','Figures S1')]: s=s.replace(a,b)
    for i in range(1,5):
        s=s.replace(f'表W{i}',f'表S{i+9}').replace(f'Table W{i}',f'Table S{i+9}')
    for i in range(1,4): s=s.replace(f'CW{i}',f'S14.{i+2}')
    return s

table_files={10:'Table_S10_paired_width_conductance.csv',11:'Table_S11_common_multiplier.csv',
             12:'Table_S12_gradient_excess.csv',13:'Table_S13_gradient_residuals.csv'}
pairs=list(csv.DictReader((CAND/'paired_evidence.csv').open()))
terms=list(csv.DictReader((CAND/'mechanism_link.csv').open()))
records=list(csv.DictReader((CAND/'selected_records.csv').open()))
def write_csv(path,rows):
    assert not path.exists(),path
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

data10=[];data11=[];data13=[]
for w in (60.,240.):
    for dx in (5.,2.5):
        p=next(p for p in pairs if float(p['w_nm'])==w and float(p['dx_nm'])==dx)
        rec={r['direction']:r for r in records if float(r['w_nm'])==w and float(r['dx_nm'])==dx}
        shared=dict(h_nm=75.,d_nm=120.,w_nm=w,P_nm=2*w,dx_nm=dx,
                    run_id_P=rec['P']['run_id'],run_id_T=rec['T']['run_id'])
        data10.append(dict(shared,**{k:p[k] for k in ['F_P','F_T','A_reference','A_LC','B']},
                           source_P=rec['P']['source'],source_T=rec['T']['source']))
        data11.append(dict(shared,**{k:p[k] for k in ['A_bias_percent','scalar_c_opt','scalar_floor_percent']}))
        for scheme in ('wall_quadratic','odd_extension'):
            for direction in ('P','T'):
                ts=[t for t in terms if float(t['w_nm'])==w and float(t['dx_nm'])==dx
                    and t['direction']==direction and t['scheme']==scheme]
                vals={t['term']:t['term_over_directional_R_LC'] for t in ts}
                assert len(ts)==(2 if direction=='P' else 3)
                S=float(ts[0]['sum_positive']);r=float(ts[0]['drive_excess']);b=float(ts[0]['signed_residual'])
                data13.append(dict(h_nm=75.,d_nm=120.,w_nm=w,P_nm=2*w,dx_nm=dx,scheme=scheme,direction=direction,
                    run_id=ts[0]['run_id'],profile_departure=vals['profile_departure'],
                    transverse_gradient=vals.get('transverse_gradient',''),axial_gradient=vals.get('axial_gradient',''),
                    vertical_velocity_gradient=vals.get('vertical_velocity_gradient',''),
                    S_i=S,r_i=r,b_i_r_minus_S=b,b_over_r_percent=100*b/r))
data12=[r for r in data13 if r['dx_nm']==2.5 and r['scheme']=='wall_quadratic']
for n,rows in [(10,data10),(11,data11),(12,data12),(13,data13)]: write_csv(SUP/table_files[n],rows)
assets=[]
(SUP/'figures').mkdir(exist_ok=True)
for lang in ('CN','EN'):
    for ext in ('png','pdf','svg'):
        src=CAND/f'width_evidence_{lang}.{ext}';dst=SUP/'figures'/f'Figure_S1_paired_widths_{lang}.{ext}'
        assert not dst.exists(),dst
        shutil.copy2(src,dst);assert sha(src)==sha(dst);assets.append(dst)

for lang,main_name,sup_name in [
    ('CN','SIM240_中文稿_导师审阅版_20261022.md','SUPPLEMENTARY_METHODS.md'),
    ('EN','SIM240_First_Paper_English_20261028.md','SUPPLEMENTARY_METHODS_EN_20261028.md')]:
    cn=lang=='CN'; cand=(CAND/f'CANDIDATE_{lang}.md').read_text()
    headings=re.findall(r'^## (.+)$',cand,re.M)
    blocks=[between(cand,'## '+headings[i], '## '+headings[i+1]) for i in range(4)]
    main43,main51,supp_block,caption=map(number,blocks)
    if cn:
        duplicate='固定 $h,d$ 而改变 $w$ 同时改变 $h/w$ 与 $d/w$，两宽度对照仍不能辨识唯一控制尺度；原窄槽网格目标未通过、宽槽仅有两档网格的限制继续适用。'
    else:
        duplicate='Varying $w$ at fixed $h,d$ changes both $h/w$ and $d/w$, so the two-width comparison does not identify a unique controlling scale. The historical failure of the narrow-groove grid target and the availability of only two grids for the wide groove remain applicable.'
    assert duplicate in main51
    main51=main51.replace(duplicate,'').rstrip()
    # Remove no scientific condition: both qualifications already occur unchanged later in Section 5.1.
    main_rel='docs/reports/'+main_name
    sup_rel=str((SUP/sup_name).relative_to(ROOT))
    link=f'SIM240_Supplementary_Methods_20261024/{sup_name}#sm-s14-paired'
    main43+='\n\n'+(f'完整配对结果及诊断定义见[补充S14.4、图S1与表S10—S13]({link})。' if cn else
                         f'Complete paired results and diagnostic definitions are given in [Supplement S14.4, Figure S1 and Tables S10–S13]({link}).')
    main51+='\n\n'+(f'绝对归一化分量和账差的完整数值见[补充图S1及表S12、S13]({link})。' if cn else
                         f'Full absolute normalized contributions and residuals are given in [Supplementary Figure S1 and Tables S12 and S13]({link}).')
    (OUT/f'adopted_{lang}_4p3.md').write_text(main43+'\n')
    (OUT/f'adopted_{lang}_5p1.md').write_text(main51+'\n')
    h44='### 4.4 '
    target=next(x for x in texts[main_rel].splitlines() if x.startswith(h44))
    replace(main_rel,'\n'+target,'\n'+main43+'\n\n'+target,'append paired-width evidence to Section 4.3')
    anchor=('以上份额的分母为已列非负项之和，并非离散驱动额外阻力的精确值。' if cn else
            'The denominator of each reported share is the sum of the listed nonnegative terms, rather than the exact discrete driving excess resistance.')
    replace(main_rel,anchor,main51+'\n\n'+anchor,'connect absolute gradient excess after existing directional groups')

    # Update the live navigation only; historical report and candidate prose stay immutable.
    if cn:
        old=next(x for x in texts[main_rel].splitlines() if x.startswith('同步日期：'))
        new='同步日期：2026-11-10。本轮按已审定范围合入成对宽度的导度倍率、方向比与绝对梯度差额，并同步英文及补充S14；新增补充图S1、表S10—S13和式(S14.3)—(S14.5)。使用既有开发记录与已审离线诊断，未新增求解或拟合。合入前快照与差异见 `PAPER1_width_evidence_merge_20261110/`。本稿仍待作者全篇最终科学审定及目标期刊格式、声明和访问条件检查。'
        replace(main_rel,old,new,'update current synchronization note')
        old='既有表S1—S8保留，表S9汇总补充梯度诊断，不并入主图统计。'
        new='既有表S1—S9保留；新增图S1及表S10—S13汇总成对宽度倍率、方向比和绝对梯度差额，不并入主图统计。'
        replace(main_rel,old,new,'update Appendix B evidence navigation')
        old=next(x for x in texts[main_rel].splitlines() if x.startswith('| [S14]'))
        replace(main_rel,old,old.replace('§2.1、§2.4、§5.1','§2.1、§2.4、§4.3、§5.1').replace('| 表S9 |','| 表S9—S13；图S1 |'),'update Appendix B S14 mapping')

    index=next(x for x in texts[sup_rel].splitlines() if x.startswith('| S14 |'))
    revised=index.replace('§2.1、§2.4、§5.1','§2.1、§2.4、§4.3、§5.1').replace('§§2.1, 2.4, 5.1','§§2.1, 2.4, 4.3, 5.1')
    revised=revised.replace('| 表S9 |','| 表S9—S13；图S1 |').replace('| Table S9 |','| Tables S9–S13; Figure S1 |')
    replace(sup_rel,index,revised,'update S14 navigation')
    old=next(x for x in texts[sup_rel].splitlines() if x.startswith('编号版本：' if cn else 'Numbering version:'))
    if cn:
        new=old.replace('本轮同步日期2026-11-09。保留S1—S13及表S1—S8，新增S14两宽度补充组的梯度结构诊断及表S9。',
                        '本轮同步日期2026-11-10。保留S1—S14及表S1—S9，在S14追加成对宽度的倍率/方向比诊断、图S1及表S10—S13。')
    else:
        new=old.replace('synchronized on 2026-11-09. S1–S13 and Tables S1–S8 are retained, with S14 for the supplementary two-width gradient-structure diagnostic and Table S9 added.',
                        'synchronized on 2026-11-10. S1–S14 and Tables S1–S9 are retained; paired-width conductance-factor and anisotropy diagnostics, Figure S1 and Tables S10–S13 are appended to S14.')
    assert new!=old
    replace(sup_rel,old,new,'update supplement synchronization note')

    alt=number(cand.split('## '+headings[-1],1)[1].strip()).replace('\n',' ')
    extra='\n\n<a id="sm-s14-paired"></a>\n\n'
    extra+=('### S14.4 成对宽度的倍率与方向比诊断关系\n\n' if cn else '### S14.4 Paired-width relations for conductance factors and anisotropy\n\n')
    extra+=supp_block+'\n\n'
    extra+=('### S14.5 成对宽度图与汇总表\n\n' if cn else '### S14.5 Paired-width figure and summary tables\n\n')
    extra+='<a id="figure-s1"></a>\n\n'
    extra+=f'![{alt}](figures/Figure_S1_paired_widths_{lang}.png)\n\n'+caption+'\n\n'
    extra+=f'[PDF](figures/Figure_S1_paired_widths_{lang}.pdf) · [SVG](figures/Figure_S1_paired_widths_{lang}.svg)\n\n'
    tab=(CAND/f'TABLES_{lang}.md').read_text()
    table_blocks=re.split(r'^## ',tab,flags=re.M)[1:]
    assert len(table_blocks)==4
    for n,block in zip(range(10,14),table_blocks):
        title,body=number(block).split('\n',1)
        body=body.strip()
        if cn:
            body=body.replace('逐分量全精度和run_id见mechanism_link.csv，标量全精度见paired_evidence.csv。',
                '逐分量全精度见[完整正项诊断](../PAPER1_mechanism_offline_20261109/positive_excess_diagnostic.csv)，配对标量与原运行来源见[表S10数据](Table_S10_paired_width_conductance.csv)。')
        else:
            body=body.replace('Full-precision components and run IDs are in mechanism_link.csv; scalar values are in paired_evidence.csv.',
                'Full-precision components are in the [complete positive-excess diagnostic](../PAPER1_mechanism_offline_20261109/positive_excess_diagnostic.csv); paired scalar values and run provenance are in the [Table S10 data](Table_S10_paired_width_conductance.csv).')
        extra+=f'<a id="table-s{n}"></a>\n\n**{title}**\n\n[{table_files[n]}]({table_files[n]})\n\n'+body+'\n\n'
    (OUT/f'adopted_{lang}_supplement.md').write_text(extra)
    append(sup_rel,extra,'append S14.4/S14.5 with Figure S1, Tables S10–S13 and Eqs. S14.3–S14.5')

map_rel=str((SUP/'SUPPLEMENT_NUMBER_MAP.csv').relative_to(ROOT))
rows=list(csv.DictReader(io.StringIO(texts[map_rel])))
r=next(r for r in rows if r['supplement_section']=='S14')
r['main_location']='§2.1、§2.4、§4.3、§5.1、§5.4、§6'
r['supplementary_table']='表S9—S13；图S1'
buff=io.StringIO(newline='');writer=csv.DictWriter(buff,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
replace(map_rel,texts[map_rel],buff.getvalue(),'update machine-readable S14 cross-reference map')

# All changes remain in memory until the entire adoption has been prepared.
for rel in before_hashes:
    if rel.endswith('MANIFEST.md'): continue
    assert sha(ROOT/rel)==before_hashes[rel],rel
    (ROOT/rel).write_text(texts[rel])

manifest_rel='docs/reports/PAPER1_submission_package_20261109/MANIFEST.md'
for n in range(1,5):
    line=next(x for x in texts[manifest_rel].splitlines() if x.startswith(f'| {n} |'))
    rel=re.search(r'`([^`]+)`',line).group(1);p=ROOT/rel
    new=re.sub(r'`[a-f0-9]{16}` \| \d+ \|',f'`{sha(p)[:16]}` | {p.stat().st_size} |',line)
    replace(manifest_rel,line,new,f'rebind primary item {n}')
marker='## 2 数据证据件'
insertion='## 1.3 成对宽度证据定点合入（2026-11-10）\n\n'
insertion+='按已审候选同步两正文§4.3、§5.1及两补充S14，新增补充图S1、表S10—S13与式(S14.3)—(S14.5)。原正文图1—4、表1—8、式1—8和附录E编号不变；科学文献[1]—[14]身份与编号不变。原18几何36条主统计、V2四参数与已知反例、摘要和结论保持。\n\n'
insertion+='第1—4行SHA与字节数按实际文件重绑定；新增共享CSV、编号映射和双语图件分别绑定于§2.1和§3.1。完整SHA、候选采用审查、可逆改动记录及检查见 `docs/reports/PAPER1_width_evidence_merge_20261110/REPORT.md`、`output_hashes.json`与`verification.json`。旧候选和旧合稿哈希保留历史身份；本轮不重做上下界理论复核、求解、拟合或物理验收，不改变既有FAIL及投稿准备状态。\n\n---\n\n'
replace(manifest_rel,marker,insertion+marker,'record authorized width-evidence adoption')
replace(manifest_rel,'同目录其余 S 表：S1 运行清单、S2 加密、S3 周期检查、S4 网格归档、S5 条件 GCI、S6 新增间隙构建对照、S8 控制证据、S9 机制诊断——**表体与上表同期**，改动时须同步核对。',
        '同目录既有S表：S1运行清单、S2加密、S3周期检查、S4网格归档、S5条件GCI、S6新增间隙构建对照、S8控制证据、S9机制诊断。新增表S10—S13及编号映射见下表；改动时须同步核对。','update live supplementary-data inventory')
new_data=[SUP/table_files[n] for n in range(10,14)]+[SUP/'SUPPLEMENT_NUMBER_MAP.csv']
inventory='## 2.1 成对宽度共享数据与编号映射（2026-11-10）\n\n| # | 文件 | SHA256（前16位） | 字节 | 用途 |\n|---|---|---|---|---|\n'
for n,p,meaning in zip(range(9,14),new_data,['表S10：两网格导度倍率与方向比及run_id来源','表S11：共同倍率辅助诊断','表S12：2.5nm主模板绝对梯度差额','表S13：两网格/两模板梯度差额与带符号余额','S1—S14正文/补充交叉索引，S14含图S1及表S9—S13']):
    inventory+=f'| {n} | `{p.relative_to(ROOT)}` | `{sha(p)[:16]}` | {p.stat().st_size} | {meaning} |\n'
inventory+='\n两种语言使用同一组CSV；它们来自既有开发记录与已审离线诊断，不是新增运行。\n\n---\n\n'
replace(manifest_rel,'## 3 图件（4 组，各 PDF + PNG）',inventory+'## 3 图件（原4组及补充图S1）','bind new data files without renumbering old entries')
figure_inventory='## 3.1 补充图S1双语资产（2026-11-10）\n\n| 文件 | SHA256（前16位） | 字节 |\n|---|---|---|\n'
for p in assets: figure_inventory+=f'| `{p.relative_to(ROOT)}` | `{sha(p)[:16]}` | {p.stat().st_size} |\n'
figure_inventory+='\n补充文稿中分别引用对应语言PNG，PDF/SVG供导出；图注与正式编号在双语S14。图件与已审候选逐字节相同，未重新处理原场。\n\n---\n\n'
replace(manifest_rel,'## 4 非投稿件',figure_inventory+'## 4 非投稿件','bind bilingual Figure S1 assets')
assert sha(ROOT/manifest_rel)==before_hashes[manifest_rel]
(ROOT/manifest_rel).write_text(texts[manifest_rel])

(OUT/'edits.json').write_text(json.dumps(edits,ensure_ascii=False,indent=2)+'\n')
for rel in before_hashes:
    old=(OUT/'before'/rel).read_text();new=(ROOT/rel).read_text()
    (OUT/(Path(rel).name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel+' before',tofile=rel+' after')))
outputs=list(before_hashes)+[str(p.relative_to(ROOT)) for p in new_data if str(p.relative_to(ROOT)) not in before_hashes]+[str(p.relative_to(ROOT)) for p in assets]
(OUT/'output_hashes.json').write_text(json.dumps({rel:{'sha256':sha(ROOT/rel),'bytes':(ROOT/rel).stat().st_size} for rel in outputs},ensure_ascii=False,indent=2)+'\n')
for rel,digest in protected.items(): assert sha(ROOT/rel)==digest,rel
print(json.dumps({'modified_existing':len(before_hashes),'new_data_tables':4,'new_figure_files':len(assets),
                  'edits':len(edits),'protected_inputs_unchanged':True},ensure_ascii=False))
