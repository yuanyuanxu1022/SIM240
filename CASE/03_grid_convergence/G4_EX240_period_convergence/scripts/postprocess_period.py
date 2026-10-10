#!/usr/bin/env python3
"""G4 level postprocess: re-verify frozen gates, level linearity, E ratios.

Usage: postprocess_period.py BATCH_DIR
Reads the 6 steady run directories, re-checks the 10 frozen gates from
result.txt / boundary_audit.txt / exit_code.txt / diagnostics.csv, fits the
3-force linearity per direction, and computes E(2Nx,Nx) against the previous
level (Nx=1 baseline from the SHA-frozen G2 evidence in REUSE_AUDIT.md).
"""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
TAGS = ("a5e4", "a1e5", "a2e5")
DIRECTIONS = ("P", "T")
ACCELERATIONS = {"a5e4": 5.0e4, "a1e5": 1.0e5, "a2e5": 2.0e5}

G2_RESULTS = (CASE_ROOT / "../../02_geometry_transport/G2_EX240_single_period_transport/"
              "results/g2_ex240_20260917T105523+0800").resolve()
G2_SHA = {"P": "5a6d580631974e22b899e696421dd14ad7abdf21295439559a8c253e629708e5",
          "T": "74aa68823379a9533846aa5ebb8f665b90c82c134e865c964b78aac39ac162d9"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_kv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def baseline_r(direction: str) -> float:
    """Nx=1 frozen R from the SHA-pinned G2 evidence (REUSE_AUDIT.md)."""
    result = G2_RESULTS / f"G2-{direction}" / "steady" / "result.txt"
    if sha256(result) != G2_SHA[direction]:
        raise SystemExit(f"G2 baseline SHA mismatch: {result}")
    values = parse_kv(result)
    return float(values["R_eff_Pa_s_per_m3"])


def check_gates(result: dict[str, str], nx: int, exit_code: int) -> list[str]:
    problems: list[str] = []
    expect_nodes = 460800 * nx

    def num(key: str) -> float:
        return float(result[key])

    def flag(name: str, bad: bool) -> None:
        if bad:
            problems.append(name)

    flag("PASS", result.get("PASS") != "true")
    flag("exit_code", exit_code != 0)
    flag("fluid_nodes", int(result.get("fluid_nodes", "-1")) != expect_nodes)
    flag("candidate==installed",
         int(result.get("candidate_links", "-1")) != int(result.get("installed_links", "-2")))
    flag("fallback=0", num("fallback_count") != 0.0)
    flag("unresolved=0", num("unresolved_links") != 0.0)
    flag("q=0.5", abs(num("q_min") - 0.5) > 1e-10 or abs(num("q_max") - 0.5) > 1e-10)
    flag("mass<=1e-10", num("max_mass_abs_relative") >= 1e-10)
    flag("density<=1e-6", num("max_density_deviation") > 1e-6)
    flag("Mach<0.05", num("max_Mach") >= 0.05)
    flag("section<=1e-5", num("section_relative_difference") > 1e-5)
    flag("cross<=1e-12", num("window_cross_abs_max") > 1e-12)
    flag("window std/span",
         num("window_main_rel_std") > 1e-6 or num("window_main_rel_span") > 5e-6)
    flag("material unchanged", result.get("material_unchanged") != "true")
    flag("finite", result.get("finite") != "true")
    return problems


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_period.py BATCH_DIR")
    batch = Path(sys.argv[1]).resolve()
    level = int(batch.name.split("_")[2].lstrip("nx"))
    runs_root = batch / "runs"

    rows: list[dict] = []
    gate_ok = True
    for tag in TAGS:
        for direction in DIRECTIONS:
            steady = runs_root / f"nx{level}_{direction}_{tag}" / "steady"
            if not steady.exists():
                print(f"MISSING run: {steady}")
                gate_ok = False
                continue
            exit_code = int((steady / "exit_code.txt").read_text().strip())
            values = parse_kv(steady / "result.txt")
            problems = check_gates(values, level, exit_code)
            if problems:
                gate_ok = False
                print(f"GATE FAIL nx{level}_{direction}_{tag}: {problems}")
            rows.append({
                "nx": level, "direction": direction, "tag": tag,
                "a": ACCELERATIONS[tag], "J": float(values.get("J_main_m2_s", "nan")),
                "K": float(values.get("Keff_m3", "nan")),
                "R": float(values.get("R_eff_Pa_s_per_m3", "nan")),
                "steps": int(values.get("steps_completed", "-1")),
                "gates_pass": not problems,
            })

    summary = batch / "postprocess_summary.csv"
    with summary.open("w") as fh:
        fh.write("nx,direction,acceleration,J,K,R,steps,gates_pass\n")
        for row in rows:
            fh.write(f"{row['nx']},{row['direction']},{row['a']:.6g},"
                     f"{row['J']:.17g},{row['K']:.17g},{row['R']:.17g},"
                     f"{row['steps']},{row['gates_pass']}\n")

    # per-level linearity (3 forces per direction)
    linearity = batch / "linearity.csv"
    with linearity.open("w") as fh:
        fh.write("direction,slope,intercept,R2,K_max_relative_spread\n")
        for direction in DIRECTIONS:
            pts = [(r["a"], r["J"], r["K"]) for r in rows if r["direction"] == direction]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            n = len(xs)
            mean_x = sum(xs) / n
            mean_y = sum(ys) / n
            slope = (sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
                     / sum((x - mean_x) ** 2 for x in xs))
            intercept = mean_y - slope * mean_x
            residual = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
            total = sum((y - mean_y) ** 2 for y in ys)
            r2 = 1.0 - residual / total if total > 0 else float("nan")
            ks = [p[2] for p in pts]
            k_span = (max(ks) - min(ks)) / (max(ks) + min(ks))
            fh.write(f"{direction},{slope:.17g},{intercept:.17g},"
                     f"{r2:.17g},{k_span:.17g}\n")
            if r2 < 0.9999 or k_span > 0.01:
                gate_ok = False
                print(f"LINEARITY FAIL {direction}: R2={r2}, K_span={k_span}")

    # E ratios against previous level (baseline for level 2)
    eratios = batch / "E_ratios.csv"
    with eratios.open("w") as fh:
        fh.write("pair,direction,R_prev,R_curr,E_relative\n")
        for direction in DIRECTIONS:
            curr = [r for r in rows if r["direction"] == direction and r["tag"] == "a1e5"][0]
            if level == 2:
                prev_r = baseline_r(direction)
                prev_source = f"G2 frozen (sha {G2_SHA[direction][:12]})"
            else:
                prev_batches = sorted((CASE_ROOT / "results").glob(
                    f"g4_period_nx{level // 2}_*/postprocess_summary.csv"))
                if not prev_batches:
                    raise SystemExit("previous level summary missing")
                prev_file = prev_batches[-1]
                prev_rows = {}
                for line in prev_file.read_text().splitlines()[1:]:
                    parts = line.split(",")
                    prev_rows[(parts[1], parts[2])] = float(parts[5])
                prev_r = prev_rows[(direction, "1e+05")]
                prev_source = prev_file.name
            err = abs(curr["R"] - prev_r) / prev_r
            fh.write(f"{level//2}->{level},{direction},{prev_r:.17g},"
                     f"{curr['R']:.17g},{err:.17g}\n")
            verdict = "PASS" if err <= 0.01 else "OVER 1%"
            print(f"E({level//2}->{level}) {direction}: {err:.6g} "
                  f"({verdict}; prev={prev_source})")

    report = batch / "G4_LEVEL_REPORT.md"
    report.write_text(
        f"# G4 level Nx={level} postprocess\n\n"
        f"- batch: {batch.name}\n"
        f"- gates: {'ALL PASS' if gate_ok else 'FAIL — see errors above'}\n"
        f"- linearity: see {linearity.name} (R2>=0.9999, K span<=1%)\n"
        f"- E ratios: see {eratios.name} (threshold 1%, a=1e5)\n"
        f"- summary: {summary.name}\n\n"
        "Evidence boundary: numerical invariance / seam integrity only; "
        "not physical representative-scale convergence.\n")
    print(f"postprocess done: {summary.name}, {linearity.name}, {eratios.name}")
    if not gate_ok:
        raise SystemExit("postprocess FAIL (gates or linearity)")


if __name__ == "__main__":
    main()
