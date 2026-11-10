#!/usr/bin/env python3
"""Add calibrated axes, annotations and one shared scale to native ParaView renders."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.ticker import ScalarFormatter
import numpy as np
from PIL import Image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def common_axis(ax, plane):
    ax.set_xlim(0, 240)
    ax.set_ylim(0, 240 if plane == "XY" else 175)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ (nm)")
    ax.set_ylabel("$y$ (nm)" if plane == "XY" else "$z$ (nm)")
    ax.set_xticks([0, 60, 120, 180, 240])
    ax.set_yticks([0, 60, 120, 180, 240] if plane == "XY" else [0, 50, 75, 125, 175])
    ax.tick_params(direction="out", width=0.6, length=3, pad=3)
    if plane == "XY":
        for x in (60, 180):
            ax.axvline(x, color="white", linestyle=(0, (3, 3)), linewidth=0.65, alpha=0.9)
    else:
        ax.plot([0, 60, 60, 180, 180, 240], [75, 75, 175, 175, 75, 75],
                color="#272727", linewidth=0.8)
        ax.text(30, 128, "Solid", ha="center", va="center", color="#404040", fontsize=8)
        ax.text(210, 128, "Solid", ha="center", va="center", color="#404040", fontsize=8)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--render-dir", type=Path, default=Path(__file__).resolve().parent / "rendered")
    p.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "figures")
    args = p.parse_args()
    render = args.render_dir.resolve()
    out = args.output_dir.resolve()
    if out.exists():
        raise RuntimeError("Choose a new figure output directory; existing exports are preserved.")
    out.mkdir(parents=True)
    metadata = json.loads((render / "render_manifest.json").read_text())
    cmap = ListedColormap(metadata["color"]["rgb_table"], name="ParaViewViridis256")
    norm = Normalize(*metadata["color"]["range"])
    style = {
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.labelsize": 9,
        "axes.titlesize": 10, "axes.linewidth": 0.65, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "none", "savefig.bbox": None, "savefig.facecolor": "white",
    }
    exported = []
    with plt.rc_context(style):
        for plane in ("XY", "XZ"):
            fig = plt.figure(figsize=(8, 4), dpi=300, facecolor="white")
            if plane == "XY":
                boxes = [[0.075, 0.16, 0.34, 0.68], [0.49, 0.16, 0.34, 0.68]]
                bar_box = [0.875, 0.16, 0.021, 0.68]
                extent = [0, 240, 0, 240]
            else:
                panel_h = 0.34 * 8 / 4 * 175 / 240
                boxes = [[0.075, 0.24, 0.34, panel_h], [0.49, 0.24, 0.34, panel_h]]
                bar_box = [0.875, 0.24, 0.021, panel_h]
                extent = [0, 240, 0, 175]
            for i, (tag, title) in enumerate((("P", "Along grooves (P)"), ("T", "Across grooves (T)"))):
                ax = fig.add_axes(boxes[i])
                image = np.asarray(Image.open(render / (tag + "_" + plane + ".png")).convert("RGB"))
                ax.imshow(image, origin="upper", extent=extent, interpolation="none", aspect="equal")
                common_axis(ax, plane)
                label = "(a)" if tag == "P" else "(b)"
                fig.text(boxes[i][0], 0.95, label + "  " + title, fontsize=10, fontweight="bold", va="top")
                drive = r"Drive: $+y\ \uparrow$" if plane == "XY" and tag == "P" else r"Drive: $+x\ \rightarrow$"
                if plane == "XZ" and tag == "P":
                    drive = r"Drive: $+y\ \otimes$ (into plane)"
                ax.text(0.5, 1.025, drive, ha="center", va="bottom", transform=ax.transAxes, fontsize=8.5)
            cax = fig.add_axes(bar_box)
            sm = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
            formatter = ScalarFormatter(useMathText=True)
            formatter.set_powerlimits((-4, -4))
            colorbar = fig.colorbar(sm, cax=cax, ticks=[0, 0.6e-4, 1.2e-4, 1.8e-4], format=formatter)
            colorbar.set_label(r"Speed, $|\mathbf{u}|$ (m s$^{-1}$)", labelpad=7)
            colorbar.outline.set_linewidth(0.6)
            colorbar.ax.tick_params(labelsize=8, width=0.6, length=3)
            cut = r"$z=37.5$ nm" if plane == "XY" else r"$y=120$ nm"
            fig.text(0.5, 0.045, r"$h=75$ nm; $d=100$ nm; $\Delta x=5$ nm; " + cut,
                     ha="center", fontsize=8.5)
            stem = "Fig_PT_velocity_" + ("XY_z37p5nm" if plane == "XY" else "XZ_y120nm")
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            canvas_box = fig.bbox
            text_artists = list(fig.texts)
            for axis in fig.axes:
                text_artists.extend(axis.texts)
                text_artists.extend([axis.xaxis.label, axis.yaxis.label,
                                     axis.xaxis.offsetText, axis.yaxis.offsetText])
                text_artists.extend(axis.get_xticklabels() + axis.get_yticklabels())
            for artist in text_artists:
                if not artist.get_visible() or not artist.get_text():
                    continue
                bounds = artist.get_window_extent(renderer)
                if (bounds.x0 < -1 or bounds.y0 < -1 or bounds.x1 > canvas_box.width + 1
                        or bounds.y1 > canvas_box.height + 1):
                    raise RuntimeError("Export text is clipped: " + artist.get_text())
            for extension in ("png", "pdf", "svg"):
                destination = out / (stem + "." + extension)
                fig.savefig(destination, dpi=300, facecolor="white", transparent=False)
                exported.append({"path": str(destination), "sha256": sha(destination)})
            plt.close(fig)
    audit = {
        "formats": ["PNG", "PDF (raster field with vector text)", "SVG (raster field with editable text)"],
        "figure_size_inches": [8, 4], "figure_size_mm": [203.2, 101.6],
        "png_pixels": [2400, 1200], "raster_dpi": 300,
        "shared_range_m_s": metadata["color"]["range"], "shared_palette": "ParaView Viridis 256 RGB samples",
        "no_per_panel_normalization": True,
        "axes_registration": "Raw orthographic cameras exactly span the physical axis extent; only uniform image placement is used.",
        "field_rendering": "ParaView images are composited unchanged, with scientific axes and annotations; no image filtering or color/contrast edits.",
        "reconstruction": metadata["sampling_note"],
        "journal_specific_compliance": "Pending journal/phase selection",
        "manuscript_width_note": "203.2 mm is a working size, not a publisher rule. Inspect font sizes and pixel density at final journal width.",
        "matplotlib_version": matplotlib.__version__,
        "layout_script_sha256": sha(__file__),
        "render_manifest_sha256": sha(render / "render_manifest.json"),
        "outputs": exported,
        "visual_QA": "Pending actual-image review, separate from numerical/source checks.",
    }
    for file in out.glob("*.png"):
        with Image.open(file) as im:
            assert im.size == (2400, 1200)
            audit.setdefault("raster_metadata", []).append({"path": str(file), "size": list(im.size),
                                                           "mode": im.mode, "dpi": list(im.info.get("dpi", []))})
    (out / "figure_manifest.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"output_dir": str(out), "files": len(exported), "status": "exported_QA_pending"}))


if __name__ == "__main__":
    main()

