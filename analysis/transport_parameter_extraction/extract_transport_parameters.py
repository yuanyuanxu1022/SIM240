#!/usr/bin/env python3
"""Extract reproducible meso-scale transport parameter tables from OpenLB results."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


DEFAULT_ROOT = Path("CASE/03_grid_convergence/G2_EX240_grid_convergence/results")
OUTPUT_DIR = Path("analysis/transport_parameter_extraction")
DATABASE_DIR = OUTPUT_DIR / "transport_database"


def key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def number(values: dict[str, str], key: str, default: float = math.nan) -> float:
    try:
        return float(values[key])
    except (KeyError, TypeError, ValueError):
        return default


def vector(values: dict[str, str], key: str) -> list[float]:
    raw = values.get(key, "")
    try:
        return [float(part) for part in raw.split(",")]
    except ValueError:
        return []


def run_records(root: Path) -> list[tuple[Path, dict[str, str]]]:
    records = []
    for result in sorted(root.rglob("result.txt")):
        values = key_values(result)
        if "Keff_m3" in values and "J_main_m2_s" in values:
            records.append((result.parent, values))
    return records


def metadata(run: Path, values: dict[str, str]) -> dict[str, object]:
    drive = values.get("acceleration_m_s2", "")
    direction = values.get("direction", "")
    case = values.get("case", run.parent.name)
    Lx = number(values, "Lx_m")
    Ly = number(values, "Ly_m")
    drive_axis = Ly if direction == "parallel" else Lx
    area = Lx * Ly if math.isfinite(Lx) and math.isfinite(Ly) else math.nan
    rho = number(values, "rho_phys_kg_m3")
    mu = rho * number(values, "nu_phys_m2_s")
    J = number(values, "J_main_m2_s")
    effective_grad = rho * number(values, "acceleration_m_s2")
    Q_from_J = J * area
    return {
        "run_path": str(run), "case": case, "direction": direction, "dx_m": number(values, "dx_m"),
        "mesa_gap_m": number(values, "mesa_gap_m"), "groove_depth_m": number(values, "groove_depth_m"),
        "groove_width_m": number(values, "groove_width_m"), "Lx_m": Lx, "Ly_m": Ly,
        "rho_kg_m3": rho, "nu_m2_s": number(values, "nu_phys_m2_s"), "mu_Pa_s": mu,
        "acceleration_m_s2": number(values, "acceleration_m_s2"), "drive_axis_length_m": drive_axis,
        "area_plan_m2": area, "J_main_m2_s": J, "Q_from_J_m3_s": Q_from_J,
        "Keff_m3": number(values, "Keff_m3"), "R_eff_Pa_s_per_m3": number(values, "R_eff_Pa_s_per_m3"),
        "mass_error": number(values, "max_mass_abs_relative"), "Mach": number(values, "max_Mach"),
        "PASS": values.get("PASS", ""), "exit_code": values.get("exit_code", ""),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def find_g2_batch(results_root: Path) -> Path | None:
    batches = sorted(
        (p for p in results_root.iterdir() if p.is_dir() and (p / "g2_richardson_gci.csv").exists()),
        key=lambda p: p.name,
    )
    return batches[-1] if batches else None


def discover_latest_results(project_root: Path) -> Path:
    candidates = []
    for result in project_root.glob("CASE/**/results/**/result.txt"):
        values = key_values(result)
        if "Keff_m3" not in values or "J_main_m2_s" not in values:
            continue
        results_dir = next((parent for parent in result.parents if parent.name == "results"), None)
        if results_dir is None:
            continue
        batch = result.parent
        while batch.parent != results_dir and batch.parent != batch:
            batch = batch.parent
        candidates.append((result.stat().st_mtime, results_dir))
    if not candidates:
        raise SystemExit(f"no completed OpenLB results found under {project_root / 'CASE'}")
    return max(candidates, key=lambda item: item[0])[1]


def build_g2_database(meta: list[dict[str, object]], results_root: Path, database_dir: Path) -> None:
    """Pair P/T runs by grid and write the meso-scale G2 database."""
    ex = [row for row in meta if row["direction"] in ("parallel", "perpendicular")]
    grouped: dict[float, dict[str, dict[str, object]]] = {}
    for row in ex:
        grouped.setdefault(float(row["dx_m"]), {})[str(row["direction"])] = row
    batch = find_g2_batch(results_root)
    gci: dict[str, dict[str, str]] = {}
    if batch:
        with (batch / "g2_richardson_gci.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                gci[row["metric"]] = row
    group_name = "G3" if any(str(row["case"]).startswith("G3") for row in ex) else "G2"
    database_dir = database_dir.parent / group_name
    mobility = []
    resistance = []
    for dx_m in sorted(grouped):
        pair = grouped[dx_m]
        if "parallel" not in pair or "perpendicular" not in pair:
            continue
        p = pair["parallel"]
        t = pair["perpendicular"]
        gci_p = gci.get("K_parallel", {})
        gci_t = gci.get("K_perpendicular", {})
        gci_a = gci.get("anisotropy", {})
        common = {
            "case_name": "EX240" if group_name == "G2" else str(p["case"]).rsplit("-", 1)[0], "period_nm": float(p["Lx_m"]) * 1e9,
            "groove_width_nm": float(p["groove_width_m"]) * 1e9,
            "groove_depth_nm": float(p["groove_depth_m"]) * 1e9,
            "gap_height_nm": float(p["mesa_gap_m"]) * 1e9,
            "grid_size_nm": float(p["dx_m"]) * 1e9,
            "K_parallel_m3": p["Keff_m3"], "K_perpendicular_m3": t["Keff_m3"],
            "flux_parallel_m2_s": p["J_main_m2_s"], "flux_perpendicular_m2_s": t["J_main_m2_s"],
            "pressure_gradient_Pa_m": float(p["rho_kg_m3"]) * float(p["acceleration_m_s2"]),
            "energy_dissipation_source": "energy_dissipation.csv profile; no volume integral",
            "anisotropy_ratio": float(p["Keff_m3"]) / float(t["Keff_m3"]),
            "GCI_parallel_percent": gci_p.get("GCI_fine_percent", ""),
            "GCI_perpendicular_percent": gci_t.get("GCI_fine_percent", ""),
            "GCI_anisotropy_percent": gci_a.get("GCI_fine_percent", ""),
            "mass_gate_status": "PASS" if p["PASS"] == "true" and t["PASS"] == "true" else "FAIL",
            "parallel_result_PASS": p["PASS"], "perpendicular_result_PASS": t["PASS"],
            "source_batch": str(batch) if batch else "",
        }
        mobility.append(common)
        resistance.append({
            "case_name": common["case_name"], "grid_size_nm": common["grid_size_nm"], "gap_height_nm": common["gap_height_nm"],
            "R_parallel_Pa_s_per_m3": 1.0 / float(p["Keff_m3"]),
            "R_perpendicular_Pa_s_per_m3": 1.0 / float(t["Keff_m3"]),
            "anisotropy_ratio": common["anisotropy_ratio"], "mass_gate_status": common["mass_gate_status"],
        })
    if not mobility:
        raise SystemExit("no paired EX240 parallel/perpendicular G2 results found")
    database_dir.mkdir(parents=True, exist_ok=True)
    write_csv(database_dir / "mobility.csv", mobility, list(mobility[0]))
    write_csv(database_dir / "resistance.csv", resistance, list(resistance[0]))
    lines = [
        "# G2 介尺度输运数据库总结", "", f"输入结果根目录：`{results_root}`", "",
        "## 几何与输运参数", "", "该数据库将同一 dx 的 Parallel/Perpendicular 结果配对；`R=1/K`，单位为 `Pa·s/m³`。", "",
        "| grid_size_nm | gap_height_nm | K_parallel_m3 | K_perpendicular_m3 | R_parallel | R_perpendicular | anisotropy_ratio | mass_gate_status |", 
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for m, r in zip(mobility, resistance):
        lines.append(f"| {m['grid_size_nm']} | {m['gap_height_nm']} | {m['K_parallel_m3']} | {m['K_perpendicular_m3']} | {r['R_parallel_Pa_s_per_m3']:.8e} | {r['R_perpendicular_Pa_s_per_m3']:.8e} | {m['anisotropy_ratio']:.8f} | {m['mass_gate_status']} |")
    lines += [
        "", "## 已有 OpenLB 输出审计", "", "G2 结果目录中已发现 `result.txt/result_summary.csv`（K_eff、J、几何、质量/Mach/门禁）、`pressure_profile.csv`、`velocity_profile.csv`、`energy_dissipation.csv`、`field_slice.csv` 和 `diagnostics.csv`。压力驱动接口由周期体力 `rho*a` 定义；`energy_dissipation.csv` 是位置剖面，不是全域积分。", 
        "", "## 数值验证", "", "GCI 字段来自原始 `g2_richardson_gci.csv`；质量状态沿用每个 steady 结果的原始 `PASS` 字段，不修改任何门禁。", "",
        "## 填充预测可用性", "", "这些表可作为固定 h、固定 EX240 RVE 的局部 Darcy/迁移率输入。周期体力驱动对应的有效压力梯度仍需在宏观填充模型中明确，不应把周期场的局部 pressure range 直接当作入口-出口压降。", "",
        "## 限制", "", "`dx=1.25 nm / EX240_perpendicular` 的质量门禁异常保留为 FAIL；当前 G2 数据库不等于完整瞬态填充模型，也不包含 H_eff(x,y,t) 或全域耗散积分。",
    ]
    (database_dir / "transport_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_database_index(database_dir: Path) -> None:
    rows = []
    for path in sorted(database_dir.glob("*/mobility.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    if not rows:
        return
    fields = ["case", "geometry", "h", "dx", "K_parallel", "K_perpendicular", "R_parallel", "R_perpendicular", "anisotropy", "GCI", "mass_gate_status", "flux_parallel", "flux_perpendicular", "pressure_gradient", "energy_dissipation"]
    index_rows = []
    for row in rows:
        index_rows.append({
            "case": row.get("case_name", ""), "geometry": "EX240", "h": row.get("gap_height_nm", ""), "dx": row.get("grid_size_nm", ""),
            "K_parallel": row.get("K_parallel_m3", ""), "K_perpendicular": row.get("K_perpendicular_m3", ""),
            "R_parallel": 1.0 / float(row["K_parallel_m3"]), "R_perpendicular": 1.0 / float(row["K_perpendicular_m3"]),
            "anisotropy": row.get("anisotropy_ratio", ""),
            "GCI": f"parallel={row.get('GCI_parallel_percent','')};perpendicular={row.get('GCI_perpendicular_percent','')};anisotropy={row.get('GCI_anisotropy_percent','')}",
            "mass_gate_status": row.get("mass_gate_status", ""), "flux_parallel": row.get("flux_parallel_m2_s", ""), "flux_perpendicular": row.get("flux_perpendicular_m2_s", ""),
            "pressure_gradient": "" if row.get("pressure_gradient_Pa_m", "nan") in ("nan", "NaN") else row.get("pressure_gradient_Pa_m", ""), "energy_dissipation": row.get("energy_dissipation_source", "profile only (see dissipation.csv)"),
        })
    write_csv(database_dir / "transport_database.csv", index_rows, fields)
    reports = database_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report = ["# SIM240 输运数据库自动总结", "", f"数据库目录：`{database_dir}`", "", "## 自动发现与提取", "", f"数据库记录数：{len(index_rows)}", "", "字段包含几何、K、R=1/K、方向比、GCI 和质量门禁状态。pressure_gradient 使用周期体力等效定义；energy_dissipation 当前为剖面数据，不是全域积分。", "", "## 数据边界", "", "原始 OpenLB results 只读；本流程不修改 OpenLB、G2/G3 结果或 PASS/FAIL 逻辑。"]
    (reports / "TRANSPORT_DATABASE_SUMMARY.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--auto-latest", action="store_true", help="discover the newest completed OpenLB results batch")
    parser.add_argument("--database-root", type=Path, default=None)
    args = parser.parse_args()
    if args.auto_latest:
        args.results_root = discover_latest_results(Path.cwd())
    records = run_records(args.results_root)
    if not records:
        raise SystemExit(f"no completed transport result.txt found under {args.results_root}")
    args.output.mkdir(parents=True, exist_ok=True)
    meta = [metadata(run, values) for run, values in records]
    common = list(meta[0])
    write_csv(args.output / "mobility.csv", meta, common)

    resistance = []
    pressure_drop = []
    flow_rate = []
    dissipation = []
    for run, values in records:
        m = metadata(run, values)
        resistance.append({k: m[k] for k in ("run_path", "case", "direction", "dx_m", "Keff_m3", "R_eff_Pa_s_per_m3", "J_main_m2_s", "mu_Pa_s")})
        pressure_range = values.get("pressure_range_Pa", "")
        pmin, pmax = (pressure_range.split(",") + [""])[:2] if pressure_range else ("", "")
        pressure_drop.append({
            "run_path": m["run_path"], "case": m["case"], "direction": m["direction"],
            "p_min_reported_Pa": pmin, "p_max_reported_Pa": pmax,
            "delta_p_range_reported_Pa": number({"x": pmax}, "x") - number({"x": pmin}, "x") if pmin and pmax else math.nan,
            "effective_grad_p_Pa_m": number(values, "rho_phys_kg_m3") * number(values, "acceleration_m_s2"),
            "delta_p_over_period_Pa": number(values, "rho_phys_kg_m3") * number(values, "acceleration_m_s2") * m["drive_axis_length_m"],
            "definition": "effective body-force gradient; pressure range is local periodic-field diagnostic",
        })
        jvec = vector(values, "J_vector_m2_s")
        qsec = vector(values, "Q_sections_m3_s")
        flow_rate.append({
            "run_path": m["run_path"], "case": m["case"], "direction": m["direction"],
            "J_main_m2_s": m["J_main_m2_s"], "Jx_m2_s": jvec[0] if len(jvec) > 0 else math.nan,
            "Jy_m2_s": jvec[1] if len(jvec) > 1 else math.nan, "Jz_m2_s": jvec[2] if len(jvec) > 2 else math.nan,
            "Q_from_J_m3_s": m["Q_from_J_m3_s"], "Q_section1_m3_s": qsec[0] if len(qsec) > 0 else math.nan,
            "Q_section2_m3_s": qsec[1] if len(qsec) > 1 else math.nan,
            "section_relative_difference": number(values, "section_relative_difference"),
        })
        energy = run / "energy_dissipation.csv"
        if energy.exists():
            with energy.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    dissipation.append({"run_path": m["run_path"], "case": m["case"], "direction": m["direction"], "position": row.get("position", ""), "Phi": row.get("Phi", ""), "source": str(energy), "volume_integral_available": "false"})

    write_csv(args.output / "resistance.csv", resistance, list(resistance[0]))
    write_csv(args.output / "pressure_drop.csv", pressure_drop, list(pressure_drop[0]))
    write_csv(args.output / "flow_rate.csv", flow_rate, list(flow_rate[0]))
    write_csv(args.output / "dissipation.csv", dissipation, list(dissipation[0]) if dissipation else ["run_path", "case", "direction", "position", "Phi", "source", "volume_integral_available"])
    build_g2_database(meta, args.results_root, args.output / "transport_database" / "G2")
    build_database_index(args.database_root or args.output / "transport_database")
    print(f"results={len(meta)} output={args.output}")


if __name__ == "__main__":
    main()
