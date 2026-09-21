from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


CASE_RESULT_FIELDS = [
    "run_id", "height_nm", "model", "direction", "K_m3", "R_input_pa_s_m3",
    "Vp_m_s", "N", "pmax_num_Pa", "pmax_exact_Pa", "pmax_rel_error",
    "Fz_num_N", "Fz_exact_N", "Fz_rel_error",
    "CF_num_N_s_m", "CF_exact_N_s_m", "Qout_m3_s", "Qdisplaced_m3_s",
    "mass_rel_error", "status",
]

PROFILE_FIELDS = ["run_id", "height_nm", "model", "direction", "centers_m", "pressure_pa"]

GATE_ORDER = ["INPUT_GATE", "NUMERICAL_GATE", "ANALYTIC_GATE", "MASS_GATE", "LINEARITY_GATE", "RESULT_PASS"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_case_results(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CASE_RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_profiles(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROFILE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_validation_report(path: Path, gates: dict[str, bool], metadata: dict[str, object]) -> None:
    lines = ["# G5A Validation Report", ""]
    for gate in GATE_ORDER:
        lines.append(f"{gate}: {str(bool(gates.get(gate, False))).lower()}")
    lines += [
        "",
        f"INPUT_CLOSURE_STATUS: {metadata.get('input_closure_status', 'CANDIDATE_FIXED_GRID')}",
        f"SOURCE_GRID_DX_NM: {metadata.get('source_grid_dx_nm', 2.5)}",
        f"G5A_N_CELLS: {metadata.get('n_cells', 401)}",
        "FINAL_GRID_INDEPENDENT_CLOSURE: false",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_pressure_figure(path: Path, profile_rows: list[dict[str, object]]) -> None:
    import itertools

    fig, ax = plt.subplots()
    key = lambda row: (row["model"], row["height_nm"], row["direction"])
    for (model, height_nm, direction), group in itertools.groupby(
        sorted(profile_rows, key=key), key=key
    ):
        rows = list(group)
        ax.plot(
            [row["centers_m"] for row in rows],
            [row["pressure_pa"] for row in rows],
            label=f"{model} {direction} h={height_nm} nm",
        )
    ax.set_xlabel("s (m)")
    ax.set_ylabel("pressure (Pa)")
    ax.legend()
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)


def make_impedance_figure(path: Path, case_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots()
    for model in sorted({row["model"] for row in case_rows}):
        xs = [row["height_nm"] for row in case_rows if row["model"] == model]
        ys = [row["CF_num_N_s_m"] for row in case_rows if row["model"] == model]
        ax.plot(xs, ys, marker="o", label=model)
    ax.set_xlabel("height (nm)")
    ax.set_ylabel("CF (N s / m)")
    ax.legend()
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)


def make_direction_ratio_figure(path: Path, case_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots()
    by_key = {(row["height_nm"], row["direction"]): row for row in case_rows}
    heights = sorted({row["height_nm"] for row in case_rows})
    ratios = [
        float(by_key[(h, "perpendicular")]["CF_num_N_s_m"]) / float(by_key[(h, "parallel")]["CF_num_N_s_m"])
        for h in heights
    ]
    ax.plot(heights, ratios, marker="o")
    ax.set_xlabel("height (nm)")
    ax.set_ylabel("CF_perp / CF_parallel")
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)
