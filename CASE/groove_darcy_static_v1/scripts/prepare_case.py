#!/usr/bin/env python3
"""Prepare one GDI01 template; copy existing mesh/library, never run a solver."""
import ast
import hashlib
import json
import shutil
from pathlib import Path

PKG=Path(__file__).resolve().parents[1]
ROOT=PKG.parents[1]
DESIGN=ROOT/'docs/reports/GrooveDarcy_static_protocol_20261030'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    case=PKG/'cases/GDI01'
    if case.exists(): raise FileExistsError('Refusing existing GDI01 template')
    common=PKG/'common';common.mkdir()
    for name in ['protocol.json','PROTOCOL.md','squeeze_interface.json','reference_values.json','input_bindings.json']:
        shutil.copy2(DESIGN/name,common/name)
    bindings=json.loads((common/'input_bindings.json').read_text())
    assert all(sha(Path(p) if p.startswith('/') else ROOT/p)==h for p,h in bindings.items())
    run=ROOT/'CASE/interface_static_darcy_v1/runs/SDI_C01_v1_20261030_01'
    old=json.loads((run/'common/C01.json').read_text())
    cfg=dict(old,case_id='GDI01',protocol_id='GDI-v1',schema='GDI01-1',baseline_case_id='C01',
        baseline_run_id='SDI_C01_v1_20261030_01',coefficient_input_id='V2_published_rounded',orientation_id='groove_along_long_y',
        GDI_protocol_sha256=sha(common/'protocol.json'),source_coefficient_sha256=old['source_hashes']['coefficient_source'])
    (common/'GDI01.json').write_text(json.dumps(cfg,indent=2)+'\n')
    for sub in ['system','constant/polyMesh']:
        shutil.copytree(run/'openfoam'/sub,case/sub)
    (case/'0').mkdir()
    shutil.copy2(run/'openfoam/0/p',case/'0/p')
    (case/'0/U').write_text('''FoamFile { format ascii; class volVectorField; object U; }
dimensions [0 1 -1 0 0 0 0];
internalField uniform (0 0 0);
boundaryField
{
 xLow { type zeroGradient; }
 xHigh { type zeroGradient; }
 yLow { type slip; value uniform (0 0 0); }
 yHigh { type slip; value uniform (0 0 0); }
 frontAndBack { type empty; }
}
''')
    control=case/'system/controlDict'
    control.write_text(control.read_text().replace('application depthAveragedDarcyFoam;','application grooveDarcyStaticFoam;')+'\nlibs ("libgroovePorosity.so");\n')
    (case/'constant/polyMesh/cellZones').write_text('FoamFile { format ascii; class cellZoneList; object cellZones; }\n1\n(\ngroove { type cellZone; cellLabels List<label> 512 (\n'+'\n'.join(map(str,range(512)))+'\n); }\n)\n')
    model=(ROOT/'CASE/groove_porosity_model_v1/examples/fvModels').read_text()
    (case/'constant/fvModels').write_text(model.replace('e1 (1 0 0)','e1 (0 1 0)').replace('e2 (0 1 0)','e2 (-1 0 0)'))
    expected=json.loads((common/'reference_values.json').read_text())['cases'][0]['analytic_expectation']
    (case/'constant/gdiProperties').write_text('FoamFile { format ascii; class dictionary; object gdiProperties; }\n'
        'mu [1 -1 -1 0 0 0 0] 0.001;\nrho [1 -3 0 0 0 0 0] 1000;\nnu [0 2 -1 0 0 0 0] 1e-6;\n'
        f'velocityScale [0 1 -1 0 0 0 0] {expected["Ux_m_s"]:.17g};\n')
    (PKG/'build/lib').mkdir(parents=True,exist_ok=True)
    source=ROOT/'CASE/groove_porosity_model_v1/build/lib/libgroovePorosity.so'
    shutil.copy2(source,PKG/'build/lib/libgroovePorosity.so')
    inherited=[]
    for name in ['grooveDarcy.C','grooveDarcy.H','grooveTransport.H']:
        p=ROOT/'CASE/groove_porosity_model_v1/src'/name
        target=PKG/'provenance/subclass'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        inherited.append(dict(source=str(p),copied_path=str(target.relative_to(PKG)),sha256=sha(p)))
    inherited.append(dict(source=str(source),copied_path='build/lib/libgroovePorosity.so',sha256=sha(source)))
    (common/'subclass_binding.json').write_text(json.dumps(inherited,indent=2)+'\n')
    refs=PKG/'references/C01'
    for folder in ['two_dimensional','openfoam/SDI_output']:
        target=refs/folder;target.mkdir(parents=True)
        for name in ['cells.csv','faces.csv','solver.json']:shutil.copy2(run/folder/name,target/name)
    shutil.copy2(ROOT/'docs/reports/SDI_C01_results_20261030/interface_analysis_geometry_v1_1.json',refs/'accepted_analysis.json')
    shutil.copy2(run/'run_manifest.json',refs/'original_run_manifest.json')
    shutil.copy2(run/'execution.json',refs/'original_execution.json')
    source_checker=ROOT/'CASE/interface_static_darcy_v1_3/analysis/check_results.py'
    text=source_checker.read_text();tree=ast.parse(text);lines=text.splitlines(True)
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['sha','read_csv','evaluate']]
    metrics='''"""Frozen SDI metric kernels, unchanged AST; pure data functions only.
Source: C04 checker 1.3.0. GDI identity and additional checks live separately.
"""\nimport csv\nimport hashlib\nimport math\n'''
    metrics+='\n\n'.join(''.join(lines[n.lineno-1:n.end_lineno]) for n in functions)
    target=PKG/'analysis/sdi_metrics.py';target.parent.mkdir();target.write_text(metrics)
    (common/'metric_origin.json').write_text(json.dumps(dict(source=str(source_checker),source_sha256=sha(source_checker),
        functions=[n.name for n in functions],copied_AST_unchanged=True),indent=2)+'\n')
    print(json.dumps(dict(case='GDI01',template_created=True,full_zone_cells=512,flow_solved=False,run_id=None)))
if __name__=='__main__':main()
