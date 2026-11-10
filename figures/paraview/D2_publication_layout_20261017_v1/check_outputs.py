#!/usr/bin/env python3
"""Check unchanged inputs, native/assembled field colors, metadata and PDF fonts."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FINAL = HERE / "figures_v2"
PRIOR = ROOT / "figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/rendered_v4"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xml_values(path, name):
    return np.fromstring(ET.parse(path).find(".//CellData/DataArray[@Name='" + name + "']").text, sep=" ")


def preview(images, output):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5), dpi=180, layout="constrained")
    for i, (ax, image) in enumerate(zip(axes.ravel(), images)):
        ax.imshow(np.asarray(Image.open(image)), interpolation="none")
        ax.set_axis_off()
        ax.set_title("Figure " + str(i + 1), fontsize=10, loc="left")
    fig.savefig(output, facecolor="white", transparent=False)
    plt.close(fig)


eps = json.loads((HERE / "rendered/render_manifest.json").read_text())
speed = json.loads((PRIOR / "render_manifest.json").read_text())
layout = json.loads((FINAL / "layout_manifest.json").read_text())
qa = {"scope": "Final figure checks; no new numerical or physical Gate release",
      "final_directory": str(FINAL), "files": [], "pixel_checks": [],
      "earlier_layout": "figures/ retained; Fig3 legend was near a curve. Final figures_v2 relocates it above axes.",
      "script_sha256": sha(__file__), "source_hashes_unchanged": False}

# Original 5 nm sample-center colors must survive native rendering and final placement.
for figure_number, plane in [(1, "XY"), (2, "XZ"), (4, "XZ")]:
    tags = ("P", "T") if figure_number < 4 else ("T",)
    item = next(r for r in layout["figures"] if r["stem"].startswith("Fig" + str(figure_number) + "_"))
    output_png = FINAL / (item["stem"] + ".png")
    assembled = np.asarray(Image.open(output_png).convert("RGB"))
    for k, tag in enumerate(tags):
        nx, ny = 48, 48 if plane == "XY" else 35
        if figure_number == 4:
            raw_path = HERE / "rendered/T_dissipation_XZ.png"
            vti_path = HERE / "rendered/T_XZ_sample_footprints.vti"
            expected = np.array(eps["expected_grid_center_rgb"]).reshape(ny, nx, 3)
        else:
            raw_path = PRIOR / (tag + "_" + plane + ".png")
            vti_path = PRIOR / (tag + "_" + plane + "_sample_footprints.vti")
            values = xml_values(vti_path, "speed_m_s").reshape(ny, nx)
            table = np.rint(np.array(speed["color"]["rgb_table"]) * 255).astype(int)
            idx = np.clip((values / 1.8e-4 * 256).astype(int), 0, 255)
            expected = table[idx]
        mat = xml_values(vti_path, "material").astype(int).reshape(ny, nx)
        expected[mat == 3] = [214, 217, 219]
        raw = np.asarray(Image.open(raw_path).convert("RGB"))
        ys = ((ny - np.arange(ny) - 0.5) * raw.shape[0] / ny).astype(int)
        xs = ((np.arange(nx) + 0.5) * raw.shape[1] / nx).astype(int)
        raw_samples = raw[ys[:, None], xs[None, :]].astype(int)
        raw_error = abs(raw_samples - expected).max()
        assert raw_error == 0, (raw_path, raw_error)
        x0, y0, w, h = item["axes_boxes"][k]
        yy = ((1 - (y0 + h * (np.arange(ny) + 0.5) / ny)) * assembled.shape[0]).astype(int)
        xx = ((x0 + w * (np.arange(nx) + 0.5) / nx) * assembled.shape[1]).astype(int)
        placed = assembled[yy[:, None], xx[None, :]].astype(int)
        placed_error = abs(placed[mat == 1] - expected[mat == 1]).max()
        assert placed_error == 0, (output_png, tag, placed_error)
        qa["pixel_checks"].append({"figure": figure_number, "tag": tag,
                                   "native_all_material_center_max_8bit_error": int(raw_error),
                                   "final_liquid_center_max_8bit_error": int(placed_error),
                                   "liquid_samples": int((mat == 1).sum())})

pdf_dir = HERE / "pdf_previews"
pdf_dir.mkdir(exist_ok=True)
stems = [v["stem"] for v in layout["figures"]]
for stem in stems:
    png, pdf, svg = [FINAL / (stem + "." + ext) for ext in ("png", "pdf", "svg")]
    with Image.open(png) as image:
        alpha = image.getchannel("A").getextrema() if "A" in image.getbands() else (255, 255)
        assert alpha == (255, 255)
        raster = {"size": list(image.size), "mode": image.mode, "dpi": image.info.get("dpi"),
                  "alpha_extrema": list(alpha)}
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True).stdout
    fonts = subprocess.run(["pdffonts", str(pdf)], check=True, capture_output=True, text=True).stdout
    for line in fonts.splitlines()[2:]:
        assert " yes " in line and "DejaVu" in line, line
    tree = ET.parse(svg)
    svg_texts = tree.findall(".//{http://www.w3.org/2000/svg}text")
    assert svg_texts, "SVG lost editable text"
    prefix = pdf_dir / stem
    subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-scale-to", "1600", "-png",
                    str(pdf), str(prefix)], check=True, capture_output=True)
    qa["files"].append({"stem": stem, "raster": raster, "pdfinfo": info,
                        "pdffonts": fonts, "editable_svg_text_elements": len(svg_texts),
                        "sha256": {ext: sha(FINAL / (stem + "." + ext)) for ext in ("png", "pdf", "svg")}})

preview([FINAL / (stem + ".png") for stem in stems], HERE / "PREVIEW.png")
preview([pdf_dir / (stem + ".png") for stem in stems], HERE / "PDF_PREVIEW.png")
with Image.open(HERE / "PREVIEW.png") as image:
    image.convert("L").save(HERE / "GRAYSCALE_PREVIEW.png")

table = np.array(eps["rgb_table"])
linear = np.where(table <= 0.04045, table / 12.92, ((table + 0.055) / 1.055) ** 2.4)
luminance = linear @ np.array([0.2126, 0.7152, 0.0722])
delta = np.diff(luminance)
qa["palette_screen"] = {
    "quantized_Viridis_negative_luminance_steps": int((delta < 0).sum()),
    "minimum_step": float(delta.min()),
    "curve_blue_white_contrast": 5.185, "curve_orange_white_contrast": 3.867,
    "curve_pair_grayscale_delta_Lstar": 8.214,
    "qualifications": "Curve colors also use solid/dashed styles and labels. A named palette, contrast ratio or grayscale preview is not complete accessibility certification; tiny quantized-table reversals are retained.",
}
for entry in eps["original_inputs_and_evidence"] + eps["user_reference_files"]:
    assert sha(entry["path"]) == entry["sha256"], entry["path"]
qa["source_hashes_unchanged"] = True
qa["automated_checks"] = "Completed; all explicit assertions passed"
qa["manual_visual_review"] = "Pending assistant inspection of final PNGs and PDF preview; recorded separately"
qa["journal_compliance"] = "Not asserted; exact destination/phase and human author approval pending"
(HERE / "QA_RECORD.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"figures": len(stems), "pixel_checks": qa["pixel_checks"],
                  "source_hashes_unchanged": True, "pdf_previews_created": True}))
