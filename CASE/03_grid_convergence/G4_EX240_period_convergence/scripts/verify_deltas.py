#!/usr/bin/env python3
"""White-list audit of G4 generated sources against the frozen G2 source.

Checks:
  1. Idempotence: re-running the generator on the frozen source reproduces
     each checked-in generated source byte-for-byte (also re-verifies the
     frozen source SHA-256 inside the generator).
  2. Nx=1 serial identity: the serial nx=1 source differs from the frozen
     source only in the whitelisted R-series hunks (semantically identical
     geometry at nx=1); any other line is a hard error.

Usage: verify_deltas.py --build-dir <generated dir> [--nx 1,2,4,8]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FROZEN = (SCRIPT_DIR.parents[2] / "02_geometry_transport" /
          "G2_EX240_single_period_transport" / "src" /
          "g2_ex240_single_period_transport.cpp").resolve()

# Lines the Nx=1 serial identity check accepts as removed (-) / added (+).
# All R-series edits at nx=1 collapse to these hunks.
IDENTITY_ALLOWED_MINUS = {
    "constexpr T lx = 240.0e-9;",
    "constexpr int nx = 96;",
    "constexpr int maximumSteps = 60000;",
    "constexpr T grooveStart = 60.0e-9;",
    "  + (grooveEnd - grooveStart) * ly * grooveDepth;",
    "  x = std::fmod(x, lx);",
    "  return x < 0.0 ? x + lx : x;",
    "      for (int image = -1; image <= 1; ++image) {",
    "        for (T wallX : {grooveStart + image * lx, grooveEnd + image * lx}) {",
    '    p.caseId = "G2-P";',
    '    p.caseId = "G2-T";',
    "  constexpr long long expectedFluidNodes = 460800;",
    '  SuperVTMwriter3D<T> writer("g2_ex240_" + p.directionName, overlap);',
}
IDENTITY_ALLOWED_PLUS = {
    "constexpr T lx = 240.0e-9 * 1;",
    "constexpr int nx = 96 * 1;",
    "constexpr int maximumSteps = 60000;",
    "constexpr T grooveStart = 60.0e-9;",
    "constexpr T period = 240.0e-9;",
    "constexpr int groovePeriods = 1;",
    "  + 1 * (grooveEnd - grooveStart) * ly * grooveDepth;",
    "  x = std::fmod(x, period);",
    "  return x < 0.0 ? x + period : x;",
    "      for (int image = -1; image <= groovePeriods; ++image) {",
    "        for (T wallX : {grooveStart + image * period, grooveEnd + image * period}) {",
    '    p.caseId = "G4-nx1-P";',
    '    p.caseId = "G4-nx1-T";',
    "  constexpr long long expectedFluidNodes = 460800LL * 1;",
    '  SuperVTMwriter3D<T> writer("g4_nx1_" + p.directionName, overlap);',
}


def regenerate(build_dir: Path, nx: int, mode: str) -> Path:
    tmp = build_dir / f"regen_nx{nx}_{mode}.cpp"
    subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "generate_period_source.py"),
         "--nx", str(nx), "--mode", mode, "--output", str(tmp)],
        check=True)
    return tmp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--nx-list", type=str, default="1,2,4,8")
    args = parser.parse_args()
    nx_list = [int(v) for v in args.nx_list.split(",")]

    errors: list[str] = []
    for nx in nx_list:
        for mode in ("serial", "mpi"):
            checked_in = args.build_dir / f"g4_nx{nx}_{mode}.cpp"
            if not checked_in.exists():
                errors.append(f"missing generated source: {checked_in}")
                continue
            regenerated = regenerate(args.build_dir, nx, mode)
            if checked_in.read_bytes() != regenerated.read_bytes():
                errors.append(f"idempotence FAIL: {checked_in.name}")
            regenerated.unlink()

    identity_src = args.build_dir / "g4_nx1_serial.cpp"
    if identity_src.exists() and not errors:
        frozen_lines = FROZEN.read_text().splitlines()
        generated = identity_src.read_text()
        body = generated.split("\n\n", 1)[1]  # drop generated header comment
        gen_lines = body.splitlines()
        removed = [l for l in frozen_lines
                   if l not in set(gen_lines) and not l.startswith("// Generated")]
        added = [l for l in gen_lines
                 if l not in set(frozen_lines)]
        bad_minus = [l for l in removed if l not in IDENTITY_ALLOWED_MINUS]
        bad_plus = [l for l in added if l not in IDENTITY_ALLOWED_PLUS]
        if bad_minus or bad_plus:
            errors.append("identity FAIL: unexpected delta lines\n"
                          "  minus: " + repr(bad_minus[:5]) +
                          "\n  plus: " + repr(bad_plus[:5]))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print(f"verify_deltas PASS (nx={nx_list}, serial+mpi idempotent, "
          "nx1 serial identity whitelist clean)")


if __name__ == "__main__":
    main()
