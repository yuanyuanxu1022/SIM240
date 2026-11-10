"""Inventory formal D4 records and verify frozen evidence; no reserved result read."""
from pathlib import Path
import csv,json,hashlib,datetime
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def write(n,v):(HERE/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def main():
    expected=rows(CASE/'protocol/candidate_cases.csv');assert len(expected)==90
    plan={r['planned_case_id']:r for r in expected};actual={};before={}
    def protect(p):before[str(p)]=sha(p)
    for p in [CASE/'PROTOCOL.md',CASE/'protocol/candidate_cases.csv',CASE/'protocol/execution.json',CASE/'development_stage_20261023/PROTOCOL.md',CASE/'development_stage_20261023/stage_cases.csv',CASE/'development_stage_20261023/held_grid_references.csv',CASE/'development_stage_20261023/policy.json',CASE/'src/variable_groove_transport.cpp',CASE/'build/variable_groove_transport']:
        protect(p)
    batch_names=sorted(p.name for p in (CASE/'results').iterdir() if p.is_dir())
    known={'foundation_20261023_v1','development_screen_20261023_v1'}
    unknown=sorted(set(batch_names)-known)
    # Unknown batches and any reserved result payloads are never opened.
    for bn in sorted(set(batch_names)&known):
        batch=CASE/'results'/bn
        bm=json.loads((batch/'stage_manifest.json').read_text());protect(batch/'stage_manifest.json')
        for ident in bm['case_ids']:
            assert ident in plan and plan[ident]['blind_geometry']=='False'
            out=batch/(ident.replace('CAND_','D4_',1)+'_'+bn)/'steady'
            if (out/'result.txt').exists():
                result=dict(x.split('=',1) for x in (out/'result.txt').read_text().splitlines() if '=' in x)
                m=json.loads((out/'run_manifest.json').read_text())
                assert m['planned_case_id']==ident and m['mode']=='steady' and m['formal_simulation'] is True
                assert ident not in actual
                actual[ident]=dict(output=str(out),batch=bn,run_id=m['run_id'],exit_code=int((out/'exit_code.txt').read_text()),raw_NUMERICAL_GATE=result['NUMERICAL_GATE'],raw_geometry_PASS=result['geometry_PASS'],raw_RESULT_PASS=result['RESULT_PASS'])
    inventory=[]
    for r in expected:
        reserved=r['blind_geometry']=='True';a=actual.get(r['planned_case_id'])
        inventory.append(dict(planned_case_id=r['planned_case_id'],role=r['role'],h_nm=r['h_nm'],d_nm=r['d_nm'],w_nm=r['w_nm'],P_nm=r['P_nm'],direction=r['direction'],dx_nm=r['dx_nm'],acceleration_m_s2=r['acceleration_m_s2'],reserved=reserved,formal_result_present=bool(a),status='RESERVED_NOT_READ' if reserved else ('FORMAL_RESULT_FOUND' if a else ('LEGACY_CONDITIONAL_REUSE' if r['role']=='legacy_dev' else 'NO_FORMAL_RESULT_FOUND')),**(a or {})))
    fields=list(dict.fromkeys(k for r in inventory for k in r))
    with (HERE/'matrix_inventory.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(inventory)
    foundation=HERE.parent/'D4_foundation_acceptance_20261023/complete'
    retained={}
    for name in ['all_raw_files_sha256.json','flow_files_sha256.json','analysis_scripts_sha256.json']:
        p=foundation/name;protect(p)
        for k,v in json.loads(p.read_text()).items():
            k=str(Path(k) if Path(k).is_absolute() else foundation.parent/k)
            assert k not in retained or retained[k]==v;retained[k]=v
    assert all(sha(p)==v for p,v in retained.items())
    accept=json.loads((foundation/'acceptance.json').read_text());assert accept['FOUNDATION_RESULT_PASS'] is True
    for p in foundation.iterdir():
        if p.is_file():protect(p)
    release=json.loads((CASE/'development_stage_20261023/release.json').read_text());binding=release['bound_inputs_sha256']
    assert all(sha(p)==v for p,v in binding.items())
    # Case manifests include actual config + stage release in addition to the common binding.
    run_binding={}
    for a in actual.values():
        m=json.loads((Path(a['output'])/'run_manifest.json').read_text())
        for p,v in m['inputs_sha256'].items():
            assert p not in run_binding or run_binding[p]==v;run_binding[p]=v
    assert all(sha(p)==v for p,v in run_binding.items())
    lockdir=HERE.parent/'Correlation_selection_freeze_20261024';lockpath=lockdir/'candidate_lock.json'
    lock=json.loads(lockpath.read_text());assert sha(lockpath)==(lockdir/'candidate_lock.sha256').read_text().split()[0]
    for n,v in lock['bound_files'].items():assert sha(lockdir/n)==v;protect(lockdir/n)
    lock_inputs=json.loads((lockdir/'input_hashes.json').read_text());assert all(sha(p)==v for p,v in lock_inputs.items())
    protect(lockpath);protect(lockdir/'candidate_lock.sha256')
    # Capture all originals in the allowed completed screen, including VTK payloads.
    raw={str(p):sha(p) for p in (CASE/'results/development_screen_20261023_v1').rglob('*') if p.is_file()}
    write('screen_raw_hashes.json',raw)
    all_protected={**retained,**binding,**run_binding,**lock_inputs,**before,**raw}
    assert all(sha(p)==v for p,v in all_protected.items())
    write('protected_inputs.json',all_protected)
    groups={}
    for role in sorted({r['role'] for r in expected}):
        subset=[r for r in expected if r['role']==role]
        groups[role]=dict(planned=len(subset),formal_results_found=sum(r['planned_case_id'] in actual for r in subset))
    write('inventory_summary.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),canonical_results_root=str(CASE/'results'),batch_names=batch_names,unknown_batches_not_opened=unknown,role_counts=groups,completed_formal_cases=len(actual),development_release_binding_count=len(binding),all_completed_run_bindings_unique_count=len(run_binding),retained_foundation_unique_hash_count=len(retained),foundation_acceptance_retained=True,model_lock_id=lock['lock_id'],model_lock_sha256=sha(lockpath),model_lock_intact=True,model_locked_utc=lock['created_utc'],external_prediction_nonexposure_verified=False,screen_raw_files_count=len(raw),protected_unique_file_count=len(all_protected),protected_unchanged=True,reserved_result_payloads_read=0,solver_runs=0,scope_limit='No results found means absent from canonical D4 results tree at this snapshot; other machines or external copies not audited.'))
    print(json.dumps(json.loads((HERE/'inventory_summary.json').read_text()),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
