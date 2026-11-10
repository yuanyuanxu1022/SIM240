#!/usr/bin/env python3
"""Checker 1.1.0: read completed C01 or C02 outputs; never import or launch a flow solver."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

CHECKER_VERSION = "1.1.0"
SUPPORTED_CASES = {"C01", "C02"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline='') as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        for key in row:
            if key!='patch':
                row[key]=float(row[key])
                if not math.isfinite(row[key]):raise ValueError('Nonfinite raw CSV value')
    return rows


def evaluate(cfg,cells,faces,solver):
    """Pure data check, also exercised using explicitly synthetic in-memory fixtures."""
    t=cfg['thresholds']; H=cfg['H_m'];mu=cfg['mu_Pa_s']; nx,ny,nz=cfg['mesh_cells']
    lx,ly,b=cfg['L_m']; dx,dy=lx/nx,ly/ny; axis=cfg['drive_axis']; G=cfg['G_Pa_per_m']
    K=cfg['K_m3'][axis][axis]; D=cfg['D_m_minus2']; lengths=[lx,ly]
    Ustar=K*G/(mu*H);Jstar=H*Ustar;Qstar=Jstar*lengths[1-axis];dp=G*lengths[axis]
    checks=[]
    def add(name,value,limit):
        if not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Invalid metric '+name)
        checks.append(dict(name=name,value=value,limit=limit,satisfied=value<=limit))
    if nz!=1 or len(cells)!=nx*ny or len(faces)!=(nx+1)*ny+(ny+1)*nx:raise ValueError('Wrong cell/active face count')
    ids={};grid={}
    for r in cells:
        cid=int(r['cell_id'])
        if cid!=r['cell_id'] or cid in ids:raise ValueError('Invalid/duplicate cell id')
        i=round(r['x_m']/dx-.5);j=round(r['y_m']/dy-.5)
        if not (0<=i<nx and 0<=j<ny) or (i,j) in grid:raise ValueError('Wrong/duplicate cell position')
        if max(abs(r['x_m']/dx-i-.5),abs(r['y_m']/dy-j-.5),abs(r['z_m']/H-.5),abs(r['volume_m3']/(dx*dy*H)-1))>1e-10:raise ValueError('Wrong cell geometry')
        ids[cid]=r;grid[i,j]=r
        for a in 'xyz':
            if abs(r['J'+a+'_m2_s']-H*r['U'+a+'_m_s'])>max(abs(Jstar)*1e-12,1e-28):raise ValueError('J != H U')
    residual={k:0. for k in ids};boundary={s:0. for s in ['xLow','xHigh','yLow','yHigh']}
    leakage=0.;fluxdiff=0.;interpdiff=0.;fluxscale=0.;seen=set()
    for r in faces:
        owner=int(r['owner']);neighbour=int(r['neighbour'])
        if owner!=r['owner'] or neighbour!=r['neighbour'] or owner not in ids or (neighbour!=-1 and neighbour not in ids):raise ValueError('Invalid face addressing')
        sx,sy,sz=r['Sx_m2'],r['Sy_m2'],r['Sz_m2']
        # Geometry recognition repair only: reuse the existing 1e-10
        # normalized geometry tolerance, retaining every raw Sf/phi value.
        # Original strict-zero classifier rejected roundoff (max 5.44e-14).
        a=0 if abs(sx)>=abs(sy) else 1
        s=sx if a==0 else sy
        if s==0 or math.hypot(sy if a==0 else sx,sz)/abs(s)>1e-10:
            raise ValueError('Non-axis-aligned active face')
        i=round(r['x_m']/dx-(.5 if a==1 else 0));j=round(r['y_m']/dy-(.5 if a==0 else 0))
        n=nx if a==0 else ny;coord=i if a==0 else j
        if not (0<=i<=nx and 0<=j<=ny) or (a==0 and j>=ny) or (a==1 and i>=nx):raise ValueError('Face outside grid')
        key=(a,i,j)
        if key in seen:raise ValueError('Duplicate face')
        seen.add(key)
        if max(abs(r['x_m']/dx-i-(.5 if a==1 else 0)),abs(r['y_m']/dy-j-(.5 if a==0 else 0)),abs(r['z_m']/H-.5),abs(abs(s)/((dy if a==0 else dx)*H)-1))>1e-10:raise ValueError('Wrong face geometry')
        internal=coord not in [0,n]
        expected_patch='internal' if internal else ('xy'[a]+('Low' if coord==0 else 'High'))
        if r['patch']!=expected_patch or (neighbour>=0)!=internal:raise ValueError('Wrong patch/connectivity')
        # Owner must lie on the inward side of its outward face normal.
        cr=ids[owner];dot_normal=s*(r['x_m' if a==0 else 'y_m']-cr['x_m' if a==0 else 'y_m'])
        if dot_normal<=0:raise ValueError('Face normal inconsistent with owner')
        others=[cr]+([ids[neighbour]] if internal else [])
        for k,c in enumerate(others):
            sign=1 if k==0 else -1
            expected_x=r['x_m']-sign*math.copysign(dx/2,s) if a==0 else r['x_m']
            expected_y=r['y_m']-sign*math.copysign(dy/2,s) if a==1 else r['y_m']
            if max(abs((c['x_m']-expected_x)/dx),abs((c['y_m']-expected_y)/dy))>1e-10:raise ValueError('Face connected to wrong cell')
        q=r['phi_m3_s'];qu=r['phi_U_m3_s'];residual[owner]+=q
        if internal:residual[neighbour]-=q
        else:
            boundary[r['patch']]+=q
            if a!=axis:leakage+=abs(q)
        face_u=sum(c['U'+'xy'[a]+'_m_s'] for c in others)/len(others)
        if not internal and a!=axis:face_u=0.
        fluxdiff+=abs(q-qu);interpdiff+=abs(qu-face_u*s);fluxscale+=abs(q)
    if not solver.get('flow_solved') or not solver.get('converged'):raise ValueError('Solver did not report completed convergence')
    add('linear_normalized_residual',solver['normalized_residual'],1e-12)
    add('linear_true_normalized_residual',solver['true_normalized_residual'],1e-12)
    add('linear_iterations',solver['iterations'],2000)
    if solver['iterations']!=int(solver['iterations']) or solver['iterations']<0:raise ValueError('Bad iteration count')
    add('reported_raw_residual_finite',abs(solver['raw_residual_L1_m3_s']),1e100)
    V=sum(c['volume_m3'] for c in cells)
    mean=lambda field:sum(c[field]*c['volume_m3'] for c in cells)/V
    rms=lambda fn:math.sqrt(sum(fn(c)**2*c['volume_m3'] for c in cells)/V)
    main='xy'[axis];cross='yx'[axis]
    Q=boundary['xy'[axis]+'High']
    E=sum(mu*(D[0][0]*c['Ux_m_s']**2+2*D[0][1]*c['Ux_m_s']*c['Uy_m_s']+D[1][1]*c['Uy_m_s']**2)*c['volume_m3'] for c in cells)
    W=dp*Q
    if G:
        pstar=lambda c:G*(lengths[axis]-c['x_m' if axis==0 else 'y_m'])
        add('pressure_relative_rms',rms(lambda c:c['p_Pa']-pstar(c))/abs(dp),t['pressure_relative_rms_and_max'])
        add('pressure_relative_max',max(abs(c['p_Pa']-pstar(c)) for c in cells)/abs(dp),t['pressure_relative_rms_and_max'])
        for prefix,unit,target in [('U','m_s',Ustar),('J','m2_s',Jstar)]:
            field=prefix+main+'_'+unit
            add(prefix+'_relative_L2',rms(lambda c:c[field]-target)/abs(target),t['main_velocity_flux_relative_L2_and_mean'])
            add(prefix+'_relative_mean',abs(mean(field)/target-1),t['main_velocity_flux_relative_L2_and_mean'])
        for a in [cross,'z']:
            add('U'+a+'_relative_max',max(abs(c['U'+a+'_m_s']) for c in cells)/abs(Ustar),t['transverse_and_z_relative_max'])
        add('Q_relative',abs(Q/Qstar-1),t['Q_relative'])
        add('Q_sign',0 if Q*Qstar>0 else 1,0)
        add('K_from_U_relative',abs(mu*H*mean('U'+main+'_m_s')/G/K-1),t['recovered_K_relative'])
        add('K_from_Q_relative',abs(mu*Q/(lengths[1-axis]*G)/K-1),t['recovered_K_relative'])
        add('global_mass_relative',abs(sum(boundary.values()))/abs(Qstar),t['global_mass_relative'])
        add('local_mass_relative',sum(abs(x) for x in residual.values())/abs(Qstar),t['sum_absolute_cell_mass_relative'])
        add('side_leakage_relative',leakage/abs(Qstar),t['side_leakage_relative'])
        add('face_flux_consistency_relative',fluxdiff/max(fluxscale,1e-300),t['face_flux_consistency_relative'])
        add('exported_U_face_interpolation_relative',interpdiff/max(fluxscale,1e-300),t['face_flux_consistency_relative'])
        add('energy_relative',abs(E-W)/max(abs(W),1e-300),t['power_dissipation_relative'])
        add('positive_energy_and_power',0 if E>=0 and W>0 else 1,0)
    else:
        add('zero_pressure',max(abs(c['p_Pa']) for c in cells),t['zero_pressure_max_Pa'])
        add('zero_velocity',max(math.sqrt(sum(c['U'+a+'_m_s']**2 for a in 'xyz')) for c in cells),t['zero_velocity_max_m_s'])
        add('zero_each_boundary_flow',max(abs(q) for q in boundary.values()),t['zero_each_boundary_Q_and_net_m3_s'])
        add('zero_net_flow',abs(sum(boundary.values())),t['zero_each_boundary_Q_and_net_m3_s'])
    return dict(checks=checks,interface_checks_satisfied=all(c['satisfied'] for c in checks),boundary_Q_m3_s=boundary,
                mean_U_main_m_s=mean('U'+main+'_m_s'),mean_J_main_m2_s=mean('J'+main+'_m2_s'),
                dissipation_W=E,pressure_power_W=W,analytic_expected_Q_m3_s=Qstar),grid


def check_run(run):
    manifest=json.loads((run/'run_manifest.json').read_text())
    case_id=manifest.get('case_id')
    if case_id not in SUPPORTED_CASES or manifest.get('protocol_id')!='SDI-v1':raise ValueError('Not a supported bound C01/C02 run')
    for rec in manifest['files']:
        p=Path(rec['path'])
        if p.is_absolute() or '..' in p.parts:raise ValueError('Invalid manifest path')
        if sha(run/p)!=rec['sha256']:raise ValueError('Bound input changed: '+str(p))
    execution=json.loads((run/'execution.json').read_text())
    if execution.get('status')!='completed' or len(execution.get('steps',[]))!=2:raise ValueError('Both runs must finish before analysis')
    if [s['label'] for s in execution['steps']]!=['two_dimensional','openfoam'] or any(s['exit_code']!=0 for s in execution['steps']):raise ValueError('Nonzero/missing independent exit code')
    cfg=json.loads((run/'common'/f'{case_id}.json').read_text())
    if sha(run/'common/protocol.json')!=cfg['source_hashes']['design_protocol']:raise ValueError('Protocol binding mismatch')
    if cfg['case_id']!=case_id or cfg['drive_axis']!=0 or cfg['pressure_units']!='Pa' or cfg['velocity_definition']!='U=J/H':raise ValueError('Unsupported configuration')
    results={};grids={}
    for label,rel in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
        d=run/rel
        results[label],grids[label]=evaluate(cfg,read_csv(d/'cells.csv'),read_csv(d/'faces.csv'),json.loads((d/'solver.json').read_text()))
    nx,ny,_=cfg['mesh_cells'];dp=cfg['G_Pa_per_m']*cfg['L_m'][cfg['drive_axis']]
    Ustar=cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/(cfg['mu_Pa_s']*cfg['H_m'])
    cross=[]
    for field,scale in [('p_Pa',abs(dp)),('Jx_m2_s',abs(Ustar*cfg['H_m'])),('Jy_m2_s',abs(Ustar*cfg['H_m']))]:
        a,b=grids.values();value=max(abs(a[k][field]-b[k][field]) for k in a)/scale
        cross.append(dict(name=field+'_cross_relative_max',value=value,limit=cfg['thresholds']['cross_implementation_relative'],satisfied=value<=cfg['thresholds']['cross_implementation_relative']))
    qkey='xHigh';qa=results['two_dimensional']['boundary_Q_m3_s'][qkey];qb=results['openfoam']['boundary_Q_m3_s'][qkey]
    value=abs(qa-qb)/abs(results['two_dimensional']['analytic_expected_Q_m3_s'])
    cross.append(dict(name='Q_cross_relative',value=value,limit=cfg['thresholds']['cross_implementation_relative'],satisfied=value<=cfg['thresholds']['cross_implementation_relative']))
    satisfied=all(r['interface_checks_satisfied'] for r in results.values()) and all(c['satisfied'] for c in cross)
    raw=[]
    for rel in ['two_dimensional','openfoam/SDI_output']:
        for name in ['cells.csv','faces.csv','solver.json']:
            p=run/rel/name;raw.append(dict(path=str(p.relative_to(run)),sha256=sha(p)))
    for rel in ['openfoam/1/p','openfoam/1/U','openfoam/1/J','openfoam/1/phi','openfoam/1/phi_U',
                'logs/two_dimensional.log','logs/openfoam.log','execution.json']:
        p=run/rel;raw.append(dict(path=rel,sha256=sha(p)))
    return dict(checker_version=CHECKER_VERSION,protocol_id='SDI-v1',case_id=case_id,run_id=manifest['run_id'],kind='COMPLETED_RUN_INTERFACE_ANALYSIS',
                independent_exit_codes_checked=True,results=results,cross_checks=cross,interface_checks_satisfied=satisfied,
                NUMERICAL_GATE='PASS' if satisfied else 'FAIL',RESULT_PASS=satisfied,geometry_PASS=True,
                geometry_scope='synthetic_average_domain_only',physical_validation='NOT_EVALUATED',
                independent_human_acceptance=False,raw_files=raw,run_manifest_sha256=sha(run/'run_manifest.json'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',required=True,type=Path);parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError('Report exists; refusing overwrite')
    try:report=check_run(args.run_dir.resolve())
    except (ValueError,KeyError,OSError,TypeError) as exc:
        report=dict(kind='INCOMPLETE_OR_INVALID_EVIDENCE',error=str(exc),NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=None,physical_validation='NOT_EVALUATED')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report.get(k) for k in ['kind','NUMERICAL_GATE','RESULT_PASS','geometry_PASS']}))
    return 0 if report.get('RESULT_PASS') is True else 2


if __name__=='__main__':raise SystemExit(main())
