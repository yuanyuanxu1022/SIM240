"""Read-only diagnostic of the user's saved dissipation view; no solver execution."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from vtk.util.numpy_support import vtk_to_numpy
from paraview.simple import (
    ColorBy, GetParaViewVersion, GetSources, GetViews, GetDisplayProperties,
    LoadState, Render, SaveScreenshot,
)
from paraview import servermanager

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
STATE = ROOT / "CASE/D_series/D1_nanoimprint_droplet_filling/h75_d100_dx5_T_dissipation_XZ_y120nm.pvsm"
FIELD = "dissipation_m2_s3"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def val(proxy, name):
    if name not in proxy.ListProperties():
        return None
    item = getattr(proxy, name)
    if isinstance(item, (str, int, float)):
        return item
    try:
        return list(item)
    except TypeError:
        return str(item)


def leaves(data):
    if data.IsA("vtkCompositeDataSet"):
        iterator = data.NewIterator()
        iterator.SkipEmptyNodesOn()
        iterator.InitTraversal()
        while not iterator.IsDoneWithTraversal():
            yield iterator.GetCurrentDataObject()
            iterator.GoToNextItem()
    else:
        yield data


state_before = sha(STATE)
LoadState(str(STATE))
sources = {key[0]: source for key, source in GetSources().items()}
view = next(v for v in GetViews() if v.GetXMLName() == "RenderView")
reader = sources["g2_ex240_perpendicular_iT0002940.vtm"]
section = sources["Slice2"]
reader.UpdatePipeline()
section.UpdatePipeline()
reader_display = GetDisplayProperties(reader, view=view)
section_display = GetDisplayProperties(section, view=view)

payloads = [Path(str(reader.FileName[0]))]
root_vtm = ET.parse(payloads[0]).getroot()
payloads.extend(payloads[0].parent / node.attrib["file"]
                for node in root_vtm.iter() if "file" in node.attrib)
hashes_before = {str(p): sha(p) for p in payloads}

report = {
    "scope": "Diagnostic only; no original file edits or solver runs",
    "paraview_version": str(GetParaViewVersion()),
    "state": {"path": str(STATE), "sha256_before": state_before},
    "input_hashes_before": hashes_before,
    "sources": {}, "original_displays": [],
    "camera": {name: val(view, name) for name in (
        "CameraPosition", "CameraFocalPoint", "CameraViewUp",
        "CameraParallelProjection", "CameraParallelScale", "CameraClippingRange")},
}
for name, source in sources.items():
    entry = {"type": source.GetXMLName()}
    if "FileName" in source.ListProperties():
        entry["files"] = list(source.FileName)
    if source.GetXMLName() == "Cut":
        entry.update(origin_m=list(source.SliceType.Origin),
                     normal=list(source.SliceType.Normal),
                     input_type=source.Input.GetXMLName())
    report["sources"][name] = entry
    display = next((rep for rep in view.Representations
                    if "Input" in rep.ListProperties() and rep.Input
                    and rep.Input.SMProxy.GetGlobalID() == source.SMProxy.GetGlobalID()), None)
    if display:
        report["original_displays"].append({"source": name, **{
            key: val(display, key) for key in (
                "Visibility", "Representation", "ColorArrayName", "Opacity",
                "InterpolateScalarsBeforeMapping", "BackfaceRepresentation",
                "Ambient", "Diffuse")}})

lut = reader_display.LookupTable
report["lookup_table"] = {key: val(lut, key) for key in (
    "RGBPoints", "UseLogScale", "AutomaticRescaleRangeMode", "VectorMode")}

Render(view)
SaveScreenshot(str(OUT / "01_saved_state_raw_surface.png"), view,
               ImageResolution=[1200, 800])

# A controlled contrast: only replace the raw 3-D surface by its saved section.
# Camera and lookup table remain unchanged; original saved state is never written.
reader_display.Visibility = 0
section_display.Visibility = 1
ColorBy(section_display, ("POINTS", FIELD))
section_display.LookupTable = lut
Render(view)
SaveScreenshot(str(OUT / "02_isolated_saved_slice.png"), view,
               ImageResolution=[1200, 800])

report["slice_data"] = []
for block in leaves(servermanager.Fetch(section)):
    if not block.IsA("vtkDataSet"):
        continue
    xyz = vtk_to_numpy(block.GetPoints().GetData())
    material = vtk_to_numpy(block.GetPointData().GetArray("material"))
    eps = vtk_to_numpy(block.GetPointData().GetArray(FIELD))
    physical = ((xyz >= [0, 0, 0]) &
                (xyz <= [2.4e-7, 2.4e-7, 1.75e-7])).all(axis=1)
    liquid = physical & np.isclose(material, 1, rtol=0, atol=1e-6)
    finite = liquid & np.isfinite(eps)
    report["slice_data"].append({
        "selected_liquid_points_including_repeats": int(finite.sum()),
        "nonfinite_liquid_values": int((liquid & ~np.isfinite(eps)).sum()),
        "min": float(eps[finite].min()), "max": float(eps[finite].max()),
    })

report["raw_grid_y_planes"] = []
for block in leaves(servermanager.Fetch(reader)):
    if not block.IsA("vtkImageData"):
        continue
    nx, ny, nz = block.GetDimensions()
    spacing = np.array(block.GetSpacing())
    origin = np.array(block.GetOrigin())
    extent = np.array(block.GetExtent())
    xs = origin[0] + (np.arange(nx) + extent[0]) * spacing[0]
    ys = origin[1] + (np.arange(ny) + extent[2]) * spacing[1]
    zs = origin[2] + (np.arange(nz) + extent[4]) * spacing[2]
    eps = vtk_to_numpy(block.GetPointData().GetArray(FIELD)).reshape(nz, ny, nx)
    mat = vtk_to_numpy(block.GetPointData().GetArray("material")).reshape(nz, ny, nx)
    domain_xz = ((xs[None, :] >= 0) & (xs[None, :] <= 2.4e-7) &
                 (zs[:, None] >= 0) & (zs[:, None] <= 1.75e-7))
    center = int(np.argmin(abs(ys - 1.2e-7)))
    physical_y = (ys >= 0) & (ys <= 2.4e-7)
    physical_liquid = (domain_xz[:, None, :] & physical_y[None, :, None] &
                       np.isclose(mat, 1, rtol=0, atol=1e-6))
    center_liquid = np.isclose(mat[:, center, :], 1, rtol=0, atol=1e-6)
    comparable = physical_liquid & center_liquid[:, None, :]
    difference = abs(eps - eps[:, center, :][:, None, :])
    maximum_index = np.unravel_index(np.argmax(eps), eps.shape)
    iz, iy, ix = maximum_index
    raw_extrema = {
        "all_point_max": float(eps[maximum_index]),
        "all_point_max_xyz_nm": [float(xs[ix] * 1e9), float(ys[iy] * 1e9),
                                  float(zs[iz] * 1e9)],
        "all_point_max_material": float(mat[maximum_index]),
        "physical_liquid_count": int(physical_liquid.sum()),
        "physical_liquid_min": float(eps[physical_liquid].min()),
        "physical_liquid_max": float(eps[physical_liquid].max()),
        "physical_liquid_nonfinite_count": int((~np.isfinite(eps[physical_liquid])).sum()),
        "physical_liquid_negative_count": int((eps[physical_liquid] < 0).sum()),
        "physical_y_planes": int(physical_y.sum()),
        "physical_y_max_abs_difference_from_center": float(difference[comparable].max()),
    }
    plane_results = []
    for j in sorted({0, 1, center, ny - 2, ny - 1}):
        good = domain_xz & np.isclose(mat[:, j, :], 1, rtol=0, atol=1e-6)
        both = good & np.isclose(mat[:, center, :], 1, rtol=0, atol=1e-6)
        plane_results.append({
            "y_nm": float(ys[j] * 1e9), "liquid_count": int(good.sum()),
            "liquid_min": float(eps[:, j, :][good].min()) if good.any() else None,
            "liquid_max": float(eps[:, j, :][good].max()) if good.any() else None,
            "max_abs_difference_from_center_plane":
                float(abs(eps[:, j, :][both] - eps[:, center, :][both]).max())
                if both.any() else None,
        })
    report["raw_grid_y_planes"].append({"dimensions": [nx, ny, nz],
                                         "raw_extrema": raw_extrema,
                                         "planes": plane_results})

report["state"]["sha256_after"] = sha(STATE)
report["input_hashes_after"] = {str(p): sha(p) for p in payloads}
report["original_files_unchanged"] = (
    state_before == report["state"]["sha256_after"] and
    hashes_before == report["input_hashes_after"])
assert report["original_files_unchanged"]
(OUT / "evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
