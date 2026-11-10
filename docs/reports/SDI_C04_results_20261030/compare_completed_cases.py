"""Read-only C04/C02 same-direction and C04/C03 axis comparisons. No new gate."""
import csv
import hashlib
import json
import math
from pathlib import Path

OUT=Path(__file__).resolve().parent
PROJECT=OUT.parents[2]
RUNS={
    'C02':PROJECT/'CASE/interface_static_darcy_v1_1/runs/SDI_C02_v1_1_20261030_01',
    'C03':PROJECT/'CASE/interface_static_darcy_v1_2/runs/SDI_C03_v1_2_20261030_01',
    'C04':PROJECT/'CASE/interface_static_darcy_v1_3/runs/SDI_C04_v1_3_20261030_01',
}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(p):
    with p.open() as stream:
        data=[{k:v if k=='patch' else float(v) for k,v in r.items()} for r in csv.DictReader(stream)]
    assert all(math.isfinite(v) for r in data for k,v in r.items() if k!='patch')
    return data


def main():
    target=OUT/'C04_C02_C03_comparison.json'
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
    for key in same:assert cfg['C02'][key]==cfg['C03'][key]==cfg['C04'][key],key
    proto=json.loads((RUNS['C04']/'common/protocol.json').read_text())
    source=Path(cfg['C04']['source_paths']['coefficient_source'])
    assert sha(source)==cfg['C04']['source_hashes']['coefficient_source']
    coeff=json.loads(source.read_text());identities={}
    for case in RUNS:
        planned=next(c for c in proto['planned_cases'] if c['case_id']==case)
        row=next(r for r in coeff['rows'] if r['input_id']==planned['input_id'] and r['orientation_id']==planned['orientation_id'])
        assert cfg[case]['K_m3']==row['K_global_m3'] and cfg[case]['D_m_minus2']==row['D_global_m_minus2_conditional_total_drag']
        assert cfg[case]['thresholds']==proto['thresholds'] and cfg[case]['linear_solver']==proto['linear_solver']
        identities[case]=dict(input_id=planned['input_id'],orientation_id=planned['orientation_id'])
    assert identities['C04']['input_id']==identities['C03']['input_id']=='original_local_cubic'
    assert identities['C02']['input_id']=='V2_published_rounded'
    assert identities['C04']['orientation_id']==identities['C02']['orientation_id']=='groove_along_short_x'
    assert identities['C03']['orientation_id']=='groove_along_long_y'
    for key in ['K_m3','D_m_minus2']:
        assert cfg['C04'][key][0][0]==cfg['C03'][key][1][1] and cfg['C04'][key][1][1]==cfg['C03'][key][0][0]
        assert cfg['C04'][key][0][1]==cfg['C04'][key][1][0]==0
    identical=['0/p','system/blockMeshDict','system/controlDict','system/fvSchemes','system/fvSolution']
    identical+=['constant/polyMesh/'+n for n in ['boundary','faces','neighbour','owner','points']]
    shared=['bin/darcy2d','bin/depthAveragedDarcyFoam','provenance/two_dimensional/darcy2d.cpp',
            'provenance/openfoam/application/depthAveragedDarcyFoam.C',
            'provenance/openfoam/application/Make/files','provenance/openfoam/application/Make/options']
    for other in ['C02','C03']:
        for rel in identical:assert (RUNS['C04']/'openfoam'/rel).read_bytes()==(RUNS[other]/'openfoam'/rel).read_bytes(),rel
        for rel in shared:assert sha(RUNS['C04']/rel)==sha(RUNS[other]/rel),rel
    comparison={};sources=[]
    for label,folder in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
        actual={};fields={}
        for case,run in RUNS.items():
            cells=rows(run/folder/'cells.csv');faces=rows(run/folder/'faces.csv');config=cfg[case]
            volume=math.fsum(c['volume_m3'] for c in cells)
            mean=lambda name:math.fsum(c[name]*c['volume_m3'] for c in cells)/volume
            Q=math.fsum(f['phi_m3_s'] for f in faces if f['patch']=='xHigh')
            dp=config['G_Pa_per_m']*config['L_m'][0]
            actual[case]=dict(Umean_m_s=mean('Ux_m_s'),Jmean_m2_s=mean('Jx_m2_s'),Q_m3_s=Q,
                recovered_K_from_U_m3=config['mu_Pa_s']*config['H_m']*mean('Ux_m_s')/config['G_Pa_per_m'],
                recovered_K_from_Q_m3=config['mu_Pa_s']*Q/(config['G_Pa_per_m']*config['L_m'][1]),
                static_hydraulic_resistance_Pa_s_per_m3=dp/Q)
            dx=config['L_m'][0]/config['mesh_cells'][0];dy=config['L_m'][1]/config['mesh_cells'][1]
            fields[case]={(round(c['x_m']/dx-.5),round(c['y_m']/dy-.5)):c for c in cells}
            assert len(fields[case])==512
            for name in ['cells.csv','faces.csv']:
                p=run/folder/name;sources.append(dict(path=str(p.relative_to(PROJECT)),sha256=sha(p)))
        pairs={}
        for other in ['C02','C03']:
            assert fields['C04'].keys()==fields[other].keys()
            ratio=actual['C04']['Q_m3_s']/actual[other]['Q_m3_s']
            expected=cfg['C04']['K_m3'][0][0]/cfg[other]['K_m3'][0][0]
            maxp=max(abs(fields['C04'][k]['p_Pa']-fields[other][k]['p_Pa']) for k in fields['C04'])
            pairs['C04_over_'+other]=dict(Q_ratio=ratio,analytic_Q_ratio=expected,
                ratio_relative_deviation=abs(ratio/expected-1),
                U_ratio=actual['C04']['Umean_m_s']/actual[other]['Umean_m_s'],
                static_R_ratio=actual['C04']['static_hydraulic_resistance_Pa_s_per_m3']/actual[other]['static_hydraulic_resistance_Pa_s_per_m3'],
                pressure_max_difference_Pa=maxp,pressure_max_difference_over_24Pa=maxp/24)
        comparison[label]=dict(cases=actual,pairs=pairs,
            V2_along_flow_change_relative_to_original_along_percent=100*(actual['C02']['Q_m3_s']/actual['C04']['Q_m3_s']-1),
            V2_along_static_R_change_relative_to_original_along_percent=100*(pairs['C04_over_C02']['Q_ratio']-1))
    report=dict(kind='DESCRIPTIVE_C04_SAME_DIRECTION_FORMULA_AND_SAME_FORMULA_DIRECTION_COMPARISONS',
        run_ids={case:run.name for case,run in RUNS.items()},case_identities=identities,
        shared_parameters_equal=same,identical_boundary_mesh_numerics_files=identical,
        identical_solver_source_make_binary_files=shared,
        C04_C02_comparison='same groove/drive axes, only original versus V2 K/D coefficient family',
        C04_C03_comparison='same original coefficient family, K/D principal values swapped together',
        comparison=comparison,ratio_role='descriptive check, no added numerical acceptance threshold',
        static_R_definition='delta_p/Q, Pa s / m^3',squeeze_resistance_F_over_V=None,
        physical_validation='NOT_EVALUATED',independent_physical_reference=False,solver_rerun=False,sources=sources)
    target.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(comparison,indent=2))


if __name__=='__main__':main()
