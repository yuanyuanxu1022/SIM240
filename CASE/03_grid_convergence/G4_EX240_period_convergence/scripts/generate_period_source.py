#!/usr/bin/env python3
"""Mechanically derive one G4 period-sweep source from the SHA-pinned frozen G2 source.

Two modes:
  --mode serial : period scaling only (R-series). Binary stays strictly 1-rank,
                  identical in structure to the frozen G2 solver (fallback path
                  and Nx=1 identity self-check).
  --mode mpi    : period scaling + the MPI instrumentation layer (M-series),
                  the frozen production mode declared in
                  PERIOD_CONVERGENCE_PROTOCOL.md section 7.

Every replacement is anchored on text that must occur exactly once in the
frozen source; the script aborts otherwise.  A replacements.tsv is emitted for
the white-list diff audit (scripts/verify_deltas.py).
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

PINNED_G2_SHA256 = "4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002"

FROZEN_REL = (
    "../../02_geometry_transport/G2_EX240_single_period_transport/"
    "src/g2_ex240_single_period_transport.cpp"
)


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one occurrence of: {old!r}")
    return text.replace(old, new)


def r_series(nx: int) -> list[tuple[str, str, str]]:
    """Period scaling replacements (frozen in protocol section 3-4)."""
    return [
        ("R1-lx", "constexpr T lx = 240.0e-9;",
         f"constexpr T lx = 240.0e-9 * {nx};"),
        ("R2-nx", "constexpr int nx = 96;",
         f"constexpr int nx = 96 * {nx};"),
        ("R3-steps", "constexpr int maximumSteps = 60000;",
         f"constexpr int maximumSteps = {60000 * nx * nx};"),
        ("R4-period-consts", "constexpr T grooveStart = 60.0e-9;",
         "constexpr T grooveStart = 60.0e-9;\n"
         "constexpr T period = 240.0e-9;\n"
         f"constexpr int groovePeriods = {nx};"),
        ("R5-volume", "  + (grooveEnd - grooveStart) * ly * grooveDepth;",
         f"  + {nx} * (grooveEnd - grooveStart) * ly * grooveDepth;"),
        ("R6-wrapx", "  x = std::fmod(x, lx);\n  return x < 0.0 ? x + lx : x;",
         "  x = std::fmod(x, period);\n  return x < 0.0 ? x + period : x;"),
        ("R7-images", "for (int image = -1; image <= 1; ++image) {",
         "for (int image = -1; image <= groovePeriods; ++image) {"),
        ("R8-walls", "for (T wallX : {grooveStart + image * lx, grooveEnd + image * lx}) {",
         "for (T wallX : {grooveStart + image * period, grooveEnd + image * period}) {"),
        ("R9-case-p", 'p.caseId = "G2-P";', f'p.caseId = "G4-nx{nx}-P";'),
        ("R10-case-t", 'p.caseId = "G2-T";', f'p.caseId = "G4-nx{nx}-T";'),
        ("R12-nodes", "constexpr long long expectedFluidNodes = 460800;",
         f"constexpr long long expectedFluidNodes = 460800LL * {nx};"),
        ("R13-writer", 'SuperVTMwriter3D<T> writer("g2_ex240_" + p.directionName, overlap);',
         f'SuperVTMwriter3D<T> writer("g4_nx{nx}_" + p.directionName, overlap);'),
    ]


def m_series(nx: int) -> list[tuple[str, str, str]]:
    """MPI instrumentation layer (frozen in protocol section 7)."""
    reduce_measure = (
        "  for (int iD = 0; iD < 3; ++iD) {\n"
        "    value.meanVelocity[iD] = value.integratedVelocity[iD] / value.volume;"
    )
    reduce_measure_new = (
        "  if (singleton::mpi().getSize() > 1) {\n"
        "    double fluidNodesValue = static_cast<double>(value.fluidNodes);\n"
        "    singleton::mpi().allReduce(fluidNodesValue, MPI_SUM);\n"
        "    value.fluidNodes = static_cast<long long>(fluidNodesValue);\n"
        "    singleton::mpi().allReduce(value.volume, MPI_SUM);\n"
        "    singleton::mpi().allReduce(value.mass, MPI_SUM);\n"
        "    singleton::mpi().allReduce(value.densityIntegral, MPI_SUM);\n"
        "    singleton::mpi().allReduce(value.maxDensityDeviation, MPI_MAX);\n"
        "    singleton::mpi().allReduce(value.maxLatticeSpeed, MPI_MAX);\n"
        "    singleton::mpi().allReduce(value.pressureMin, MPI_MIN);\n"
        "    singleton::mpi().allReduce(value.pressureMax, MPI_MAX);\n"
        "    singleton::mpi().allReduce(value.sectionQ1, MPI_SUM);\n"
        "    singleton::mpi().allReduce(value.sectionQ2, MPI_SUM);\n"
        "    for (int iD = 0; iD < 3; ++iD) {\n"
        "      singleton::mpi().allReduce(value.integratedVelocity[iD], MPI_SUM);\n"
        "    }\n"
        "    int finiteValue = value.finite ? 1 : 0;\n"
        "    singleton::mpi().allReduce(finiteValue, MPI_LAND);\n"
        "    value.finite = finiteValue != 0;\n"
        "  }\n"
        + reduce_measure
    )
    return [
        ("M0-cstdlib", "#include <numeric>", "#include <numeric>\n#include <cstdlib>"),
        ("M1-rankcheck",
         '  if (singleton::mpi().getSize() != 1) {\n'
         '    std::cerr << "G2 requires exactly one MPI rank\\n";\n'
         '    return 2;\n'
         '  }',
         "  const char* expectedRanksEnv = std::getenv(\"G4_EXPECTED_RANKS\");\n"
         "  const int expectedRanks = expectedRanksEnv != nullptr\n"
         "    ? std::stoi(expectedRanksEnv) : singleton::mpi().getSize();\n"
         "  if (singleton::mpi().getSize() != expectedRanks) {\n"
         '    std::cerr << "G4 rank mismatch: expected " << expectedRanks\n'
         '              << ", got " << singleton::mpi().getSize() << \'\\n\';\n'
         '    return 2;\n'
         '  }'),
        ("M2-split", "  CuboidDecomposition<T, 3> cuboids(domain, dx, 1);",
         "  CuboidDecomposition<T, 3> cuboids(domain, dx, 1);\n"
         "  cuboids.splitRegular(0, 48);"),
        ("M3-measure-reduce", reduce_measure, reduce_measure_new),
        ("M3-measure-globalR",
         "      const int coordinate = drive == 0 ? latticeR[0] : latticeR[1];",
         "      const auto physR = blockGeometry.getPhysR(latticeR);\n"
         "      const Vector<int, 3> globalR{\n"
         "        static_cast<int>(std::llround(physR[0] / dx - 0.5)),\n"
         "        static_cast<int>(std::llround(physR[1] / dx - 0.5)),\n"
         "        static_cast<int>(std::llround(physR[2] / dx - 0.5))};\n"
         "      const int coordinate = drive == 0 ? globalR[0] : globalR[1];"),
        ("M4-counts-reduce", "  return counts;",
         "  if (singleton::mpi().getSize() > 1) {\n"
         "    for (int m = 0; m < 4; ++m) {\n"
         "      double countValue = static_cast<double>(counts[m]);\n"
         "      singleton::mpi().allReduce(countValue, MPI_SUM);\n"
         "      counts[m] = static_cast<long long>(countValue);\n"
         "    }\n"
         "  }\n"
         "  return counts;"),
        ("M5-audit-neighbour",
         "        const int material = block.getMaterial(wrapPeriodicXY(solidR));",
         "        const int material = block.get(solidR[0], solidR[1], solidR[2]);"),
        ("M5-audit-reduce", "  return audit;",
         "  if (singleton::mpi().getSize() > 1) {\n"
         "    double candidateValue = static_cast<double>(audit.candidateLinks);\n"
         "    singleton::mpi().allReduce(candidateValue, MPI_SUM);\n"
         "    audit.candidateLinks = static_cast<long long>(candidateValue);\n"
         "    double validValue = static_cast<double>(audit.validDistanceLinks);\n"
         "    singleton::mpi().allReduce(validValue, MPI_SUM);\n"
         "    audit.validDistanceLinks = static_cast<long long>(validValue);\n"
         "    double fallbackValue = static_cast<double>(audit.geometricFallbacks);\n"
         "    singleton::mpi().allReduce(fallbackValue, MPI_SUM);\n"
         "    audit.geometricFallbacks = static_cast<long long>(fallbackValue);\n"
         "    double missingValue =\n"
         "      static_cast<double>(audit.missingFluidNeighbourFallbacks);\n"
         "    singleton::mpi().allReduce(missingValue, MPI_SUM);\n"
         "    audit.missingFluidNeighbourFallbacks = static_cast<long long>(missingValue);\n"
         "    singleton::mpi().allReduce(audit.qMin, MPI_MIN);\n"
         "    singleton::mpi().allReduce(audit.qMax, MPI_MAX);\n"
         "  }\n"
         "  return audit;"),
        ("M5-installed-reduce", "  audit.pass = audit.candidateLinks > 0",
         "  if (singleton::mpi().getSize() > 1) {\n"
         "    double installedValue = static_cast<double>(audit.installedLinks);\n"
         "    singleton::mpi().allReduce(installedValue, MPI_SUM);\n"
         "    audit.installedLinks = static_cast<long long>(installedValue);\n"
         "    double unresolvedValue = static_cast<double>(audit.unresolvedLinks);\n"
         "    singleton::mpi().allReduce(unresolvedValue, MPI_SUM);\n"
         "    audit.unresolvedLinks = static_cast<long long>(unresolvedValue);\n"
         "    singleton::mpi().allReduce(audit.installedQMin, MPI_MIN);\n"
         "    singleton::mpi().allReduce(audit.installedQMax, MPI_MAX);\n"
         "  }\n"
         "  audit.pass = audit.candidateLinks > 0"),
        ("M7-profiles-globalR",
         "      const int slice = p.drive == 0 ? latticeR[0] : latticeR[1];",
         "      const auto physR = blockGeometry.getPhysR(latticeR);\n"
         "      const Vector<int, 3> globalR{\n"
         "        static_cast<int>(std::llround(physR[0] / dx - 0.5)),\n"
         "        static_cast<int>(std::llround(physR[1] / dx - 0.5)),\n"
         "        static_cast<int>(std::llround(physR[2] / dx - 0.5))};\n"
         "      const int slice = p.drive == 0 ? globalR[0] : globalR[1];"),
        ("M7-profiles-midplane", "      if (latticeR[1] == ny / 2) {",
         "      if (globalR[1] == ny / 2) {"),
        ("M8-profiles-reduce",
         '  std::ofstream pressure(p.outputDirectory / "pressure_profile.csv");',
         "  if (singleton::mpi().getSize() > 1) {\n"
         "    for (int i = 0; i < slices; ++i) {\n"
         "      singleton::mpi().allReduce(rhoSum[i], MPI_SUM);\n"
         "      singleton::mpi().allReduce(pressureSum[i], MPI_SUM);\n"
         "      singleton::mpi().allReduce(velocitySum[i], MPI_SUM);\n"
         "      singleton::mpi().allReduce(phiSum[i], MPI_SUM);\n"
         "      double countValue = static_cast<double>(counts[i]);\n"
         "      singleton::mpi().allReduce(countValue, MPI_SUM);\n"
         "      counts[i] = static_cast<long long>(countValue);\n"
         "    }\n"
         "  }\n"
         '  std::ofstream pressure(p.outputDirectory / "pressure_profile.csv");'),
        ("M9-writepath-helper",
         "Vector<int, 3> wrapPeriodicXY(Vector<int, 3> latticeR)\n"
         "{\n"
         "  latticeR[0] = wrapIndex(latticeR[0], nx);\n"
         "  latticeR[1] = wrapIndex(latticeR[1], ny);\n"
         "  return latticeR;\n"
         "}",
         "Vector<int, 3> wrapPeriodicXY(Vector<int, 3> latticeR)\n"
         "{\n"
         "  latticeR[0] = wrapIndex(latticeR[0], nx);\n"
         "  latticeR[1] = wrapIndex(latticeR[1], ny);\n"
         "  return latticeR;\n"
         "}\n"
         "\n"
         "std::filesystem::path writePath(const std::filesystem::path& path)\n"
         "{\n"
         "  return singleton::mpi().isMainProcessor()\n"
         "    ? path : std::filesystem::path(\"/dev/null\");\n"
         "}"),
        ("M9-write-audit",
         'writeBoundaryAudit(\n    p.outputDirectory / "boundary_audit.txt",',
         'writeBoundaryAudit(\n    writePath(p.outputDirectory / "boundary_audit.txt"),'),
        ("M9-write-precheck",
         '    std::ofstream result(p.outputDirectory / "result.txt");\n'
         "    result << std::setprecision(17) << std::boolalpha\n"
         '           << "case=" << p.caseId << \'\\n\'\n'
         '           << "direction=" << p.directionName << \'\\n\'\n'
         '           << "formal_simulation=false\\n"',
         '    std::ofstream result(writePath(p.outputDirectory / "result.txt"));\n'
         "    result << std::setprecision(17) << std::boolalpha\n"
         '           << "case=" << p.caseId << \'\\n\'\n'
         '           << "direction=" << p.directionName << \'\\n\'\n'
         '           << "formal_simulation=false\\n"'),
        ("M9-write-steady",
         '  std::ofstream result(p.outputDirectory / "result.txt");\n'
         "  result << std::setprecision(17) << std::boolalpha\n"
         '         << "case=" << p.caseId << \'\\n\'\n'
         '         << "direction=" << p.directionName << \'\\n\'\n'
         '         << "PASS=" << pass << \'\\n\'',
         '  std::ofstream result(writePath(p.outputDirectory / "result.txt"));\n'
         "  result << std::setprecision(17) << std::boolalpha\n"
         '         << "case=" << p.caseId << \'\\n\'\n'
         '         << "direction=" << p.directionName << \'\\n\'\n'
         '         << "PASS=" << pass << \'\\n\''),
        ("M9-write-diagnostics",
         'std::ofstream diagnostics(p.outputDirectory / "diagnostics.csv");',
         'std::ofstream diagnostics(writePath(p.outputDirectory / "diagnostics.csv"));'),
        ("M9-write-summary",
         'std::ofstream summary(p.outputDirectory / "result_summary.csv");',
         'std::ofstream summary(writePath(p.outputDirectory / "result_summary.csv"));'),
        ("M9-write-field",
         'std::ofstream field(p.outputDirectory / "field_slice.csv");',
         'std::ofstream field(writePath(p.outputDirectory / "field_slice.csv"));'),
        ("M9-write-pressure",
         'std::ofstream pressure(p.outputDirectory / "pressure_profile.csv");',
         'std::ofstream pressure(writePath(p.outputDirectory / "pressure_profile.csv"));'),
        ("M9-write-velocity",
         'std::ofstream velocity(p.outputDirectory / "velocity_profile.csv");',
         'std::ofstream velocity(writePath(p.outputDirectory / "velocity_profile.csv"));'),
        ("M9-write-energy",
         'std::ofstream energy(p.outputDirectory / "energy_dissipation.csv");',
         'std::ofstream energy(writePath(p.outputDirectory / "energy_dissipation.csv"));'),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nx", type=int, required=True, choices=[1, 2, 4, 8])
    parser.add_argument("--mode", required=True, choices=["serial", "mpi"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frozen = (Path(__file__).resolve().parents[1] / FROZEN_REL).resolve()
    source = frozen.read_text()
    actual_sha = hashlib.sha256(source.encode()).hexdigest()
    if actual_sha != PINNED_G2_SHA256:
        raise SystemExit(f"frozen G2 source hash mismatch: {actual_sha}")

    replacements = r_series(args.nx)
    if args.mode == "mpi":
        replacements += m_series(args.nx)
    elif args.nx != 1:
        # serial mode keeps the frozen 1-rank check; only relabel the message
        replacements.append(("R11-rankmsg", "G2 requires exactly one MPI rank",
                             "G4 serial mode requires exactly one MPI rank"))

    generated = source
    for name, old, new in replacements:
        generated = replace_once(generated, old, new)

    header = (
        "// Generated by scripts/generate_period_source.py; do not edit.\n"
        f"// frozen_g2_sha256={PINNED_G2_SHA256}\n"
        f"// nx={args.nx}; mode={args.mode}; "
        f"expected_fluid_nodes={460800 * args.nx}; "
        f"maximum_steps={60000 * args.nx * args.nx}\n\n"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header + generated)

    tsv = args.output.with_suffix(".replacements.tsv")
    with tsv.open("w") as fh:
        fh.write("name\tmode\n")
        for name, _, _ in replacements:
            fh.write(f"{name}\t{args.mode}\n")
    print(f"generated={args.output} nx={args.nx} mode={args.mode} "
          f"replacements={len(replacements)}")


if __name__ == "__main__":
    main()
