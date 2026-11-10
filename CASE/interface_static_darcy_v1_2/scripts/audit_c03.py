#!/usr/bin/env python3
"""C03 static audit only: verify reused binaries, checkMesh, assemble without solve."""
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
    if os.environ.get('WM_PROJECT_VERSION')!='13':raise RuntimeError('Foundation 13 environment required')
    report_path=ROOT/'reports/preparation.json'
    if report_path.exists():raise FileExistsError('Static preparation already recorded')
    reuse=json.loads((ROOT/'reports/solver_reuse.json').read_text())
    for rec in reuse['files']:
        if sha(ROOT/rec['path'])!=rec['sha256']:raise ValueError('Reused source or binary changed')
    cfg=json.loads((ROOT/'common/C03.json').read_text());proto=json.loads((ROOT/'common/protocol.json').read_text())
    if cfg['thresholds']!=proto['thresholds']:raise ValueError('Scientific thresholds changed')
    for key,path in cfg['source_paths'].items():
        if sha(Path(path))!=cfg['source_hashes'][key]:raise ValueError('Upstream source changed')
    baseline=json.loads((ROOT.parent/'interface_static_darcy_v1/common/C01.json').read_text())
    for key in ['H_m','L_m','mu_Pa_s','rho_kg_m3','mesh_cells','drive_axis','G_Pa_per_m','thresholds','linear_solver']:
        if cfg[key]!=baseline[key]:raise ValueError('Unintended C01/C03 difference: '+key)
    planned=next(c for c in proto['planned_cases'] if c['case_id']=='C03')
    c01=next(c for c in proto['planned_cases'] if c['case_id']=='C01')
    assert planned['input_id']=='original_local_cubic'
    assert planned['orientation_id']==c01['orientation_id']=='groove_along_long_y'
    assert cfg['coefficient_input_id']==planned['input_id'] and cfg['orientation_id']==planned['orientation_id']
    source=json.loads(Path(cfg['source_paths']['coefficient_source']).read_text())
    row=next(r for r in source['rows'] if r['input_id']==planned['input_id'] and r['orientation_id']==planned['orientation_id'])
    assert cfg['K_m3']==row['K_global_m3'] and cfg['D_m_minus2']==row['D_global_m_minus2_conditional_total_drag']
    h,d=75e-9,100e-9
    original_perp=(h+d)**3*h**3/(6*((h+d)**3+h**3))
    original_para=((h+d)**3+h**3)/24
    for a,expected in enumerate([original_perp,original_para]):
        assert abs(cfg['K_m3'][a][a]/expected-1)<2e-15
    assert cfg['K_m3'][0][1]==cfg['K_m3'][1][0]==0
    assert cfg['D_m_minus2'][0][1]==cfg['D_m_minus2'][1][0]==0
    oldcase=ROOT.parent/'interface_static_darcy_v1/openfoam/cases/C01'
    newcase=ROOT/'openfoam/cases/C03'
    same_files=['0/p','system/blockMeshDict','system/controlDict','system/fvSchemes','system/fvSolution']
    same_files += ['constant/polyMesh/'+name for name in ['boundary','faces','neighbour','owner','points']]
    for rel in same_files:
        if (newcase/rel).read_bytes()!=(oldcase/rel).read_bytes():
            raise ValueError('C01/C03 boundary/mesh/numerics changed: '+rel)
    # Only Kxx/Kyy may differ in the two-dimensional input.
    def read_input(path):
        return dict(line.split() for line in path.read_text().splitlines() if line.strip())
    oldinput=read_input(ROOT.parent/'interface_static_darcy_v1/common/C01_2d.txt')
    newinput=read_input(ROOT/'common/C03_2d.txt')
    assert set(oldinput)==set(newinput)
    for key in oldinput:
        if key not in ['Kxx','Kyy']:assert oldinput[key]==newinput[key], key
    commands=[]
    def call(label,argv):
        start=time.time();log_path=ROOT/'reports'/(label+'.log')
        if log_path.exists():raise FileExistsError('Refusing existing audit log')
        with log_path.open('w') as log:
            p=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        commands.append(dict(label=label,argv=argv,exit_code=p.returncode,seconds=time.time()-start,log=str(log_path.relative_to(ROOT))))
        (ROOT/'reports/audit_commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if p.returncode:raise RuntimeError(label+' failed; no retry or solve')
        return log_path.read_text()
    case=ROOT/'openfoam/cases/C03'
    mesh=call('checkMesh',['checkMesh','-case',str(case),'-allGeometry','-allTopology'])
    if 'Mesh OK.' not in mesh:raise RuntimeError('Mesh check did not report OK')
    two=json.loads(call('audit_2d',[str(ROOT/'build/bin/darcy2d'),'--input',str(ROOT/'common/C03_2d.txt'),'--audit-only']).strip())
    text=call('audit_openfoam',[str(ROOT/'build/bin/depthAveragedDarcyFoam'),'-case',str(case),'-auditOnly'])
    foam=json.loads(next(line.split('SDI_AUDIT ',1)[1] for line in text.splitlines() if line.startswith('SDI_AUDIT ')))
    assert two['cells']==foam['cells']==512 and two['flow_solved'] is False and foam['flow_solved'] is False
    assert foam['matrix_assembled'] and foam['matrix_symmetric'] and foam['matrix_min_diagonal']>0
    assert foam['Dxx_m_minus2']==cfg['D_m_minus2'][0][0] and foam['Dyy_m_minus2']==cfg['D_m_minus2'][1][1]
    V=cfg['L_m'][0]*cfg['L_m'][1]*cfg['H_m']
    assert abs(two['volume_m3']/V-1)<1e-12 and abs(foam['volume_m3']/V-1)<1e-12
    for p in ROOT.rglob('*.py'):ast.parse(p.read_text())
    for axis in range(2):assert abs(cfg['K_m3'][axis][axis]*cfg['D_m_minus2'][axis][axis]/cfg['H_m']-1)<2e-12
    expected=dict(kind='ANALYTIC_EXPECTATION_NOT_C03_SOLVER_OUTPUT',pressure_drop_Pa=24,
                  Kxx_m3=cfg['K_m3'][0][0],Kyy_m3=cfg['K_m3'][1][1],
                  Dxx_m_minus2=cfg['D_m_minus2'][0][0],Dyy_m_minus2=cfg['D_m_minus2'][1][1],
                  Ux_m_s=cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/(cfg['mu_Pa_s']*cfg['H_m']),
                  Jx_m2_s=cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/cfg['mu_Pa_s'],
                  Qx_m3_s=cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/cfg['mu_Pa_s']*cfg['L_m'][1],
                  C03_to_C01_analytic_Q_ratio=cfg['K_m3'][0][0]/baseline['K_m3'][0][0])
    (ROOT/'common/C03_expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    result=dict(date='2026-10-30',release_version='1.2.0',protocol_id='SDI-v1',case_id='C03',
                kind='UNCHANGED_BINARY_REUSE_AND_STATIC_AUDIT_ONLY',commands=commands,
                binary_source_binding=[dict(path=r['path'],sha256=r['sha256']) for r in reuse['files']],
                inherited_compile_evidence='reports/inherited_C01_preparation.json',new_compilation_performed=False,
                two_dimensional_audit=two,openfoam_audit=foam,thresholds_unchanged=True,
                C01_C03_only_tensors_and_case_identity_differ=True,flow_solver_executed=False,
                NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=True,geometry_scope='synthetic_average_domain_only')
    report_path.write_text(json.dumps(result,indent=2)+'\n')
    print('C03 reused program hashes, mesh, inputs, and matrix assembly verified; no pressure iterations.')


if __name__=='__main__':main()
