#!/usr/bin/env python3
"""C04 static checks: source identity, physical inputs, mesh and matrix; no solve."""
import ast
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    if os.environ.get('WM_PROJECT_VERSION')!='13':raise RuntimeError('Foundation13 required')
    target=ROOT/'reports/preparation.json'
    if target.exists():raise FileExistsError('Preparation already recorded')
    reuse=json.loads((ROOT/'reports/solver_reuse.json').read_text())
    for rec in reuse['files']:
        if sha(ROOT/rec['path'])!=rec['sha256']:raise ValueError('Reused source/binary changed')
    cfg=json.loads((ROOT/'common/C04.json').read_text())
    proto=json.loads((ROOT/'common/protocol.json').read_text())
    assert cfg['thresholds']==proto['thresholds'] and cfg['linear_solver']==proto['linear_solver']
    for key,path in cfg['source_paths'].items():assert sha(Path(path))==cfg['source_hashes'][key]
    baseline=json.loads((ROOT.parent/'interface_static_darcy_v1_1/common/C02.json').read_text())
    transverse=json.loads((ROOT.parent/'interface_static_darcy_v1_2/common/C03.json').read_text())
    shared=['H_m','L_m','mu_Pa_s','rho_kg_m3','mesh_cells','drive_axis','G_Pa_per_m',
            'pressure_units','velocity_definition','thresholds','linear_solver','source_hashes','source_paths']
    for key in shared:assert cfg[key]==baseline[key]==transverse[key],key
    planned=next(c for c in proto['planned_cases'] if c['case_id']=='C04')
    other=next(c for c in proto['planned_cases'] if c['case_id']=='C02')
    assert planned['input_id']==cfg['coefficient_input_id']=='original_local_cubic'
    assert planned['orientation_id']==other['orientation_id']==cfg['orientation_id']=='groove_along_short_x'
    coefficients=json.loads(Path(cfg['source_paths']['coefficient_source']).read_text())
    row=next(r for r in coefficients['rows'] if r['input_id']==planned['input_id'] and r['orientation_id']==planned['orientation_id'])
    assert cfg['K_m3']==row['K_global_m3'] and cfg['D_m_minus2']==row['D_global_m_minus2_conditional_total_drag']
    h,d=75e-9,100e-9
    para=((h+d)**3+h**3)/24
    perp=(h+d)**3*h**3/(6*((h+d)**3+h**3))
    for a,value in enumerate([para,perp]):assert abs(cfg['K_m3'][a][a]/value-1)<2e-15
    for key in ['K_m3','D_m_minus2']:
        assert cfg[key][0][0]==transverse[key][1][1] and cfg[key][1][1]==transverse[key][0][0]
        assert cfg[key][0][1]==cfg[key][1][0]==0
    for a in range(2):assert abs(cfg['K_m3'][a][a]*cfg['D_m_minus2'][a][a]/cfg['H_m']-1)<2e-12
    oldcase=ROOT.parent/'interface_static_darcy_v1_1/openfoam/cases/C02'
    case=ROOT/'openfoam/cases/C04'
    identical=['0/p','system/blockMeshDict','system/controlDict','system/fvSchemes','system/fvSolution']
    identical+=['constant/polyMesh/'+s for s in ['boundary','faces','neighbour','owner','points']]
    for rel in identical:assert (case/rel).read_bytes()==(oldcase/rel).read_bytes(),rel
    def values(p):return dict(line.split() for line in p.read_text().splitlines() if line.strip())
    old=values(ROOT.parent/'interface_static_darcy_v1_1/common/C02_2d.txt')
    new=values(ROOT/'common/C04_2d.txt');assert old.keys()==new.keys()
    for key in old:
        if key not in ['Kxx','Kyy']:assert old[key]==new[key],key
    commands=[]
    def call(label,argv):
        log=ROOT/'reports'/(label+'.log')
        if log.exists():raise FileExistsError('Audit log already exists')
        start=time.time()
        with log.open('w') as stream:
            p=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=300)
        commands.append(dict(label=label,argv=argv,exit_code=p.returncode,seconds=time.time()-start,log=str(log.relative_to(ROOT))))
        (ROOT/'reports/audit_commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if p.returncode:raise RuntimeError(label+' failed; no retry or flow solve')
        return log.read_text()
    text=call('checkMesh',['checkMesh','-case',str(case),'-allGeometry','-allTopology'])
    assert 'Mesh OK.' in text
    two=json.loads(call('audit_2d',[str(ROOT/'build/bin/darcy2d'),'--input',str(ROOT/'common/C04_2d.txt'),'--audit-only']).strip())
    text=call('audit_openfoam',[str(ROOT/'build/bin/depthAveragedDarcyFoam'),'-case',str(case),'-auditOnly'])
    foam=json.loads(next(line.split('SDI_AUDIT ',1)[1] for line in text.splitlines() if line.startswith('SDI_AUDIT ')))
    assert two['cells']==foam['cells']==512 and two['flow_solved'] is False and foam['flow_solved'] is False
    assert foam['matrix_assembled'] and foam['matrix_symmetric'] and foam['matrix_min_diagonal']>0
    assert foam['initial_p_max_Pa']==0 and foam['Dxx_m_minus2']==cfg['D_m_minus2'][0][0] and foam['Dyy_m_minus2']==cfg['D_m_minus2'][1][1]
    volume=cfg['L_m'][0]*cfg['L_m'][1]*cfg['H_m']
    assert abs(two['volume_m3']/volume-1)<1e-12 and abs(foam['volume_m3']/volume-1)<1e-12
    for path in ROOT.rglob('*.py'):ast.parse(path.read_text())
    expected=dict(kind='ANALYTIC_EXPECTATION_NOT_C04_SOLVER_OUTPUT',pressure_drop_Pa=24,
        Kxx_m3=cfg['K_m3'][0][0],Kyy_m3=cfg['K_m3'][1][1],Dxx_m_minus2=cfg['D_m_minus2'][0][0],Dyy_m_minus2=cfg['D_m_minus2'][1][1],
        Ux_m_s=cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/(cfg['mu_Pa_s']*cfg['H_m']),
        Jx_m2_s=cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/cfg['mu_Pa_s'],
        Qx_m3_s=cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/cfg['mu_Pa_s']*cfg['L_m'][1],
        C04_to_C02_analytic_Q_ratio=cfg['K_m3'][0][0]/baseline['K_m3'][0][0],
        C04_to_C03_analytic_Q_ratio=cfg['K_m3'][0][0]/transverse['K_m3'][0][0])
    (ROOT/'common/C04_expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    report=dict(date='2026-10-30',release_version='1.3.0',protocol_id='SDI-v1',case_id='C04',
        kind='UNCHANGED_BINARY_REUSE_AND_STATIC_AUDIT_ONLY',commands=commands,
        binary_source_binding=[dict(path=r['path'],sha256=r['sha256']) for r in reuse['files']],
        inherited_compile_evidence='reports/inherited_C01_preparation.json',new_compilation_performed=False,
        two_dimensional_audit=two,openfoam_audit=foam,thresholds_unchanged=True,linear_solver_unchanged=True,
        C02_same_direction_only_coefficient_family_changed=True,C03_K_D_principal_values_swapped_together=True,
        identical_C02_boundary_mesh_numerics_files=identical,flow_solver_executed=False,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=True,geometry_scope='synthetic_average_domain_only')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print('C04 source/binary identity, original coefficients, mesh and matrix verified; no flow solve.')


if __name__=='__main__':main()
