#!/usr/bin/env python3
"""Short algebraic tests only: no PDE solve, time loop, fitting, or formal run."""
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import time
from prepare_fixture import PKG, ROOT, prepare

def main():
    if os.environ.get('WM_PROJECT_VERSION') != '13':
        raise SystemExit('Source the Foundation 13 environment first')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    fixture=prepare()
    logs=PKG/'build/logs'
    logs.mkdir(parents=True, exist_ok=True)
    entries=[]
    variants={
        'normal':None, 'noMu':None, 'noNu':None,
        'zeroGap':'Require positive gap', 'negativeGap':'Require positive gap',
        'nanGap':'Require positive gap', 'wrongGapUnits':'gapField must have length dimensions',
        'unequalDuty':'equal groove/land widths', 'manualD':'Do not supply d/f/H',
        'wrongMatrixUnits':'Unsupported momentum matrix dimensions',
    }
    for variant,message in variants.items():
        cmd=[str(PKG/'build/bin/auditPorosity'),'-case',str(fixture),'-variant',variant]
        start=time.monotonic()
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
        (logs/f'audit_{variant}.log').write_text(p.stdout)
        passed=(p.returncode==0 and 'ASSEMBLY_PASS' in p.stdout) if message is None else (p.returncode!=0 and message in p.stdout and 'Invalid fixture unexpectedly accepted' not in p.stdout)
        entries.append(dict(variant=variant,command=cmd,exit_code=p.returncode,seconds=time.monotonic()-start,expected_rejection=message,passed=passed))
        if not passed:
            print(p.stdout[-3000:])
            raise RuntimeError(f'{variant} check failed')
    p=subprocess.run([str(PKG/'build/bin/testTransport')],capture_output=True,text=True,timeout=10)
    (logs/'coefficients.log').write_text(p.stdout+p.stderr)
    if p.returncode or 'COEFFICIENT_PASS' not in p.stdout: raise RuntimeError('Coefficient tests failed')
    examples=ROOT/'docs/reports/Shared_transport_interface_20261030/coefficient_examples.json'
    expected=json.loads(examples.read_text())['rows']
    matches=[]
    for line in (logs/'audit_normal.log').read_text().splitlines():
        if not line.startswith('COEFF '): continue
        _,family,angle,field,update,h,H,kp,kt,dxx,dyy=line.split()
        if angle not in ('0','90') or field!='0' or update!='0': continue
        orientation='groove_along_short_x' if angle=='0' else 'groove_along_long_y'
        row=next(r for r in expected if r['input_id']==family and r['orientation_id']==orientation)
        pairs=[(float(H),125e-9),(float(kp),row['K_parallel_m3']),(float(kt),row['K_perpendicular_m3']),
            (float(dxx),row['D_global_m_minus2_conditional_total_drag'][0][0]),
            (float(dyy),row['D_global_m_minus2_conditional_total_drag'][1][1])]
        errors=[abs(a/b-1) for a,b in pairs]
        assert all(math.isfinite(e) and e<=1e-12 for e in errors)
        matches.append(dict(family=family,orientation=orientation,max_relative_error=max(errors)))
    assert len(matches)==4
    result=dict(status='ASSEMBLY_TESTS_PASS_NOT_FLOW_VALIDATION',tests=entries,
        coefficient_test=p.stdout.strip(),frozen_coefficient_comparisons=matches,
        coefficient_source=str(examples.relative_to(ROOT)),
        coefficient_source_sha256=hashlib.sha256(examples.read_bytes()).hexdigest(),
        source_sha256={str(f.relative_to(PKG)):hashlib.sha256(f.read_bytes()).hexdigest()
            for sub in ('src','tests','scripts') for f in (PKG/sub).rglob('*')
            if f.is_file() and not f.is_symlink() and 'linux64GccDPInt32Opt' not in f.parts and '__pycache__' not in f.parts},
        flow_solved=False,mesh_motion_tested=False,continuity_coupling_tested=False,
        physical_validation='NOT_EVALUATED',NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None)
    (logs/'assembly_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','coefficient_test','frozen_coefficient_comparisons','flow_solved')},indent=2))
if __name__=='__main__': main()
