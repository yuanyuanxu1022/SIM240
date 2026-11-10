"""Independent scope/guard review. Never runs the solver or calls execute_batch."""
from pathlib import Path
import argparse,copy,ast,json,importlib.util,tempfile,subprocess,sys
HERE=Path(__file__).resolve().parent;CASE=HERE.parent
spec=importlib.util.spec_from_file_location('stage_entry',HERE/'run_remaining.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def must_reject(fn):
    try:fn()
    except (RuntimeError,KeyError,ValueError):return
    raise AssertionError('expected rejection')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--released',action='store_true');a=ap.parse_args()
    rows=r.validate_table();assert len(rows)==14
    rel=dict(released=True,allowed_case_ids=[x['planned_case_id'] for x in rows])
    for row in rows:r.validate_row(row,rel)
    rejected=0
    for row in r.csvrows(CASE/'protocol/candidate_cases.csv'):
        if row['planned_case_id'] not in rel['allowed_case_ids']:
            must_reject(lambda row=row:r.validate_row(row,rel));rejected+=1
    assert rejected==76
    negatives=0
    for key,val in [('w_nm','120'),('direction','X'),('dx_nm','2.5'),('blind_geometry','True'),('acceleration_m_s2','50000'),('P_nm','240'),('h_nm','50'),('role','prediction_test')]:
        bad={**rows[0],key:val};must_reject(lambda bad=bad:r.validate_row(bad,rel));negatives+=1
    must_reject(lambda:r.validate_row(rows[0],{**rel,'released':False}));negatives+=1
    must_reject(lambda:r.ensure_new_batch('foundation_20261023_v1'));negatives+=1
    p=r.policy();r.resource_check(p,available=p['minimum_available_RAM_bytes'],free=p['minimum_free_disk_bytes'])
    must_reject(lambda:r.resource_check(p,available=p['minimum_available_RAM_bytes']-1,free=p['minimum_free_disk_bytes']));negatives+=1
    must_reject(lambda:r.resource_check(p,available=p['minimum_available_RAM_bytes'],free=p['minimum_free_disk_bytes']-1));negatives+=1
    # Isolated temporary file: no mutation of actual source or frozen bindings.
    with tempfile.TemporaryDirectory(prefix='d4-remaining14-review-') as td:
        f=Path(td)/'input';f.write_text('frozen');bound=dict(bound_inputs_sha256={str(f):r.sha(f)})
        r.validate_binding(bound);f.write_text('changed');must_reject(lambda:r.validate_binding(bound));negatives+=1
    must_reject(lambda:r.validate_binding({}));negatives+=1
    # Isolated batch directory tests the existing-batch branch, not only wrong IDs.
    with tempfile.TemporaryDirectory(prefix='d4-batch-guard-') as td:
        old_case=r.CASE;r.CASE=Path(td)
        try:
            (r.CASE/'results'/p['batch_id']).mkdir(parents=True)
            must_reject(lambda:r.ensure_new_batch(p['batch_id']));negatives+=1
        finally:r.CASE=old_case
    for row in rows:assert r.template_path(row).read_text()==r.config_text(row)
    for script in HERE.glob('*.py'):ast.parse(script.read_text())
    out=dict(ok=True,allowed_rows_checked=14,other_canonical_rows_rejected=rejected,additional_negative_checks=negatives,config_templates_checked=14,all_scripts_AST_parse=True,formal_solver_executed=False,formal_batch_exists=(CASE/'results'/p['batch_id']).exists())
    assert not out['formal_batch_exists']
    if a.released:
        release=json.loads((HERE/'release.json').read_text());r.validate_ready(p['batch_id'],release)
        for env in ({'OMPI_COMM_WORLD_SIZE':'2'},{'PMI_SIZE':'2'},{'SIM240_OLB_ROOT':'/different/root'}):must_reject(lambda env=env:r.runtime_environment(release,env))
        command=[sys.executable,str(HERE/'run_remaining.py'),'--batch-id',p['batch_id']]
        check=subprocess.run(command,capture_output=True,text=True);assert check.returncode==0,check.stderr
        dry=json.loads(check.stdout);assert dry['will_run'] is False and dry['cases']==14
        (HERE/'evidence/command_dry_run.json').write_text(json.dumps(dry,ensure_ascii=False,indent=2)+'\n')
        out.update(runtime_environment_guards_checked=3,bound_inputs_checked=len(release['bound_inputs_sha256']),release_sha256=r.sha(HERE/'release.json'),command_dry_run=True)
    name='final_review.json' if a.released else 'prebinding_review.json'
    (HERE/'evidence'/name).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
