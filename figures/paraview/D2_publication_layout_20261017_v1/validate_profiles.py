#!/usr/bin/env pvpython
"""Bind user CSV curves to existing P field by reprobe; no new simulation."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from paraview.simple import OpenDataFile
from paraview import servermanager

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
USER = ROOT / "CASE/D_series/D1_nanoimprint_droplet_filling"
P = ROOT / "CASE/D_series/D2_groove_error_map/results/h75_d100_dx5_P/steady/vtkData/data/g2_ex240_parallel_iT0004329.vtm"
reader = OpenDataFile(str(P))
reader.UpdatePipeline()
data = servermanager.Fetch(reader)
results = []
for location, expected_x, ceiling in (("groove", 120, 175), ("mesa", 30, 75)):
    source = USER / ("h75_d100_dx5_P_profile_" + location + "_x" + str(expected_x) + "nm.csv")
    with source.open() as stream:
        rows = list(csv.DictReader(stream))
    xyz = np.array([[float(row["Points:" + str(i)]) for i in range(3)] for row in rows])
    velocity = np.array([[float(row["velocity_m_s:" + str(i)]) for i in range(3)] for row in rows])
    material = np.array([float(row["material"]) for row in rows])
    valid = np.array([int(row["vtkValidPointMask"]) for row in rows])
    assert np.allclose(xyz[:, 0] * 1e9, expected_x, rtol=0, atol=1e-4)
    assert np.allclose(xyz[:, 1] * 1e9, 120, rtol=0, atol=1e-4)
    selected = (valid == 1) & np.isclose(material, 1, rtol=0, atol=1e-6) & np.isfinite(velocity).all(axis=1)
    assert np.all(np.diff(xyz[:, 2]) > 0)
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(xyz, deep=True))
    cloud = vtk.vtkPolyData()
    cloud.SetPoints(points)
    probe = vtk.vtkCompositeDataProbeFilter()
    probe.SetInputData(cloud)
    probe.SetSourceData(data)
    probe.Update()
    pd = probe.GetOutput().GetPointData()
    sampled = vtk_to_numpy(pd.GetArray("velocity_m_s"))
    assert np.all(vtk_to_numpy(pd.GetArray("vtkValidPointMask"))[selected] == 1)
    difference = abs(sampled[selected] - velocity[selected])
    # The CSV contains float32 coordinates; two ParaView versions can evaluate
    # at slightly different double/float locations. Report actual errors too.
    assert np.allclose(sampled[selected], velocity[selected], atol=1e-10, rtol=5e-6)
    uy = velocity[:, 1]
    results.append({
        "location": location, "x_nm": expected_x, "y_nm": 120,
        "nominal_ceiling_nm": ceiling, "path": str(source),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "input_rows": len(rows), "selected_liquid_rows": int(selected.sum()),
        "excluded_rows": int((~selected).sum()),
        "selected_z_range_nm": [float(xyz[selected, 2].min() * 1e9), float(xyz[selected, 2].max() * 1e9)],
        "max_uy_m_s": float(uy[selected].max()),
        "max_abs_velocity_difference_from_original_P_reprobe_m_s": float(difference.max()),
        "reprobe_tolerances": {"atol_m_s": 1e-10, "rtol": 5e-6},
        "interior_exclusions": int(np.count_nonzero(~selected[np.flatnonzero(selected)[0]:np.flatnonzero(selected)[-1] + 1])),
    })
output = OUT / "profile_validation.json"
if output.exists():
    raise RuntimeError("Refusing to overwrite an existing validation record.")
output.write_text(json.dumps({"source_P_reader": str(P), "profiles": results,
                              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                              "purpose": "CSV provenance and sample checks, not physical validation"}, indent=2) + "\n")
print(json.dumps(results, indent=2))
