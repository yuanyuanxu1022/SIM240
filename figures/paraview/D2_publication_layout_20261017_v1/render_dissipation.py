#!/usr/bin/env pvpython
"""Render existing T dissipation using the same verified 5 nm footprints as speed."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from paraview.simple import *
from paraview import servermanager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "rendered")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    prior = root / "figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1"
    spec = importlib.util.spec_from_file_location("verified_speed_renderer", prior / "render_fields.py")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    old = json.loads((prior / "rendered_v4/render_manifest.json").read_text())
    assert base.sha(prior / "render_fields.py") == old["render_script_sha256"]
    recorded = [v for tag in ("P", "T") for v in
                old["inputs"][tag]["original_input_chain"] + old["inputs"][tag]["evidence"]]
    for item in recorded:
        assert base.sha(item["path"]) == item["sha256"], item["path"]
    out = args.output_dir.resolve()
    if out.exists():
        raise RuntimeError("Choose a new output directory; no overwrite of prior renders.")
    out.mkdir(parents=True)
    original = OpenDataFile(old["inputs"]["T"]["reader"])
    original.UpdatePipeline()
    data = servermanager.Fetch(original)
    image, sampling = base.probe_grid(data, "XZ", 5e-9, 240e-9, 175e-9)
    centers = vtk.vtkCellCenters()
    centers.SetInputData(image)
    centers.Update()
    probe = vtk.vtkCompositeDataProbeFilter()
    probe.SetInputData(centers.GetOutput())
    probe.SetSourceData(data)
    probe.Update()
    points = probe.GetOutput()
    pd = points.GetPointData()
    assert np.all(vtk_to_numpy(pd.GetArray("vtkValidPointMask")) == 1)
    eps = vtk_to_numpy(pd.GetArray("dissipation_m2_s3")).copy()
    material = vtk_to_numpy(image.GetCellData().GetArray("material"))
    assert np.allclose(vtk_to_numpy(pd.GetArray("material")), material, rtol=0, atol=1e-6)
    liquid = material == 1
    assert liquid.sum() == 1200
    assert np.isfinite(eps[liquid]).all() and (eps[liquid] >= 0).all()
    assert eps[liquid].max() < 32
    eps_array = numpy_to_vtk(eps, deep=True)
    eps_array.SetName("epsilon_m2_s3")
    image.GetCellData().AddArray(eps_array)
    derived_path = out / "T_XZ_sample_footprints.vti"
    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName(str(derived_path))
    writer.SetInputData(image)
    writer.SetDataModeToAscii()
    assert writer.Write() == 1
    xyz = vtk_to_numpy(points.GetPoints().GetData())
    with (out / "sampled_epsilon_XZ.csv").open("w", newline="") as stream:
        table = csv.writer(stream)
        table.writerow(["x_nm", "z_nm", "material", "epsilon_m2_s3"])
        table.writerows((p[0] * 1e9, p[2] * 1e9, int(m), float(e))
                        for p, m, e in zip(xyz, material, eps))
    reader = XMLImageDataReader(FileName=[str(derived_path)])
    fluid = Threshold(registrationName="T_XZ_epsilon_liquid", Input=reader)
    fluid.Scalars = ["CELLS", "material"]
    fluid.ThresholdMethod = "Between"
    fluid.UpperThreshold = 1
    fluid.LowerThreshold = 1
    solid = Threshold(registrationName="T_XZ_solid", Input=reader)
    solid.Scalars = ["CELLS", "material"]
    solid.ThresholdMethod = "Between"
    solid.UpperThreshold = 3
    solid.LowerThreshold = 3
    view = CreateView("RenderView")
    view.ViewSize = [1920, 1400]
    view.UseColorPaletteForBackground = 0
    view.Background = [1, 1, 1]
    view.OrientationAxesVisibility = 0
    view.CenterAxesVisibility = 0
    display = Show(fluid, view)
    ColorBy(display, ("CELLS", "epsilon_m2_s3"))
    lut = GetColorTransferFunction("epsilon_m2_s3")
    assert lut.ApplyPreset("Viridis (matplotlib)", True)
    lut.Discretize = 1
    lut.NumberOfTableValues = 256
    lut.UseLogScale = 0
    lut.AutomaticRescaleRangeMode = "Never"
    lut.RescaleTransferFunction(0, 32)
    display.LookupTable = lut
    display.Ambient = 1
    display.Diffuse = 0
    display.Specular = 0
    display.InterpolateScalarsBeforeMapping = 0
    solid_display = Show(solid, view)
    solid_display.ColorArrayName = ["CELLS", ""]
    gray = [0.84, 0.85, 0.86]
    solid_display.DiffuseColor = gray
    solid_display.AmbientColor = gray
    solid_display.Ambient = 1
    solid_display.Diffuse = 0
    ResetCamera(view)
    view.CameraParallelProjection = 1
    view.CameraPosition = [120e-9, -880e-9, 87.5e-9]
    view.CameraFocalPoint = [120e-9, 120e-9, 87.5e-9]
    view.CameraViewUp = [0, 0, 1]
    view.CameraParallelScale = 87.5e-9
    Render(view)
    SaveScreenshot(str(out / "T_dissipation_XZ.png"), view, ImageResolution=[1920, 1400])
    SaveState(str(out / "dissipation_footprints.pvsm"))
    lut.GetClientSideObject().Build()
    rgb_table = []
    for value in np.linspace(0, 32, 256):
        rgb = [0.0, 0.0, 0.0]
        lut.GetClientSideObject().GetColor(float(value), rgb)
        rgb_table.append(rgb)
    expected = []
    for m, e in zip(material, eps):
        rgb = gray[:]
        if m == 1:
            lut.GetClientSideObject().GetColor(float(e), rgb)
        expected.append(np.rint(np.array(rgb) * 255).astype(int).tolist())
    assert all(base.sha(i["path"]) == i["sha256"] for i in recorded)
    user_dir = root / "CASE/D_series/D1_nanoimprint_droplet_filling"
    user_files = list(user_dir.glob("h75_d100_dx5_*profile*.csv"))
    user_files += list(user_dir.glob("h75_d100_dx5_*draft_v1.*"))
    manifest = {
        "field": "epsilon_m2_s3", "original_array": "dissipation_m2_s3", "unit": "m2/s3",
        "range": [0, 32], "mapping": "linear", "automatic_rescale": "Never",
        "preset": "Viridis (matplotlib)", "rgb_table": rgb_table,
        "physical_liquid_min": float(eps[liquid].min()),
        "physical_liquid_max": float(eps[liquid].max()),
        "liquid_samples": int(liquid.sum()), "sample_grid": [48, 35],
        "sample_footprint_nm": 5, "nominal_physical_extent_nm": [0, 240, 0, 175],
        "camera_position_m": list(view.CameraPosition),
        "camera_focal_m": list(view.CameraFocalPoint),
        "camera_up": list(view.CameraViewUp),
        "camera_parallel_scale_m": float(view.CameraParallelScale),
        "orthographic": int(view.CameraParallelProjection),
        "view_size": [1920, 1400], "expected_grid_center_rgb": expected,
        "sampling": sampling,
        "method": "Same original point values and 5 nm sample footprints as verified speed views; not wall-value extrapolation or cell averaging.",
        "contrast_to_user_draft": "User draft used interpolated POINTS then AllScalars threshold, losing mixed boundary cells. This layout uses declared half-way footprints, with method explicitly disclosed.",
        "original_inputs_and_evidence": recorded,
        "user_reference_files": [{"path": str(p), "sha256": base.sha(p)} for p in user_files],
        "source_hashes_unchanged": True, "renderer_sha256": base.sha(__file__),
        "previous_renderer_sha256": base.sha(prior / "render_fields.py"),
        "paraview_version": str(GetParaViewVersion()), "vtk_version": vtk.vtkVersion.GetVTKVersion(),
        "new_OpenLB_run": False, "physical_or_energy_validation": False,
    }
    (out / "render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"rendered": str(out), "liquid_samples": int(liquid.sum()),
                      "max_epsilon_m2_s3": float(eps[liquid].max()), "source_hashes_unchanged": True}))


if __name__ == "__main__":
    main()
