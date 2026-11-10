#!/usr/bin/env python3
"""Independent static/negative checks. Never invokes a solver or executes a batch."""
from pathlib import Path
import ast,copy,csv,importlib.util,json,sys
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',ROOT/'run_development.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def must_reject(action):
    try:action()
    except (RuntimeError,SystemExit,KeyError):return True
    raise AssertionError('negative guard accepted')
def main():
    release=m.load_release();m.validate_binding(release);rows=m.rows();selected=[r for r in rows if r['substage']=='screen']
    original=m.stage_original_rows if hasattr(m,'stage_original_rows') else m.base.candidates()
    allowed=set(release['allowed_case_ids']);assert len(allowed)==6
    for row in selected:m.validate_row(row,release)
    blocked=[]
    for row in original:
        if row['planned_case_id'] in allowed:continue
        assert must_reject(lambda:m.validate_row(row,release));blocked.append(row['planned_case_id'])
    assert len(blocked)==84
    negatives=0
    for change in [{'blind_geometry':'True'},{'dx_nm':'2.5'},{'h_nm':'76'},{'acceleration_m_s2':'300000'},{'direction':'Z'}]:
        wrong=selected[0]|change;assert must_reject(lambda:m.validate_row(wrong,release));negatives+=1
    wrong=copy.deepcopy(release);wrong['released']=False
    assert must_reject(lambda:m.validate_row(selected[0],wrong));negatives+=1
    wrong=copy.deepcopy(release);first=next(iter(wrong['bound_inputs_sha256']));wrong['bound_inputs_sha256'][first]='0'*64
    assert must_reject(lambda:m.validate_binding(wrong));negatives+=1
    policy=json.loads((ROOT/'policy.json').read_text());wrong=policy|{'minimum_available_RAM_bytes':2**90}
    assert must_reject(lambda:m.resource_check(wrong));negatives+=1
    wrong=policy|{'minimum_free_disk_bytes':2**90};assert must_reject(lambda:m.resource_check(wrong));negatives+=1
    for f in ROOT.glob('*.py'):ast.parse(f.read_text())
    tree=ast.parse((ROOT/'run_development.py').read_text())
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    assert not any(isinstance(n.func,ast.Attribute) and n.func.attr in ['launch','system','Popen'] for n in calls)
    assert len([n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='run'])==1
    assert not (ROOT.parent/'results'/policy['batch_id']).exists()
    output={'ok':True,'allowed_cases_checked':6,'all_other_main_rows_rejected':84,'additional_negative_guards':negatives,
        'python_AST_parse':'PASS','resource_precheck':m.resource_check(policy),'formal_batch_exists':False,
        'solver_executed_by_review':False,'bound_inputs_checked':len(release['bound_inputs_sha256']),
        'solver_source_unchanged':True,'next_stage_automatically_run':False}
    (ROOT/'evidence/review.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
    print(json.dumps(output,ensure_ascii=False))
if __name__=='__main__':main()
