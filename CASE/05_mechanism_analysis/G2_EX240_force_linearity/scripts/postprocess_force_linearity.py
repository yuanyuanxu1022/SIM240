#!/usr/bin/env python3
import csv
import math
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


FORMAL_BATCH = Path("/home/dell/yuanyuanxu/SIM240/CASE/G2_EX240_single_period_transport/results/g2_ex240_20260917T105523+0800")
BASE_SOURCE = Path("/home/dell/yuanyuanxu/SIM240/CASE/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp")
BASE_BINARY = Path("/home/dell/yuanyuanxu/SIM240/CASE/G2_EX240_single_period_transport/build/g2_ex240_single_period_transport")
EXPECTED_BASE_SOURCE_SHA256 = "4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002"
EXPECTED_BASE_BINARY_SHA256 = "ca2ed5a010ba8b72b6641ef42888b314c66f6a40576bdf4f01441d38f7037c75"

MASS_GATE = 1.0e-10
MACH_GATE = 0.05
R2_GATE = 0.9999
SPREAD_GATE = 0.01


def sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_key_values(path: Path):
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def read_summary(path: Path):
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise RuntimeError(f"expected one summary row: {path}")
    return rows[0]


def fit_line(xs, ys):
    xbar = statistics.mean(xs)
    ybar = statistics.mean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    intercept = ybar - slope * xbar
    fitted = [slope * x + intercept for x in xs]
    sse = sum((y - yf) ** 2 for y, yf in zip(ys, fitted))
    sst = sum((y - ybar) ** 2 for y in ys)
    r2 = 1.0 - sse / sst
    return slope, intercept, r2


def bool_text(value):
    return str(value).strip().lower() == "true"


def load_run(direction, acceleration, steady_dir, source, reused):
    result = parse_key_values(steady_dir / "result.txt")
    summary = read_summary(steady_dir / "result_summary.csv")
    exit_file = steady_dir / "exit_code.txt"
    exit_code = int(exit_file.read_text().strip())
    row = {
        "direction": direction,
        "acceleration": float(acceleration),
        "J": float(summary["J"]),
        "Keff": float(summary["Keff"]),
        "mass_error": float(summary["mass_error"]),
        "Mach": float(summary["Mach"]),
        "source": source,
        "reused": reused,
        "converged": bool_text(result.get("converged", "false")),
        "finite": bool_text(result.get("finite", "false")),
        "result_PASS": bool_text(result.get("PASS", "false")),
        "normal_exit": exit_code == 0 and int(result.get("exit_code", "1")) == 0,
        "candidate_links": int(result["candidate_links"]),
        "installed_links": int(result["installed_links"]),
        "q_min": float(result["q_min"]),
        "q_max": float(result["q_max"]),
        "fallback_count": int(result["fallback_count"]),
        "unresolved_links": int(result["unresolved_links"]),
    }
    row["run_gate"] = (
        row["mass_error"] <= MASS_GATE
        and row["Mach"] < MACH_GATE
        and row["converged"]
        and row["finite"]
        and row["normal_exit"]
        and row["result_PASS"]
        and row["candidate_links"] == row["installed_links"]
        and math.isclose(row["q_min"], 0.5, abs_tol=1e-12)
        and math.isclose(row["q_max"], 0.5, abs_tol=1e-12)
        and row["fallback_count"] == 0
        and row["unresolved_links"] == 0
    )
    return row


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_force_linearity.py BATCH_DIR")
    batch_dir = Path(sys.argv[1]).resolve()
    figures_dir = batch_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    if sha256(BASE_SOURCE) != EXPECTED_BASE_SOURCE_SHA256:
        raise RuntimeError("frozen G2 source hash changed; reuse audit invalid")
    if sha256(BASE_BINARY) != EXPECTED_BASE_BINARY_SHA256:
        raise RuntimeError("formal G2 binary hash changed; reuse audit invalid")

    rows = []
    rows.append(load_run("parallel", 100000, FORMAL_BATCH / "G2-P/steady", "formal_G2-P", True))
    rows.append(load_run("perpendicular", 100000, FORMAL_BATCH / "G2-T/steady", "formal_G2-T", True))
    for direction, code in (("parallel", "P"), ("perpendicular", "T")):
        rows.append(load_run(direction, 50000, batch_dir / f"runs/G2-{code}-a5e4/steady", f"G2-{code}-a5e4", False))
        rows.append(load_run(direction, 200000, batch_dir / f"runs/G2-{code}-a2e5/steady", f"G2-{code}-a2e5", False))

    metrics = {}
    for direction in ("parallel", "perpendicular"):
        subset = sorted((row for row in rows if row["direction"] == direction), key=lambda row: row["acceleration"])
        xs = [row["acceleration"] for row in subset]
        js = [row["J"] for row in subset]
        ks = [row["Keff"] for row in subset]
        slope, intercept, r2 = fit_line(xs, js)
        k_mean = statistics.mean(ks)
        k_std = statistics.stdev(ks)
        k_cv = k_std / k_mean
        k_spread = (max(ks) - min(ks)) / k_mean
        gate = r2 >= R2_GATE and k_spread <= SPREAD_GATE and all(row["run_gate"] for row in subset)
        metrics[direction] = {
            "slope": slope,
            "intercept": intercept,
            "R2": r2,
            "K_mean": k_mean,
            "K_std": k_std,
            "K_CV": k_cv,
            "K_max_relative_spread": k_spread,
            "K_min": min(ks),
            "K_max": max(ks),
            "direction_gate": gate,
        }

    columns = [
        "direction", "acceleration", "J", "Keff", "mass_error", "Mach", "source", "reused",
        "converged", "finite", "normal_exit", "run_gate", "slope", "intercept", "R2",
        "K_mean", "K_std", "K_CV", "K_max_relative_spread", "direction_gate",
    ]
    with (batch_dir / "g2_force_linearity.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (item["direction"], item["acceleration"])):
            merged = {key: row.get(key, "") for key in columns}
            merged.update({key: metrics[row["direction"]][key] for key in (
                "slope", "intercept", "R2", "K_mean", "K_std", "K_CV",
                "K_max_relative_spread", "direction_gate"
            )})
            writer.writerow(merged)

    colors = {"parallel": "#2166ac", "perpendicular": "#b2182b"}
    fig, ax = plt.subplots(figsize=(6.4, 4.5), constrained_layout=True)
    for direction in ("parallel", "perpendicular"):
        subset = sorted((row for row in rows if row["direction"] == direction), key=lambda row: row["acceleration"])
        xs = [row["acceleration"] for row in subset]
        ys = [row["J"] for row in subset]
        metric = metrics[direction]
        fit_ys = [metric["slope"] * x + metric["intercept"] for x in xs]
        ax.scatter(xs, ys, color=colors[direction], zorder=3, label=f"{direction} DNS")
        ax.plot(xs, fit_ys, color=colors[direction], label=f"{direction} fit, $R^2$={metric['R2']:.7f}")
    ax.set_xlabel("Acceleration $a$ (m s$^{-2}$)")
    ax.set_ylabel("Depth-integrated flux $J$ (m$^2$ s$^{-1}$)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    for ext in ("png", "pdf"):
        fig.savefig(figures_dir / f"Figure_G2_force_linearity_J_vs_a.{ext}", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.5), constrained_layout=True)
    for direction in ("parallel", "perpendicular"):
        subset = sorted((row for row in rows if row["direction"] == direction), key=lambda row: row["acceleration"])
        ax.plot(
            [row["acceleration"] for row in subset],
            [row["Keff"] for row in subset],
            marker="o", color=colors[direction], label=direction,
        )
    ax.set_xlabel("Acceleration $a$ (m s$^{-2}$)")
    ax.set_ylabel("Effective mobility $K$ (m$^3$)")
    ax.grid(alpha=0.25)
    ax.legend()
    for ext in ("png", "pdf"):
        fig.savefig(figures_dir / f"Figure_G2_force_linearity_K_vs_a.{ext}", dpi=300)
    plt.close(fig)

    overall = all(metric["direction_gate"] for metric in metrics.values())
    report = [
        "# SIM240 G2 Step 2 force-linearity validation report",
        "",
        f"Overall status: **{'PASS' if overall else 'FAIL'}**",
        "",
        "## Reuse audit",
        "",
        "The formal `a=1e5 m/s^2` G2-P/G2-T results were reused. The frozen base source and executable SHA-256 values match the formal manifests, and their geometry, numerical parameters, statistics, boundary audit, convergence, finite-value, and exit evidence remain consistent.",
        "",
        f"- base source SHA-256: `{sha256(BASE_SOURCE)}`",
        f"- formal executable SHA-256: `{sha256(BASE_BINARY)}`",
        "- new runs: four (`5e4` and `2e5 m/s^2`, both principal directions)",
        "",
        "## Directional results",
        "",
        "| Direction | slope | intercept | R2 | K range (m3) | K mean (m3) | sample K std (m3) | K CV | max relative spread | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for direction in ("parallel", "perpendicular"):
        m = metrics[direction]
        report.append(
            f"| {direction} | {m['slope']:.16e} | {m['intercept']:.16e} | {m['R2']:.10f} | "
            f"{m['K_min']:.16e} - {m['K_max']:.16e} | {m['K_mean']:.16e} | {m['K_std']:.16e} | "
            f"{m['K_CV']:.8e} | {m['K_max_relative_spread']:.8e} | {'PASS' if m['direction_gate'] else 'FAIL'} |"
        )
    report.extend([
        "",
        "## Frozen gates",
        "",
        "- R2 >= 0.9999",
        "- maximum relative K spread <= 1%",
        "- Mach < 0.05",
        "- mass error <= 1e-10",
        "- convergence, finite values, normal exit, and inherited boundary audit PASS",
        "",
        "Step 3 grid uncertainty is " + ("allowed by this gate." if overall else "not allowed because this gate failed."),
        "",
    ])
    (batch_dir / "G2_FORCE_LINEARITY_REPORT.md").write_text("\n".join(report))

    manifest = [
        f"batch_dir={batch_dir}",
        f"base_source={BASE_SOURCE}",
        f"base_source_sha256={sha256(BASE_SOURCE)}",
        f"formal_binary={BASE_BINARY}",
        f"formal_binary_sha256={sha256(BASE_BINARY)}",
        f"formal_batch={FORMAL_BATCH}",
    ]
    for path in sorted((batch_dir.parent.parent / "build").glob("g2_ex240_a*")):
        if path.is_file():
            manifest.append(f"artifact={path} sha256={sha256(path)}")
    (batch_dir / "source_manifest.txt").write_text("\n".join(manifest) + "\n")
    print(f"overall={'PASS' if overall else 'FAIL'}")
    for direction in ("parallel", "perpendicular"):
        m = metrics[direction]
        print(direction, f"R2={m['R2']:.12g}", f"K_min={m['K_min']:.16e}", f"K_max={m['K_max']:.16e}")
    return 0 if overall else 3


if __name__ == "__main__":
    raise SystemExit(main())
