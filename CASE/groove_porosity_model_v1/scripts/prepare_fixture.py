#!/usr/bin/env python3
"""Copy only the existing SDI mesh/dictionaries; no mesh or flow solver."""
from pathlib import Path
import shutil

PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parents[1]
def prepare():
    fixture = PKG / 'build/fixture'
    if fixture.exists():
        return fixture
    source = ROOT / 'CASE/interface_static_darcy_v1_3/runs/SDI_C04_v1_3_20261030_01/openfoam'
    shutil.copytree(source/'constant/polyMesh', fixture/'constant/polyMesh')
    shutil.copytree(source/'system', fixture/'system')
    control = fixture/'system/controlDict'
    control.write_text(control.read_text() + '\nlibs ("' + str(PKG/'build/lib/libgroovePorosity.so') + '" "libfvModels.so");\n')
    (fixture/'constant/polyMesh/cellZones').write_text(
        'FoamFile { format ascii; class cellZoneList; object cellZones; }\n1\n(\n'
        'groove { type cellZone; cellLabels List<label> 256 (\n'
        + '\n'.join(map(str,range(256))) + '\n); }\n)\n')
    return fixture
if __name__ == '__main__':
    print(prepare())
