#!/usr/bin/env python3
"""Check internal consistency, original-input immutability, and snapshot sources."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
summary=json.loads((OUT/'summary.json').read_text())
runs=json.loads((OUT/'runs.json').read_text())
historical=json.loads((OUT/'historical.json').read_text())
viscosity=json.loads((OUT/'viscosity_text_check.json').read_text())
checks={
    '48_complete_numerical_records':len(runs)==48 and summary['all_48_num_gate_recomputed'],
    '228211_diagnostic_rows':sum(x['csv_rows'] for x in runs)==228211,
    'all_contiguous':all(x['contiguous_steps'] and x['csv_rows']==x['steps']+1 for x in runs),
    'K_recomputation':summary['agreement_max']['K']<1e-14,
    'slice_J_recomputation':summary['agreement_max']['J_field']<1e-11,
    'VTK_J_recomputation':summary['vtk_max_J_relative_difference']<1e-7,
    'VTK_material_geometry':summary['vtk_geometry_mismatches_total']==0,
    'VTK_expected_candidate_links':summary['vtk_independent_link_counts_all_match'],
    'old_fine_T_exit3':next(x for x in historical['archived_runs'] if x['grid']=='dx1p25' and x['case']=='EX240_perpendicular')['exit']=='3',
    'scheme_C_shell_exit0':historical['scheme_C']['shell_exit']=='0',
    'scheme_C_old_columns_identical':historical['scheme_C']['different_common_rows']==0,
    'scheme_C_source_hashes':all(historical['scheme_C']['source_hash_check'].values()),
    'GCI_ratio_identity':all(abs(x['asymptotic_ratio']-x['ratio_equals_fine_over_medium'])<1e-14 for x in historical['recomputed_GCI']),
}
all_hashes={}
for name in ('source_hashes.json','historical_source_hashes.json'):
    all_hashes.update(json.loads((OUT/name).read_text()))
changed=[]
for path,expected in all_hashes.items():
    p=ROOT/path
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    if actual!=expected:changed.append(path)
checks['all_original_inputs_unchanged']=not changed
checks['viscosity36_raw_parameter_derivation']=viscosity['map_count']==36 and all(abs(x/1e-6-1)<1e-14 for x in viscosity['nu_range'])
checks['viscosity_inputs_unchanged']=all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected for path,expected in viscosity['inputs'].items())
snapshots={}
for path in [ROOT/'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',ROOT/'CASE/D_series/D2_groove_error_map/src/Makefile',ROOT/'CASE/D_series/D3_oblique_groove_tensor_check/src/d3_oblique_groove_tensor_check.cpp',ROOT/'CASE/03_grid_convergence/G2_EX240_grid_convergence/scripts/postprocess_grid.py',ROOT/'docs/reports/SIM240_manuscript_revision_20261018/CORE_CLAIMS.md',ROOT/'docs/reports/Chapter5_mechanism_audit_20261018/REPORT.md',ROOT/'docs/reports/第一篇论文_第2章方法草稿_20261017.md',ROOT/'docs/reports/第一篇论文_第3章验证草稿_20261017.md',ROOT/'CASE/D_series/D2_groove_error_map/results/analysis/CODE_REVIEW_20261017.md',ROOT/'CASE/D_series/D2_groove_error_map/results/analysis/ACCEPTANCE_AND_ANALYSIS_20261016.md',Path('/home/dell/openlb/CITATION.cff'),Path('/home/dell/openlb/src/dynamics/dynamics.h'),Path('/home/dell/openlb/src/dynamics/momenta/elements.h')]:
    snapshots[str(path)]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'lines':len(path.read_text().splitlines())}
    assert path.is_file()
records=[]
for script,argument in [('validate_review_intake.py','review_intake.json'),('select_reporting_guidelines.py','study_profile.json'),('validate_claim_evidence.py','claim_evidence.csv'),('lint_review.py','REPORT.md')]:
    command=[sys.executable,'/home/dell/.codex/skills/peer-review/scripts/'+script,str(OUT/argument)]
    result=subprocess.run(command,capture_output=True,text=True)
    records.append({'command':command,'exit_code':result.returncode,'stdout':json.loads(result.stdout),'stderr':result.stderr})
    checks[script]=result.returncode==0
data={'checked_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':checks,'PASS':all(checks.values()),'original_file_count':len(all_hashes),'changed_original_paths':changed,'source_and_claim_snapshots':snapshots,'process_tool_records':records,'new_solver_runs':0,'new_solver_compiles':0,'new_gate_releases':0,'author_review':'pending','scope':'Independent local audit of existing outputs; no editorial decision.'}
(OUT/'verification.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'PASS':data['PASS'],'checks':checks,'original_file_count':len(all_hashes),'changed_original_paths':changed},indent=2))
sys.exit(0 if data['PASS'] else 1)
