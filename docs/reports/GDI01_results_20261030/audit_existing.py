#!/usr/bin/env python3
"""Read existing artifacts only. Supplement, never replace, the frozen checker."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PKG = ROOT / 'CASE/groove_darcy_static_v1'
RUN = PKG / 'runs/GDI01_v1_20261030_01'
OLD = ROOT / 'CASE/interface_static_darcy_v1/runs/SDI_C01_v1_20261030_01'

def load(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(name, obj):
    p = OUT / name
    if p.exists():
        raise FileExistsError(p)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

def rows(p):
    with p.open() as f:
        return [{k: (v if k == 'patch' else float(v)) for k, v in r.items()}
                for r in csv.DictReader(f)]

def main():
    cfg = load(RUN/'common/GDI01.json')
    oldcfg = load(OLD/'common/C01.json')
    protocol = load(RUN/'common/protocol.json')
    manifest = load(RUN/'run_manifest.json')
    release = load(PKG/'common/release_manifest.json')
    launch = load(ROOT/'docs/reports/GDI01_launch_binding_20261030/launch_binding.json')
    bindings = []
    def bind(label, path, expected):
        actual = sha(path)
        bindings.append(dict(label=label, path=str(path.relative_to(ROOT))
                            if path.is_relative_to(ROOT) else str(path),
                            expected_sha256=expected, actual_sha256=actual,
                            satisfied=actual == expected))
    for r in manifest['files']:
        bind('run_input', RUN/r['path'], r['sha256'])
    for r in release['files']:
        bind('release_file', PKG/r['path'], r['sha256'])
    for r in release['libraries']:
        bind('runtime_library', Path(r['path']), r['sha256'])
    bind('delivered_release', RUN/'common/release_manifest.json', launch['release_manifest_sha256'])
    bind('original_GDI_protocol', ROOT/'docs/reports/GrooveDarcy_static_protocol_20261030/protocol.json', cfg['GDI_protocol_sha256'])
    for key, path in cfg['source_paths'].items():
        bind('original_'+key, Path(path), cfg['source_hashes'][key])
    for r in load(PKG/'common/subclass_binding.json'):
        bind('subclass_original', Path(r['source']), r['sha256'])
        bind('subclass_copy', PKG/r['copied_path'], r['sha256'])
    for folder in ['two_dimensional', 'openfoam/SDI_output']:
        for name in ['cells.csv','faces.csv','solver.json']:
            bind('C01_original_vs_copy', OLD/folder/name, sha(RUN/'references/C01'/folder/name))
    bind('C01_accepted_report', ROOT/'docs/reports/SDI_C01_results_20261030/interface_analysis_geometry_v1_1.json', sha(RUN/'references/C01/accepted_analysis.json'))
    samekeys = ['pressure_units','velocity_definition','H_m','L_m','mu_Pa_s','rho_kg_m3',
                'mesh_cells','drive_axis','G_Pa_per_m','K_m3','D_m_minus2','thresholds','linear_solver']
    conditions = {k: cfg[k] == oldcfg[k] for k in samekeys}
    mesh = {}
    for name in ['boundary','faces','neighbour','owner','points']:
        a = RUN/'openfoam/constant/polyMesh'/name
        b = OLD/'openfoam/constant/polyMesh'/name
        mesh[name] = dict(new_sha256=sha(a), old_sha256=sha(b), equal=sha(a)==sha(b))
    p_initial_equal = sha(RUN/'openfoam/0/p') == sha(OLD/'openfoam/0/p')
    frozen = dict(thresholds_equal=cfg['thresholds']==protocol['inherited_SDI_thresholds'],
                  linear_solver_equal=cfg['linear_solver']==protocol['inherited_linear_solver'])
    ok = all(r['satisfied'] for r in bindings) and all(conditions.values()) and all(
        r['equal'] for r in mesh.values()) and p_initial_equal and all(frozen.values())
    save('binding_audit.json', dict(satisfied=ok, binding_count=len(bindings),
         run_inputs=len(manifest['files']), release_files=len(release['files']),
         runtime_libraries=len(release['libraries']), checks=bindings,
         shared_conditions=conditions, mesh=mesh, initial_pressure_file_equal=p_initial_equal,
         frozen_criteria=frozen, environment=manifest['environment'],
         note='Release protocol preparation flags are historical, not current run status.'))
    assert ok, 'Binding or comparable-condition audit failed'

    H=cfg['H_m']; mu=cfg['mu_Pa_s']; G=cfg['G_Pa_per_m']
    lx,ly,_=cfg['L_m']; dp=G*lx; K=cfg['K_m3'][0][0]; Ustar=K*G/mu/H; Qstar=K*G/mu*ly
    def summarize(folder):
        c=rows(folder/'cells.csv'); f=rows(folder/'faces.csv'); n=len(c)
        V=math.fsum(r['volume_m3'] for r in c)
        U=math.fsum(r['Ux_m_s']*r['volume_m3'] for r in c)/V
        J=math.fsum(r['Jx_m2_s']*r['volume_m3'] for r in c)/V
        B={p:math.fsum(r['phi_m3_s'] for r in f if r['patch']==p)
           for p in ['xLow','xHigh','yLow','yHigh']}
        imbalance={int(r['cell_id']):[] for r in c}
        for r in f:
            imbalance[int(r['owner'])].append(r['phi_m3_s'])
            if r['neighbour']>=0:
                imbalance[int(r['neighbour'])].append(-r['phi_m3_s'])
        E=math.fsum(mu*r['volume_m3']*math.fsum(
            r['U'+a+'_m_s']*cfg['D_m_minus2'][i][j]*r['U'+b+'_m_s']
            for i,a in enumerate('xy') for j,b in enumerate('xy')) for r in c)
        return dict(cells=n,faces=len(f),volume_m3=V,mean_Ux_m_s=U,mean_Jx_m2_s=J,
            boundary_Q_m3_s=B,K_from_U_m3=mu*H*U/G,K_from_Q_m3=mu*B['xHigh']/G/ly,
            R_Q_Pa_s_m_minus3=dp/B['xHigh'],dissipation_W=E,pressure_power_W=dp*B['xHigh'],
            global_mass_relative=abs(math.fsum(B.values()))/Qstar,
            local_mass_relative=math.fsum(abs(math.fsum(v)) for v in imbalance.values())/Qstar,
            side_leakage_relative=math.fsum(abs(r['phi_m3_s']) for r in f if r['patch'] in ['yLow','yHigh'])/Qstar,
            max_Uy_m_s=max(abs(r['Uy_m_s']) for r in c),max_Uz_m_s=max(abs(r['Uz_m_s']) for r in c),
            p_cell_min_Pa=min(r['p_Pa'] for r in c),p_cell_max_Pa=max(r['p_Pa'] for r in c),
            max_pressure_error_Pa=max(abs(r['p_Pa']-G*(lx-r['x_m'])) for r in c),
            max_J_equals_HU_error_m2_s=max(abs(r['J'+a+'_m2_s']-H*r['U'+a+'_m_s']) for r in c for a in 'xyz'))
    datasets={'GDI01':RUN/'openfoam/GDI_output', 'C01_2D':OLD/'two_dimensional', 'C01_old_OpenFOAM':OLD/'openfoam/SDI_output'}
    metrics={k:summarize(v) for k,v in datasets.items()}
    hist=rows(RUN/'openfoam/GDI_output/iteration_history.csv')
    ev=rows(RUN/'openfoam/GDI_output/momentum_residual.csv')
    cells=rows(RUN/'openfoam/GDI_output/cells.csv')
    Eforce=math.fsum(math.fsum(r['force_'+a+'_N']*c['U'+a+'_m_s'] for a in 'xyz') for r,c in zip(ev,cells))
    iteration=dict(outer_count=len(hist),total_pressure_iterations=int(math.fsum(r['linear_iterations'] for r in hist)),
        min_pressure_iterations=int(min(r['linear_iterations'] for r in hist)),
        max_pressure_iterations=int(max(r['linear_iterations'] for r in hist)),first=hist[0],last=hist[-1],
        max_normalized_residual=max(r['normalized_residual'] for r in hist),
        max_true_normalized_residual=max(r['true_normalized_residual'] for r in hist),
        last_true_residual_recomputed=math.fsum(abs(r['pressure_matrix_raw_residual_m3_s']) for r in ev)/hist[-1]['initial_raw_L1_m3_s'])
    save('independent_raw_audit.json', dict(kind='supplementary_direct_arithmetic_not_new_acceptance_criteria',
        analytic=dict(Ux_m_s=Ustar,Jx_m2_s=K*G/mu,Q_m3_s=Qstar,R_Q_Pa_s_m_minus3=dp/Qstar),
        datasets=metrics,iteration=iteration,force_dissipation_W=Eforce,
        note='Uses math.fsum and actual cell volumes. Last digits can differ from inherited arithmetic; frozen checker remains controlling. No solver or checker module is imported.'))
    cross={}
    new={int(r['cell_id']):r for r in cells}
    for label,folder in list(datasets.items())[1:]:
        old={int(r['cell_id']):r for r in rows(folder/'cells.csv')}
        cross[label]=dict(
            max_p_difference_Pa=max(abs(new[i]['p_Pa']-old[i]['p_Pa']) for i in new),
            max_Jx_difference_relative=max(abs(new[i]['Jx_m2_s']-old[i]['Jx_m2_s']) for i in new)/(K*G/mu),
            max_Jy_difference_relative=max(abs(new[i]['Jy_m2_s']-old[i]['Jy_m2_s']) for i in new)/(K*G/mu),
            Q_difference_relative_analytic=abs(metrics['GDI01']['boundary_Q_m3_s']['xHigh']-metrics[label]['boundary_Q_m3_s']['xHigh'])/Qstar,
            Q_difference_signed_percent=(metrics['GDI01']['boundary_Q_m3_s']['xHigh']/metrics[label]['boundary_Q_m3_s']['xHigh']-1)*100)
    save('comparison.json',dict(shared_conditions=conditions,comparisons=cross,
         baseline_run_id='SDI_C01_v1_20261030_01',new_run_id=manifest['run_id'],
         conclusion='Implementation agreement for the same model; not independent physical validation.'))
    print(json.dumps(dict(binding_pass=ok,binding_count=len(bindings),datasets=metrics,
                         iteration_count=len(hist),total_pressure_iterations=iteration['total_pressure_iterations'],comparisons=cross),indent=2))

if __name__ == '__main__':
    main()
