#!/usr/bin/env python3
"""Native invalid-input audits ONLY. No -solve option is ever invoked here."""
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import time
PKG=Path(__file__).resolve().parents[1]
def main():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    definitions=[('half_zone','Porous zone must cover every cell'),('wrong_units','p must be Pa'),
        ('nonzero_initial','Internal initial p and U must be zero'),('wrong_orientation','Wrong GDI01 cross-groove tensor response')]
    records=[]
    for name,message in definitions:
        case=PKG/'build/negative_audits'/name
        if case.exists():raise FileExistsError('Refusing old negative fixture')
        shutil.copytree(PKG/'cases/GDI01',case)
        if name=='half_zone':
            (case/'constant/polyMesh/cellZones').write_text('FoamFile { format ascii; class cellZoneList; object cellZones; }\n1\n( groove { type cellZone; cellLabels List<label> 256 ( '+' '.join(map(str,range(256)))+' ); } )\n')
        elif name=='wrong_units':
            f=case/'0/p';f.write_text(f.read_text().replace('[1 -1 -2 0 0 0 0]','[0 2 -2 0 0 0 0]'))
        elif name=='nonzero_initial':
            f=case/'0/p';f.write_text(f.read_text().replace('internalField uniform 0;','internalField uniform 1;'))
        else:
            f=case/'constant/fvModels';f.write_text(f.read_text().replace('e1 (0 1 0)','e1 (1 0 0)').replace('e2 (-1 0 0)','e2 (0 1 0)'))
        cmd=[str(PKG/'build/bin/grooveDarcyStaticFoam'),'-case',str(case),'-auditOnly']
        start=time.monotonic();r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
        (PKG/'reports'/('reject_'+name+'.log')).write_text(r.stdout)
        passed=r.returncode!=0 and message in r.stdout and not (case/'GDI_output').exists()
        records.append(dict(name=name,argv=cmd,exit_code=r.returncode,seconds=time.monotonic()-start,expected_error=message,passed=passed,flow_solved=False))
        if not passed:raise RuntimeError(name+' did not fail as intended: '+r.stdout[-1500:])
    report=dict(kind='NEGATIVE_NO_SOLVE_AUDITS_ONLY',tests=records,all_passed=True,flow_solved=False)
    (PKG/'reports/negative_audit_tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
