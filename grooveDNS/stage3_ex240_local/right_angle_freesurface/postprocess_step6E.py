#!/usr/bin/env python3
"""Plot only the frozen STEP 6-E v2 output; never changes simulation data."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

HERE = Path(__file__).resolve().parent
RUN = HERE / "output" / "step6E_freesurface_h65_dx5_sigma00309_v2_20260910"
FIG = HERE / "figures"
DX_NM = 5.0


def history() -> dict[str, np.ndarray]:
    with (RUN / "fill_fraction_history.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}


def read_vti(step: int) -> dict[str, np.ndarray]:
    files = list((RUN / "vtkData" / "data").glob(f"*iT{step:07d}iC*.vti"))
    if len(files) != 1:
        raise RuntimeError(f"expected one VTI at step {step}, got {files}")
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(str(files[0])); reader.Update()
    image = reader.GetOutput(); dims = image.GetDimensions(); extent = image.GetExtent()
    arrays = {}
    for name in ("material", "velocity_m_s", "pressure_Pa", "liquid_volume_fraction", "free_surface_cell_type"):
        raw = vtk_to_numpy(image.GetPointData().GetArray(name))
        shape = (dims[2], dims[1], dims[0]) + (() if raw.ndim == 1 else (raw.shape[1],))
        arrays[name] = raw.reshape(shape)
    # One cuboid, overlap=3. The physical core is x/y=0..47 and z=0..37.
    ox, oy, oz = -extent[0], -extent[2], -extent[4]
    zcount = 38
    core = {}
    for key, value in arrays.items():
        core[key] = value[oz:oz+zcount, oy:oy+48, ox:ox+48, ...]
    core["x_nm"] = (np.arange(48)+0.5)*DX_NM
    core["y_nm"] = (np.arange(48)+0.5)*DX_NM
    core["z_nm"] = (np.arange(zcount)-0.5)*DX_NM
    core["file"] = np.array([str(files[0])])
    return core


def main() -> None:
    FIG.mkdir(exist_ok=True)
    h = history()
    time_ns = h["time_s"]*1e9
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.2), sharex=True, constrained_layout=True)
    axes[0].plot(time_ns, h["fill_fraction"], label="all recess")
    axes[0].plot(time_ns, h["junction_fill_fraction"], label="junction")
    axes[0].plot(time_ns, h["arm_fill_fraction"], label="side arms")
    axes[0].set_ylabel("Fill fraction"); axes[0].legend(ncol=3, fontsize=8)
    axes[1].plot(time_ns, h["liquid_mass_relative_drift"])
    axes[1].axhline(0, color="0.6", lw=.7); axes[1].set_ylabel("Liquid mass drift")
    axes[2].plot(time_ns, h["max_Mach"], label="Mach")
    ax2 = axes[2].twinx(); ax2.plot(time_ns, h["epsilon_min"], color="tab:red", label="epsilon min")
    ax2.axhline(-1e-3, color="tab:red", ls="--", lw=.8)
    axes[2].set(xlabel="Physical time (ns)", ylabel="Maximum Mach")
    ax2.set_ylabel("Minimum liquid fraction", color="tab:red")
    fig.suptitle("SIM-EC1XT240 right-angle FreeSurface baseline")
    fig.savefig(FIG/"fill_mass_stability.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG/"fill_mass_stability.pdf", bbox_inches="tight")
    plt.close(fig)

    steps = [0, 1500, 1623]
    labels = ["Initial", "Before stop", "Stop: epsilon violation"]
    fig, axes = plt.subplots(len(steps), 2, figsize=(9.2, 10.2), constrained_layout=True)
    audit_rows = []
    for row, (step, label) in enumerate(zip(steps, labels)):
        data = read_vti(step)
        material = data["material"].astype(int); eps = data["liquid_volume_fraction"]
        fluid = material == 1
        zmask = data["z_nm"] >= 65
        recess_eps = np.ma.masked_where(~fluid[zmask], eps[zmask])
        top = np.ma.max(recess_eps, axis=0)
        iy = 23
        section = np.ma.masked_where(~fluid[:, iy, :], eps[:, iy, :])
        im0 = axes[row,0].imshow(top, origin="lower", extent=(0,240,0,240), vmin=0, vmax=1,
                                 cmap="Blues", interpolation="nearest")
        im1 = axes[row,1].imshow(section, origin="lower", extent=(0,240,-5,185), vmin=0, vmax=1,
                                 cmap="Blues", interpolation="nearest", aspect="auto")
        axes[row,0].set(title=f"{label}, step {step}", xlabel="x (nm)", ylabel="y (nm)")
        axes[row,1].set(title="Center y section", xlabel="x (nm)", ylabel="z (nm)")
        vals=np.where(fluid,eps,np.nan); index=np.unravel_index(np.nanargmin(vals),vals.shape)
        audit_rows.append({
            "step":step,"source_vti":str(data["file"][0]),"epsilon_min":float(vals[index]),
            "min_ix":index[2],"min_iy":index[1],"min_iz":index[0],
            "min_x_nm":float(data["x_nm"][index[2]]),"min_y_nm":float(data["y_nm"][index[1]]),
            "min_z_nm":float(data["z_nm"][index[0]]),"material":int(material[index]),
            "cell_type":int(data["free_surface_cell_type"][index]),
        })
    fig.colorbar(im0, ax=axes[:,0], label="Recess max liquid fraction")
    fig.colorbar(im1, ax=axes[:,1], label="Liquid volume fraction")
    fig.suptitle("SIM-EC1XT240 FreeSurface interface states")
    fig.savefig(FIG/"key_interface_states.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG/"key_interface_states.pdf", bbox_inches="tight")
    plt.close(fig)

    with (RUN/"interface_state_audit.csv").open("w", newline="") as handle:
        writer=csv.DictWriter(handle, fieldnames=audit_rows[0].keys()); writer.writeheader(); writer.writerows(audit_rows)
    print(audit_rows[-1])


if __name__ == "__main__":
    main()
