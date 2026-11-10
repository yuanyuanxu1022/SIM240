"""Apply only the authorized mechanism integration to the current manuscript snapshots."""
from pathlib import Path
import csv, difflib, hashlib, io, json, re

OUT=Path(__file__).resolve().parent
REP=OUT.parent
REVIEW=REP/'PAPER1_mechanism_claim_review_20261109'
OLD=REP/'PAPER1_mechanism_offline_20261109'
SUP=REP/'SIM240_Supplementary_Methods_20261024'
names=['SIM240_中文稿_导师审阅版_20261022.md','SIM240_First_Paper_English_20261028.md',
       'SUPPLEMENTARY_METHODS.md','SUPPLEMENTARY_METHODS_EN_20261028.md','SUPPLEMENT_NUMBER_MAP.csv']
paths={n:(REP/n if i<2 else SUP/n) for i,n in enumerate(names)}
original={n:(OUT/(n+'.before')).read_text() for n in names}
for n,p in paths.items():
    assert p.read_bytes()==(OUT/(n+'.before')).read_bytes(),'Current text changed since this merge snapshot: '+n
edits=[]
def subst(text,old,new,label):
    assert text.count(old)==1,(label,text.count(old))
    edits.append({'label':label,'old_sha256':hashlib.sha256(old.encode()).hexdigest(),
                  'new_sha256':hashlib.sha256(new.encode()).hexdigest(),'old':old,'new':new})
    return text.replace(old,new,1)
def candidate(lang):
    t=(REVIEW/('CANDIDATE_'+lang+'.md')).read_text()
    parts=re.split(r'^## ([A-F])[．.]',t,flags=re.M)
    return {parts[i]:parts[i+1].split('\n',1)[1].strip() for i in range(1,len(parts),2)}
def section(text,start,end):
    a=text.index(start);b=text.index(end,a);return text[a:b].rstrip()

cn=original[names[0]];en=original[names[1]]
for lang,t,name in [('CN',cn,names[0]),('EN',en,names[1])]:
    c=candidate(lang);zh=lang=='CN';supname=names[2] if zh else names[3]
    slink='SIM240_Supplementary_Methods_20261024/'+supname+'#sm-s14'
    c['C']=c['C'].replace('另见机制补充候选。',f'见[补充材料S14]({slink})。') if zh else c['C'].replace('documented in the mechanism supplement candidate.',f'documented in [Supplementary S14]({slink}).')
    c['D']=c['D'].replace('余额在5 nm目标中最大约','余额的绝对值在5 nm目标中最大约') if zh else c['D']
    c['D']+='\n\n'+(f'分解推导、逐运行诊断及来源见[补充材料S14、表S9]({slink})。' if zh else f'Derivations, per-run diagnostics and provenance are given in [Supplementary S14 and Table S9]({slink}).')
    old=section(t,'**这一模型之所以' if zh else '**The construction remains','保留无量纲记号' if zh else 'Retaining dimensionless notation')
    t=subst(t,old,c['B'],lang+' section 2.3 explanation')
    anchor='本章支持资料按S1—S13编号' if zh else 'Supporting methods are numbered S1–S13.'
    t=subst(t,anchor,c['A']+'\n\n'+('本章支持资料按S1—S14编号' if zh else 'Supporting methods are numbered S1–S14.'),lang+' diagnostic set and index')
    start='### 2.4 ';a=t.index(start);b=t.index('\n## 3 ',a);old=t[a:b]
    trailing='\n\n---\n' if old.rstrip().endswith('---') else ''
    body=old.rstrip();body=body[:-3].rstrip() if trailing else body
    t=subst(t,old,body+'\n\n'+c['C']+trailing+'\n',lang+' section 2.4 methods')
    old=section(t,'### 5.1 ','### 5.2 ')
    t=subst(t,old,c['D'],lang+' section 5.1 replacement')
    a=t.index('### 5.4 ');a=t.index('\n\n',a)+2;b=t.index('\n\n',a)
    t=subst(t,t[a:b],c['E'],lang+' section 5.4 scope')
    a=t.index('## 6 ');b=t.index('\n---',a)
    old=t[a:b];t=subst(t,old,old.rstrip()+'\n\n'+c['F']+'\n',lang+' conclusion 5')
    if zh:
        t=subst(t,'同步日期：2026-11-07。','同步日期：2026-11-09。',lang+' sync date')
        old=t.split('\n')[4]
        new='同步日期：2026-11-09。本轮按已审定范围合入两宽度补充组的梯度结构诊断，并同步英文与补充S14；既有主图双向偏差、连续上界、V2评价和静态接入保持各自证据范围。合入前快照及差异见 `PAPER1_mechanism_merge_20261109/`。使用既有运行与离线诊断结果，未新增求解或拟合。本稿仍为作者审阅工作稿，待完成全篇最终科学审定及目标期刊格式、声明和访问条件检查。'
        t=subst(t,old,new,lang+' revision note')
        t=subst(t,'沟槽周期为240 nm，槽与凸台等宽；主数据','主参数图的沟槽周期为240 nm，槽与凸台等宽；主数据',lang+' abstract primary scope')
        t=subst(t,'本文针对固定周期、等宽槽与凸台的全充液矩形沟槽，','本文的主比较针对固定周期、等宽槽与凸台的全充液矩形沟槽，',lang+' intro primary scope')
        scope='四个几何的加密结果用于报告参考敏感性，不构成全地图连续解精度证书。'
        t=subst(t,scope,scope+'另对两种槽宽的已知开发几何作梯度能量诊断，为所测条件的方向性偏差提供受限定量解释，见第5.1节和补充材料S14。',lang+' intro diagnostic scope')
        t=subst(t,'周期 $P=240$ nm、槽宽 $w=120$ nm，槽与凸台等宽。','主参数图的周期 $P=240$ nm、槽宽 $w=120$ nm，槽与凸台等宽。',lang+' primary geometry')
        t=subst(t,'计算域平面尺寸 $L_x=L_y=240$ nm，即恰好一个图案周期；','主地图的计算域平面尺寸 $L_x=L_y=240$ nm，即恰好一个图案周期；',lang+' primary domain')
        role='| 旧附加检查 | 2条黏度、6条斜向结果 | 分别核物性响应与张量内部自洽 |'
        t=subst(t,role,role+'\n| 补充梯度诊断 | h75/d120、w60/240两几何的10份目标末态，另2份平板控制 | 已知开发组，单列于S14，不并入主统计 |',lang+' dataset role')
        t=subst(t,'因此公式比较合计19种几何、46条离散记录','主图及新增间隙的公式比较合计19种几何、46条离散记录',lang+' 46-record scope')
        t=subst(t,'下表保留既有方法支持索引S1—S11，并增列后续控制与静态接入S12—S13；既有表S1—S5保留，新增表S6为新增间隙与构建对照，表S7为薄隙修正的两网格比较，表S8为控制证据索引。','下表列出方法支持索引S1—S14；S12—S13分别对应后续控制与静态接入，S14为单列补充组的梯度结构诊断。既有表S1—S8保留，表S9汇总补充梯度诊断，不并入主图统计。',lang+' Appendix B index text')
        row='| [S13](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s13) | 静态平均模型接入 | §5.3 | — |'
        t=subst(t,row,row+f'\n| [S14]({slink}) | 两宽度补充组的梯度结构诊断 | §2.1、§2.4、§5.1、§5.4、§6 | 表S9 |',lang+' Appendix B S14 row')
    else:
        old=t.split('\n')[2]
        new='**Author-review working manuscript; synchronized on 2026-11-09.** The bounded gradient-structure diagnostic for the supplementary two-width set is integrated with Supplementary S14. Existing main-map discrepancies, continuous upper bounds, V2 assessment and static interfacing retain their respective evidence scopes. Pre-merge snapshots and differences are in `PAPER1_mechanism_merge_20261109/`. Existing runs and offline diagnostics are used without new solver runs or fitting. Whole-manuscript scientific approval, venue formatting, declarations and access arrangements remain pending.'
        t=subst(t,old,new,lang+' revision note')
        t=subst(t,'The period is 240 nm, with equal groove and rib widths.','The main parameter map has a period of 240 nm, with equal groove and rib widths.',lang+' abstract primary scope')
        scope='Refinements at four geometries characterize reference sensitivity, rather than certifying continuous-solution accuracy across the map.'
        t=subst(t,scope,scope+' A gradient-energy diagnostic on known development geometries at two groove widths provides a bounded quantitative interpretation of directional discrepancies under the tested conditions; see Section 5.1 and Supplementary S14.',lang+' intro diagnostic scope')
        t=subst(t,'The period is $P=240$ nm and groove width is $w=120$ nm,','The main parameter map uses period $P=240$ nm and groove width $w=120$ nm,',lang+' primary geometry')
        t=subst(t,'The in-plane dimensions are $L_x=L_y=240$ nm,','For the main map, the in-plane dimensions are $L_x=L_y=240$ nm,',lang+' primary domain')
        role='| Legacy additional checks | 2 viscosity and 6 oblique results | Property response and internal tensor consistency |'
        t=subst(t,role,role+'\n| Supplementary gradient diagnostic | 10 target final states for two h75/d120 geometries at w60/240, plus 2 flat-channel controls | Known development set; reported separately in S14 and excluded from main statistics |',lang+' dataset role')
        t=subst(t,'The formula-comparison set therefore contains 19 geometries and 46 discrete records','The main-map and additional-gap formula-comparison set contains 19 geometries and 46 discrete records',lang+' 46-record scope')
    if zh:cn=t
    else:en=t

# Build S14 from the approved bilingual supplement; supply the same equations in
# each language and replace provisional notation/links with formal S14 references.
module=(REVIEW/'SUPPLEMENT_CANDIDATE.md').read_text()
zhdef=section(module,'## 中文：定义与推导','## 中文：离散实现与数值界限').split('\n',1)[1].strip()
zhlim=section(module,'## 中文：离散实现与数值界限','## English: definitions and derivation').split('\n',1)[1].strip()
endef=section(module,'## English: definitions and derivation','## English: discrete implementation and limitations').split('\n',1)[1].strip()
enlim=section(module,'## English: discrete implementation and limitations','## 随文保存的证据').split('\n',1)[1].strip()
zhlim=zhlim.replace('主表取2.5 nm作为两宽度均有的比较档位','正文取2.5 nm作为两宽度均有的比较档位')
enlim=enlim.replace('The main comparison uses 2.5 nm','The main-text comparison uses 2.5 nm')
eqs=re.findall(r'\\\[\n(.*?)\\\]',zhdef,re.S)
assert len(eqs)==3
for i,eq in enumerate(eqs[1:],1):
    anchor='Expanding the square yields Eq. (M1).' if i==1 else 'which gives Eq. (M2).'
    replacement='Expanding the square gives\n\n\\[\n'+eq+'\\]\n\n' if i==1 else 'which gives\n\n\\[\n'+eq+'\\]\n\n'
    endef=endef.replace(anchor,replacement)
for i in [1,2]:
    zhdef=zhdef.replace('M'+str(i),'S14.'+str(i));endef=endef.replace('M'+str(i),'S14.'+str(i))
zhdef=zhdef.replace('沿槽取 $v=v_y$','沿槽取 $v=u_y/J$').replace('横槽取 $v=v_x$、$s=v_z$','横槽取 $v=u_x/J$、$s=u_z/J$')
endef=endef.replace('set $v=v_y$','set $v=u_y/J$').replace('set $v=v_x$, $s=v_z$','set $v=u_x/J$, $s=u_z/J$')
# Use explicit partial derivatives for cross-products to avoid confusing scalar
# derivatives with components of the normalized vector.
for var in ['v','b','c']:
    zhdef=zhdef.replace(var+'_z',r'\partial_z '+var)
    endef=endef.replace(var+'_z',r'\partial_z '+var)
for var in ['b','c']:
    zhdef=zhdef.replace(r'\partial_z '+var+'^2',r'(\partial_z '+var+')^2')
    endef=endef.replace(r'\partial_z '+var+'^2',r'(\partial_z '+var+')^2')
endef=endef.replace('\n Its second','\nIts second').replace('\n We report','\nWe report')
zhdef=zhdef.replace('$2\\mu D:D$；','$2\\mu D:D$，其中 $D=(\\nabla\\boldsymbol u+\\nabla\\boldsymbol u^T)/2$；')
endef=endef.replace('$2\\mu D:D$;','$2\\mu D:D$, where $D=(\\nabla\\boldsymbol u+\\nabla\\boldsymbol u^T)/2$;')

evidence_cn='完整逐运行身份与场核查见 [field_checks.csv](../PAPER1_mechanism_offline_20261109/field_checks.csv)；原生及两模板功率见 [power_checks.csv](../PAPER1_mechanism_offline_20261109/power_checks.csv)；正项与全部余额见 [positive_excess_diagnostic.csv](../PAPER1_mechanism_offline_20261109/positive_excess_diagnostic.csv)；六应变分量见 [strain_components.csv](../PAPER1_mechanism_offline_20261109/strain_components.csv)；三半径空间分区见 [spatial_regions.csv](../PAPER1_mechanism_offline_20261109/spatial_regions.csv)。读取与导数实现见 [diagnose_fields.py](../PAPER1_mechanism_offline_20261109/diagnose_fields.py)，输入SHA见 [source_manifest.json](../PAPER1_mechanism_offline_20261109/source_manifest.json)，诊断范围见 [REPORT.md](../PAPER1_mechanism_offline_20261109/REPORT.md)。这些是已知开发末态的离线诊断，不是新增运行或独立预测验证。'
evidence_en='Per-run identities and field checks are in [field_checks.csv](../PAPER1_mechanism_offline_20261109/field_checks.csv); native and both reconstructed power estimates in [power_checks.csv](../PAPER1_mechanism_offline_20261109/power_checks.csv); all positive terms and residuals in [positive_excess_diagnostic.csv](../PAPER1_mechanism_offline_20261109/positive_excess_diagnostic.csv); six strain components in [strain_components.csv](../PAPER1_mechanism_offline_20261109/strain_components.csv); and all three spatial-partition radii in [spatial_regions.csv](../PAPER1_mechanism_offline_20261109/spatial_regions.csv). The reader and derivative implementation are in [diagnose_fields.py](../PAPER1_mechanism_offline_20261109/diagnose_fields.py), input hashes in [source_manifest.json](../PAPER1_mechanism_offline_20261109/source_manifest.json), and diagnostic scope in [REPORT.md](../PAPER1_mechanism_offline_20261109/REPORT.md). These are offline diagnostics of known development final states, not new runs or independent prediction tests.'
intro_cn='本节对应正文§2.1、§2.4及§5.1。诊断组为h75/d120、槽/凸台等宽、w60/240 nm（P120/480 nm）；两方向5/2.5 nm及窄槽1.25 nm共10份目标末态，另2份h75平板5 nm末态为后处理控制。主图18几何36结果、新增间隙和本补充组分别报告。'
intro_en='This section supports Sections 2.1, 2.4 and 5.1 of the main text. The diagnostic set has h75/d120, equal groove and ridge widths, and w60/240 nm (P120/480 nm). Both directions at 5/2.5 nm and the narrow-groove 1.25 nm states give ten target fields; two h75 flat-channel states at 5 nm are postprocessing controls. The 18-geometry, 36-result main map, added gap and supplementary diagnostic set are reported separately.'
table_cn='**表 S9　两宽度补充组逐运行梯度诊断（10份目标末态，主模板）**\n\n[Table_S9_mechanism_diagnostic.csv](Table_S9_mechanism_diagnostic.csv)保留run_id、几何/周期/网格、R/RLC、各正项/RLC、正项和S、驱动差额E、各项份额与两种余额的完整精度。P为沿槽，T为横槽；不适用的分量留空，不记为零。另一模板及2份平板控制保留于下列完整诊断表，不混入本表10目标。'
table_en='**Table S9. Per-run gradient diagnostics for the two-width supplementary set (ten target final states, primary derivative treatment).**\n\n[Table_S9_mechanism_diagnostic.csv](Table_S9_mechanism_diagnostic.csv) retains run_id, geometry/period/grid, R/RLC, each positive term/RLC, their sum S, driving excess E, component shares and both residual types at full precision. P denotes along-groove and T across-groove flow. Inapplicable components are blank rather than zero. The alternative derivative treatment and two flat-channel controls remain in the complete diagnostic tables linked below and are excluded from these ten target rows.'

supps=[]
for zh,n,defs,limits,intro,tab,evidence in [(True,names[2],zhdef,zhlim,intro_cn,table_cn,evidence_cn),(False,names[3],endef,enlim,intro_en,table_en,evidence_en)]:
    t=original[n]
    if zh:
        old=t.split('\n')[4]
        new='编号版本：2026-10-24；本轮同步日期2026-11-09。保留S1—S13及表S1—S8，新增S14两宽度补充组的梯度结构诊断及表S9。既有数据来自D2/D3、历史基准和已完成的后续控制检查；S14仅使用已知D4开发末态，不读取保留预测结果、不替换V2。代码和小型数据的已核私有快照仍为e05b3f21171ce52a66af41dfe172e79c0a099c20，入口 `07_第一篇代码数据更新_20261107/`；本轮稿件和补充修订未新增上传。审稿访问与最终期刊格式仍待作者确定。'
        row='| S13 | 静态平均模型接入 | §5.3 | — |';newrow='| S14 | 两宽度补充组的梯度结构诊断 | §2.1、§2.4、§5.1、§5.4、§6 | 表S9 |'
        title='## S14 两宽度补充组的梯度结构诊断';head1='### S14.1 定义与连续分解';head2='### S14.2 离散实现与数值界限';head3='### S14.3 逐运行数据与来源'
    else:
        old=t.split('\n')[4]
        new='Numbering version: 2026-10-24; synchronized on 2026-11-09. S1–S13 and Tables S1–S8 are retained, with S14 for the supplementary two-width gradient-structure diagnostic and Table S9 added. Existing sources are D2/D3 records, historical benchmarks and completed later controls; S14 uses only known D4 development final states, excludes reserved prediction results and does not replace V2. The checked private code/small-data snapshot remains e05b3f21171ce52a66af41dfe172e79c0a099c20 under `07_第一篇代码数据更新_20261107/`; the present manuscript and supplement revision have not been newly uploaded. Reviewer access and final venue formatting remain for the authors to determine.'
        row='| S13 | Static averaged-model interfacing | §5.3 | — |';newrow='| S14 | Gradient-structure diagnostic for the two-width set | §§2.1, 2.4, 5.1, 5.4, 6 | Table S9 |'
        title='## S14 Gradient-structure diagnostic for the two-width set';head1='### S14.1 Definitions and continuous decomposition';head2='### S14.2 Discrete implementation and limitations';head3='### S14.3 Per-run data and provenance'
    t=subst(t,old,new,('CN' if zh else 'EN')+' supplement revision note')
    t=subst(t,row,row+'\n'+newrow,('CN' if zh else 'EN')+' supplement index S14')
    t=t.rstrip()+'\n\n<a id="sm-s14"></a>\n\n'+title+'\n\n'+intro+'\n\n'+head1+'\n\n'+defs+'\n\n'+head2+'\n\n'+limits+'\n\n'+head3+'\n\n<a id="table-s9"></a>\n\n'+tab+'\n\n'+evidence+'\n'
    supps.append(t)

# Derived display table; original diagnostic products remain byte-for-byte intact.
def rows(path):
    with path.open() as f:return list(csv.DictReader(f))
pr=rows(OLD/'positive_excess_diagnostic.csv');keys=rows(OLD/'key_results.csv');table=[]
for k in keys:
    rr=[v for v in pr if v['run_id']==k['run_id'] and v['scheme']=='wall_quadratic']
    assert len(rr) in [2,3]
    record={col:rr[0][col] for col in ['run_id','direction','h_nm','d_nm','w_nm','dx_nm']}
    record['P_nm']=float(record['w_nm'])*2
    for col in ['R_drive_over_R_LC','R_strain_over_R_LC','strain_input_residual_percent']:
        record[col]=k[col]
    for term in ['profile_departure','transverse_gradient','axial_gradient','vertical_velocity_gradient']:
        part=[v for v in rr if v['term']==term]
        record[term+'_over_R_LC']=part[0]['R_excess_term_over_R_LC'] if part else ''
        record[term+'_share_percent']=100*float(part[0]['term_fraction_of_positive_sum']) if part else ''
    for col in ['sum_terms_over_R_LC','drive_excess_over_R_LC','grad_excess_over_R_LC','identity_sum_minus_grad_excess']:
        record[col]=rr[0][col]
    record['positive_sum_vs_drive_excess_relative_percent']=k['positive_sum_vs_drive_excess_relative_percent']
    table.append(record)
assert len(table)==10
buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
table_text=buf.getvalue()
mapping=original[names[4]].rstrip()+'\n'
for line in [
'S12,S12,后续控制证据及失败记录,sm-s12,SUPPLEMENTARY_METHODS.md,§3.3—3.4,表S8',
'S13,S13,静态平均模型接入,sm-s13,SUPPLEMENTARY_METHODS.md,§5.3,',
'S14,S14,两宽度补充组的梯度结构诊断,sm-s14,SUPPLEMENTARY_METHODS.md,§2.1、§2.4、§5.1、§5.4、§6,表S9']:
    assert not any(x.startswith(line.split(',')[0]+',') for x in mapping.splitlines())
    mapping+=line+'\n'
result=dict(zip(names,[cn,en,*supps,mapping]))
for n,text in result.items():
    paths[n].write_text(text)
    (OUT/(n+'.diff')).write_text(''.join(difflib.unified_diff(original[n].splitlines(True),text.splitlines(True),fromfile=n+'.before',tofile=n)))
newtable=SUP/'Table_S9_mechanism_diagnostic.csv';assert not newtable.exists();newtable.write_text(table_text,newline='')
(OUT/'edits.json').write_text(json.dumps(edits,ensure_ascii=False,indent=2)+'\n')
(OUT/'output_hashes.json').write_text(json.dumps({str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*paths.values(),newtable]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'modified_manuscripts':4,'number_map_updated':True,'new_table_rows':len(table),'scoped_replacements':len(edits)}))
