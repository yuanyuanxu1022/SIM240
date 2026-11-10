#!/usr/bin/env python3
"""Materialise C01 dictionaries only; never mesh, compile, or solve."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
DESIGN = PROJECT/'docs/reports/Static_Darcy_interface_protocol_20261030'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def foam_header(cls, obj):
    return f'FoamFile\n{{\n    version 2.0;\n    format ascii;\n    class {cls};\n    object {obj};\n}}\n'


def main():
    protocol = json.loads((DESIGN/'protocol.json').read_text())
    source = PROJECT/protocol['coefficient_source']
    if sha(source) != protocol['coefficient_source_sha256']:
        raise ValueError('Frozen coefficient source changed')
    case = next(c for c in protocol['planned_cases'] if c['case_id'] == 'C01')
    row = next(r for r in json.loads(source.read_text())['rows']
               if r['input_id'] == case['input_id'] and r['orientation_id'] == case['orientation_id'])
    cfg = dict(schema='SDI-C01-1', protocol_id=protocol['protocol_id'], case_id='C01',
               pressure_units='Pa', velocity_definition='U=J/H', H_m=protocol['H_m'],
               L_m=protocol['L_m'], mu_Pa_s=protocol['mu_Pa_s'], rho_kg_m3=protocol['rho_kg_m3'],
               mesh_cells=case['mesh_cells'], drive_axis=case['drive_axis'], G_Pa_per_m=case['G_Pa_per_m'],
               K_m3=row['K_global_m3'], D_m_minus2=row['D_global_m_minus2_conditional_total_drag'],
               thresholds=protocol['thresholds'], linear_solver=protocol['linear_solver'],
               source_hashes={'design_protocol':sha(DESIGN/'protocol.json'),'coefficient_source':sha(source)},
               source_paths={'design_protocol':str(DESIGN/'protocol.json'),'coefficient_source':str(source)},
               solve_authorized_in_preparation=False)
    common=ROOT/'common'
    if (common/'C01.json').exists():
        raise FileExistsError('Inputs already prepared; no silent regeneration')
    (common/'C01.json').write_text(json.dumps(cfg,indent=2)+'\n')
    for filename in ['protocol.json','PROTOCOL.md']:
        (common/filename).write_bytes((DESIGN/filename).read_bytes())
    nx,ny,nz=cfg['mesh_cells']; lx,ly,H=cfg['L_m']; mu=cfg['mu_Pa_s']
    dp=cfg['G_Pa_per_m']*lx
    values=dict(nx=nx,ny=ny,Lx=lx,Ly=ly,H=H,mu=mu,Kxx=cfg['K_m3'][0][0],Kyy=cfg['K_m3'][1][1],
                axis=0,pressureLow=dp,tolerance=1e-12,maxIter=2000)
    (common/'C01_2d.txt').write_text(''.join(f'{k} {v:.17g}\n' for k,v in values.items()))
    case_dir=ROOT/'openfoam/cases/C01'
    def write(rel,cls,obj,body):
        (case_dir/rel).write_text(foam_header(cls,obj)+body+'\n')
    write('0/p','volScalarField','p',f'''dimensions [1 -1 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{{
    xLow {{ type fixedValue; value uniform {dp:.17g}; }}
    xHigh {{ type fixedValue; value uniform 0; }}
    yLow {{ type zeroGradient; }}
    yHigh {{ type zeroGradient; }}
    frontAndBack {{ type empty; }}
}}''')
    write('constant/darcyProperties','dictionary','darcyProperties',f'''H [0 1 0 0 0 0 0] {H:.17g};
mu [1 -1 -1 0 0 0 0] {mu:.17g};
Dxx [0 -2 0 0 0 0 0] {cfg['D_m_minus2'][0][0]:.17g};
Dyy [0 -2 0 0 0 0 0] {cfg['D_m_minus2'][1][1]:.17g};
Dxy [0 -2 0 0 0 0 0] 0;''')
    verts=[(0,0,0),(lx,0,0),(lx,ly,0),(0,ly,0),(0,0,H),(lx,0,H),(lx,ly,H),(0,ly,H)]
    vertex_text='\n'.join('    ('+' '.join(f'{v:.17g}' for v in xyz)+')' for xyz in verts)
    write('system/blockMeshDict','dictionary','blockMeshDict',f'''convertToMeters 1;
vertices\n(\n{vertex_text}\n);
blocks (hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1));
edges ();
boundary
(
 xLow {{ type patch; faces ((0 4 7 3)); }}
 xHigh {{ type patch; faces ((1 2 6 5)); }}
 yLow {{ type patch; faces ((0 1 5 4)); }}
 yHigh {{ type patch; faces ((3 7 6 2)); }}
 frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7)); }}
);
mergePatchPairs ();''')
    write('system/controlDict','dictionary','controlDict','''application depthAveragedDarcyFoam;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime 1;
deltaT 1;
writeControl timeStep;
writeInterval 1;
purgeWrite 0;
writeFormat ascii;
writePrecision 17;
writeCompression off;
timeFormat general;
timePrecision 6;
runTimeModifiable false;
functions {};''')
    write('system/fvSchemes','dictionary','fvSchemes','''ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes { default none; }
laplacianSchemes { default Gauss linear orthogonal; }
interpolationSchemes { default linear; }
snGradSchemes { default orthogonal; }
fluxRequired { default no; p; }''')
    write('system/fvSolution','dictionary','fvSolution','''solvers
{
 p { solver PCG; preconditioner DIC; tolerance 1e-12; relTol 0; maxIter 2000; }
}''')
    print('C01 input and dictionaries prepared; no flow solver invoked')


if __name__=='__main__':
    main()
