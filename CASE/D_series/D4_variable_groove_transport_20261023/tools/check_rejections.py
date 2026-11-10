#!/usr/bin/env python3
"""Negative CLI/config tests and stage guard tests, without any time advancement."""
from pathlib import Path
import importlib.util
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('runner',ROOT/'tools/run_case.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
report=json.loads((ROOT/'evidence/preflight.json').read_text())
sample=ROOT/report['configuration_output_directories'][0]/'run_config.txt'
base=run.kv(sample);negative=ROOT/'evidence/negative_configs';negative.mkdir(exist_ok=True)
changes=[('dx_zero',{'dx_nm':'0'}),('h_negative',{'h_nm':'-1'}),('d_negative',{'d_nm':'-1'}),
         ('w_equal_period',{'w_nm':base['period_nm']}),('nonaligned',{'w_nm':'61'}),
         ('nan',{'h_nm':'nan'}),('inf',{'nu_m2_s':'inf'}),('suffix',{'dx_nm':'5oops'}),
         ('bad_direction',{'direction':'45'}),('unknown',{'surprise':'1'}),
         ('bad_mode',{'mode':'run_all'}),('runid_path',{'run_id':'../bad'}),
         ('frames_reverse',{'frame_tstar':'0,.2,.1'}),('frames_trailing',{'frame_tstar':'0,.2,'}),
         ('window_zero',{'window_tstar':'0'}),('window_over_cap',{'window_tstar':'9'}),
         ('huge_grid',{'dx_nm':'0.00001'})]
records=[]
for name,patch in changes:
    values=base|patch;file=negative/(name+'.txt');file.write_text(''.join(f'{k}={v}\n' for k,v in values.items()))
    command=[str(ROOT/'build/variable_groove_transport'),str(file)]
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=20)
    assert result.returncode==2,(name,result.returncode)
    records.append({'case':name,'exit_code':result.returncode,'reason':result.stderr.strip()})
# Reusing an already completed directory must be rejected, not overwritten.
old=run.sha(sample.parent/'effective_config.txt')
result=subprocess.run([str(ROOT/'build/variable_groove_transport'),str(sample)],cwd=ROOT,capture_output=True,text=True)
assert result.returncode==2 and run.sha(sample.parent/'effective_config.txt')==old
records.append({'case':'overwrite_guard','exit_code':2,'reason':result.stderr.strip()})
fake={'released':True,'allowed_case_ids':['allowed'],'bound_inputs_sha256':{str(sample):run.sha(sample)}}
for row,rel in [({'planned_case_id':'forbidden'},fake),({'planned_case_id':'allowed'},fake|{'released':False}),
                ({'planned_case_id':'allowed'},fake|{'bound_inputs_sha256':{}})]:
    try:run.validate_release(row,rel)
    except RuntimeError:pass
    else:raise AssertionError('invalid stage release accepted')
run.validate_release({'planned_case_id':'allowed'},fake)
out={'ok':True,'config_and_overwrite_rejections':len(records),'stage_guard_negative_tests':3,
     'stage_guard_positive_test':1,'records':records,'solver_time_advancement':False}
(ROOT/'evidence/rejection_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='records'},ensure_ascii=False))
