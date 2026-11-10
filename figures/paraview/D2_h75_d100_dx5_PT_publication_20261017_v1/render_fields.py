#!/usr/bin/env pvpython
"""Read existing OpenLB fields, reconstruct declared 5 nm sample footprints, render."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from paraview.simple import *
from paraview import servermanager


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def kv(path):
    return dict(line.strip().split("=", 1) for line in Path(path).read_text().splitlines() if "=" in line)


def sources(path, visited=None):
    visited = set() if visited is None else visited
    path = Path(path).resolve()
    if path in visited:
        return
    visited.add(path)
    yield {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}
    if path.suffix in {".vtm", ".pvd", ".pvti", ".pvtu"}:
        for element in ET.parse(path).iter():
            name = element.get("file") or element.get("Source")
            if name:
                yield from sources(path.parent / name, visited)


def probe_grid(data, plane, dx, length, height):
    xs = (np.arange(round(length / dx)) + 0.5) * dx
    if plane == "XY":
        rows = xs
        x, y = np.meshgrid(xs, rows)
        xyz = np.column_stack((x.ravel(), y.ravel(), np.full(x.size, 37.5e-9)))
        origin, dims = (0, 0, 37.5e-9), (len(xs) + 1, len(rows) + 1, 1)
    else:
        rows = (np.arange(round(height / dx)) + 0.5) * dx
        x, z = np.meshgrid(xs, rows)
        xyz = np.column_stack((x.ravel(), np.full(x.size, 120e-9), z.ravel()))
        origin, dims = (0, 120e-9, 0), (len(xs) + 1, 1, len(rows) + 1)
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(xyz, deep=True))
    cloud = vtk.vtkPolyData()
    cloud.SetPoints(points)
    probe = vtk.vtkCompositeDataProbeFilter()
    probe.SetInputData(cloud)
    probe.SetSourceData(data)
    probe.Update()
    pd = probe.GetOutput().GetPointData()
    valid = vtk_to_numpy(pd.GetArray("vtkValidPointMask"))
    if not np.all(valid == 1):
        raise RuntimeError("Some grid samples fall outside the supplied original field.")
    material_raw = vtk_to_numpy(pd.GetArray("material"))
    material = np.rint(material_raw).astype(np.int32)
    if not np.allclose(material_raw, material, atol=1e-6, rtol=0):
        raise RuntimeError("Categorical material interpolated across a boundary.")
    velocity = vtk_to_numpy(pd.GetArray("velocity_m_s")).copy()
    speed = np.linalg.norm(velocity, axis=1)
    fluid = material == 1
    if not np.isfinite(velocity[fluid]).all():
        raise RuntimeError("Nonfinite velocity in selected liquid.")
    roof = np.where((xyz[:, 0] >= 60e-9) & (xyz[:, 0] < 180e-9), 175e-9, 75e-9)
    expected = np.where(xyz[:, 2] < roof, 1, 3)
    if not np.array_equal(material, expected):
        raise RuntimeError("Sampled material does not agree with the declared half-way geometry.")
    derived = vtk.vtkImageData()
    derived.SetOrigin(origin)
    derived.SetSpacing(dx, dx, dx)
    derived.SetDimensions(dims)
    for name, values in [("material", material), ("speed_m_s", speed), ("velocity_sample_m_s", velocity)]:
        array = numpy_to_vtk(values, deep=True)
        array.SetName(name)
        derived.GetCellData().AddArray(array)
    assert derived.GetNumberOfCells() == len(speed)
    return derived, {
        "plane": plane,
        "sample_count": int(len(speed)),
        "liquid_sample_count": int(fluid.sum()),
        "liquid_min_speed_m_s": float(speed[fluid].min()),
        "liquid_max_speed_m_s": float(speed[fluid].max()),
        "max_abs_out_of_plane_velocity_m_s": float(np.abs(velocity[fluid, 2 if plane == "XY" else 1]).max()),
        "bounds_m": list(derived.GetBounds()),
        "cell_dimensions": list(dims),
        "material_matches_halfway_geometry": True,
        "reconstruction": "Each original/probed point sample fills its 5 nm half-way cell footprint; piecewise constant, not a volume average.",
        "sample_location": "z=37.5 nm (native z node)" if plane == "XY" else "y=120 nm (linear probe between y nodes)",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "rendered")
    args = parser.parse_args()
    root = args.project_root.resolve()
    out = args.output_dir.resolve()
    if out.exists():
        raise RuntimeError("Choose a new output directory; original renders are preserved.")
    out.mkdir(parents=True)
    helper = Path("/home/dell/.codex/skills/paraview-publication/scripts/audit_fields.py")
    audit = runpy.run_path(str(helper))
    color_range = [0.0, 1.8e-4]
    configs = {
        "P": ("g2_ex240_parallel", 4329, "parallel"),
        "T": ("g2_ex240_perpendicular", 2940, "perpendicular"),
    }
    records = {}
    raw_hashes = []
    originals = {}
    for tag, (prefix, step, direction) in configs.items():
        steady = root / "CASE/D_series/D2_groove_error_map/results" / ("h75_d100_dx5_" + tag) / "steady"
        result = kv(steady / "result.txt")
        boundary = kv(steady / "boundary_audit.txt")
        if any(result.get(k) != "true" for k in ("PASS", "converged", "finite")):
            raise RuntimeError("Existing representative result is not PASS/converged/finite.")
        if (steady / "exit_code.txt").read_text().strip() != "0":
            raise RuntimeError("Independent representative shell exit is not zero.")
        if boundary.get("geometry_PASS") != "true" or boundary.get("q_audit_PASS") != "true":
            raise RuntimeError("Existing geometry/q record is not true.")
        if int(result["steps_completed"]) != step or result["direction"] != direction:
            raise RuntimeError("Final-frame/result association mismatch.")
        for k, expected in (("dx_m", 5e-9), ("mesa_gap_m", 75e-9), ("groove_depth_m", 100e-9), ("acceleration_m_s2", 1e5)):
            if not np.isclose(float(result[k]), expected, rtol=1e-12, atol=1e-22):
                raise RuntimeError("Unexpected recorded parameter: " + k)
        file = steady / "vtkData/data" / (prefix + "_iT{:07d}.vtm".format(step))
        originals[tag] = OpenDataFile(str(file))
        originals[tag].UpdatePipeline()
        chain = list(sources(file))
        raw_hashes.extend(chain)
        evidence = [{"path": str(steady / name), "sha256": sha(steady / name)}
                    for name in ("result.txt", "boundary_audit.txt", "exit_code.txt", "run_manifest.txt")]
        raw_hashes.extend(evidence)
        stats = audit["summarize"](originals[tag], SimpleNamespace(
            field="velocity_m_s", magnitude=True, material="material", fluid_value=1.0,
            material_atol=1e-8, bounds=[0, 240e-9, 0, 240e-9, 0, 175e-9]))
        if stats["max"] > color_range[1] or stats["min"] < color_range[0]:
            raise RuntimeError("Shared color range would clip measured speed.")
        nu = (float(result["tau"]) - 0.5) * float(result["dx_m"]) ** 2 / (3 * float(result["dt_s"]))
        records[tag] = {
            "case_id": result["case"], "unique_run_id_verified": False, "reader": str(file),
            "step": step, "dt_s": float(result["dt_s"]), "physical_time_s": step * float(result["dt_s"]),
            "existing_result_record": result, "existing_geometry_record": boundary,
            "original_input_chain": chain, "evidence": evidence, "fluid_volume_point_audit": stats,
            "nu_m2_s_inferred_from_recorded_BGK_mapping": nu,
            "viscosity_note": "This selected baseline is nu=1e-6 m2/s; with model rho=1000 kg/m3 it corresponds to mu=1 mPa s, not the separate mu15 run directories.",
        }
    lut = GetColorTransferFunction("speed_m_s")
    if not lut.ApplyPreset("Viridis (matplotlib)", True):
        raise RuntimeError("Required Viridis preset unavailable.")
    lut.NumberOfTableValues = 256
    lut.Discretize = 1
    lut.UseLogScale = 0
    lut.AutomaticRescaleRangeMode = "Never"
    lut.RescaleTransferFunction(*color_range)
    lut.GetClientSideObject().Build()
    table = []
    for value in np.linspace(*color_range, 256):
        rgb = [0.0, 0.0, 0.0]
        lut.GetClientSideObject().GetColor(float(value), rgb)
        table.append(rgb)
    manifest = {
        "paraview_version": str(GetParaViewVersion()), "vtk_version": vtk.vtkVersion.GetVTKVersion(),
        "scope": "Existing representative dx=5 nm P/T steady fields only; no new OpenLB computation or Gate release.",
        "color": {"array": "speed_m_s", "derived_from": "norm(original velocity_m_s)", "unit": "m/s",
                  "association": "CELLS (sample footprints from original POINTS)", "preset": "Viridis (matplotlib)",
                  "range": color_range, "mapping": "linear", "automatic_rescale": "Never",
                  "range_basis": "Union of the two original physical-domain liquid-volume sample ranges.",
                  "rgb_table": table},
        "geometry_nm": {"period": 240, "width": 120, "groove_start_x": 60, "groove_end_x": 180,
                        "mesa_gap": 75, "depth": 100, "maximum_height": 175, "dx": 5},
        "inputs": records, "panels": [], "audit_helper_sha256": sha(helper),
        "unit_note": "Original coordinates remain SI metres. Final montage axes are labelled in nm without transforming the velocity vectors.",
        "sampling_note": "No smoothing, new physical samples, or wall-speed extrapolation. Finite 5 nm sample footprints provide exact half-way geometry boundaries but do not resolve within-cell variation.",
        "journal_adaptation": "General manuscript draft; no exact journal compliance asserted.",
    }
    for plane in ("XY", "XZ"):
        layout = CreateLayout(name="Matched_" + plane)
        layout.SplitHorizontal(0, 0.5)
        for index, tag in enumerate(("P", "T")):
            data = servermanager.Fetch(originals[tag])
            image, stats = probe_grid(data, plane, 5e-9, 240e-9, 175e-9)
            derived_path = out / (tag + "_" + plane + "_sample_footprints.vti")
            writer = vtk.vtkXMLImageDataWriter()
            writer.SetFileName(str(derived_path)); writer.SetInputData(image)
            writer.SetDataModeToAscii()
            if writer.Write() != 1:
                raise RuntimeError("Could not write derived slice.")
            reader = XMLImageDataReader(FileName=[str(derived_path)])
            reader.UpdatePipeline()
            fluid = Threshold(registrationName=tag + "_" + plane + "_liquid", Input=reader)
            fluid.Scalars = ["CELLS", "material"]; fluid.LowerThreshold = 1; fluid.UpperThreshold = 1
            fluid.UpdatePipeline()
            view = CreateView("RenderView")
            layout.AssignView(index + 1, view)
            width, height = (1200, 1200) if plane == "XY" else (1200, 875)
            view.ViewSize = [width, height]
            view.UseColorPaletteForBackground = 0
            view.Background = [1, 1, 1]
            view.OrientationAxesVisibility = 0
            view.CenterAxesVisibility = 0
            display = Show(fluid, view)
            ColorBy(display, ("CELLS", "speed_m_s"))
            display.LookupTable = lut
            display.Ambient = 1
            display.Diffuse = 0
            display.Specular = 0
            display.Opacity = 1
            display.InterpolateScalarsBeforeMapping = 0
            if plane == "XZ":
                solid = Threshold(registrationName=tag + "_" + plane + "_solid", Input=reader)
                solid.Scalars = ["CELLS", "material"]; solid.LowerThreshold = 3; solid.UpperThreshold = 3
                solid_display = Show(solid, view)
                solid_display.ColorArrayName = ["CELLS", ""]
                solid_display.DiffuseColor = [0.84, 0.85, 0.86]
                solid_display.AmbientColor = [0.84, 0.85, 0.86]
                solid_display.Ambient = 1
                solid_display.Diffuse = 0
            ResetCamera(view)
            if plane == "XY":
                focal = [120e-9, 120e-9, 37.5e-9]
                position = [120e-9, 120e-9, 1037.5e-9]
                up = [0, 1, 0]
                scale = 120e-9
            else:
                focal = [120e-9, 120e-9, 87.5e-9]
                position = [120e-9, -880e-9, 87.5e-9]
                up = [0, 0, 1]
                scale = 87.5e-9
            view.CameraParallelProjection = 1
            view.CameraPosition = position; view.CameraFocalPoint = focal
            view.CameraViewUp = up; view.CameraParallelScale = scale
            lut.RescaleTransferFunction(*color_range)
            lut.AutomaticRescaleRangeMode = "Never"
            Render(view)
            destination = out / (tag + "_" + plane + ".png")
            SaveScreenshot(str(destination), view, ImageResolution=[width, height],
                           OverrideColorPalette="WhiteBackground")
            record = {"tag": tag, "plane": plane, "raw_png": str(destination),
                      "derived_vti": str(derived_path), "sampling": stats, "view_size": [width, height],
                      "camera": {"parallel": 1, "position_m": list(view.CameraPosition),
                                 "focal_m": list(view.CameraFocalPoint), "view_up": list(view.CameraViewUp),
                                 "parallel_scale_m": float(view.CameraParallelScale)},
                      "effective_color_range": [float(lut.RGBPoints[0]), float(lut.RGBPoints[-4])],
                      "auto_rescale": str(lut.AutomaticRescaleRangeMode),
                      "opacity": float(display.Opacity), "ambient": float(display.Ambient),
                      "diffuse": float(display.Diffuse)}
            manifest["panels"].append(record)
        layout.SetSize(2400, 1200 if plane == "XY" else 875)
    SaveState(str(out / "matched_fields.pvsm"))
    manifest["raw_input_hashes_unchanged_after_render"] = all(sha(v["path"]) == v["sha256"] for v in raw_hashes)
    if not manifest["raw_input_hashes_unchanged_after_render"]:
        raise RuntimeError("An original input/evidence file changed during rendering; inspect concurrent work.")
    manifest["outputs"] = [{"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size}
                           for p in sorted(out.iterdir()) if p.is_file()]
    manifest["render_script_sha256"] = sha(__file__)
    (out / "render_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output_dir": str(out), "panels": len(manifest["panels"]),
                      "raw_inputs_unchanged": True, "status": "rendered"}, ensure_ascii=False))


if __name__ == "__main__":
    main()

