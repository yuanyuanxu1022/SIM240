#!/usr/bin/env python3
"""Read-only descriptive C01/C02 comparison; no new acceptance gate or solver."""
import csv
import hashlib
import json
import math
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
RUNS={
    'C01':ROOT/'CASE/interface_static_darcy_v1/runs/SDI_C01_v1_20261030_01',
    'C02':ROOT/'CASE/interface_static_darcy_v1_1/runs/SDI_C02_v1_1_20261030_01',
}


def rows(p):
    with p.open() as f:
        return [{k:v if k=='patch' else float(v) for k,v in r.items()} for r in csv.DictReader(f)]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cfg={k:json.loads((r/'common'/f'{k}.json').read_text()) for k,r in RUNS.items()}
    for r in RUNS.values():
        manifest=json.loads((r/'run_manifest.json').read_text())
        assert all(sha(r/f['path'])==f['sha256'] for f in manifest['files'])
        e=json.loads((r/'execution.json').read_text())
        assert e['status']=='completed' and len(e['steps'])==2 and all(s['exit_code']==0 for s in e['steps'])
    same=['H_m','L_m','mu_Pa_s','rho_kg_m3','mesh_cells','drive_axis','G_Pa_per_m','thresholds','linear_solver']
    assert all(cfg['C01'][k]==cfg['C02'][k] for k in same)
    for key in ['K_m3','D_m_minus2']:
        assert cfg['C02'][key][0][0]==cfg['C01'][key][1][1] and cfg['C02'][key][1][1]==cfg['C01'][key][0][0]
    for rel in ['0/p','system/blockMeshDict','system/fvSchemes','system/fvSolution']:
        assert (RUNS['C01']/'openfoam'/rel).read_bytes()==(RUNS['C02']/'openfoam'/rel).read_bytes()
    expected=cfg['C02']['K_m3'][0][0]/cfg['C01']['K_m3'][0][0]
    result={};sources=[]
    for label,folder in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
        data={};fields={}
        for case,run in RUNS.items():
            c=rows(run/folder/'cells.csv');f=rows(run/folder/'faces.csv');config=cfg[case]
            V=math.fsum(x['volume_m3'] for x in c)
            mean=math.fsum(x['Ux_m_s']*x['volume_m3'] for x in c)/V
            Q=math.fsum(x['phi_m3_s'] for x in f if x['patch']=='xHigh')
            data[case]=dict(Q_m3_s=Q,Umean_m_s=mean,recovered_K_from_U_m3=config['mu_Pa_s']*config['H_m']*mean/config['G_Pa_per_m'],
                            recovered_K_from_Q_m3=config['mu_Pa_s']*Q/(config['G_Pa_per_m']*config['L_m'][1]))
            dx=config['L_m'][0]/config['mesh_cells'][0];dy=config['L_m'][1]/config['mesh_cells'][1]
            fields[case]={(round(x['x_m']/dx-.5),round(x['y_m']/dy-.5)):x for x in c}
            for name in ['cells.csv','faces.csv']:
                p=run/folder/name;sources.append(dict(path=str(p),sha256=sha(p)))
        actual=data['C02']['Q_m3_s']/data['C01']['Q_m3_s']
        pressure_max=max(abs(fields['C02'][k]['p_Pa']-fields['C01'][k]['p_Pa']) for k in fields['C01'])
        result[label]=dict(cases=data,Q_ratio_C02_over_C01=actual,analytic_Q_ratio=expected,
                           ratio_relative_deviation=abs(actual/expected-1),
                           U_ratio_C02_over_C01=data['C02']['Umean_m_s']/data['C01']['Umean_m_s'],
                           pressure_field_max_absolute_difference_Pa=pressure_max,
                           pressure_field_max_difference_over_24Pa=pressure_max/24.)
    report=dict(kind='DESCRIPTIVE_C01_C02_AXIS_SWAP_COMPARISON',cases={k:json.loads((r/'run_manifest.json').read_text())['run_id'] for k,r in RUNS.items()},
                common_parameters_equal=same,pressure_mesh_schemes_equal=True,tensors_swapped=True,
                comparison=result,ratio_role='descriptive identity, not a newly added numerical gate',
                applies_to='constant-coefficient static pressure-driven average flow only',
                squeeze_resistance_ratio=None,physical_validation='NOT_EVALUATED',solver_rerun=False,sources=sources)
    (OUT/'C01_C02_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
