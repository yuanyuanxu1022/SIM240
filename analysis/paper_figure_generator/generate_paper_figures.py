#!/usr/bin/env python3
"""Generate publication figures and captions from SIM240 result tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
G2_DEFAULT = PROJECT / "CASE/03_grid_convergence/G2_EX240_grid_convergence/results"
DB_DEFAULT = PROJECT / "analysis/transport_parameter_extraction/transport_database"


def save_pub(fig, out: Path, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(out / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(out / f"{stem}.pdf", dpi=600, bbox_inches="tight")
    plt.close(fig)


def latest_g2(root: Path) -> Path:
    batches = sorted(p for p in root.iterdir() if p.is_dir() and (p / "g2_grid_summary.csv").exists())
    if not batches:
        raise FileNotFoundError(f"no G2 batch under {root}")
    return batches[-1]


def detect_latest_case() -> str:
    candidates = []
    for result in PROJECT.glob("CASE/**/results/**/result.txt"):
        if "Keff_m3=" not in result.read_text(encoding="utf-8", errors="ignore"):
            continue
        text = str(result)
        label = "G3" if "/G3_" in text or "/G3-h" in text else "G2"
        candidates.append((result.stat().st_mtime, label))
    return max(candidates)[1] if candidates else "G2"


def plot_g2(batch: Path, output: Path) -> tuple[list[str], list[str]]:
    figures = output / "figures"
    summary = pd.read_csv(batch / "g2_grid_summary.csv")
    gci = pd.read_csv(batch / "g2_richardson_gci.csv")
    ex = summary[summary["case"].isin(["EX240_parallel", "EX240_perpendicular"])].copy()
    ex["dx_nm"] = ex["dx"] * 1e9
    captions = []
    discussion = []
    plt.rcParams.update({"font.size": 11, "axes.labelsize": 12, "axes.titlesize": 12, "legend.fontsize": 10})

    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    for direction, label, color in (("parallel", r"$K_{\parallel}$", "#2166ac"), ("perpendicular", r"$K_{\perp}$", "#b2182b")):
        data = ex[ex["direction"] == direction].sort_values("dx_nm")
        ax.plot(data["dx_nm"], data["Keff"], "o-", lw=1.8, label=label, color=color)
    ax.set(xlabel=r"Grid spacing $\Delta x$ (nm)", ylabel=r"$K_{\mathrm{eff}}$ (m$^3$)", title="EX240 mobility grid convergence")
    ax.legend(frameon=False)
    save_pub(fig, figures, "Figure_G2_K_convergence")
    captions.append("Figure G2-1. Grid convergence of the EX240 effective mobilities in the parallel and perpendicular directions.")

    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    eta = ex.drop_duplicates("dx_nm").sort_values("dx_nm")
    ax.plot(eta["dx_nm"], eta["anisotropy"], "o-", lw=1.8, color="#4d9221")
    ax.set(xlabel=r"Grid spacing $\Delta x$ (nm)", ylabel=r"$K_{\parallel}/K_{\perp}$", title="EX240 directional anisotropy")
    save_pub(fig, figures, "Figure_G2_anisotropy")
    captions.append("Figure G2-2. Directional anisotropy ratio of the EX240 effective mobility over the three-grid sequence.")

    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    for direction, label, color in (("parallel", r"$R_{\parallel}=1/K_{\parallel}$", "#2166ac"), ("perpendicular", r"$R_{\perp}=1/K_{\perp}$", "#b2182b")):
        data = ex[ex["direction"] == direction].sort_values("dx_nm")
        ax.plot(data["dx_nm"], 1.0 / data["Keff"], "o-", lw=1.8, label=label, color=color)
    ax.set(xlabel=r"Grid spacing $\Delta x$ (nm)", ylabel=r"$R$ (Pa·s/m$^3$)", title="EX240 hydraulic resistance")
    ax.legend(frameon=False)
    save_pub(fig, figures, "Figure_G2_resistance")
    captions.append("Figure G2-3. Effective hydraulic resistance, calculated as the reciprocal of the corresponding mobility.")

    g = gci[gci["metric"].isin(["K_parallel", "K_perpendicular", "anisotropy"])]
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    labels = [r"$K_{\parallel}$", r"$K_{\perp}$", "anisotropy"]
    ax.bar(labels, g["GCI_fine_percent"], color=["#2166ac", "#b2182b", "#4d9221"])
    ax.axhline(2.0, color="black", ls="--", lw=1, label="2% criterion")
    ax.set(ylabel="Fine-grid GCI (%)", title="EX240 Richardson/GCI uncertainty")
    ax.legend(frameon=False)
    save_pub(fig, figures, "Figure_G2_GCI")
    captions.append("Figure G2-4. Fine-grid GCI estimates for the principal mobilities and anisotropy.")

    p = dict(zip(g["metric"], g["GCI_fine_percent"]))
    discussion.append(f"The three-grid GCI is {p.get('K_parallel', float('nan')):.3g}% for parallel mobility and {p.get('K_perpendicular', float('nan')):.3g}% for perpendicular mobility; the anisotropy GCI is {p.get('anisotropy', float('nan')):.3g}%.")
    discussion.append("The 1.25 nm EX240-perpendicular mass-gate anomaly remains a separate validation limitation and is not reclassified by figure generation.")
    return captions, discussion


def plot_g3(database: Path, output: Path) -> tuple[list[str], list[str]]:
    figures = output / "figures"
    data = pd.read_csv(database / "G3" / "mobility.csv")
    captions, discussion = [], []
    data = data.sort_values("gap_height_nm")
    curves = (("K_parallel_m3", r"$K_{\parallel}$", "Figure_G3_K_parallel_h", "K_parallel-h"), ("K_perpendicular_m3", r"$K_{\perp}$", "Figure_G3_K_perpendicular_h", "K_perpendicular-h"), ("anisotropy_ratio", r"$K_{\parallel}/K_{\perp}$", "Figure_G3_anisotropy_h", "anisotropy-h"))
    for col, ylabel, stem, title in curves:
        fig, ax = plt.subplots(figsize=(6.8, 4.4))
        ax.plot(data["gap_height_nm"], data[col], "o-", lw=1.8)
        ax.set(xlabel=r"Liquid-film height $h$ (nm)", ylabel=ylabel, title=f"EX240 {title}")
        save_pub(fig, figures, stem)
        captions.append(f"Figure {stem}. Height dependence of {ylabel} for EX240.")
    diss = database / "dissipation.csv"
    if diss.exists():
        d = pd.read_csv(diss)
        if "gap_height_nm" in d and "Phi" in d:
            agg = d.groupby("gap_height_nm", as_index=False)["Phi"].mean()
            fig, ax = plt.subplots(figsize=(6.8, 4.4))
            ax.plot(agg["gap_height_nm"], agg["Phi"], "o-", lw=1.8)
            ax.set(xlabel=r"Liquid-film height $h$ (nm)", ylabel=r"Mean $\Phi$", title="EX240 dissipation-h")
            save_pub(fig, figures, "Figure_G3_dissipation_h")
            captions.append("Figure G3-d. Height dependence of the mean dissipation profile value.")
        else:
            discussion.append("Dissipation-h was not plotted because the existing dissipation table has no height key; a height-tagged dissipation export is required.")
    return captions, discussion


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("auto", "G2", "G3"), default="auto")
    parser.add_argument("--results-root", type=Path, default=G2_DEFAULT)
    parser.add_argument("--database-root", type=Path, default=DB_DEFAULT)
    parser.add_argument("--output", type=Path, default=PROJECT / "paper_figures")
    args = parser.parse_args()
    case = args.case
    if case == "auto":
        case = detect_latest_case()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "figures").mkdir(parents=True, exist_ok=True)
    captions, discussion = (plot_g2(latest_g2(args.results_root), args.output) if case == "G2" else plot_g3(args.database_root, args.output))
    (args.output / "figure_captions.md").write_text("# SIM240 论文图注\n\n" + "\n\n".join(f"- {c}" for c in captions) + "\n", encoding="utf-8")
    (args.output / "result_discussion.md").write_text("# SIM240 结果描述\n\n" + "\n\n".join(f"- {d}" for d in discussion) + "\n", encoding="utf-8")
    print(f"case={case} output={args.output} figures={len(captions)}")


if __name__ == "__main__":
    main()
