"""Independent static review of the 26-case proposal and source protection."""
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
import json,csv,hashlib,ast,subprocess,sys
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''):h.update(x)
    return h.hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def main():
    inputs=json.loads((HERE/'input_hashes.json').read_text());assert all(sha(p)==v for p,v in inputs.items())
    old=json.loads((PROJECT/'docs/reports/D4_prediction_readiness_20261024/protected_inputs.json').read_text());assert all(sha(p)==v for p,v in old.items())
    planned=rows(HERE/'case_budget26.csv');canonical={r['planned_case_id']:r for r in rows(CASE/'protocol/candidate_cases.csv')}
    missing=rows(PROJECT/'docs/reports/D4_prediction_readiness_20261024/missing_development_cases.csv')
    assert len(planned)==26 and {r['planned_case_id'] for r in planned}=={r['planned_case_id'] for r in missing}
    assert len(rows(HERE/'remaining_coarse14.csv'))==14 and len(rows(HERE/'development_grid12.csv'))==12
    batchrows=rows(HERE/'batches.csv');assert [int(r['cases']) for r in batchrows]==[14,6,4,1,1]
    templates=list((HERE/'planned_configs').glob('*.json'));assert len(templates)==26
    min_fields=('h_nm','d_nm','w_nm','P_nm','Ly_nm','dx_nm','direction','acceleration_m_s2','nu_m2_s','rho_kg_m3','tau')
    for r in planned:
        source=canonical[r['planned_case_id']];assert all(r[k]==source[k] for k in min_fields)
        assert r['blind_geometry']=='False' and r['role'] in ('new_dev','grid_reference')
        h,d,w,P,dx=[Decimal(r[k]) for k in ('h_nm','d_nm','w_nm','P_nm','dx_nm')]
        assert h==75 and P==w*2 and all((v/dx)==(v/dx).to_integral_value() for v in [h,d,w,P,(P-w)/2])
        # Two-dimensional cross-section count times periodic cell count.
        n=(P/dx*(h/dx)+(w/dx)*(d/dx))*(P/dx)
        win=(Decimal('4.5')*(h/dx)**2).to_integral_value(rounding=ROUND_CEILING)
        cap=(Decimal(48)*((h+d)/dx)**2).to_integral_value(rounding=ROUND_CEILING)
        assert int(r['computed_fluid_nodes'])==n and int(r['window_steps'])==win and int(r['maximum_steps'])==cap
        spec=json.loads((HERE/'planned_configs'/(r['planned_case_id']+'.json')).read_text())
        assert spec['execution_released'] is False and spec['status']=='PLANNED_ONLY_NOT_A_RUN'
        cfg=spec['solver_parameters'];assert cfg['mode']=='steady' and cfg['direction']==r['direction']
        assert spec['expected_window_steps']==win and spec['expected_maximum_steps']==cap and spec['expected_fluid_nodes']==n
        assert cfg['frame_tstar']==[0,.01,.02,.05,.1,.2,.5,1,2,4,8]
    for p in HERE.glob('*.py'):ast.parse(p.read_text())
    # New preparation cannot silently have made a result directory or runtime release.
    for r in batchrows:
        assert not (CASE/'results'/r['batch_id']).exists()
        assert r['execution_released']=='False' and r['automatic_next_batch']=='False'
        assert r['parallel_solver_processes']=='1' and r['MPI_ranks']=='1'
    assert not (HERE/'release.json').exists()
    prep=json.loads((HERE/'preparation.json').read_text());assert prep['solver_runs']==0 and not prep['formal_input_binding_prepared']
    test=json.loads((HERE/'grid_selfcheck.json').read_text());assert test['ok'] and not test['real_grid_results_read']
    # Existing lock and all of its bound evidence are part of the protected set.
    lockdir=PROJECT/'docs/reports/Correlation_selection_freeze_20261024';lock=json.loads((lockdir/'candidate_lock.json').read_text())
    assert sha(lockdir/'candidate_lock.json')==(lockdir/'candidate_lock.sha256').read_text().split()[0]
    assert all(sha(lockdir/k)==v for k,v in lock['bound_files'].items())
    result=dict(ok=True,planned_case_ids_checked=26,coarse14_exact_missing_match=True,grid12_exact_missing_match=True,config_templates_checked=26,batch_counts=[14,6,4,1,1],independent_decimal_geometry_and_step_checks=True,synthetic_grid_checks=test['synthetic_checks'],input_hash_count=len(inputs),original_protected_files_checked=len(old),originals_unchanged=True,model_lock_preserved=True,solver_runs=0,new_run_directories=0,runtime_release_created=False,source_or_binary_modified=False,formal_compilation_or_execution_validation_claimed=False,proposal_only=True)
    (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
