#!/usr/bin/env python3
"""Check bounded prose changes, numbering, links, data and protected inputs."""
import csv
import difflib
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TARGET=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
INDEX=ROOT/'docs/reports/Methods_support_audit_20261022/SUPPORTING_MATERIALS_INDEX.md'
before=(HERE/'manuscript_before.md').read_text()
after=TARGET.read_text()
supp=(HERE/'SUPPLEMENTARY_METHODS.md').read_text()
checks={}
def check(name,condition):checks[name]=bool(condition)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvrows(name):return list(csv.DictReader((HERE/name).open()))
def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12)
def part(s,start,end):return s.split(start,1)[1].split(end,1)[0]

prep=json.loads((HERE/'preparation.json').read_text())
check('before_snapshot_matches_preparation',digest(HERE/'manuscript_before.md')==prep['manuscript_before_sha256'])
math_before=re.findall(r'\$\$.*?\$\$',before,re.S)
check('all_displayed_math_unchanged',math_before==re.findall(r'\$\$.*?\$\$',after,re.S))
check('equation_numbers_1_to_7',re.findall(r'\\tag\{(\d+)\}',after)==[str(i) for i in range(1,8)])
check('main_tables_1_to_8',re.findall(r'^\*\*表 (\d+)\s',after,re.M)==[str(i) for i in range(1,9)])
check('bibliography_1_to_11_unchanged',part(before,'## 参考文献','## 附录 A')==part(after,'## 参考文献','## 附录 A') and re.findall(r'^\[(\d+)\] ',after,re.M)==[str(i) for i in range(1,12)])
check('abstract_introduction_unchanged',before.split('## 2 研究对象与比较方法')[0]==after.split('## 2 研究对象与比较方法')[0])
check('results_discussion_conclusions_unchanged',part(before,'## 4 结果','## 参考文献')==part(after,'## 4 结果','## 参考文献'))
mechanism='实际沟槽还包含侧壁及深浅区域之间的连接段。相邻区域的横向黏性作用和台阶附近的流动重分布，均未被局部平板组合显式解析。本文未分解这些因素对整体输运的贡献。'
check('previous_section_2_3_correction_preserved',mechanism in after)
check('overbroad_three_sentences_removed',all(s not in after for s in ['可据以复现。','现有正式运行共 52 次','也说明全文采用单一驱动幅值是合理的']))
check('historical_provenance_limit_explicit','部分历史运行的源码、编译配置及 OpenLB 依赖版本绑定尚未完整核实' in after)
check('52_scope_explicit','包括 36 个主方向样点、8 次加密、2 次黏度对照和 6 次斜向驱动' in after and '不计入这 52 项' in after)
check('linearity_scope_explicit','基准几何 $(h,d)=(75,100)$ nm、2.5 nm 网格' in after and '未对全部 36 个 5 nm 主地图样点逐一做多力检查' in after)
check('supplement_sections_1_to_11',re.findall(r'^## S(\d+) ',supp,re.M)==[str(i) for i in range(1,12)])
anchors=re.findall(r'<a id="([^"]+)"',supp)
check('supplement_anchors_unique',len(anchors)==len(set(anchors)) and all(f'sm-s{i}' in anchors for i in range(1,12)))
check('supplement_tables_1_to_4',re.findall(r'^\*\*表 S(\d+)\s',supp,re.M)==[str(i) for i in range(1,5)])
mapping=csvrows('SUPPLEMENT_NUMBER_MAP.csv')
check('one_to_one_11_section_map',len(mapping)==11 and all(r['previous_index']==r['supplement_section']==f'S{i}' and r['anchor']==f'sm-s{i}' for i,r in enumerate(mapping,1)))
check('main_and_old_index_use_all_section_links',all(f'#sm-s{i})' in after and f'#sm-s{i})' in INDEX.read_text() for i in range(1,12)))

t1=csvrows('Table_S1_run_inventory.csv');t2=csvrows('Table_S2_refinement.csv')
t3=csvrows('Table_S3_periodic_checks.csv');t4=csvrows('Table_S4_grid_archive.csv')
check('four_table_row_counts',[len(t) for t in [t1,t2,t3,t4]]==[52,8,18,9])
audit=json.loads((ROOT/'docs/reports/Methods_support_audit_20261022/support_audit.json').read_text())
check('table_s1_exact_audit_values',all(r['run_id']==a['run_id'] and float(r['K_m3'])==a['K'] and r['binary_sha256']==a['binary_sha256'] and r['result_path']==a['result'] and r['recorded_PASS']==a['recorded_PASS'] and str(r['independent_exit_code'])==str(a['shell_exit']) for r,a in zip(t1,audit['runs'])))
refinement_ok=True
for r in t2:
    h=float(r['h'])*1e-9;d=float(r['d'])*1e-9
    direction=r['direction']
    model=((h+d)**3+h**3)/24 if direction=='parallel' else (h+d)**3*h**3/(6*((h+d)**3+h**3))
    k5=float(r['K5']);k25=float(r['K2_5'])
    for dx,k in [(5,k5),(2.5,k25)]:
        rows=[x for x in t1 if float(x['h_nm'])==float(r['h']) and float(x['d_nm'])==float(r['d']) and float(x['dx_nm'])==dx and x['direction']==direction]
        refinement_ok &= len(rows)==1 and float(rows[0]['K_m3'])==k
    e5=100*(model/k5-1);e25=100*(model/k25-1)
    refinement_ok &= all(close(a,b) for a,b in [(r['K_change_percent'],100*(k25/k5-1)),(r['E5_percent'],e5),(r['E2_5_percent'],e25),(r['E_change_percentage_points'],e25-e5)])
check('table_s2_independently_recomputed',refinement_ok)
check('table_s3_exact_audit_values',all(float(r['K_m3'])==a['K'] and float(r['R_Pa_s_per_m3'])==a['R'] and r['run_id']==a['run_id'] and r['independent_exit_code']==str(a['shell_exit']) for r,a in zip(t3,audit['G4_runs'])))
check('table_s3_design_3nx_2directions_3forces',set((int(r['nx']),r['direction'],float(r['acceleration_m_s2'])) for r in t3)=={(nx,d,a) for nx in [2,4,8] for d in ['P','T'] for a in [5e4,1e5,2e5]})
force_spans={}
period_diffs={}
for direction in ['P','T']:
    spans=[]
    for nx in [2,4,8]:
        ks=[float(r['K_m3']) for r in t3 if r['direction']==direction and int(r['nx'])==nx]
        spans.append((max(ks)-min(ks))/(sum(ks)/len(ks)))
    force_spans[direction]=max(spans)
    rs={int(r['nx']):float(r['R_Pa_s_per_m3']) for r in t3 if r['direction']==direction and float(r['acceleration_m_s2'])==1e5}
    period_diffs[direction]=[abs(rs[4]-rs[2])/rs[2],abs(rs[8]-rs[4])/rs[4]]
check('table_s3_linearity_and_period_aggregates_recomputed',
      all(math.isclose(force_spans[d],expected,rel_tol=1e-8) for d,expected in [('P',2.47850560e-8),('T',3.66006070e-8)]) and
      all(period_diffs[d][0]==0 for d in ['P','T']) and
      all(math.isclose(period_diffs[d][1],expected,rel_tol=1e-8) for d,expected in [('P',8.71496562e-14),('T',3.80797839e-14)]))
check('table_s4_exact_audit_values',all(float(r['K_m3'])==a['K'] and r['recorded_PASS']==a['recorded_PASS'] and r['independent_exit_code']==str(a['shell_exit']) for r,a in zip(t4,audit['archived_grid'])))
smooth=[r for r in t4 if r['case']=='Smooth75']
check('table_s4_smooth_errors_recomputed',len(smooth)==3 and all(close(r['analytic_error_percent'],100*(float(r['K_m3'])/((75e-9)**3/12)-1)) for r in smooth))
failure=[r for r in t4 if r['grid']=='dx1p25' and r['case']=='EX240_perpendicular']
check('historical_fine_transverse_failure_preserved',len(failure)==1 and failure[0]['recorded_PASS']=='false' and failure[0]['independent_exit_code']=='3')

broken=[];link_count=0
for p in [TARGET,INDEX,HERE/'SUPPLEMENTARY_METHODS.md',HERE/'README.md',HERE/'REVISION_NOTE.md']:
    for url in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if re.match(r'https?://',url):continue
        link_count+=1
        raw,sep,anchor=url.partition('#')
        raw=re.sub(r':\d+$','',raw)
        target=(p.parent/raw).resolve() if raw else p
        if not target.exists():broken.append(dict(file=str(p),url=url,reason='missing file'))
        elif sep and anchor and f'id="{anchor}"' not in target.read_text():broken.append(dict(file=str(p),url=url,reason='missing explicit anchor'))
check('local_links_and_explicit_anchors_resolve',not broken)
hashes=json.loads((HERE/'input_hashes.json').read_text())
changed=[key for key,sha in hashes.items() if digest(ROOT/key)!=sha]
check('protected_raw_and_previous_audit_inputs_unchanged',not changed and len(hashes)==213)
for name,old,new in [('manuscript',before,after),('support_index',(HERE/'support_index_before.md').read_text(),INDEX.read_text())]:
    (HERE/f'{name}.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=name+'_before',tofile=name+'_after')))
result=dict(date='2026-10-24',all_checks_pass=all(checks.values()),check_count=len(checks),checks=checks,
            protected_input_count=len(hashes),changed_protected_inputs=changed,local_link_count=link_count,broken_links=broken,
            table_rows={'S1':len(t1),'S2':len(t2),'S3':len(t3),'S4':len(t4)},
            recomputed_force_spans=force_spans,recomputed_period_differences=period_diffs,
            manuscript_before_sha256=digest(HERE/'manuscript_before.md'),manuscript_after_sha256=digest(TARGET),
            limitation='Document/data-link verification only; no solver, fitting, complete numerical Gate, provenance recovery, publication or remote synchronization.')
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['all_checks_pass'] else 1)
