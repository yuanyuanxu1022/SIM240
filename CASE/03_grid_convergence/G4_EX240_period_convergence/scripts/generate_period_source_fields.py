#!/usr/bin/env python3
"""Opt-in output-only repair. Original generator/binaries remain untouched."""
import argparse
import hashlib
from pathlib import Path

import generate_period_source as original


def field_series(mode):
    changes = [
        ("F1-probe-mode",
         'p.mode != "precheck" && p.mode != "steady"',
         'p.mode != "precheck" && p.mode != "steady" && p.mode != "fieldcheck"'),
        ("F2-mode-help", "precheck|steady P|T OUTPUT_DIRECTORY",
         "precheck|steady|fieldcheck P|T OUTPUT_DIRECTORY"),
        ("F3-mode-error", "mode must be precheck or steady",
         "mode must be precheck, steady or fieldcheck"),
        ("F4-export-probe", "  lattice.initialize();",
         "  lattice.initialize();\n\n"
         '  if (p.mode == "fieldcheck") {\n'
         "    writeFinalProfiles(lattice, geometry, converter, p);\n"
         + ('    std::ofstream probe(writePath(p.outputDirectory / "fieldcheck_result.txt"));\n'
            if mode == "mpi" else
            '    std::ofstream probe(p.outputDirectory / "fieldcheck_result.txt");\n')
         + '    probe << "formal_simulation=false\\ncollide_and_stream_calls=0\\n"\n'
         '          << "fieldcheck_PASS=true\\n";\n'
         "    return 0;\n"
         "  }"),
    ]
    if mode == "serial":
        return changes
    changes += [
        ("F5-field-buffer",
         '  std::ofstream field(writePath(p.outputDirectory / "field_slice.csv"));',
         "  const int sliceNz = static_cast<int>(std::llround((mesaGap + grooveDepth) / dx));\n"
         "  std::vector<T> fieldValues(nx * sliceNz * 9, 0.0);\n"
         "  std::vector<int> fieldOwners(nx * sliceNz, 0);\n"
         '  std::ofstream field(writePath(p.outputDirectory / "field_slice.csv"));'),
        ("F6-field-local",
         "        field << position[0] << ',' << position[2] << ','\n"
         "              << velocity[0] << ',' << velocity[1] << ',' << velocity[2] << ','\n"
         "              << std::sqrt(speedSquared) << ',' << rho << ',' << pressure << ','\n"
         '              << phi << ",1\\n";',
         "        if (globalR[0] < 0 || globalR[0] >= nx\n"
         "            || globalR[2] < 0 || globalR[2] >= sliceNz) {\n"
         '          throw std::runtime_error("field slice coordinate outside physical grid");\n'
         "        }\n"
         "        const int point = globalR[0] * sliceNz + globalR[2];\n"
         "        ++fieldOwners[point];\n"
         "        const std::array<T, 9> values{position[0], position[2],\n"
         "          velocity[0], velocity[1], velocity[2], std::sqrt(speedSquared),\n"
         "          rho, pressure, phi};\n"
         "        for (int k = 0; k < 9; ++k) {\n"
         "          fieldValues[9 * point + k] += values[k];\n"
         "        }"),
        ("F7-field-collect-and-write",
         '  std::ofstream pressure(writePath(p.outputDirectory / "pressure_profile.csv"));',
         "  if (singleton::mpi().getSize() > 1) {\n"
         "    MPI_Allreduce(MPI_IN_PLACE, fieldValues.data(),\n"
         "      static_cast<int>(fieldValues.size()), MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);\n"
         "    MPI_Allreduce(MPI_IN_PLACE, fieldOwners.data(),\n"
         "      static_cast<int>(fieldOwners.size()), MPI_INT, MPI_SUM, MPI_COMM_WORLD);\n"
         "  }\n"
         "  int fieldRows = 0;\n"
         "  for (int point = 0; point < nx * sliceNz; ++point) {\n"
         "    if (fieldOwners[point] == 0) { continue; }\n"
         "    if (fieldOwners[point] != 1) {\n"
         '      throw std::runtime_error("duplicate ownership in field slice");\n'
         "    }\n"
         "    ++fieldRows;\n"
         "    for (int k = 0; k < 9; ++k) {\n"
         "      field << fieldValues[9 * point + k] << ',';\n"
         "    }\n"
         '    field << "1\\n";\n'
         "  }\n"
         "  field.close();\n"
         "  int outputOkay = field && fieldRows == 4800 * groovePeriods ? 1 : 0;\n"
         "  singleton::mpi().allReduce(outputOkay, MPI_MIN);\n"
         "  if (!outputOkay) {\n"
         '    throw std::runtime_error("field slice write/row-count failure");\n'
         "  }\n"
         '  std::ofstream pressure(writePath(p.outputDirectory / "pressure_profile.csv"));'),
    ]
    return changes


def generate(nx, mode):
    frozen = (Path(__file__).resolve().parents[1] / original.FROZEN_REL).resolve()
    source = frozen.read_text()
    if hashlib.sha256(source.encode()).hexdigest() != original.PINNED_G2_SHA256:
        raise RuntimeError("frozen G2 source hash mismatch")
    replacements = original.r_series(nx)
    if mode == "mpi":
        replacements += original.m_series(nx)
    elif nx != 1:
        replacements += [("R11-rankmsg", "G2 requires exactly one MPI rank",
                          "G4 serial mode requires exactly one MPI rank")]
    for _, old, new in replacements:
        source = original.replace_once(source, old, new)
    baseline = source
    for _, old, new in field_series(mode):
        source = original.replace_once(source, old, new)
    # Exact reverse audit: no numerical change can escape the F-series list.
    restored = source
    for _, old, new in reversed(field_series(mode)):
        restored = original.replace_once(restored, new, old)
    if restored != baseline:
        raise RuntimeError("output-only reverse audit failed")
    header = ("// Generated by generate_period_source_fields.py; do not edit.\n"
              f"// frozen_g2_sha256={original.PINNED_G2_SHA256}\n"
              f"// nx={nx}; mode={mode}; output_revision=fields_v1\n\n")
    return header + source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nx", type=int, choices=[1, 2, 4, 8], required=True)
    parser.add_argument("--mode", choices=["serial", "mpi"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generate(args.nx, args.mode))
    print(f"generated={args.output}; output-only reverse audit PASS")


if __name__ == "__main__":
    main()
