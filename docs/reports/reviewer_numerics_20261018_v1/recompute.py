#!/usr/bin/env python3
"""Independent read-only numerical audit. Never imports project audit/fit scripts.

Run /usr/bin/python3 recompute.py [--vtk]. Inputs are original result, diagnostics,
field slices, boundary audits, manifests and VTI files. Outputs stay beside script.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = {}


def track(path):
    path = Path(path)
    SOURCES[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return path


def kv(path):
    data = {}
    for line in track(path).read_text().splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            data[key] = value
    return data


def rows(path):
    with track(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def relative(a, b):
    return abs(a-b)/abs(b) if b else abs(a-b)


def vtk_integrate(steady, r):
    import vtk
    import numpy as np
    from vtk.util.numpy_support import vtk_to_numpy
    n = int(r['steps_completed'])
    candidates = list((steady/'vtkData'/'data').glob('*iT%07diC*.vti' % n))
    assert len(candidates) == 1, (steady, candidates)
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(str(track(candidates[0])))
    reader.Update()
    data = reader.GetOutput()
    dims = data.GetDimensions()
    origin = data.GetOrigin()
    spacing = data.GetSpacing()
    extent = data.GetExtent()
    mesh = np.meshgrid(*[origin[k] + spacing[k]*np.arange(extent[2*k], extent[2*k+1]+1) for k in range(3)], indexing='ij')
    xyz = [x.ravel(order='F') for x in mesh]
    material = vtk_to_numpy(data.GetPointData().GetArray('material')).ravel()
    velocity = vtk_to_numpy(data.GetPointData().GetArray('velocity_m_s'))
    dx = float(r['dx_m'])
    lx = float(r['Lx_m']); ly = float(r['Ly_m'])
    # Half-cell lattice excludes all halo and duplicate periodic-image points.
    core = (xyz[0] > 0) & (xyz[0] < lx) & (xyz[1] > 0) & (xyz[1] < ly)
    selected = core & (material == 1)
    expected = (xyz[2] > 0) & (xyz[2] < float(r['mesa_gap_m']) + ((xyz[0] > 60e-9) & (xyz[0] < 180e-9))*float(r['groove_depth_m']))
    geometry_mismatch = int(np.count_nonzero(core & ((material == 1) != expected)))
    volume = np.count_nonzero(selected)*dx**3
    j = np.sum(velocity[selected], axis=0,dtype=np.float64)*dx**3/(lx*ly)
    # VTI writer uses Float32: comparison tolerance must reflect serialization.
    reference = [float(x) for x in r['J_vector_m2_s'].split(',')]
    scale = max(abs(x) for x in reference)
    delta = max(abs(j[k]-reference[k]) for k in range(3))/scale
    # Check invariance along groove without relying on field_slice extrusion.
    vel_grid = velocity.reshape((dims[2], dims[1], dims[0], 3))
    mat_grid = material.reshape((dims[2], dims[1], dims[0]))
    inds_x = np.where((origin[0]+spacing[0]*np.arange(extent[0],extent[1]+1)>0)&(origin[0]+spacing[0]*np.arange(extent[0],extent[1]+1)<lx))[0]
    inds_y = np.where((origin[1]+spacing[1]*np.arange(extent[2],extent[3]+1)>0)&(origin[1]+spacing[1]*np.arange(extent[2],extent[3]+1)<ly))[0]
    strip = vel_grid[:, inds_y][:, :, inds_x]
    mats = mat_grid[:, inds_y][:, :, inds_x]
    spread = np.ptp(strip, axis=1)
    liquid = mats[:,0,:] == 1
    max_y_variation = float(np.max(np.abs(spread[liquid])))
    fluid = mats == 1
    # Independently enumerate the 18 non-rest D3Q19 lattice links using the
    # saved material field. Periodicity applies only to x/y; z ends are solid.
    directions=[(a,b,c) for a in (-1,0,1) for b in (-1,0,1) for c in (-1,0,1) if 1<=abs(a)+abs(b)+abs(c)<=2]
    links=sum(int(np.count_nonzero(fluid & ~np.roll(fluid,shift=(c,b,a),axis=(0,1,2)))) for a,b,c in directions)
    return {'vtk_nodes':int(np.count_nonzero(selected)), 'vtk_volume_m3':float(volume), 'vtk_J':[float(x) for x in j], 'vtk_J_relative_difference':float(delta), 'vtk_geometry_mismatches':geometry_mismatch, 'vtk_y_velocity_variation_m_s':max_y_variation, 'vtk_independent_candidate_links':links,'vtk_links_match_record':links==int(r['candidate_links'])==int(r['installed_links']), 'vtk_storage_type':data.GetPointData().GetArray('velocity_m_s').GetDataTypeAsString()}


def audit_run(steady, group, use_vtk=False):
    r = kv(steady/'result.txt')
    diag = rows(steady/'diagnostics.csv')
    shell_exit = track(steady/'exit_code.txt').read_text().strip()
    boundary = kv(steady/'boundary_audit.txt')
    manifest = kv(steady/'run_manifest.txt')
    pre = kv(steady.parent/'precheck'/'result.txt')
    pre_exit = track(steady.parent/'precheck'/'exit_code.txt').read_text().strip()
    dx = float(r['dx_m']); dt = float(r['dt_s']); tau = float(r['tau'])
    h = float(r['mesa_gap_m']); d = float(r['groove_depth_m'])
    rho = float(r.get('rho_phys_kg_m3',1000))
    nu = (tau-.5)*dx**2/(3*dt)
    mu = rho*nu
    j = float(diag[-1]['J'])
    k = mu*j/(rho*float(r['acceleration_m_s2']))
    window = [float(x['J']) for x in diag[-1000:]]
    mean = statistics.fmean(window)
    std = statistics.stdev(window)/abs(mean)
    span = (max(window)-min(window))/abs(mean)
    series = {key:[float(x[key]) for x in diag] for key in ('mass','Mach','max_density_deviation','rho','mass_error')}
    initial_mass = series['mass'][0]
    mass_errors = [(x-initial_mass)/initial_mass for x in series['mass']]
    mass_max = max(abs(x) for x in mass_errors)
    mach_max = max(series['Mach'])
    density_max = max(series['max_density_deviation'])
    last = diag[-1]
    qs = [float(last['Q_section1']),float(last['Q_section2'])]
    sec = abs(qs[0]-qs[1])/max(abs(x) for x in qs)
    field = rows(steady/'field_slice.csv')
    # High-precision saved slice supports a final-state density cross-check;
    # VTI density serialization is Float32 and too coarse for 1e-8 changes.
    final_density_dev=max(abs(float(x['rho'])-1) for x in field)
    final_mean_density=statistics.fmean(float(x['rho']) for x in field)
    forces = [float(x) for x in r['force_lattice'].split(',')]
    mag = math.hypot(forces[0],forces[1])
    fx,fy = forces[0]/mag,forces[1]/mag
    j_field = math.fsum((fx*float(x['ux'])+fy*float(x['uy']))*dx**2 for x in field)/float(r['Lx_m'])
    main_d = 0 if abs(fx)>abs(fy) else 1
    comp = 'ux' if main_d == 0 else 'uy'
    by_x = {}
    for row in field:
        by_x.setdefault(round(float(row['x'])/dx-.5), []).append(row)
    all_q = [math.fsum(float(x['ux'])*dx for x in cell)*float(r['Ly_m']) for cell in by_x.values()]
    spatial_span = (max(all_q)-min(all_q))/abs(statistics.fmean(all_q)) if abs(fx)>.1 else 0.0
    cross_values = [-fy*float(x['Jx'])+fx*float(x['Jy']) for x in diag[-1000:]]
    cross = max(abs(x) for x in cross_values)
    cross_rel_std = statistics.stdev(cross_values)/abs(statistics.fmean(cross_values))
    thresholds = {'std':std<=1e-6,'span':span<=5e-6,'mass':mass_max<1e-10,'rho':density_max<=1e-6,'mach':mach_max<.05,'sections':sec<=1e-5,'finite':all(x['finite'] in ('1','true') for x in diag),'precheck':pre_exit=='0' and all(pre.get(x)=='true' for x in ('geometry_PASS','converter_PASS','q_audit_PASS')),'shell_exit':shell_exit=='0'}
    # D3 permits physical in-plane cross-response and gates its relative std.
    thresholds['cross'] = cross_rel_std<=1e-6 if group=='oblique' else cross<=1e-12
    diagnostics_agreement = {
        'K':relative(k,float(r['Keff_m3'])),
        'J_field':relative(j_field,j),
        'std':relative(std,float(r['window_main_rel_std'])),
        'span':relative(span,float(r['window_main_rel_span'])),
        'mass':abs(mass_max-float(r['max_mass_abs_relative'])),
        'Mach':relative(mach_max,float(r['max_Mach'])),
        'rho':relative(density_max,float(r['max_density_deviation'])),
        'mass_column':max(abs(a-b) for a,b in zip(mass_errors,series['mass_error'])),
    }
    expected_nodes=round(float(r['Lx_m'])/dx)*round(float(r['Ly_m'])/dx)*round(h/dx)+round(float(r['groove_width_m'])/dx)*round(float(r['Ly_m'])/dx)*round(d/dx)
    node_agreement = expected_nodes==int(r['fluid_nodes'])==int(boundary['material_1'])
    result = {'run':str(steady.parent.relative_to(ROOT)), 'group':group,'direction':r['direction'],'h_nm':h*1e9,'d_nm':d*1e9,'dx_nm':dx*1e9,'mu_Pa_s_inferred_from_dt':mu,'K_recomputed_m3':k,'J_recomputed_m2_s':j,'J_field_m2_s':j_field,'mean_speed_along_drive_m_s':j/(h+.5*d),'num_gate_recomputed':all(thresholds.values()),'thresholds':thresholds,'original_PASS':r['PASS'],'steps':int(r['steps_completed']),'csv_rows':len(diag),'contiguous_steps':all(int(x['step'])==i for i,x in enumerate(diag)),'window_std':std,'window_span':span,'cross_response_m2_s':cross,'mass_max':mass_max,'Mach_max':mach_max,'density_dev_max':density_max,'mean_density_min':min(series['rho']),'mean_density_max':max(series['rho']),'section_final':sec,'all_x_section_span':spatial_span,'rho_physical_near_1000':rho,'node_agreement':node_agreement,'q_min':float(boundary['q_min']),'q_max':float(boundary['q_max']),'fallback':int(r['fallback_count']),'unresolved':int(r['unresolved_links']),'agreement':diagnostics_agreement,'binary_sha256_manifest':manifest.get('binary_sha256'),'source_sha256_manifest':manifest.get('source_sha256'),'first_step_convergence_pass':next((int(x['step']) for x in diag if float(x['window_rel_std'])>=0 and float(x['window_rel_std'])<=1e-6 and float(x['window_rel_span'])<=5e-6 and (group=='oblique' or float(x['window_cross_abs_max'])<=1e-12)),None),'raw_max_locations':{key:{'value':max(vals),'line':vals.index(max(vals))+2} for key,vals in series.items() if key in ('Mach','max_density_deviation')}}
    result['cross_response_relative_std']=cross_rel_std
    result['field_density_max_deviation']=final_density_dev
    result['field_density_max_vs_last_diagnostics']=abs(final_density_dev-float(last['max_density_deviation']))
    result['field_mean_density_vs_last_diagnostics']=abs(final_mean_density-float(last['rho']))
    # Conditional last-window scalar relaxation estimate; not a velocity-field
    # residual or a rigorous bound, and not a modified stopping rule.
    j0,j1,j2=[float(diag[-1-offset]['J']) for offset in (500,250,0)]
    denominator=(j1-j0)-(j2-j1)
    result['conditional_scalar_tail_relative']=(j2-j1)**2/denominator/abs(j2) if denominator>0 and j1>j0 and j2>j1 else None
    if use_vtk:
        result.update(vtk_integrate(steady,r))
    return result


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--vtk',action='store_true'); args=parser.parse_args()
    runs=[]
    base=ROOT/'CASE/D_series/D2_groove_error_map/results'
    for steady in sorted(base.glob('*/steady')):
        if steady.parent.name.startswith('_') or not (steady/'exit_code.txt').exists(): continue
        group='viscosity' if steady.parent.name.startswith('mu15') else ('refinement' if 'dx2.5' in steady.parent.name else 'map')
        runs.append(audit_run(steady,group,args.vtk))
    for steady in sorted((ROOT/'CASE/D_series/D3_oblique_groove_tensor_check/results').glob('a*/steady')):
        runs.append(audit_run(steady,'oblique',args.vtk))
    assert len(runs)==48,len(runs)
    maprows=[x for x in runs if x['group']=='map']; assert len(maprows)==36
    errors=[]
    for row in maprows:
        h=row['h_nm']*1e-9; d=row['d_nm']*1e-9
        model=((h**3+(h+d)**3)/24) if row['direction']=='parallel' else 1/(6*(1/h**3+1/(h+d)**3))
        factor=1/(1+1.7685*(d/120e-9)**1.6331) if row['direction']=='parallel' else 1/(1+.4900*(d/120e-9)**.6990)
        errors.append({**row,'K_model_m3':model,'model_error_percent':100*(model/row['K_recomputed_m3']-1),'V2_residual_percent':100*(model*factor/row['K_recomputed_m3']-1)})
    refinements=[]
    for row in runs:
        if row['group']!='refinement':continue
        coarse=next(x for x in maprows if abs(x['h_nm']-row['h_nm'])<1e-6 and abs(x['d_nm']-row['d_nm'])<1e-6 and x['direction']==row['direction'])
        refinements.append({'h_nm':row['h_nm'],'d_nm':row['d_nm'],'direction':row['direction'],'K5':coarse['K_recomputed_m3'],'K2p5':row['K_recomputed_m3'],'coarse_over_fine_percent':100*(coarse['K_recomputed_m3']/row['K_recomputed_m3']-1)})
    summary={'run_counts':{g:sum(x['group']==g for x in runs) for g in ('map','refinement','viscosity','oblique')},'all_48_num_gate_recomputed':all(x['num_gate_recomputed'] for x in runs),'ranges':{g:{key:[min(x[key] for x in runs if x['group']==g),max(x[key] for x in runs if x['group']==g)] for key in ('mass_max','Mach_max','density_dev_max','window_std','window_span','section_final','all_x_section_span','steps','mu_Pa_s_inferred_from_dt')} for g in ('map','refinement','viscosity','oblique')},'agreement_max':{key:max(x['agreement'][key] for x in runs) for key in runs[0]['agreement']},'refinements':refinements,'model_error_ranges':{d:[min(x['model_error_percent'] for x in errors if x['direction']==d),max(x['model_error_percent'] for x in errors if x['direction']==d)] for d in ('parallel','perpendicular')},'V2_ranges':{d:[min(x['V2_residual_percent'] for x in errors if x['direction']==d),max(x['V2_residual_percent'] for x in errors if x['direction']==d)] for d in ('parallel','perpendicular')},'V2_perp_h_ge50_abs_max':max(abs(x['V2_residual_percent']) for x in errors if x['direction']=='perpendicular' and x['h_nm']>49),'environment':{'python':sys.version,'vtk_requested':args.vtk}}
    if args.vtk:
        summary['vtk_max_J_relative_difference']=max(x['vtk_J_relative_difference'] for x in runs)
        summary['vtk_geometry_mismatches_total']=sum(x['vtk_geometry_mismatches'] for x in runs)
        summary['vtk_max_y_variation_m_s']=max(x['vtk_y_velocity_variation_m_s'] for x in runs)
        summary['vtk_independent_link_counts_all_match']=all(x['vtk_links_match_record'] for x in runs)
    summary['field_density_max_agreement_abs']=max(x['field_density_max_vs_last_diagnostics'] for x in runs)
    summary['field_density_mean_agreement_abs']=max(x['field_mean_density_vs_last_diagnostics'] for x in runs)
    summary['oblique_cross_std_range']=[min(x['cross_response_relative_std'] for x in runs if x['group']=='oblique'),max(x['cross_response_relative_std'] for x in runs if x['group']=='oblique')]
    for filename,payload in [('runs.json',runs),('map36.json',errors),('summary.json',summary),('source_hashes.json',SOURCES)]:
        (OUT/filename).write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
    csvkeys=['run','group','direction','h_nm','d_nm','dx_nm','mu_Pa_s_inferred_from_dt','K_recomputed_m3','J_recomputed_m2_s','num_gate_recomputed','mass_max','Mach_max','density_dev_max','window_std','window_span','section_final','all_x_section_span','steps']
    with (OUT/'runs48.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=csvkeys);writer.writeheader();writer.writerows({k:x[k] for k in csvkeys} for x in runs)
    print(json.dumps(summary,indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
