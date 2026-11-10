#!/usr/bin/env python3
"""Read completed C01/C03 raw outputs. Descriptive comparison, no new gate/solve."""
import csv
import hashlib
import json
import math
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
RUNS={
    'C01':ROOT/'CASE/interface_static_darcy_v1/runs/SDI_C01_v1_20261030_01',
    'C03':ROOT/'CASE/interface_static_darcy_v1_2/runs/SDI_C03_v1_2_20261030_01',
}


def rows(path):
    with path.open() as f:
        result=[{k:v if k=='patch' else float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    assert all(math.isfinite(v) for row in result for k,v in row.items() if k!='patch')
    return result


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    target=OUT/'C01_C03_comparison.json'
    if target.exists():raise FileExistsError('Refusing comparison overwrite')
    cfg={case:json.loads((run/'common'/f'{case}.json').read_text()) for case,run in RUNS.items()}
    for case,run in RUNS.items():
        manifest=json.loads((run/'run_manifest.json').read_text())
        assert manifest['case_id']==case and manifest['protocol_id']=='SDI-v1'
        assert all(sha(run/r['path'])==r['sha256'] for r in manifest['files'])
        execution=json.loads((run/'execution.json').read_text())
        assert execution['status']=='completed' and len(execution['steps'])==2
        assert [s['label'] for s in execution['steps']]==['two_dimensional','openfoam']
        assert all(s['exit_code']==0 and not s['timed_out'] for s in execution['steps'])
    same=['H_m','L_m','mu_Pa_s','rho_kg_m3','mesh_cells','drive_axis','G_Pa_per_m',
          'pressure_units','velocity_definition','thresholds','linear_solver','source_hashes','source_paths']
    assert all(cfg['C01'][k]==cfg['C03'][k] for k in same)
    allowed={'case_id','schema','K_m3','D_m_minus2'}
    different=[k for k in cfg['C01'].keys() & cfg['C03'].keys() if cfg['C01'][k]!=cfg['C03'][k]]
    assert set(different)==allowed
    protocol=json.loads((RUNS['C03']/'common/protocol.json').read_text())
    source=Path(cfg['C03']['source_paths']['coefficient_source'])
    assert sha(source)==cfg['C03']['source_hashes']['coefficient_source']
    coefficients=json.loads(source.read_text())
    families={}
    for case in RUNS:
        planned=next(c for c in protocol['planned_cases'] if c['case_id']==case)
        assert planned['orientation_id']=='groove_along_long_y' and planned['drive_axis']==0
        row=next(r for r in coefficients['rows'] if r['input_id']==planned['input_id'] and r['orientation_id']==planned['orientation_id'])
        assert cfg[case]['K_m3']==row['K_global_m3']
        assert cfg[case]['D_m_minus2']==row['D_global_m_minus2_conditional_total_drag']
        assert cfg[case]['thresholds']==protocol['thresholds'] and cfg[case]['linear_solver']==protocol['linear_solver']
        families[case]=planned['input_id']
    assert families=={'C01':'V2_published_rounded','C03':'original_local_cubic'}
    identical=['0/p','system/blockMeshDict','system/controlDict','system/fvSchemes','system/fvSolution']
    identical += ['constant/polyMesh/'+n for n in ['boundary','faces','neighbour','owner','points']]
    for rel in identical:assert (RUNS['C01']/'openfoam'/rel).read_bytes()==(RUNS['C03']/'openfoam'/rel).read_bytes()
    shared=['bin/darcy2d','bin/depthAveragedDarcyFoam',
            'provenance/two_dimensional/darcy2d.cpp','provenance/openfoam/application/depthAveragedDarcyFoam.C',
            'provenance/openfoam/application/Make/files','provenance/openfoam/application/Make/options']
    for rel in shared:assert sha(RUNS['C01']/rel)==sha(RUNS['C03']/rel)
    expected=cfg['C03']['K_m3'][0][0]/cfg['C01']['K_m3'][0][0]
    result={};sources=[]
    for label,folder in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
        data={};fields={}
        for case,run in RUNS.items():
            c=rows(run/folder/'cells.csv');f=rows(run/folder/'faces.csv');config=cfg[case]
            volume=math.fsum(x['volume_m3'] for x in c)
            mean=lambda name:math.fsum(x[name]*x['volume_m3'] for x in c)/volume
            Q=math.fsum(x['phi_m3_s'] for x in f if x['patch']=='xHigh')
            dp=config['G_Pa_per_m']*config['L_m'][0]
            data[case]=dict(Q_m3_s=Q,Umean_m_s=mean('Ux_m_s'),Jmean_m2_s=mean('Jx_m2_s'),
                recovered_K_from_U_m3=config['mu_Pa_s']*config['H_m']*mean('Ux_m_s')/config['G_Pa_per_m'],
                recovered_K_from_Q_m3=config['mu_Pa_s']*Q/(config['G_Pa_per_m']*config['L_m'][1]),
                static_hydraulic_resistance_Pa_s_per_m3=dp/Q)
            dx=config['L_m'][0]/config['mesh_cells'][0];dy=config['L_m'][1]/config['mesh_cells'][1]
            fields[case]={(round(x['x_m']/dx-.5),round(x['y_m']/dy-.5)):x for x in c}
            assert len(fields[case])==512
            for name in ['cells.csv','faces.csv']:
                p=run/folder/name;sources.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p)))
        assert fields['C01'].keys()==fields['C03'].keys()
        ratio=data['C03']['Q_m3_s']/data['C01']['Q_m3_s']
        maxp=max(abs(fields['C03'][k]['p_Pa']-fields['C01'][k]['p_Pa']) for k in fields['C01'])
        result[label]=dict(cases=data,Q_ratio_C03_over_C01=ratio,analytic_Q_ratio_C03_over_C01=expected,
            ratio_relative_deviation=abs(ratio/expected-1),
            U_ratio_C03_over_C01=data['C03']['Umean_m_s']/data['C01']['Umean_m_s'],
            pressure_field_max_absolute_difference_Pa=maxp,pressure_field_max_difference_over_24Pa=maxp/24.,
            static_resistance_ratio_C03_over_C01=data['C03']['static_hydraulic_resistance_Pa_s_per_m3']/data['C01']['static_hydraulic_resistance_Pa_s_per_m3'],
            V2_flow_change_relative_to_original_percent=100*(data['C01']['Q_m3_s']/data['C03']['Q_m3_s']-1),
            V2_static_resistance_change_relative_to_original_percent=100*(ratio-1))
    report=dict(kind='DESCRIPTIVE_C01_C03_SAME_DIRECTION_COEFFICIENT_COMPARISON',
        run_ids={case:run.name for case,run in RUNS.items()},common_parameters_equal=same,
        identical_boundary_mesh_numerics_files=identical,identical_solver_source_make_binary_files=shared,
        coefficient_families=families,orientation='groove_along_y_drive_along_x_cross_groove',
        changed_physical_inputs=['K_m3','D_m_minus2'],comparison=result,
        ratio_role='descriptive comparison; no added acceptance criterion',
        resistance_definition='R_Q=delta_p/Q, Pa s / m^3, fixed-pressure static hydraulic resistance',
        squeeze_resistance_F_over_V=None,physical_validation='NOT_EVALUATED',
        independent_physical_reference=False,solver_rerun=False,sources=sources)
    target.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
