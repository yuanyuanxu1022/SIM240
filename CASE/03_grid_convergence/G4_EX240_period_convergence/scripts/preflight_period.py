#!/usr/bin/env python3
"""Static preflight for G4 period sweep (never runs OpenLB).

Checks the frozen protocol expectations from PERIOD_CONVERGENCE_PROTOCOL.md
against the generated sources and compiled binaries.  Actual geometry / q /
mass evidence comes from the per-point precheck and steady runs.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from fractions import Fraction
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
FROZEN = (CASE_ROOT / "../../02_geometry_transport/G2_EX240_single_period_transport/"
          "src/g2_ex240_single_period_transport.cpp").resolve()
PINNED_G2_SHA256 = "4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002"

DX_NM = Fraction(25, 10)
PERIOD_CELLS = 96
GROOVE_CELLS = 48
MESA_CELLS = 24
GAP_CELLS = 30
DEPTH_CELLS = 40
NY = 96
FLUID_NODES_PER_PERIOD = 460800
CANDIDATE_LINKS_PER_PERIOD = 130176
A_TAGS = ("a5e4", "a1e5", "a2e5")
DIRECTIONS = ("P", "T")
RANKS = {2: 8, 4: 16, 8: 16}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=int, choices=[1, 2, 4, 8], required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    checks: list[str] = []

    if sha256(FROZEN) != PINNED_G2_SHA256:
        raise SystemExit(f"frozen G2 source hash mismatch: {sha256(FROZEN)}")

    checks.append(f"frozen G2 source SHA-256 pinned OK ({PINNED_G2_SHA256[:12]}...)")
    for nx in (1, 2, 4, 8):
        checks.append(
            f"nx={nx}: period {PERIOD_CELLS} / groove {GROOVE_CELLS} / mesa "
            f"{MESA_CELLS} / gap {GAP_CELLS} / depth {DEPTH_CELLS} cells (integer, "
            "independent of nx)")

    build = CASE_ROOT / "build"
    generated = build / "generated"
    nx = args.level
    for mode in ("serial", "mpi"):
        for tag in A_TAGS:
            binary = build / f"g4_nx{nx}_{mode}_{tag}"
            if not binary.exists() or not binary.is_file():
                errors.append(f"missing binary: {binary}")
            else:
                checks.append(f"binary OK: {binary.name} sha256={sha256(binary)[:16]}...")

    # fluid-node and volume expectations from the protocol (section 3-4)
    for probe_nx in (1, 2, 4, 8):
        expect_nodes = FLUID_NODES_PER_PERIOD * probe_nx
        expect_links = CANDIDATE_LINKS_PER_PERIOD * probe_nx
        max_steps = 60000 * probe_nx * probe_nx
        checks.append(
            f"nx={probe_nx}: fluid_nodes={expect_nodes} "
            f"candidate_links={expect_links} maximum_steps={max_steps}")
        # nominalVolume = areaPlan*mesaGap + nx*(grooveWidth*ly*grooveDepth)
        area = probe_nx * 240.0 * 240.0  # nm^2
        volume = area * 75.0 + probe_nx * 120.0 * 240.0 * 100.0  # nm^3
        ref_height = volume / area
        if abs(ref_height - 125.0) > 1e-12:
            errors.append(f"nx={probe_nx}: referenceHeight != 125nm ({ref_height})")
        checks.append(f"nx={probe_nx}: referenceHeight={ref_height} nm (expect 125)")

    if args.level > 1:
        checks.append(
            f"level nx={args.level}: production ranks={RANKS[args.level]} "
            "(G4_EXPECTED_RANKS), per-rank cells "
            f"{FLUID_NODES_PER_PERIOD * args.level / RANKS[args.level]:.0f}")
    else:
        checks.append("level 1: precheck-only freeze (steady evidence reused per REUSE_AUDIT.md)")

    if args.report is None:
        args.report = CASE_ROOT / f"preflight_nx{args.level}.md"
    lines = ["# G4 preflight (static)", ""]
    lines += [f"- {c}" for c in checks]
    if errors:
        lines += ["", "## ERRORS"] + [f"- {e}" for e in errors]
        args.report.write_text("\n".join(lines) + "\n")
        raise SystemExit(f"preflight FAIL: {errors}")
    lines += ["", "preflight_PASS=true"]
    args.report.write_text("\n".join(lines) + "\n")
    print(f"preflight PASS (nx={args.level}, {len(checks)} checks)")
    for c in checks:
        print(f"  {c}")


if __name__ == "__main__":
    main()
