#!/usr/bin/env python3
"""Verify this citation/provenance/availability edit without any simulation imports."""
from pathlib import Path
import json,re,hashlib

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
MAIN=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
SUP=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
before=(HERE/'before'/MAIN.name).read_text();after=MAIN.read_text()
sbefore=(HERE/'before'/SUP.name).read_text();safter=SUP.read_text()
changes=json.loads((HERE/'editorial_changes.json').read_text())
expected_main,expected_sup=before,sbefore
for c in changes:
    if c['id'].startswith('M'):
        assert expected_main.count(c['old'])==1,c['id'];expected_main=expected_main.replace(c['old'],c['new'],1)
    else:
        assert expected_sup.count(c['old'])==1,c['id'];expected_sup=expected_sup.replace(c['old'],c['new'],1)
canonical={}
for path,h in json.loads((HERE/'protected_inputs.json').read_text())['sha256'].items():
    p=Path(path);p=p if p.is_absolute() else ROOT/p;p=p.resolve()
    assert p not in canonical or canonical[p]==h
    canonical[p]=h
changed=[str(p) for p,h in canonical.items() if hashlib.sha256(p.read_bytes()).hexdigest()!=h]
availability=json.loads((HERE/'availability.json').read_text());prov=json.loads((HERE/'provenance.json').read_text())
refs=lambda t:t.split('## 参考文献',1)[1].split('## 附录 A',1)[0]
equations=lambda t:re.findall(r'\$\$(.*?)\$\$',t,re.S)
main_tables=lambda t:[x for x in t.split('## 参考文献',1)[0].splitlines() if x.startswith('|')]
oldrefs=dict(re.findall(r'^\[(\d+)\] (.*)$',refs(before),re.M));newrefs=dict(re.findall(r'^\[(\d+)\] (.*)$',refs(after),re.M))
checks={
 'exactly_7_main_and_2_supplement_edits':len(changes)==9 and expected_main==after and expected_sup==safter,
 'all_main_and_appendix_displayed_equations_unchanged':equations(before)==equations(after),
 'main_and_appendix_equation_numbers_unchanged':re.findall(r'\\tag\{([^}]+)\}',before)==re.findall(r'\\tag\{([^}]+)\}',after),
 'abstract_unchanged':before.split('## 摘要',1)[1].split('## 1 引言',1)[0]==after.split('## 摘要',1)[1].split('## 1 引言',1)[0],
 'results_discussion_conclusions_unchanged':before.split('## 4 结果',1)[1].split('## 参考文献',1)[0]==after.split('## 4 结果',1)[1].split('## 参考文献',1)[0],
 'all_8_main_numeric_tables_unchanged':main_tables(before)==main_tables(after),
 'appendix_E_body_and_assumptions_unchanged':before.split('## 附录 E',1)[1]==after.split('## 附录 E',1)[1],
 '11_references_only_ref6_changed':set(oldrefs)==set(newrefs)=={str(i) for i in range(1,12)} and [k for k in oldrefs if oldrefs[k]!=newrefs[k]]==['6'],
 'ref6_title_doi_volume_pages_match_primary_metadata':all(x in newrefs['6'] for x in ['Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths','10.1016/j.euromechflu.2018.02.004','2018','70','73–84']),
 'unverified_ref6_amplitude_claim_removed': '不限制幅度的半解析谱解' not in after,
 'private_commit_access_and_scope_explicit':all(x in after for x in ['私有仓库','f11c0f20f6aaadf6920b95390855ec418cf8ae42','仅对有权限的人员开放','当前正文、方法补充材料','最终公开范围']),
 '8591_manifest_paths_present_in_fixed_remote_tree':availability['manifest_rows']==8591 and availability['all_manifest_paths_present_in_remote'] and not availability['tree_truncated'],
 '446_selected_archive_byte_checks_pass':availability['selected_package_files_byte_checked']==446 and availability['all_selected_package_byte_checks_match_remote'] and not availability['failed_package_checks'],
 '52_current_run_records_and_4_plot_inputs_match_snapshot':all(availability['coverage_groups'][k]['matches_current']==52 for k in ['run_result','run_manifest','run_log','run_exit']) and availability['coverage_groups']['main_plot_input']['matches_current']==4,
 'updated_2_scripts_and_6_figure_exports_distinguished':len(availability['different_current_plot_scripts_or_outputs'])==8 and availability['coverage_groups']['current_document']['in_snapshot']==0,
 'missing_build_fields_preserved_as_open':all(x==52 for x in prov['missing_manifest_fields'].values()) and not prov['historical_openlb_version_proved'],
 'prior_selected_inputs_and_records_unchanged':not changed,
 'fulltext_and_version_limits_recorded':all(x in safter for x in ['AIP全文请求被拒绝','APS全文接口返回401','与2008年期刊发表版','不能冒称逐页核对了期刊发表版']),
 'scientific_HOLD_not_upgraded':not availability['submission_ready'] and not availability['scientific_gate_reassessed'] and availability['new_solver_run_id'] is None,
}
broken=[]
for p in [MAIN,SUP,HERE/'REPORT.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https:','http:','#')):continue
        local_path=re.sub(r':\d+$','',target.split('#')[0])
        if not (p.parent/local_path).exists():broken.append({'file':str(p),'target':target})
checks['all_local_markdown_links_resolve']=not broken
result={'status':'DOCUMENT_AND_SOURCE_COVERAGE_CHECKS_ONLY','checks':checks,'all_checks_pass':all(checks.values()),'check_count':len(checks),
 'protected_unique_selected_files':len(canonical),'changed_protected_files':changed,'broken_links':broken,
 'manuscript_sha256':hashlib.sha256(MAIN.read_bytes()).hexdigest(),'supplement_sha256':hashlib.sha256(SUP.read_bytes()).hexdigest(),
 'human_final_scientific_approval':'PENDING','reference_qualified':False,'strict_error_bound_established':False,'submission_ready':False}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
