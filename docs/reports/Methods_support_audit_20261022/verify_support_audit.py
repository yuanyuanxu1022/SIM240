#!/usr/bin/env python3
"""Check scope of the one-paragraph edit and the supporting-material audit."""
import hashlib
import json
import math
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
manuscript=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
before=(HERE/'manuscript_before.md').read_text()
after=manuscript.read_text()
edit=json.loads((HERE/'edit_record.json').read_text())
audit=json.loads((HERE/'support_audit.json').read_text())
hashes=json.loads((HERE/'input_hashes.json').read_text())
old='实际沟槽还包含侧壁，以及深区与浅区之间的连接段：液体在浅区内流速较低，会通过黏性剪切影响相邻深区的流动；跨槽流动在台阶拐角处还需重新分布。局部平板组合不显式表示这些耦合。'
new='实际沟槽还包含侧壁及深浅区域之间的连接段。相邻区域的横向黏性作用和台阶附近的流动重分布，均未被局部平板组合显式解析。本文未分解这些因素对整体输运的贡献。'
broken=[]
for name in ('SUPPORTING_MATERIALS_INDEX.md','REPORT.md'):
    for target in re.findall(r'\]\(([^)]+)\)',(HERE/name).read_text()):
        if target.startswith(('https://','http://','#')):continue
        path=target.split('#',1)[0]
        path=re.sub(r':\d+$','',path)
        p=Path(path) if path.startswith('/') else HERE/path
        if not p.exists():broken.append(dict(document=name,target=target))

smooth=[r for r in audit['archived_grid'] if r['case']=='Smooth75']
period=audit['G4_period']
checks={
    'one_authorized_prose_replacement_only':before.count(old)==1 and before.replace(old,new)==after,
    'before_snapshot_hash_matches':hashlib.sha256(before.encode()).hexdigest()==edit['before_sha256'],
    'after_manuscript_hash_matches':hashlib.sha256(manuscript.read_bytes()).hexdigest()==edit['after_sha256'],
    'all_numbered_formula_tags_unchanged':re.findall(r'\\tag\{\d+\}',before)==re.findall(r'\\tag\{\d+\}',after),
    'equations_tables_and_bibliography_counts_unchanged':
        re.findall(r'\\tag\{(\d+)\}',after)==list(map(str,range(1,8)))
        and re.findall(r'^\*\*表 (\d+)\s',after,re.M)==list(map(str,range(1,9)))
        and re.findall(r'^\[(\d+)\] ',after,re.M)==list(map(str,range(1,12))),
    'all_read_original_inputs_unchanged':all(hashlib.sha256((ROOT/p if not Path(p).is_absolute() else Path(p)).read_bytes()).hexdigest()==h for p,h in hashes.items()),
    'support_documents_have_no_broken_local_links':not broken,
    '52_runs_partitioned_without_overlap':audit['run_counts']==dict(main=36,refinement=8,oblique=6,viscosity=2),
    '52_binary_hashes_present':audit['manifests_with_fields']['binary_sha256']==52,
    'missing_source_and_build_fields_explicit':all(audit['manifests_with_fields'][f]==0 for f in ('source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags')),
    '48_individual_and_4_shared_logs_located':audit['logs_by_style']==dict(individual=48,shared_batch=4),
    '52_recorded_exits_and_PASS_inventory_complete':len(audit['runs'])==52 and all(r['shell_exit']=='0' and r['recorded_PASS']=='true' for r in audit['runs']),
    'q_and_Mach_support_reported_ranges':audit['q_all_52_halfway'] and math.isclose(audit['Mach_range'][0],5.7e-10,rel_tol=.01) and math.isclose(audit['Mach_range'][1],4.1e-7,rel_tol=.01),
    '18_G4_existing_runs_located':len(audit['G4_runs'])==18 and all(r['shell_exit']=='0' for r in audit['G4_runs']),
    'period_replication_values_match':all(r['relative_R_difference']==0 for r in period if r['nx0']==2)
        and all(math.isclose(r['relative_R_difference'],8.7e-14 if r['direction']=='P' else 3.8e-14,rel_tol=.01) for r in period if r['nx0']==4),
    'force_span_values_match':math.isclose(max(r['K_span_over_mean'] for r in audit['G4_linearity'] if r['direction']=='P'),2.5e-8,rel_tol=.02)
        and math.isclose(max(r['K_span_over_mean'] for r in audit['G4_linearity'] if r['direction']=='T'),3.7e-8,rel_tol=.02),
    'smooth_table3_errors_match_rounding':[f"{r['analytic_error_percent']:.3f}" if i<2 else f"{r['analytic_error_percent']:.4f}" for i,r in enumerate(smooth)]==['0.444','0.111','0.0272'],
    'historical_fine_transverse_FAIL_preserved':any(r['case']=='EX240_perpendicular' and r['dx']=='dx1p25' and r['recorded_PASS']=='false' and r['shell_exit']=='3' for r in audit['archived_grid']),
    'scheme_C_record_not_promoted':audit['scheme_C']['formal_reference_accepted'] is False,
    'OAS_file_identity_matches_existing_report':audit['OAS_hash_matches_layout_report'],
}
assert all(checks.values()),dict(failed=[k for k,v in checks.items() if not v],broken_links=broken)
result=dict(completed_date='2026-10-23',checks=checks,check_count=len(checks),all_checks_pass=True,
            protected_input_count=len(hashes),manuscript_sha256=hashlib.sha256(manuscript.read_bytes()).hexdigest(),
            scope='Single prose correction, supporting-material inventory and selected reported numbers only; no formal numerical/physical gate approval.')
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
