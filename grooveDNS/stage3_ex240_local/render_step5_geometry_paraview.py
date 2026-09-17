from pathlib import Path
from paraview.simple import (
    XMLImageDataReader, XMLPolyDataReader, Transform, Slice, Show,
    Hide, GetActiveViewOrCreate, GetColorTransferFunction,
    ColorBy, SaveScreenshot, ResetCamera, Delete
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "step5_geometry_visualization_v1_20260908"
VTK = OUT / "vtkData" / "data"


def material_lut():
    lut = GetColorTransferFunction("material")
    lut.RGBPoints = [
        0.0, 0.85, 0.85, 0.85,
        1.0, 0.10, 0.45, 0.90,
        2.0, 0.25, 0.25, 0.25,
        3.0, 0.85, 0.25, 0.15,
        4.0, 0.20, 0.75, 0.40,
        5.0, 0.65, 0.30, 0.80,
    ]
    lut.ScalarRangeInitialized = 1.0
    return lut


def load_scaled(state):
    vti = VTK / f"{state}_iT0000000iC00000.vti"
    reader = XMLImageDataReader(registrationName=state, FileName=[str(vti)])
    reader.CellArrayStatus = ["material", "rho_lattice", "velocity_m_s", "pressure_Pa"]
    scaled = Transform(registrationName=f"{state}_nm", Input=reader)
    scaled.Transform.Scale = [1.0e9, 1.0e9, 1.0e9]
    surface = XMLPolyDataReader(
        registrationName=f"{state}_surface",
        FileName=[str(OUT / f"{state}_continuous_punch_nm.vtp")],
    )
    return reader, scaled, surface


def render_xz(state, label):
    view = GetActiveViewOrCreate("RenderView")
    view.ViewSize = [1800, 1000]
    view.OrientationAxesVisibility = 1
    view.Background = [1, 1, 1]
    reader, scaled, surface = load_scaled(state)
    section = Slice(registrationName=f"{state}_xz", Input=scaled)
    section.SliceType = "Plane"
    section.SliceType.Origin = [120, 120, 95]
    section.SliceType.Normal = [0, 1, 0]
    display = Show(section, view)
    ColorBy(display, ("POINTS", "material"))
    display.LookupTable = material_lut()
    display.SetScalarBarVisibility(view, True)
    display.Opacity = 0.82
    wall_display = Show(surface, view)
    wall_display.Representation = "Wireframe"
    wall_display.LineWidth = 4.0
    wall_display.AmbientColor = [0, 0, 0]
    wall_display.DiffuseColor = [0, 0, 0]
    ResetCamera(view)
    view.CameraPosition = [120, -900, 95]
    view.CameraFocalPoint = [120, 120, 95]
    view.CameraViewUp = [0, 0, 1]
    view.CameraParallelProjection = 1
    view.CameraParallelScale = 145
    SaveScreenshot(str(OUT / f"{label}_xz_paraview.png"), view, ImageResolution=[1800, 1000])
    Hide(section, view); Hide(surface, view)
    Delete(section); Delete(surface); Delete(scaled); Delete(reader)


def render_xy_initial():
    state = "state_initial"
    view = GetActiveViewOrCreate("RenderView")
    reader, scaled, surface = load_scaled(state)
    section = Slice(registrationName="initial_xy_z100nm", Input=scaled)
    section.SliceType = "Plane"
    section.SliceType.Origin = [120, 120, 100]
    section.SliceType.Normal = [0, 0, 1]
    display = Show(section, view)
    ColorBy(display, ("POINTS", "material"))
    display.LookupTable = material_lut()
    display.SetScalarBarVisibility(view, True)
    Hide(surface, view)
    ResetCamera(view)
    view.CameraPosition = [120, 120, 900]
    view.CameraFocalPoint = [120, 120, 100]
    view.CameraViewUp = [0, 1, 0]
    view.CameraParallelProjection = 1
    view.CameraParallelScale = 135
    SaveScreenshot(str(OUT / "initial_xy_z100nm_paraview.png"), view, ImageResolution=[1400, 1400])
    Hide(section, view)
    Delete(section); Delete(surface); Delete(scaled); Delete(reader)


render_xz("state_initial", "initial")
render_xz("state_pre_conversion", "pre_conversion")
render_xz("state_post_conversion", "post_conversion")
render_xy_initial()
