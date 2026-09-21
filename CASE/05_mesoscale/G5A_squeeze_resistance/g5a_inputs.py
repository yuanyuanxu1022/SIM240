from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path

from g5a_solver import SqueezeProblem, smooth_mobility


REQUIRED_COLUMNS = ["height_nm", "R_parallel", "R_perp", "K_parallel", "K_perp", "anisotropy"]
FROZEN_HEIGHTS = (50.0, 75.0, 125.0)


@dataclass(frozen=True)
class ModelConfig:
    source_grid_dx_nm: float
    transport_database: str
    heights_nm: tuple[float, ...]
    problem: SqueezeProblem
    linearity_multipliers: tuple[float, ...]
    thresholds: dict[str, float]


@dataclass(frozen=True)
class CaseDefinition:
    height_nm: float
    model: str
    direction: str
    K_m3: float
    R_input_pa_s_m3: float


def load_config(path: Path) -> ModelConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw["schema_version"] != 1:
        raise ValueError("schema_version must equal 1")
    if float(raw["source_grid_dx_nm"]) != 2.5:
        raise ValueError("source_grid_dx_nm must equal 2.5")
    heights = tuple(float(x) for x in raw["heights_nm"])
    if heights != (50.0, 75.0, 125.0):
        raise ValueError("heights_nm must equal [50.0, 75.0, 125.0]")
    problem = SqueezeProblem(
        float(raw["length_m"]),
        float(raw["width_m"]),
        float(raw["mu_pa_s"]),
        float(raw["vp_m_s"]),
        float(raw["p_out_pa"]),
        int(raw["n_cells"]),
    )
    return ModelConfig(
        source_grid_dx_nm=2.5,
        transport_database=str(raw["transport_database"]),
        heights_nm=heights,
        problem=problem,
        linearity_multipliers=tuple(float(x) for x in raw["linearity_multipliers"]),
        thresholds={str(k): float(v) for k, v in raw["thresholds"].items()},
    )


def _parse_finite(name: str, raw: str) -> float:
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return value


def load_transport_cases(csv_path: Path, config: ModelConfig) -> list[dict[str, float]]:
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
        if missing:
            raise ValueError(f"missing CSV columns: {missing}")
        raw_rows = list(reader)

    rows: list[dict[str, float]] = []
    for raw in raw_rows:
        rows.append({col: _parse_finite(f"{col} in {path.name}", raw[col]) for col in REQUIRED_COLUMNS})

    heights = [row["height_nm"] for row in rows]
    if len(heights) != len(set(heights)):
        raise ValueError("duplicate height_nm rows detected")
    if set(heights) != set(FROZEN_HEIGHTS):
        raise ValueError(f"heights_nm must be exactly {FROZEN_HEIGHTS}, got {sorted(set(heights))}")

    for row in rows:
        for col in ("K_parallel", "K_perp", "R_parallel", "R_perp"):
            if row[col] <= 0.0:
                raise ValueError(f"{col} must be > 0, got {row[col]!r}")

    mu = config.problem.mu_pa_s
    identity_tol = config.thresholds["input_identity_relative"]

    for row in rows:
        for direction in ("parallel", "perp"):
            r_key = f"R_{direction}"
            k_key = f"K_{direction}"
            rel = abs(row[r_key] * row[k_key] / mu - 1.0)
            if rel > identity_tol:
                raise ValueError(
                    f"identity R*K/mu≈1 violated for {row['height_nm']} nm {direction}: "
                    f"{r_key}*{k_key}/mu - 1 = {rel:.3e}"
                )

    for row in rows:
        k_ratio = row["K_parallel"] / row["K_perp"]
        rel = abs(row["anisotropy"] - k_ratio) / abs(k_ratio)
        if rel > identity_tol:
            raise ValueError(
                f"anisotropy mismatch for {row['height_nm']} nm: "
                f"anisotropy={row['anisotropy']!r} vs K_parallel/K_perp={k_ratio!r}"
            )

    return rows


def build_nine_cases(
    config: ModelConfig,
    transport_rows: list[dict[str, float]],
) -> list[CaseDefinition]:
    by_height = {row["height_nm"]: row for row in transport_rows}
    cases: list[CaseDefinition] = []
    for height in config.heights_nm:
        row = by_height[height]
        smooth_k = smooth_mobility(height * 1e-9)
        cases.append(
            CaseDefinition(
                height_nm=height,
                model="smooth",
                direction="isotropic",
                K_m3=smooth_k,
                R_input_pa_s_m3=config.problem.mu_pa_s / smooth_k,
            )
        )
        cases.append(
            CaseDefinition(
                height_nm=height,
                model="ex240",
                direction="parallel",
                K_m3=row["K_parallel"],
                R_input_pa_s_m3=row["R_parallel"],
            )
        )
        cases.append(
            CaseDefinition(
                height_nm=height,
                model="ex240",
                direction="perpendicular",
                K_m3=row["K_perp"],
                R_input_pa_s_m3=row["R_perp"],
            )
        )
    return cases
