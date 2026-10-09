#!/usr/bin/env python3
"""Extract R(h)=Delta-p/Q from completed G3-h steady results."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt


CASE_ROOT = Path("CASE/04_parameter_study/G3_EX240_height_sweep")
DEFAULT_RESULTS = CASE_ROOT / "results"
DEFAULT_OUTPUT = Path("transport_database")


def key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def number(values: dict[str, str], key: str, default: float = float("nan")) -> float:
    try:
        return float(values[key])
    except (KeyError, TypeError, ValueError):
        return default


def height_from(case: str, values: dict[str, str]) -> float:
    match = re.search(r"[Hh](\d+(?:\.\d+)?)", case)
    if match:
        return float(match.group(1))
    gap = number(values, "mesa_gap_m")
    if gap == gap:
        return gap * 1.0e9
    raise ValueError(f"cannot determine height for {case}")


def profile_mean(path: Path) -> float:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    values = [float(row["Phi"]) for row in rows if row.get("Phi", "")]
    if not values:
        return float("nan")
    return sum(values) / len(values)


def canonical_resistance(
    values: dict[str, str], pressure_drop: float, flow_rate: float
) -> float:
    """Use the solver's Keff-consistent resistance, with Delta-p/Q fallback."""
    resistance = number(values, "R_eff_Pa_s_per_m3")
    if resistance == resistance:
        return resistance
    if pressure_drop == pressure_drop and flow_rate == flow_rate:
        return pressure_drop / flow_rate
    return float("nan")


def extract(results_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for summary_path in sorted(results_root.rglob("result_summary.csv")):
        result_dir = summary_path.parent
        result_rows = list(csv.DictReader(summary_path.open(newline="")))
        result_txt = result_dir / "result.txt"
        if not result_rows or not result_txt.exists():
            continue
        values = key_values(result_txt)
        row = result_rows[0]
        case = row.get("Case", values.get("case", result_dir.name))
        direction = row.get("direction", values.get("direction", ""))
        height_nm = height_from(case, values)
        lx = number(values, "Lx_m")
        ly = number(values, "Ly_m")
        rho = number(values, "rho_phys_kg_m3", 1000.0)
        acceleration = number(values, "acceleration_m_s2", 1.0e5)
        drive_length = ly if direction == "parallel" else lx
        pressure_drop = number(values, "deltaP_effective_Pa")
        if pressure_drop != pressure_drop:
            pressure_drop = rho * acceleration * drive_length

        q_values = [float(x) for x in values.get("Q_sections_m3_s", "").split(",") if x]
        flow_rate = sum(q_values) / len(q_values) if q_values else float("nan")
        resistance = canonical_resistance(values, pressure_drop, flow_rate)
        if flow_rate != flow_rate and resistance == resistance:
            flow_rate = pressure_drop / resistance

        dissipation_path = result_dir / "energy_dissipation.csv"
        rows.append({
            "case": case,
            "height_nm": height_nm,
            "direction": direction,
            "pressure_drop_Pa": pressure_drop,
            "flow_rate_m3_s": flow_rate,
            "resistance_Pa_s_per_m3": resistance,
            "mobility_m3": float(row.get("Keff", "nan")),
            "energy_dissipation": profile_mean(dissipation_path) if dissipation_path.exists() else float("nan"),
            "mass_error": float(row.get("mass_error", "nan")),
            "Mach": float(row.get("Mach", "nan")),
            "PASS": values.get("PASS", ""),
            "converged": values.get("converged", ""),
            "exit_code": values.get("exit_code", ""),
            "source_result": str(result_dir),
        })
    return sorted(rows, key=lambda r: (float(r["height_nm"]), str(r["direction"])))


def pair_by_height(rows: list[dict[str, object]]) -> list[dict[str, float]]:
    """Pair principal directions at each height and derive anisotropy."""
    grouped: dict[float, dict[str, dict[str, object]]] = {}
    for row in rows:
        height_nm = float(row["height_nm"])
        direction = str(row["direction"])
        if direction not in ("parallel", "perpendicular"):
            raise ValueError(f"unsupported direction at h={height_nm:g} nm: {direction}")
        if direction in grouped.setdefault(height_nm, {}):
            raise ValueError(f"duplicate {direction} result at h={height_nm:g} nm")
        grouped[height_nm][direction] = row

    paired: list[dict[str, float]] = []
    for height_nm, directions in sorted(grouped.items()):
        for direction in ("parallel", "perpendicular"):
            if direction not in directions:
                raise ValueError(f"missing {direction} result at h={height_nm:g} nm")
        parallel = directions["parallel"]
        perpendicular = directions["perpendicular"]
        k_parallel = float(parallel["mobility_m3"])
        k_perp = float(perpendicular["mobility_m3"])
        if k_perp <= 0.0:
            raise ValueError(f"non-positive K_perp at h={height_nm:g} nm")
        paired.append({
            "height_nm": height_nm,
            "R_parallel": float(parallel["resistance_Pa_s_per_m3"]),
            "R_perp": float(perpendicular["resistance_Pa_s_per_m3"]),
            "K_parallel": k_parallel,
            "K_perp": k_perp,
            "anisotropy": k_parallel / k_perp,
        })
    return paired


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = ["height_nm", "R_parallel", "R_perp", "K_parallel", "K_perp", "anisotropy"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plot(rows: list[dict[str, object]], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    ax.plot([r["height_nm"] for r in rows], [r["R_parallel"] for r in rows], "o-", color="#2166ac", label="parallel")
    ax.plot([r["height_nm"] for r in rows], [r["R_perp"] for r in rows], "o-", color="#b2182b", label="perpendicular")
    ax.set_xlabel("Liquid-film height, h (nm)")
    ax.set_ylabel(r"Hydraulic resistance, $R=\Delta p/Q$ (Pa s m$^{-3}$)")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=600)
    plt.close(fig)


def plot_anisotropy(rows: list[dict[str, object]], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    ax.plot(
        [r["height_nm"] for r in rows],
        [r["anisotropy"] for r in rows],
        "o-",
        color="#4d9221",
    )
    ax.set_xlabel(r"Liquid-film height, $h$ (nm)")
    ax.set_ylabel(r"Anisotropy, $A=K_{\parallel}/K_{\perp}$")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=600)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = extract(args.results_root)
    if not rows:
        raise SystemExit(f"no completed G3 steady result_summary.csv found under {args.results_root}")
    paired = pair_by_height(rows)
    args.output_root.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_root / "G3_height_resistance.csv", paired)
    plot(paired, args.output_root / "Figure_R_vs_h.png")
    plot_anisotropy(paired, args.output_root / "Figure_anisotropy_vs_h.png")
    print(f"results={len(rows)} paired_heights={len(paired)} output={args.output_root}")


if __name__ == "__main__":
    main()
