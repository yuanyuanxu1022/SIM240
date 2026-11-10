#!/usr/bin/env python3
"""Independent completed-result acceptance. No solver import or execution."""
from pathlib import Path
from window_metrics import metrics
import argparse
import csv
import hashlib
import json
import math
import itertools
import numpy as np


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def kv(path):return dict(line.split('=',1) for line in Path(path).read_text().splitlines() if '=' in line)
def rows(path):return list(csv.DictReader(Path(path).open(encoding='utf-8-sig')))
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',type=Path,required=True)
    ap.add_argument('--batch',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--first',type=int,default=None);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    project=args.case.parents[2];batch_manifest=json.loads((args.batch/'stage_manifest.json').read_text())
    protocol=args.case/'protocol/execution.json';limits=json.loads(protocol.read_text())['numerical_limits']
    references={}
    registry={
        'development_remaining14_20261024_v1':('development_remaining14_20261024',14,'remaining14_development'),
        'development_screen_20261023_v1':('development_stage_20261023',6,'development_screen'),
        'development_grid_mid6_20261024_v1':('development_grid_mid6_20261024',6,'grid_mid6_development'),
        'development_grid_narrow_fine4_20261024_v1':('development_grid_narrow_fine4_20261024',4,'grid_narrow_fine4_development')}
    stage_dir,count,stage_name=registry[batch_manifest['batch_id']]
    assert args.first is None or args.first==count,'partial batch acceptance prohibited'
    args.first=count
    release=args.case/stage_dir/'release.json'
    completion=json.loads((args.batch/'stage_completion.json').read_text()) if stage_name!='development_screen' else None
    if completion is not None:assert completion['attempted_cases']==count and completion['exit_code']==0 and not completion['next_stage_started']
    assert sha(release)==batch_manifest['release_sha256']
    binding=json.loads(release.read_text())['bound_inputs_sha256']
    for path,expected in binding.items():assert sha(Path(path) if Path(path).is_absolute() else project/Path(path))==expected,path
    protected={str(protocol):sha(protocol),str(release):sha(release),str(args.batch/'stage_manifest.json'):sha(args.batch/'stage_manifest.json')}
    results=[];field_cases=[];window_summary=[];rawfiles=[]
    selected=batch_manifest['case_ids'][:args.first]
    assert len(batch_manifest['case_ids'])==count
    stage_table={r['planned_case_id']:r for r in rows(args.case/stage_dir/'stage_cases.csv')}
    for ident in selected:
        name=ident.replace('CAND_','D4_',1)+'_'+batch_manifest['batch_id']
        out=args.batch/name/'steady'
        assert (out/'exit_code.txt').read_text().strip()=='0'
        assert (out/'run.log').stat().st_size>0
        result=kv(out/'result.txt');config=kv(out/'run_config.txt');effective=kv(out/'effective_config.txt')
        manifest=json.loads((out/'run_manifest.json').read_text());boundary=kv(out/'boundary_audit.txt')
        for flag in ['converged','material_unchanged','finite','PASS','geometry_PASS']:assert result[flag]=='true',flag
        assert result['NUMERICAL_GATE']=='PASS' and result['RESULT_PASS']=='false'
        assert manifest['run_id']==result['run_id']==config['run_id']==effective['run_id']
        assert manifest['planned_case_id']==ident and manifest['formal_simulation'] is True
        assert manifest['mode']=='steady' and result['formal_simulation']=='true'
        assert json.loads((out/'inputs_after.json').read_text())['unchanged'] is True
        for path,expected in manifest['inputs_sha256'].items():assert sha(path)==expected,path
        for path,expected in manifest['OpenLB_build_environment']['library_hashes'].items():assert sha(path)==expected
        for key in ['geometry_PASS','q_audit_PASS']:assert boundary[key]=='true'
        for key in ['geometric_fallback_count','missing_fluid_neighbour_fallback_count','unresolved_link_count']:
            assert int(boundary[key])==0
        assert int(boundary['candidate_links'])==int(boundary['valid_distance_links'])==int(boundary['installed_links'])
        assert float(boundary['q_min'])==float(boundary['q_max'])==.5
        h,d,w,P,Ly,dx,nu,a=[float(config[k]) for k in ['h_nm','d_nm','w_nm','period_nm','Ly_nm','dx_nm','nu_m2_s','acceleration_m_s2']]
        planned=stage_table[ident]
        for key,val in [('h_nm',h),('d_nm',d),('w_nm',w),('P_nm',P),('Ly_nm',Ly),('dx_nm',dx),('nu_m2_s',nu),('acceleration_m_s2',a)]:
            assert float(planned[key])==val,(ident,key)
        assert config['direction']==planned['direction'] and planned['role'] in ('new_dev','linearity','grid_reference') and planned['blind_geometry']=='False'
        assert manifest['stage_release_sha256']==sha(release) and manifest['stage']==stage_name
        h*=1e-9;d*=1e-9;w*=1e-9;P*=1e-9;Ly*=1e-9;dx*=1e-9
        dt=dx*dx/(6*nu);n=math.ceil(.75*h*h/(nu*dt)-1e-9)
        assert n==int(effective['window_steps'])==int(result['window_steps'])
        physical_cap=math.ceil(8*(h+d)**2/(nu*dt)-1e-9)
        assert physical_cap==int(effective['maximum_steps'])==int(result['maximum_steps'])
        volume=P*Ly*h+w*Ly*d;node_count=round(volume/dx**3)
        assert node_count==int(result['fluid_nodes'])==int(boundary['material_1'])
        nx,ny,nh,nd=[round(v/dx) for v in [P,Ly,h,d]]
        edge=(P-w)/(2*dx)
        xx,zz=np.meshgrid(np.arange(nx)+.5,np.arange(nh+nd)+.5,indexing='ij')
        def fluid(x,z):
            x=np.remainder(x,nx)
            return (z>=0)&(z<nh+nd*((x>=edge)&(x<nx-edge)))
        mask=fluid(xx,zz);links=0
        assert int(mask.sum())*ny==node_count
        for cx,cy,cz in itertools.product([-1,0,1],repeat=3):
            if cx*cx+cy*cy+cz*cz not in [1,2]:continue
            hit=mask&~fluid(xx+cx,zz+cz);links+=int(hit.sum())*ny
            assert np.all(fluid(xx+.25*cx,zz+.25*cz)[hit])
            assert not np.any(fluid(xx+.75*cx,zz+.75*cz)[hit])
        assert links==int(boundary['candidate_links'])
        assert float(boundary['installed_q_min'])==float(boundary['installed_q_max'])==.5
        with (out/'diagnostics.csv').open() as f: header=next(csv.reader(f))
        matrix=np.loadtxt(out/'diagnostics.csv',delimiter=',',skiprows=1,ndmin=2);data={k:matrix[:,i] for i,k in enumerate(header)}
        assert all(np.isfinite(v).all() for v in data.values())
        N=len(matrix);steps=int(result['steps_completed']);assert steps<=physical_cap and N==steps+1 and np.array_equal(data['step'],np.arange(N))
        assert np.all(data['finite']==1) and np.allclose(data['time_s'],np.arange(N)*dt,rtol=1e-14,atol=1e-24)
        mass=(data['mass']-data['mass'][0])/data['mass'][0]
        assert np.allclose(mass,data['mass_error'],rtol=1e-10,atol=1e-16)
        assert np.allclose(data['J'],data['Jy'] if config['direction']=='P' else data['Jx'],rtol=1e-14,atol=1e-30)
        cross=-data['Jx'] if config['direction']=='P' else data['Jy']
        std,span,cross_max,workspace=metrics(data['J'],cross,n)
        assert np.allclose(std,data['window_rel_std'][n-1:],rtol=1e-5,atol=1e-12)
        assert np.allclose(span,data['window_rel_span'][n-1:],rtol=1e-6,atol=1e-12)
        assert np.allclose(cross_max,data['window_cross_abs_max'][n-1:],rtol=1e-12,atol=1e-28)
        gates=(std<=limits['relative_std'])&(span<=limits['relative_span'])&(cross_max<=limits['cross_flux_m2_s'])
        assert gates[-1] and not np.any(gates[:-1]),'stopping point is not the first independently accepted window'
        worst_mass=float(np.max(np.abs(mass)));worst_rho=float(np.max(data['max_density_deviation']));worst_mach=float(np.max(data['Mach']))
        q1,q2=data['Q_section1'],data['Q_section2'];den=np.maximum(np.abs(q1),np.abs(q2))
        section=np.divide(np.abs(q1-q2),den,out=np.zeros_like(den),where=den>0)
        assert np.allclose(section,data['section_relative_difference'],rtol=1e-6,atol=1e-15)
        assert worst_mass<limits['mass_relative_strict'] and worst_rho<=limits['density_deviation'] and worst_mach<limits['Mach_strict']
        assert section[-1]<=limits['section_relative_difference']
        for value,key in [(worst_mass,'max_mass_abs_relative'),(worst_rho,'max_density_deviation'),(worst_mach,'max_Mach'),(float(std[-1]),'window_main_rel_std'),(float(span[-1]),'window_main_rel_span')]:
            assert math.isclose(value,float(result[key]),rel_tol=1e-6,abs_tol=1e-15),(key,value,result[key])
        rho=float(result['rho_phys_kg_m3']);mu=rho*nu;K=mu*data['J'][-1]/(rho*a)
        assert data['J'][-1]>0 and math.isclose(K,float(result['Keff_m3']),rel_tol=1e-14)
        assert math.isclose(rho*a/data['J'][-1],float(result['R_eff_Pa_s_per_m3']),rel_tol=1e-14)
        profile=rows(out/'field_slice.csv');x=np.array([float(r['x']) for r in profile]);z=np.array([float(r['z']) for r in profile])
        velocity=np.array([float(r['uy' if config['direction']=='P' else 'ux']) for r in profile])
        expected_slice_nodes=round(P/dx)*round(h/dx)+round(w/dx)*round(d/dx)
        assert len(profile)==expected_slice_nodes and len(set(zip(x,z)))==len(profile)
        sliceK=mu*(float(np.sum(velocity))*dx*dx/P)/(rho*a)
        assert math.isclose(sliceK,K,rel_tol=2e-8)
        errK=L2=regression=None  # screen geometry is not the foundation regression geometry
        frames=rows(out/'frame_index.csv');schedule=rows(out/'frame_schedule.csv');frame_steps=[int(r['step']) for r in frames]
        assert frame_steps==sorted(set(frame_steps)) and frame_steps[0]==0 and frame_steps[-1]==steps
        assert len(frames)==int(result['frames_written'])
        expected_frames={0,steps}
        requested=json.loads(protocol.read_text())['frame_tstar']
        assert len(schedule)==len(requested)
        for target,row in zip(requested,schedule):
            target_step=math.ceil(target*h*h/(nu*dt)-1e-9)
            assert math.isclose(float(row['requested_tstar']),target,abs_tol=1e-14)
            assert int(row['target_step'])==target_step and int(row['reached'])==int(target_step<=steps)
            if target_step<=steps:expected_frames.add(target_step)
        assert set(frame_steps)==expected_frames
        for row in frames:
            step=int(row['step']);assert math.isclose(float(row['time_s']),step*dt,rel_tol=1e-13,abs_tol=1e-24)
            assert math.isclose(float(row['tstar']),nu*step*dt/(h*h),rel_tol=1e-13,abs_tol=1e-15)
        scalar={'planned_case_id':ident,'run_id':result['run_id'],'role':planned['role'],
                'direction':config['direction'],'h_nm':h*1e9,'d_nm':d*1e9,'w_nm':w*1e9,'P_nm':P*1e9,'steps':steps,'diagnostic_rows':N,
                'K_m3':K,'smooth_K_error_percent':None if errK is None else 100*errK,
                'smooth_profile_L2_percent':None if L2 is None else 100*L2,
                'regression_K_difference_percent':None if regression is None else 100*regression,
                'max_mass_drift':worst_mass,'max_density_deviation':worst_rho,'max_Mach':worst_mach,
                'final_window_rel_std':float(std[-1]),'final_window_rel_span':float(span[-1]),
                'final_section_relative_difference':float(section[-1]),'max_section_relative_difference':float(np.max(section)),
                'final_window_cross_abs_max':float(cross_max[-1]),'boundary_links':links,
                'elapsed_seconds':json.loads((out/'resource_usage.json').read_text())['elapsed_seconds'],
                'frames':len(frames),'independent_numerical_gate':True,'geometry_PASS':True,
                'smooth_or_regression_check_pass':'NOT_APPLICABLE', 'acceleration_m_s2':a,'source_self_RESULT_PASS':result['RESULT_PASS']}
        results.append(scalar);window_summary.append({'run_id':result['run_id'],'windows_recomputed':len(std),'workspace':workspace,
            'max_std_absolute_difference':float(np.max(np.abs(std-data['window_rel_std'][n-1:]))),
            'max_span_absolute_difference':float(np.max(np.abs(span-data['window_rel_span'][n-1:]))),
            'first_pass_at_final_row':True})
        field_cases.append({'output':str(out),'row':scalar,'frames':frames,'config':config,'effective':effective})
        for f in out.iterdir():
            if f.is_file():protected[str(f)]=sha(f);rawfiles.append(str(f))
    complete=args.first==count
    if complete:
        progress=json.loads((args.batch/'stage_progress.json').read_text())
        assert len(progress)==count and {r['case_id'] for r in progress}==set(selected)
        assert all(r['exit_code']==0 for r in progress) and (args.batch/'exit_code.txt').read_text().strip()=='0'
        for name in ['stage_progress.json','exit_code.txt']:protected[str(args.batch/name)]=sha(args.batch/name)
    summary={'completed_cases_checked':len(results),'whole_batch_complete':complete,'diagnostic_rows':sum(r['diagnostic_rows'] for r in results),
             'all_scalar_and_geometry_checks_passed':True,'all_flow_frames_independently_read':False,
             'next_stage_eligible':'pending VTK full-frame checks and complete batch' if not complete else 'pending VTK full-frame checks',
             'solver_executed_by_analysis':False,'protocol_changed':False,'source_solver_results_modified':False,
             'frozen_protocol_id':json.loads(protocol.read_text())['protocol_id']}
    write(args.out/'scalar_results.json',results);write(args.out/'rolling_window_checks.json',window_summary)
    write(args.out/'field_cases.json',field_cases);write(args.out/'input_hashes.json',protected);write(args.out/'scalar_summary.json',summary)
    with (args.out/'scalar_results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(results[0]),lineterminator='\n');wr.writeheader();wr.writerows(results)
    assert all(sha(path)==h for path,h in protected.items())
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
