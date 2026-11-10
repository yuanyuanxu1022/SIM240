#!/usr/bin/env python3
"""Final preparation provenance checks; no external processes or flow execution."""
import ast
import hashlib
import json
from pathlib import Path
import re
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
PKG=ROOT/'CASE/groove_darcy_static_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    protected=read(OUT/'preservation_before.json')
    assert all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in protected.items())
    release=read(PKG/'common/release_manifest.json')
    assert len({r['path'] for r in release['files']})==len(release['files'])
    assert all(sha(PKG/r['path'])==r['sha256'] for r in release['files'])
    assert all(sha(Path(r['path']))==r['sha256'] for r in release['libraries'])
    prep=read(PKG/'reports/preparation.json');audit=read(PKG/'reports/static_audit.json');preflight=read(OUT/'preflight.json')
    assert prep['compile_pass'] and prep['checker_tests_pass'] and prep['no_solve_audit_pass']
    assert all(sha(PKG/r['path'])==r['sha256'] for r in prep['binary_source_binding'])
    assert not prep['flow_solved'] and prep['solve_calls']==0 and prep['run_id'] is None
    assert preflight['preflight_satisfied'] and not preflight['flow_solver_executed']
    assert audit['cells']==audit['zone_cells']==512 and audit['solve_calls']==0
    assert not (PKG/'runs').exists()
    for sub in ['GDI_output','GDI_audit','1']:assert not (PKG/'cases/GDI01'/sub).exists()
    log=(PKG/'reports/audit_attempt1.log').read_text();assert 'Solving for p' not in log and 'GDI_AUDIT_COMPLETE' in log
    assert 'Mesh OK.' in (PKG/'reports/checkMesh.log').read_text()
    assert 'Ran 14 tests' in (PKG/'reports/checker_tests.log').read_text()
    assert read(PKG/'reports/negative_audit_tests.json')['all_passed']
    for p in PKG.rglob('*.py'):
        if 'build' not in p.parts:ast.parse(p.read_text())
    links=[]
    for doc in [PKG/'README.md',OUT/'REPORT.md']:
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if link.startswith('http'):continue
            assert (doc.parent/link).exists(),(doc,link)
            links.append(link)
    sync=read(OUT/'state_sync.json')
    assert all(sha(ROOT/r['path'])==r['sha256'] and r['subsequent_sections_preserved'] for r in sync['files'])
    files={str((PKG/r['path']).relative_to(ROOT)):r['sha256'] for r in release['files']}
    files.update({r['path']:r['sha256'] for r in release['libraries']})
    for p in OUT.rglob('*'):
        if p.is_file() and p.name not in ['verification.json','source_manifest.json']:files[str(p.relative_to(ROOT))]=sha(p)
    for p in [PKG/'common/release_manifest.json']+[ROOT/r['path'] for r in sync['files']]:files[str(p.relative_to(ROOT))]=sha(p)
    (OUT/'source_manifest.json').write_text(json.dumps(files,indent=2)+'\n')
    assert all(sha(Path(p) if p.startswith('/') else ROOT/p)==h for p,h in files.items())
    result=dict(status='IMPLEMENTED_COMPILED_NO_SOLVE_AUDIT_COMPLETE_NOT_STARTED',protocol_id='GDI-v1',case_id='GDI01',
        source_prepared=True,host_compiled=True,result_checker_implemented=True,full_zone_cells=512,
        no_solve_audit_pass=True,read_only_preflight_pass=True,checker_unit_tests=14,old_CSV_regressions=8,
        negative_native_audit_cases=4,release_files=len(release['files']),runtime_libraries=len(release['libraries']),
        protected_old_files_unchanged=len(protected),source_manifest_files=len(files),local_links_checked=len(links),
        subclass_source_modified=False,subclass_recompiled=False,subclass_library_reuse_verified=True,
        new_flow_run_started=False,flow_solved=False,solve_calls=0,run_id=None,
        tmux_command_delivered=False,first_flow_convergence_verified=False,complete_new_run_acceptance_exercised=False,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=None,physical_validation='NOT_EVALUATED',
        independent_human_acceptance=False,reference_qualified=False,strict_error_bound_established=False,
        submission_ready=False,prediction='HOLD',states_synced=True)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
