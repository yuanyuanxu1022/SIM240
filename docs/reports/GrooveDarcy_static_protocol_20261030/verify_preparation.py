#!/usr/bin/env python3
"""Verify preparation artifacts and protected files; no external process calls."""
import ast
import hashlib
import json
from pathlib import Path
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def main():
    protected=load(OUT/'preservation_before.json')
    assert all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in protected.items())
    bindings=load(OUT/'input_bindings.json')
    assert all(sha(Path(p) if p.startswith('/') else ROOT/p)==h for p,h in bindings.items())
    protocol=load(OUT/'protocol.json')
    original=load(ROOT/'docs/reports/Static_Darcy_interface_protocol_20261030/protocol.json')
    assert protocol['inherited_SDI_thresholds']==original['thresholds']
    assert protocol['inherited_linear_solver']==original['linear_solver']
    assert protocol['first_case_only']=='GDI01' and protocol['run_id'] is None
    assert not protocol['launch_ready'] and not protocol['simulation_authorized']
    assert not protocol['solver_exists'] and not protocol['stages']['host_compiled']
    assert not protocol['stages']['new_flow_run_started']
    assert protocol['inputs']['porous_zone_cells']==512
    squeeze=load(OUT/'squeeze_interface.json')
    assert not squeeze['simulation_authorized'] and not squeeze['continuity_implemented']
    assert all(squeeze[k] is None for k in ['squeezing_velocity_m_s','time_step_s','duration_s','dynamic_thresholds','new_run_id'])
    refs=load(OUT/'reference_values.json')['cases']; assert len(refs)==4
    assert all(r['new_result'] is None and r['planned_new_run_id'] is None for r in refs)
    sync=load(OUT/'state_sync.json')
    for row in sync['files']:
        assert sha(ROOT/row['path'])==row['sha256'] and row['subsequent_sections_preserved']
    links=[]
    for doc in OUT.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if link.startswith('http'): continue
            if link=='verification.json': continue
            assert (doc.parent/link).exists(),(doc,link)
            links.append(link)
    for p in OUT.glob('*.py'): ast.parse(p.read_text())
    manifest=dict(bindings)
    for p in OUT.iterdir():
        if p.is_file() and p.name not in ['source_manifest.json','verification.json']:
            manifest[str(p.relative_to(ROOT))]=sha(p)
    for row in sync['files']:manifest[row['path']]=sha(ROOT/row['path'])
    (OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert all(sha(Path(p) if p.startswith('/') else ROOT/p)==h for p,h in manifest.items())
    verification=dict(status='PREPARATION_VERIFIED_NO_NEW_FLOW_RUN',protocol_id='GDI-v1',
        protected_files_unchanged=len(protected),input_bindings_verified=len(bindings),
        source_manifest_files=len(manifest),local_links_checked=len(links),
        inherited_thresholds_exact=True,inherited_linear_solver_exact=True,
        baseline_cases=4,baseline_CSV_programs=8,baseline_results_are_existing=True,
        new_host_implemented=False,new_compile_performed=False,new_flow_run_started=False,new_flow_run_id=None,
        squeeze_interface_defined=True,squeeze_continuity_implemented=False,
        squeeze_run_parameters_frozen=False,states_synced=True,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=None,
        physical_validation='NOT_EVALUATED',independent_human_acceptance=False,
        reference_qualified=False,strict_error_bound_established=False,submission_ready=False,prediction='HOLD')
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
