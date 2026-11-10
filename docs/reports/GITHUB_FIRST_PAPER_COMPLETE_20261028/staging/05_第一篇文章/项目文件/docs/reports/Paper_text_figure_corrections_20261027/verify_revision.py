#!/usr/bin/env python3
"""Bounded editorial/export checks; no solver import, fitting or simulation."""
import csv
import difflib
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def main():
    baseline = json.loads((HERE / "input_hashes.json").read_text())
    relative = "docs/reports/SIM240_中文稿_导师审阅版_20261022.md"
    old = (HERE / "before" / relative).read_text()
    new = (ROOT / relative).read_text()
    checks = {}
    checks["all_thirteen_before_snapshots_match"] = all(
        sha(HERE / "before" / name) == digest
        for name, digest in baseline["before_sha256"].items())
    checks["all_display_math_unchanged"] = re.findall(r"\$\$(.*?)\$\$", old, re.S) == re.findall(r"\$\$(.*?)\$\$", new, re.S)
    checks["all_original_table_rows_unchanged"] = [x for x in old.splitlines() if x.startswith("|")] == [x for x in new.splitlines() if x.startswith("|")]
    checks["abstract_and_introduction_unchanged"] = section(old, "## 摘要", "## 2 研究对象") == section(new, "## 摘要", "## 2 研究对象")
    checks["results_discussion_conclusions_references_unchanged"] = section(old, "## 4 结果", "## 附录 A") == section(new, "## 4 结果", "## 附录 A")
    checks["formula_numbers_unchanged"] = re.findall(r"\\tag\{[^}]+\}", old) == re.findall(r"\\tag\{[^}]+\}", new)
    checks["numeric_reference_scope_preserved"] = all(x in new for x in (
        "以5 nm离散数值结果为参考", "历史细跨槽运行的质量 FAIL 仍保留",
        "不能给出整个参数范围的误差上界", "同几何的独立求解器对照"))
    checks["verification_and_validation_distinguished"] = all(x in new for x in (
        "独立求解器对照属于数值交叉核验，不能单独建立物理验证",
        "尚未与目标物理系统的实验测量等证据作比较"))
    checks["appendix_table_links_corrected"] = "表 5 的 6 个倍率、表 6 的 4 个误差端点" in new
    checks["figure_captions_define_scope_and_scales"] = all(x in new for x in (
        "该范围不包含未计算几何", "局部立方律见式（3），误差定义见式（4）",
        "两面板纵轴均为对数且范围不同", "颜色深浅不能跨面板直接比较"))
    for name, a, b in (
        ("figures/paper/make_fig4.py", "over the whole range of $d$", "over the sampled depths"),
        ("figures/paper/make_fig7_fig8.py", "error of Eqs. (1)  (%)", "local cubic-law error  (%)"),
    ):
        before = (HERE / "before" / name).read_text()
        after = (ROOT / name).read_text()
        checks[f"only_label_changed_in_{Path(name).name}"] = before.count(a) == 1 and before.replace(a, b) == after
    render = json.loads((HERE / "render_comparison.json").read_text())
    checks["plot_values_axes_scales_styles_identical"] = render["plotted_values_axes_scales_and_line_styles_unchanged"]
    checks["figure8_render_block_not_executed"] = render["figure8_executed"] is False
    metadata = {}
    for stem in ("Fig4_K_and_anisotropy", "Fig7_error_vs_gap"):
        png = ROOT / "figures/paper" / f"{stem}.png"
        with Image.open(png) as im:
            dpi = list(im.info.get("dpi", ()))
            opaque = im.getchannel("A").getextrema() == (255, 255) if "A" in im.getbands() else True
            metadata[stem] = dict(png_pixels=list(im.size), png_dpi=dpi, png_mode=im.mode, opaque=opaque)
            checks[f"{stem}_png_400dpi_opaque"] = len(dpi) == 2 and all(abs(x - 400) < .1 for x in dpi) and opaque
        pdf = ROOT / "figures/paper" / f"{stem}.pdf"
        text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout
        if stem.startswith("Fig4"):
            checks["actual_PDF_sampled_scope_label"] = "over the sampled depths" in text and "whole range" not in text
        else:
            checks["actual_PDF_error_label_both_axes"] = text.count("local cubic-law error") == 2 and "Eqs. (1)" not in text
        metadata[stem]["pdfinfo"] = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True).stdout
        ET.parse(ROOT / "figures/paper" / f"{stem}.svg")
    checks["SVG_outputs_parse"] = True
    checks["six_production_exports_match_reviewed_staging"] = len(render["exports"]) == 6 and all(
        sha(ROOT / "figures/paper" / name) == digest == sha(HERE / "staged" / name)
        for name, digest in render["exports"].items())
    source_rows = []
    base = ROOT / "CASE/D_series/D2_groove_error_map/results"
    with (base / "summary.csv").open() as f:
        source_rows.extend((int(r["h_nm"]), int(r["d_nm"]), r["direction"], float(r["Keff_m3"]))
                           for r in csv.DictReader(f) if r["dx_nm"] == "5")
    for name in ("d75_summary.csv", "h25_summary.csv", "d120_summary.csv"):
        with (base / name).open() as f:
            source_rows.extend((int(r["h_nm"]), int(r["d_nm"]), r["case_id"].split("-")[1], float(r["Keff_m3"]))
                               for r in csv.DictReader(f))
    source = {(h, d, dr): value for h, d, dr, value in source_rows}
    raw = {}
    with (ROOT / "docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv").open() as f:
        for row in csv.DictReader(f):
            if row["group"] != "main":
                continue
            data = dict(line.split("=", 1) for line in (ROOT / row["result_path"]).read_text().splitlines() if "=" in line)
            raw[int(row["h_nm"]), int(row["d_nm"]), "P" if row["direction"] == "parallel" else "T"] = float(data["Keff_m3"])
    checks["36_source_values_equal_raw_results_no_duplicates"] = len(source_rows) == len(source) == len(raw) == 36 and source == raw
    checks["thin_gap_uncomputed_points_stay_absent"] = all((25, d, dr) not in source for d in (75, 120) for dr in ("P", "T"))
    changed_protected = [name for name, digest in baseline["protected_sha256"].items() if sha(ROOT / name) != digest]
    checks["all_selected_protected_sources_unchanged"] = not changed_protected
    qa = json.loads((HERE / "visual_QA.json").read_text())
    checks["PNG_and_actual_PDF_previews_visually_checked"] = qa["assistant_visual_review_complete"] is True and qa["accountable_author_final_review"] == "PENDING"
    new_text = new
    broken = []
    manuscript = ROOT / relative
    for target in re.findall(r"\]\(([^)]+)\)", new_text):
        if target.startswith(("https:", "http:", "#")):
            continue
        path = target.split("#", 1)[0]
        if not (Path(path) if path.startswith("/") else manuscript.parent / path).exists():
            broken.append(target)
    checks["manuscript_local_links_resolve"] = not broken
    for name in ("docs/reports/SIM240_AI_CONTEXT.md", "docs/reports/AI_HANDOFF_20261015.md"):
        before = (HERE / "before" / name).read_text()
        after = (ROOT / name).read_text()
        checks[f"previous_state_body_preserved_{Path(name).name}"] = after.endswith(before.split("\n", 1)[1])
        checks[f"handoff_scope_recorded_{Path(name).name}"] = "Paper_text_figure_corrections_20261027/REVISION_NOTE.md" in after and "本轮未提交或推送" in after
    diffs = []
    for name in baseline["modified_allowlist"]:
        if Path(name).suffix not in {".md", ".py"}:
            continue
        a = (HERE / "before" / name).read_text()
        b = (ROOT / name).read_text()
        diffs.extend(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile=f"before/{name}", tofile=name))
    (HERE / "changes.diff").write_text("".join(diffs))
    result = dict(date_Asia_Shanghai="2026-10-27", scope="editorial and selected-figure verification only",
                  checks=checks, check_count=len(checks), all_checks_pass=all(checks.values()),
                  protected_input_count=len(baseline["protected_sha256"]), changed_protected_inputs=changed_protected,
                  broken_links=broken, figure_metadata=metadata,
                  after_sha256={name: sha(ROOT / name) for name in baseline["modified_allowlist"]},
                  source_run_id="D4_N8_diag_v3_1_20261026_v1", new_solver_run_id=None,
                  real_N8_extraction_executed=False, solver_started=False,
                  final_theoretical_freeze=False, strict_error_bound_established=False,
                  submission_ready=False, Git_commit_or_push=False,
                  limitation="Not a new numerical/physical Gate, full scientific review, journal compliance check or author final approval.")
    (HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("check_count", "all_checks_pass", "protected_input_count", "changed_protected_inputs", "broken_links")}, ensure_ascii=False))
    if not result["all_checks_pass"]:
        print(json.dumps({k: v for k, v in checks.items() if not v}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
