#!/usr/bin/env python3
"""Post-process G3-h height-sweep mobility results."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def load_input(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    lower = {str(c).lower(): c for c in raw.columns}
    height_col = next((lower[c] for c in ("height_nm", "h_nm", "h") if c in lower), None)
    if height_col is None:
        raise ValueError("input must contain height_nm (or h_nm/h)")
    if {"k_parallel", "k_perpendicular"}.issubset(lower):
        result = raw[[height_col, lower["k_parallel"], lower["k_perpendicular"]]].copy()
        result.columns = ["height_nm", "K_parallel", "K_perpendicular"]
    else:
        direction_col = next((lower[c] for c in ("direction", "dir") if c in lower), None)
        k_col = next((lower[c] for c in ("keff", "k_eff", "k") if c in lower), None)
        if direction_col is None or k_col is None:
            raise ValueError("input must contain K_parallel/K_perpendicular or direction + Keff")
        long = raw[[height_col, direction_col, k_col]].copy()
        long.columns = ["height_nm", "direction", "Keff"]
        long["direction"] = long["direction"].astype(str).str.lower()
        long["direction"] = long["direction"].replace({"p": "parallel", "t": "perpendicular"})
        result = long.pivot_table(index="height_nm", columns="direction", values="Keff", aggfunc="last").reset_index()
        result = result.rename(columns={"parallel": "K_parallel", "perpendicular": "K_perpendicular"})
    missing = {"height_nm", "K_parallel", "K_perpendicular"} - set(result.columns)
    if missing:
        raise ValueError(f"missing direction columns: {sorted(missing)}")
    result = result[["height_nm", "K_parallel", "K_perpendicular"]].sort_values("height_nm")
    result["anisotropy"] = result["K_parallel"] / result["K_perpendicular"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="G3-h CSV input")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    data = load_input(args.input)
    out = args.output or Path("analysis/g3_postprocess/results") / datetime.now().strftime("%Y%m%dT%H%M%S")
    out.mkdir(parents=True, exist_ok=True)

    plt.style.use("seaborn-v0_8-whitegrid")
    curves = (("K_parallel", "K_parallel-h", "#2166ac"), ("K_perpendicular", "K_perpendicular-h", "#b2182b"), ("anisotropy", "anisotropy-h", "#4d9221"))
    for column, title, color in curves:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(data["height_nm"], data[column], "o-", color=color, linewidth=2)
        ax.set_xlabel("Liquid-film height h (nm)")
        ax.set_ylabel(column)
        ax.set_title(f"G3-h {title}")
        fig.tight_layout()
        fig.savefig(out / f"G3_{title.replace('-', '_')}.png", dpi=300)
        plt.close(fig)

    table = data.copy()
    summary = [
        "# G3-h 高度扫描自动后处理总结", "", f"输入文件：`{args.input}`", "",
        "## 高度依赖结果", "", markdown_table(table), "",
        "## 证据边界", "",
        "本模块只对输入 CSV 做绘图和派生量 `anisotropy=K_parallel/K_perpendicular` 计算；不启动 LBM，不修改 OpenLB 或验证门槛。输入数据的 geometry、质量、Mach、收敛和正常退出状态需由 G3-h 运行记录独立证明。",
        "",
        "图文件：`G3_K_parallel_h.png`、`G3_K_perpendicular_h.png`、`G3_anisotropy_h.png`。",
    ]
    (out / "G3_POSTPROCESS_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"output={out}")


if __name__ == "__main__":
    main()
