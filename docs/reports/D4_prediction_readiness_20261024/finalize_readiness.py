"""Assemble the bounded completed-screen verdict and prediction-readiness blockers."""
from pathlib import Path
import csv,json,hashlib
HERE=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_text())
def write(n,v):(HERE/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''):h.update(x)
    return h.hexdigest()
def main():
    inv=load(HERE/'inventory_summary.json');scalar=load(HERE/'screen_acceptance/scalar_summary.json')
    field=load(HERE/'screen_acceptance/flow_frames.json');cases=load(HERE/'screen_acceptance/scalar_results.json')
    assert scalar['whole_batch_complete'] and scalar['all_scalar_and_geometry_checks_passed']
    assert field['ok'] and field['cases']==len(cases)==6
    linear=[]
    for dr in ('P','T'):
        rs=[r for r in cases if r['direction']==dr];assert len(rs)==3
        assert sorted(r['acceleration_m_s2'] for r in rs)==[5e4,1e5,2e5]
        base=next(r['K_m3'] for r in rs if r['acceleration_m_s2']==1e5)
        diffs=[dict(a_m_s2=r['acceleration_m_s2'],K_m3=r['K_m3'],relative_difference=r['K_m3']/base-1,run_id=r['run_id']) for r in rs]
        worst=max(abs(r['relative_difference']) for r in diffs);assert worst<=.01
        linear.append(dict(direction=dr,limit_relative=.01,max_abs_relative_difference=worst,max_abs_difference_percent=worst*100,pass_linearity=True,points=diffs))
    write('linearity.json',linear)
    limits=['max_mass_drift','max_density_deviation','max_Mach','final_window_rel_std','final_window_rel_span','final_section_relative_difference','final_window_cross_abs_max']
    write('numerical_worst_values.json',{k:max(r[k] for r in cases) for k in limits})
    counts=inv['role_counts'];assert counts['new_dev']['formal_results_found']==2 and counts['linearity']['formal_results_found']==4
    assert counts['grid_reference']['formal_results_found']==0
    assert inv['unknown_batches_not_opened']==[]
    assert inv['model_lock_intact'] and inv['protected_unchanged']
    protected=load(HERE/'protected_inputs.json');assert all(sha(p)==v for p,v in protected.items())
    raw=load(HERE/'screen_raw_hashes.json');assert all(sha(p)==v for p,v in raw.items())
    verdict=dict(review_id='D4_prediction_readiness_20261024_v1',screen_batch_id='development_screen_20261023_v1',screen_acceptance='PASS',independent_NUMERICAL_GATE='PASS',geometry_PASS=True,SCREEN_RESULT_PASS=True,raw_RESULT_PASS='false preserved',scope='six drive-linearity screen cases at h75 d120 w240 P480 dx5 only; not new-width spatial accuracy',screen_cases_checked=6,diagnostic_rows_checked=scalar['diagnostic_rows'],frames_read=field['frames_read'],linearity_directions_passed=2,new_development_primary_complete='2/16',extra_linearity_complete='4/4',development_grid_reference_complete='0/12',foundation_retained='8/8 accepted; hashes checked, no rerun',total_completed_new_D4_solves=14,total_planned_new_D4_solves=60,remaining_new_solves=46,development_preconditions_remaining_solves=26,model_lock_intact=True,development_grid_accuracy_acceptance_rule='NOT_FOUND_IN_REVIEWED_D4_FROZEN_PROTOCOLS; must declare before new grid results',prediction_readiness='NOT_READY',prediction_stage_run_permit_preparation_eligible=False,remaining_development_preparation_eligible=True,prediction_execution_released=False,blockers=['14 planned primary development directions absent from canonical D4 results','12 development fine-grid references absent; no new-width spatial accuracy established','D4 reviewed protocols do not freeze a quantitative spatial-grid acceptance rule','external prediction non-exposure and future stage source/config/resources/release remain to be checked'],next_action='Prepare and review remaining 14 coarse development cases and separate development-grid validation protocol/resource plan; retain v1 model lock and all original evidence; no automatic execution',new_solver_runs=0,prediction_results_read=False,original_protocol_changed=False,protected_unique_file_count=len(protected),protected_unchanged=True)
    write('readiness.json',verdict)
    print(json.dumps(verdict,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
