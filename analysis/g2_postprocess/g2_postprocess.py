#!/usr/bin/env python3
"""Generate G2 grid-convergence figures and a Markdown summary."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_BATCH = Path(
    "CASE/03_grid_convergence/G2_EX240_grid_convergence/results/"
    "g2_grid_20260917T165045+0800"
)


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for values in frame.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(str(value) for value in values) + " |")
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    batch = args.batch
    out = args.output or Path("analysis/g2_postprocess/results") / datetime.now().strftime("%Y%m%dT%H%M%S")
    out.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(batch / "g2_grid_summary.csv")
    gci = pd.read_csv(batch / "g2_richardson_gci.csv")
    ex = summary[summary["case"].isin(["EX240_parallel", "EX240_perpendicular"])].copy()
    ex["dx_nm"] = ex["dx"] * 1e9
    wide = ex.pivot(index="dx_nm", columns="direction", values="Keff").sort_index(ascending=False)
    ratio = ex.drop_duplicates("dx_nm").set_index("dx_nm")["anisotropy"].sort_index(ascending=False)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for direction, label, color in (("parallel", "K_parallel", "#2166ac"), ("perpendicular", "K_perpendicular", "#b2182b")):
        ax.plot(wide.index, wide[direction], "o-", label=label, color=color, linewidth=2)
    ax.set_xlabel("Grid spacing dx (nm)")
    ax.set_ylabel("K_eff (m²/(Pa·s))")
    ax.set_title("G2 K convergence")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "G2_K_convergence.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ratio.index, ratio.values, "o-", color="#4d9221", linewidth=2)
    ax.set_xlabel("Grid spacing dx (nm)")
    ax.set_ylabel("Anisotropy K_parallel/K_perpendicular")
    ax.set_title("G2 directional anisotropy")
    fig.tight_layout()
    fig.savefig(out / "G2_anisotropy.png", dpi=300)
    plt.close(fig)

    gci_plot = gci[gci["metric"].isin(["K_parallel", "K_perpendicular", "anisotropy"])].copy()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(gci_plot["metric"], gci_plot["GCI_fine_percent"], color=["#2166ac", "#b2182b", "#4d9221"])
    ax.axhline(2.0, color="black", linestyle="--", linewidth=1, label="2% target")
    ax.set_ylabel("Fine-grid GCI (%)")
    ax.set_title("G2 fine-grid GCI")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "G2_GCI.png", dpi=300)
    plt.close(fig)

    lines = [
        "# G2 自动后处理总结",
        "",
        f"输入批次：`{batch}`",
        "",
        "## K 收敛与方向性",
        "",
        markdown_table(ex[["dx_nm", "direction", "Keff", "anisotropy", "run_gate_PASS"]].sort_values(["dx_nm", "direction"], ascending=[False, True])),
        "",
        "## GCI",
        "",
        markdown_table(gci_plot[["metric", "apparent_order_p", "GCI_fine_percent", "asymptotic_ratio", "mathematical_valid"]]),
        "",
        "## 证据边界",
        "",
        "GCI 图和 K 收敛图由原始 CSV 自动生成。`dx=1.25 nm / EX240_perpendicular` 的质量门禁失败仍保留在输入数据中；该后处理不修改阈值，也不把数学收敛改写为完整 Gate PASS。",
        "",
        "图文件：`G2_K_convergence.png`、`G2_anisotropy.png`、`G2_GCI.png`。",
    ]
    (out / "G2_POSTPROCESS_SUMMARY.md").write_text("\n".join(lines) + "\n")
    print(f"output={out}")


if __name__ == "__main__":
    main()
