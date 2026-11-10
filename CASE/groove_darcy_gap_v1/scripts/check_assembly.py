#!/usr/bin/env python3
"""Compile separately; this script runs native matrix/flux audits, never solve()."""
import csv
import hashlib
import json
import math
import os
import resource
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parents[1]


def records(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def near(a, b, rel=2e-12, absolute=1e-40):
    assert math.isfinite(a) and math.isfinite(b)
    assert math.isclose(a, b, rel_tol=rel, abs_tol=absolute), (a, b)


def field(name, values, dims='0 1 0 0 0 0 0'):
    return ('FoamFile { format ascii; class volScalarField; object '+name+'; }\n'
            'dimensions ['+dims+'];\ninternalField nonuniform List<scalar>\n512\n(\n'
            +'\n'.join(format(x, '.17g') for x in values)+'\n);\nboundaryField\n{\n'
            +'\n'.join(p+' { type zeroGradient; }' for p in ('xLow','xHigh','yLow','yHigh'))
            +'\nfrontAndBack { type empty; }\n}\n')


def prepare(case, variant):
    base = ROOT/'CASE/groove_darcy_static_v1/cases/GDI01'
    mesh = ROOT/'CASE/groove_darcy_static_v1/runs/GDI01_v1_20261030_01/openfoam/constant/polyMesh'
    shutil.copytree(base, case)
    shutil.copytree(mesh, case/'constant/polyMesh', dirs_exist_ok=True)
    ctrl = case/'system/controlDict'
    ctrl.write_text(ctrl.read_text().replace('grooveDarcyStaticFoam','grooveDarcyGapFoam')
                    .replace('"libgroovePorosity.so"', '"'+str(PKG/'build/lib/libgroovePorosity.so')+'"'))
    config=(ROOT/'CASE/groove_porosity_model_v1/examples/fvModels.gapField').read_text()
    if variant=='uniformMode':
        config=config.replace('gapMode field;', 'gapMode uniform;').replace('gapField mesaGap;', 'mesaGap [0 1 0 0 0 0 0] 75e-9;')
    if variant=='originalModel':
        config=config.replace('conductanceModel V2_published_rounded;', 'conductanceModel original_local_cubic;')
    (case/'constant/fvModels').write_text(config)
    dt=.25
    h=[75e-9]*512; previous=h.copy()
    if variant=='uniformClosure':
        h=[70e-9]*512;previous=[72e-9]*512
    if variant in ('spatialGap','spatialClosure','spatialOpening'):
        h=[(50e-9 if i%2 else 100e-9) for i in range(512)]
        increment=2e-9 if variant=='spatialClosure' else -2e-9 if variant=='spatialOpening' else 0
        previous=[x+increment for x in h]
    if variant=='negativeGap': h[0]=-1e-9
    if variant=='negativePrevious': previous[0]=-1e-9
    if variant=='zeroDeltaT': dt=0
    (case/'0/mesaGap').write_text(field('mesaGap',h,'0 0 0 0 0 0 0' if variant=='wrongUnits' else '0 1 0 0 0 0 0'))
    (case/'0/previousMesaGap').write_text(field('previousMesaGap',previous))
    props=case/'constant/gdiProperties'
    props.write_text(props.read_text()+'\nreferenceThickness [0 1 0 0 0 0 0] '
                     +('100e-9' if variant=='wrongReferenceThickness' else '125e-9')
                     +';\ngapDeltaT [0 0 1 0 0 0 0] '+str(dt)+';\ngapEpoch audit_'+variant+';\n')
    return h,previous,dt


def check_native(case, h, previous, dt, baseline):
    out=case/'GAP_audit'
    receipt=json.loads((out/'audit.json').read_text())
    assert receipt['solve_calls']==0 and receipt['flow_solved'] is False
    assert receipt['cells']==512 and receipt['zone_cells']==512
    gaps=records(out/'gap_snapshot.csv');matrix=records(out/'matrix.csv')
    coeff=records(out/'coefficients.csv');links=records(out/'pressure_links.csv')
    probe=records(out/'pressure_flux_probe.csv')
    assert len(gaps)==len(matrix)==len(coeff)==512 and len(probe)==len(links)==976
    total=0
    v2='conductanceModel V2_published_rounded;' in (case/'constant/fvModels').read_text()
    for i,(g,m,d) in enumerate(zip(gaps,matrix,coeff)):
        height=h[i]+50e-9;rate=(h[i]-previous[i])/dt
        near(float(g['mesaGap_m']),h[i]);near(float(g['previousMesaGap_m']),previous[i])
        near(float(g['H_m']),height);near(float(g['Hdot_m_s']),rate)
        area=float(g['plan_area_m2']);storage=area*rate
        near(area,24e-6*48e-6/512)
        near(float(g['storage_rate_m3_s']),storage);total+=storage
        # Zero U: phiHat is zero. RHS must be -area*dH/dt, not zero.
        near(float(m['pressure_source']),-storage)
        # Native trace split gives rAU = 1/(mu * trace(D)).
        near(float(m['rAU']),1/(.001*(float(d['Dxx_m_minus2'])+float(d['Dyy_m_minus2']))))
        near(float(d['H_m']),height)
        a,b=h[i]**3,(h[i]+100e-9)**3
        kp=(a+b)/24;kt=1/(6*(1/a+1/b))
        if v2:
            kp/=1+1.7685*(100/120)**1.6331
            kt/=1+.4900*(100/120)**.6990
        # Along y, across x: verify that the actual native submodel consumed h.
        near(float(d['Dxx_m_minus2']),height/kt)
        near(float(d['Dyy_m_minus2']),height/kp)
    near(receipt['storage_total_m3_s'],total,absolute=1e-32)
    for link,q in zip(links,probe):
        a,b=int(link['owner']),int(link['neighbour'])
        weight=((h[a]+50e-9)+(h[b]+50e-9))/(2*125e-9)
        mobility=(float(matrix[a]['rAU'])+float(matrix[b]['rAU']))/2
        near(float(link['weight_H_over_b0']),weight)
        near(float(link['rAU_face']),mobility)
        conductance=weight*mobility*float(link['area_m2'])*float(link['deltaCoeff_m_minus1'])
        near(float(link['upper']),-conductance)
        near(float(q['corrected_depth_flux_m3_s']),conductance*(float(q['owner_p_Pa'])-float(q['neighbour_p_Pa'])))
    if baseline:
        old=records(ROOT/'CASE/groove_darcy_static_v1/reports/audit_evidence/matrix.csv')
        for a,b in zip(matrix,old):
            for key in ('momentum_diag_kg_s','pressure_diagonal','pressure_source','rAU'):
                near(float(a[key]),float(b[key]))
    return {'storage_total_m3_s':total,'native_flux_links_checked':len(links),
            'storage_cells_checked':len(gaps),'static_matrix_matches_saved_GDI01':baseline,
            'solve_calls':0,'flow_solved':False}


def main():
    assert os.environ.get('WM_PROJECT_VERSION')=='13'
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    suite=PKG/'build'/('checks_'+datetime.now().strftime('%Y%m%dT%H%M%S_%f'))
    suite.mkdir(parents=True,exist_ok=False)
    variants={'baseline':None,'originalModel':None,'uniformClosure':None,'spatialGap':None,
              'spatialClosure':None,'spatialOpening':None,
              'negativeGap':'Nonpositive or nonfinite gap snapshot',
              'negativePrevious':'Nonpositive or nonfinite gap snapshot',
              'wrongUnits':'Both gap snapshots must have length dimensions',
              'zeroDeltaT':'Invalid reference thickness or gapDeltaT',
              'wrongReferenceThickness':'Reference mesh thickness must remain 125nm',
              'uniformMode':'GAP requires registered mesaGap field'}
    results=[]
    for name,error in variants.items():
        case=suite/name;h,previous,dt=prepare(case,name)
        command=[str(PKG/'build/bin/grooveDarcyGapFoam'),'-case',str(case),'-auditOnly']
        p=subprocess.run(command,capture_output=True,text=True,timeout=30)
        (suite/(name+'.log')).write_text(p.stdout+p.stderr)
        if error:
            assert p.returncode!=0 and error in p.stdout+p.stderr,(name,p.returncode,(p.stdout+p.stderr)[-2000:])
            result={'expected_rejection':error}
        else:
            assert p.returncode==0,(name,p.returncode,(p.stdout+p.stderr)[-3000:])
            result=check_native(case,h,previous,dt,name=='baseline')
        results.append({'variant':name,'exit_code':p.returncode,'passed':True,'command':command,**result})
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in suite.rglob('*') if p.is_file()}
    receipt={'status':'GAP_FIELDS_AND_CONTINUITY_ASSEMBLY_PASS_NOT_FLOW_ACCEPTANCE',
             'suite':str(suite.relative_to(ROOT)),'tests':results,'solver_calls':0,
             'physical_time_advanced':False,'formal_run_id':None,'NUMERICAL_GATE':'NOT_EVALUATED',
             'RESULT_PASS':False,'geometry_PASS':None,'file_sha256':manifest}
    (suite/'checks.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    (PKG/'build/latest_checks.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('status','suite','solver_calls','physical_time_advanced')},indent=2))


if __name__=='__main__':
    main()
