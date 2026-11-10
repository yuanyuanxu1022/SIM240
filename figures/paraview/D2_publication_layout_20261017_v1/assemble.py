#!/usr/bin/env python3
"""Uniform, source-backed four-figure layout; original exports are immutable."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.patches import Rectangle
from matplotlib.ticker import ScalarFormatter
import numpy as np
from PIL import Image

SKILL = Path("/home/dell/.codex/skills/scientific-visualization")
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL / "assets"))
from figure_export import export_figure
from style_presets import style_context

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / "figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/rendered_v4"
MM = 1 / 25.4
GRAY = (0.84, 0.85, 0.86)
ORANGE, BLUE = "#D55E00", "#0072B2"
DPI = 450


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry(ax, plane="XZ"):
    ax.set(xlim=(0, 240), ylim=(0, 240 if plane == "XY" else 175),
           xlabel=r"$x$ (nm)", ylabel=r"$y$ (nm)" if plane == "XY" else r"$z$ (nm)")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([0, 60, 120, 180, 240])
    ax.set_yticks([0, 60, 120, 180, 240] if plane == "XY" else [0, 50, 75, 125, 175])
    ax.tick_params(direction="out", length=3, width=0.65, pad=3)
    if plane == "XY":
        for x in (60, 180):
            ax.axvline(x, color="white", linestyle=(0, (3, 3)), linewidth=0.7)
    else:
        ax.plot([0, 60, 60, 180, 180, 240], [75, 75, 175, 175, 75, 75],
                color="#303030", linewidth=0.7)
        ax.text(30, 125, "Solid", ha="center", va="center", fontsize=8, color="#303030")
        ax.text(210, 125, "Solid", ha="center", va="center", fontsize=8, color="#303030")


def footer(fig, cut, prefix=""):
    text = prefix + r"$h=75$ nm; $d=100$ nm; $\Delta x=5$ nm; " + cut
    fig.text(0.5, 0.035, text, ha="center", va="bottom", fontsize=8)


def audit_text(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    artists = list(fig.texts)
    for ax in fig.axes:
        artists += list(ax.texts) + [ax.xaxis.label, ax.yaxis.label,
                                    ax.xaxis.offsetText, ax.yaxis.offsetText]
        artists += ax.get_xticklabels() + ax.get_yticklabels()
        if ax.get_legend():
            artists += ax.get_legend().get_texts()
    boxes = []
    for artist in artists:
        if not artist.get_visible() or not artist.get_text():
            continue
        box = artist.get_window_extent(renderer)
        if box.x0 < -1 or box.y0 < -1 or box.x1 > fig.bbox.width + 1 or box.y1 > fig.bbox.height + 1:
            raise RuntimeError("Text outside canvas: " + artist.get_text())
        boxes.append({"text": artist.get_text(), "bbox_px": list(box.bounds)})
    return boxes


def common_provenance():
    return {
        "scope": "Only existing h75_d100_dx5 P/T fields and user CSV; no new simulations or Gate release",
        "coordinate_units": "nm; original coordinates in metres",
        "no_new_spatial_resolution": True,
        "field_images": "Unmodified quantitative ParaView renders, no smoothing or image recoloring",
        "journal": "General manuscript working layout; exact journal/phase not selected",
        "software_guidance": {
            "skills": ["paraview-publication", "scientific-visualization", "matplotlib"],
            "citation": "Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. https://doi.org/10.48550/arXiv.2609.00065",
            "arxiv_checked": "2026-10-17; current record revised 2026-09-02; no journal reference listed",
        },
    }


def save(fig, out, stem, details):
    text_boxes = audit_text(fig)
    record = export_figure(fig, out / stem, formats=["png", "pdf", "svg"],
                           dpi=DPI, transparent=False, bbox_inches=None,
                           facecolor="white", font_mode="truetype", overwrite=False,
                           provenance={**common_provenance(), **details}, write_manifest=True)
    record["stem"] = stem
    record["text_extents"] = text_boxes
    record["axes_boxes"] = [list(ax.get_position().bounds) for ax in fig.axes]
    plt.close(fig)
    return record


def speed_figure(out, metadata, plane):
    width_mm, height_mm = (180, 95 if plane == "XY" else 85)
    fig = plt.figure(figsize=(width_mm * MM, height_mm * MM), dpi=DPI, facecolor="white")
    panel_w = 0.34
    panel_h = panel_w * width_mm / height_mm * (1 if plane == "XY" else 175 / 240)
    bottom = 0.17 if plane == "XY" else 0.24
    positions = [0.075, 0.49]
    for i, (tag, title) in enumerate((("P", "Along grooves (P)"), ("T", "Across grooves (T)"))):
        ax = fig.add_axes([positions[i], bottom, panel_w, panel_h])
        source = PRIOR / (tag + "_" + plane + ".png")
        expected = next(item for item in metadata["outputs"] if Path(item["path"]) == source)
        assert sha(source) == expected["sha256"]
        extent = [0, 240, 0, 240 if plane == "XY" else 175]
        ax.imshow(np.asarray(Image.open(source).convert("RGB")), origin="upper",
                  extent=extent, interpolation="none", aspect="equal")
        geometry(ax, plane)
        fig.text(positions[i], 0.95, ("(a)  " if i == 0 else "(b)  ") + title,
                 ha="left", va="top", fontsize=9.5, fontweight="bold")
        if tag == "P":
            drive = r"Drive: $+y$ $\uparrow$" if plane == "XY" else r"Drive: $+y$ $\otimes$ (into page)"
        else:
            drive = r"Drive: $+x$ $\rightarrow$"
        ax.text(0.5, 1.035, drive, transform=ax.transAxes, ha="center", va="bottom", fontsize=8)
    cax = fig.add_axes([0.875, bottom, 0.019, panel_h])
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((-4, -4))
    sm = matplotlib.cm.ScalarMappable(norm=Normalize(0, 1.8e-4),
                                     cmap=ListedColormap(metadata["color"]["rgb_table"]))
    cb = fig.colorbar(sm, cax=cax, ticks=[0, 0.6e-4, 1.2e-4, 1.8e-4], format=formatter)
    cb.set_label(r"Speed, $|\mathbf{u}|$ (m s$^{-1}$)", labelpad=6)
    cb.outline.set_linewidth(0.65)
    cut = r"$z=37.5$ nm" if plane == "XY" else r"$y=120$ nm"
    footer(fig, cut)
    number = 1 if plane == "XY" else 2
    return save(fig, out, f"Fig{number}_velocity_{plane}", {
        "quantity": "Absolute speed; common 0..1.8e-4 m/s; no per-panel normalization",
        "source_render_manifest": str(PRIOR / "render_manifest.json"),
        "source_render_manifest_sha256": sha(PRIOR / "render_manifest.json"),
        "plane": plane, "physical_extent_nm": extent,
        "projected_edges_not_liquid_interfaces": plane == "XY",
        "sampling_method": metadata["sampling_note"],
    })


def load_profile(item):
    assert sha(item["path"]) == item["sha256"]
    with Path(item["path"]).open() as stream:
        rows = list(csv.DictReader(stream))
    z = np.array([float(r["Points:2"]) * 1e9 for r in rows])
    u = np.array([float(r["velocity_m_s:1"]) for r in rows])
    material = np.array([float(r["material"]) for r in rows])
    mask = np.array([int(r["vtkValidPointMask"]) for r in rows])
    valid = (mask == 1) & np.isclose(material, 1, rtol=0, atol=1e-6) & np.isfinite(u)
    assert valid.sum() == item["selected_liquid_rows"]
    u[~valid] = np.nan  # Preserve exclusions as gaps; never connect through them.
    return z, u


def profile_figure(out, validation):
    fig = plt.figure(figsize=(180 * MM, 95 * MM), dpi=DPI, facecolor="white")
    geom_h = 0.32 * 180 / 95 * 175 / 240
    axg = fig.add_axes([0.075, 0.28, 0.32, geom_h])
    for x in (0, 180):
        axg.add_patch(Rectangle((x, 75), 60, 100, facecolor=GRAY, edgecolor="none"))
    geometry(axg)
    axg.text(0.5, 1.06, r"Drive: $+y$ $\otimes$", transform=axg.transAxes,
             ha="center", va="bottom", fontsize=8)
    ax = fig.add_axes([0.535, 0.20, 0.425, 0.60])
    for item, color, linestyle, label in zip(validation["profiles"], [ORANGE, BLUE], ["-", "--"],
            [r"Groove center ($x=120$ nm)", r"Under mesa ($x=30$ nm)"]):
        z, u = load_profile(item)
        selected = np.isfinite(u)
        ax.plot(z, u, color=color, linestyle=linestyle, linewidth=1.3, label=label)
        axg.plot([item["x_nm"]] * 2, item["selected_z_range_nm"], color=color,
                 linestyle=linestyle, linewidth=1.4)
        axg.text(item["x_nm"] + 6, 135 if item["location"] == "groove" else 36,
                  r"$x=" + str(item["x_nm"]) + "$", color=color, fontsize=8,
                  ha="left", va="center")
        # Export a transparent-to-audit table with flags and NaNs, not a modified raw CSV.
        target = out / ("profile_" + item["location"] + "_plotted.csv")
        with target.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["z_nm", "u_y_m_s_or_NaN", "selected_liquid"])
            writer.writerows(zip(z, u, selected.astype(int)))
    ax.set(xlabel=r"Height, $z$ (nm)", ylabel=r"Along-groove velocity, $u_y$ (m s$^{-1}$)",
           xlim=(0, 180), ylim=(0, 1.8e-4))
    ax.set_xticks([0, 25, 50, 75, 100, 125, 150, 175])
    ax.set_yticks([0, 0.6e-4, 1.2e-4, 1.8e-4])
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((-4, -4))
    ax.yaxis.set_major_formatter(formatter)
    ax.grid(color="#DDDDDD", linewidth=0.45)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", bbox_to_anchor=(1, 1.03), borderaxespad=0,
              fontsize=7.6, frameon=False, handlelength=2.3)
    fig.text(0.075, 0.95, "(a)  Sampling locations", fontsize=9.5, fontweight="bold", va="top")
    fig.text(0.535, 0.95, "(b)  Height profiles (P)", fontsize=9.5, fontweight="bold", va="top")
    footer(fig, r"$y=120$ nm; along-groove drive $+y$")
    return save(fig, out, "Fig3_velocity_profiles", {
        "quantity": "Signed along-groove component u_y (m/s), not speed magnitude",
        "profiles": validation["profiles"],
        "selection": "vtkValidPointMask=1, material approximately 1 (atol 1e-6), finite velocities",
        "excluded_rows": "NaN gaps retained, no wall-zero replacement, no smoothing or new samples",
        "no_independent_samples_claim": "1001 line-probe rows are interpolated samples, not mesh nodes or statistical replicates",
        "validation": "User CSV reprobed against original P velocity; maximum absolute difference 0",
    })


def dissipation_figure(out, metadata):
    fig = plt.figure(figsize=(140 * MM, 100 * MM), dpi=DPI, facecolor="white")
    h = 0.64 * 140 / 100 * 175 / 240
    ax = fig.add_axes([0.105, 0.20, 0.64, h])
    ax.imshow(np.asarray(Image.open(HERE / "rendered/T_dissipation_XZ.png").convert("RGB")),
              origin="upper", extent=[0, 240, 0, 175], interpolation="none", aspect="equal")
    geometry(ax)
    ax.text(0.5, 1.04, r"Drive: $+x$ $\rightarrow$", ha="center", va="bottom",
             transform=ax.transAxes, fontsize=8)
    fig.text(0.105, 0.955, "Across-groove dissipation (T)", fontsize=9.5,
             fontweight="bold", ha="left", va="top")
    cax = fig.add_axes([0.82, 0.20, 0.025, h])
    sm = matplotlib.cm.ScalarMappable(norm=Normalize(0, 32),
                                     cmap=ListedColormap(metadata["rgb_table"]))
    cb = fig.colorbar(sm, cax=cax, ticks=[0, 8, 16, 24, 32])
    cb.set_label(r"Dissipation, $\varepsilon$ (m$^2$ s$^{-3}$)", labelpad=5)
    cb.outline.set_linewidth(0.65)
    footer(fig, r"$y=120$ nm")
    return save(fig, out, "Fig4_dissipation_XZ", {
        "quantity": "Mass-specific dissipation in original m2/s3 units, not W/m3 or total power",
        "color": "Viridis, linear 0..32, fixed; no logarithm or per-panel normalization",
        "method": metadata["method"],
        "change_from_GUI_draft": metadata["contrast_to_user_draft"],
        "render_manifest": str(HERE / "rendered/render_manifest.json"),
        "render_manifest_sha256": sha(HERE / "rendered/render_manifest.json"),
        "no_physical_mechanism_validation": True,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "figures")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists():
        raise RuntimeError("Use a new output directory; previous versions are preserved.")
    out.mkdir(parents=True)
    speed = json.loads((PRIOR / "render_manifest.json").read_text())
    epsilon = json.loads((HERE / "rendered/render_manifest.json").read_text())
    profiles = json.loads((HERE / "profile_validation.json").read_text())
    for entry in epsilon["original_inputs_and_evidence"] + epsilon["user_reference_files"]:
        assert sha(entry["path"]) == entry["sha256"]
    style = {
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.labelsize": 9,
        "axes.titlesize": 9.5, "axes.linewidth": 0.65, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "legend.fontsize": 8, "savefig.bbox": None,
        "pdf.fonttype": 42, "svg.fonttype": "none", "mathtext.fontset": "dejavusans",
        "xtick.direction": "out", "ytick.direction": "out",
    }
    with style_context("default", palette_name="okabe_ito_on_white"), plt.rc_context(style):
        records = [speed_figure(out, speed, "XY"), speed_figure(out, speed, "XZ"),
                   profile_figure(out, profiles), dissipation_figure(out, epsilon)]
    manifest = {
        "figures": records, "layout_script_sha256": sha(__file__),
        "export_helper_sha256": sha(SKILL / "scripts/figure_export.py"),
        "style_helper_sha256": sha(SKILL / "scripts/style_presets.py"),
        "matplotlib_version": matplotlib.__version__, "dpi": DPI,
        "font": "DejaVu Sans, 8.5 pt base; axes 9 pt; titles 9.5 pt",
        "physical_size_mm": {"Fig1": [180, 95], "Fig2": [180, 85], "Fig3": [180, 95], "Fig4": [140, 100]},
        "color_note": "Same quantitative units/norms across speed panels, separate epsilon norm; original native field render pixels not recolored",
        "journal_specific_compliance": "Pending destination and final-width selection",
        "manual_visual_QA": "Pending actual-image review; recorded separately after inspection",
        "new_OpenLB_runs": False,
    }
    assert all(sha(e["path"]) == e["sha256"] for e in
               epsilon["original_inputs_and_evidence"] + epsilon["user_reference_files"])
    manifest["source_hashes_unchanged"] = True
    (out / "layout_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output_dir": str(out), "figures": 4,
                      "formats": ["PNG", "PDF", "SVG"], "text_bounds": "checked",
                      "source_hashes_unchanged": True}))


if __name__ == "__main__":
    main()
