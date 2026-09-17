#!/usr/bin/env python3
"""Generate minimal, auditable Step-3 diagnostic variants of frozen sources."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


CASE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CASE_ROOT.parents[1]
EX_BASE = REPO_ROOT / "CASE/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp"
SMOOTH_BASE = REPO_ROOT / "CASE/G1_Poiseuille_Bouzidi_Validation/src/g1_poiseuille_bouzidi_validation.cpp"
EX_SHA256 = "4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002"
SMOOTH_SHA256 = "872630051336bab44f01efa65aaf920cb96c2e82ac5f754bd5fe03f9c80fa59d"

GRIDS = {
    "5": {"dx": "5.0e-9", "nx": 48, "nodes": 57600},
    "2p5": {"dx": "2.5e-9", "nx": 96, "nodes": 460800},
    "1p25": {"dx": "1.25e-9", "nx": 192, "nodes": 3686400},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source marker, found {count}")
    return text.replace(old, new, 1)


def add_density_extrema(text: str, smooth: bool) -> str:
    text = replace_once(
        text,
        "  T densityIntegral = 0.0;\n  T maxDensityDeviation = 0.0;",
        "  T densityIntegral = 0.0;\n"
        "  T rhoMin = std::numeric_limits<T>::infinity();\n"
        "  T rhoMax = -std::numeric_limits<T>::infinity();\n"
        "  T maxDensityDeviation = 0.0;",
        "measurement density fields",
    )
    volume_name = "cellVolume" if smooth else "dx * dx * dx"
    text = replace_once(
        text,
        f"      value.densityIntegral += rho * {volume_name};\n"
        "      value.maxDensityDeviation = std::max(",
        f"      value.densityIntegral += rho * {volume_name};\n"
        "      value.rhoMin = std::min(value.rhoMin, rho);\n"
        "      value.rhoMax = std::max(value.rhoMax, rho);\n"
        "      value.maxDensityDeviation = std::max(",
        "density extrema accumulation",
    )
    return text


def generate_ex(grid: dict[str, object]) -> str:
    text = EX_BASE.read_text()
    text = replace_once(text, "constexpr T dx = 2.5e-9;", f"constexpr T dx = {grid['dx']};", "EX dx")
    text = replace_once(text, "constexpr int nx = 96;", f"constexpr int nx = {grid['nx']};", "EX nx")
    text = replace_once(text, "constexpr int ny = 96;", f"constexpr int ny = {grid['nx']};", "EX ny")
    text = replace_once(
        text,
        "  constexpr long long expectedFluidNodes = 460800;",
        f"  constexpr long long expectedFluidNodes = {grid['nodes']};",
        "EX expected fluid nodes",
    )
    text = add_density_extrema(text, smooth=False)
    text = replace_once(
        text,
        "           << \"q_audit_PASS=\" << boundaryAudit.pass << '\\n'\n"
        "           << \"fluid_nodes=\" << initialMaterials[1] << '\\n'",
        "           << \"q_audit_PASS=\" << boundaryAudit.pass << '\\n'\n"
        "           << \"dx_m=\" << dx << '\\n'\n"
        "           << \"dt_s=\" << dt << '\\n'\n"
        "           << \"tau=\" << converter.getLatticeRelaxationTime() << '\\n'\n"
        "           << \"rho_phys_kg_m3=\" << rhoPhys << '\\n'\n"
        "           << \"nu_phys_m2_s=\" << nuPhys << '\\n'\n"
        "           << \"nu_lattice=\" << nuPhys * dt / (dx * dx) << '\\n'\n"
        "           << \"acceleration_m_s2=\" << acceleration << '\\n'\n"
        "           << \"a_lattice=\" << acceleration * dt * dt / dx << '\\n'\n"
        "           << \"velocity_conversion_m_s_per_lattice=\" << dx / dt << '\\n'\n"
        "           << \"fluid_nodes=\" << initialMaterials[1] << '\\n'",
        "EX precheck similarity fields",
    )
    text = replace_once(
        text,
        "           << \"fallback_count=\"\n"
        "           << boundaryAudit.geometricFallbacks\n"
        "                + boundaryAudit.missingFluidNeighbourFallbacks << '\\n'\n"
        "           << \"exit_code=\" << (precheckPass ? 0 : 3) << '\\n';",
        "           << \"fallback_count=\"\n"
        "           << boundaryAudit.geometricFallbacks\n"
        "                + boundaryAudit.missingFluidNeighbourFallbacks << '\\n'\n"
        "           << \"unresolved_links=\" << boundaryAudit.unresolvedLinks << '\\n'\n"
        "           << \"exit_code=\" << (precheckPass ? 0 : 3) << '\\n';",
        "EX precheck unresolved field",
    )
    text = replace_once(
        text,
        "         << \"tau=\" << converter.getLatticeRelaxationTime() << '\\n'\n"
        "         << \"descriptor=D3Q19_FORCE\\n\"",
        "         << \"tau=\" << converter.getLatticeRelaxationTime() << '\\n'\n"
        "         << \"rho_phys_kg_m3=\" << rhoPhys << '\\n'\n"
        "         << \"nu_phys_m2_s=\" << nuPhys << '\\n'\n"
        "         << \"nu_lattice=\" << nuPhys * dt / (dx * dx) << '\\n'\n"
        "         << \"a_lattice=\" << acceleration * dt * dt / dx << '\\n'\n"
        "         << \"velocity_conversion_m_s_per_lattice=\" << dx / dt << '\\n'\n"
        "         << \"descriptor=D3Q19_FORCE\\n\"",
        "EX final similarity fields",
    )
    text = replace_once(
        text,
        "         << \"max_density_deviation=\" << maxDensityDeviation << '\\n'\n"
        "         << \"max_Mach=\" << maxMach << '\\n'",
        "         << \"max_density_deviation=\" << maxDensityDeviation << '\\n'\n"
        "         << \"rho_min=\" << final.rhoMin << '\\n'\n"
        "         << \"rho_max=\" << final.rhoMax << '\\n'\n"
        "         << \"max_Mach=\" << maxMach << '\\n'",
        "EX final density fields",
    )
    return text


def generate_smooth() -> str:
    text = SMOOTH_BASE.read_text()
    text = text.replace("G1_V2", "G2_Step3_Smooth75")
    text = text.replace("G1-V2", "G2 Step 3 Smooth75")
    text = replace_once(
        text,
        "      || std::abs(p.ny * p.dx - ly) > 1.0e-12 * ly) {",
        "      || std::abs(p.ny * p.dx - ly) > 1.0e-12 * ly\n"
        "      || std::abs(p.nz * p.dx - height) > 1.0e-12 * height) {",
        "Smooth exact height check",
    )
    text = add_density_extrema(text, smooth=True)
    text = replace_once(
        text,
        "      << \"tau=\" << converter.getLatticeRelaxationTime() << '\\n'\n"
        "      << \"q_min=\" << boundaryAudit.qMin << '\\n'",
        "      << \"tau=\" << converter.getLatticeRelaxationTime() << '\\n'\n"
        "      << \"rho_phys_kg_m3=\" << rhoPhys << '\\n'\n"
        "      << \"nu_phys_m2_s=\" << nuPhys << '\\n'\n"
        "      << \"nu_lattice=\" << nuPhys * p.dt / (p.dx * p.dx) << '\\n'\n"
        "      << \"acceleration_m_s2=\" << p.accelerationY << '\\n'\n"
        "      << \"a_lattice=\" << p.accelerationY * p.dt * p.dt / p.dx << '\\n'\n"
        "      << \"velocity_conversion_m_s_per_lattice=\" << p.dx / p.dt << '\\n'\n"
        "      << \"q_min=\" << boundaryAudit.qMin << '\\n'",
        "Smooth precheck similarity fields",
    )
    text = replace_once(
        text,
        "      << \"installed_links=\" << boundaryAudit.installedLinks << '\\n'\n"
        "      << \"exit_code=\" << (precheckPass ? 0 : 3) << '\\n';",
        "      << \"installed_links=\" << boundaryAudit.installedLinks << '\\n'\n"
        "      << \"fallback_count=\" << boundaryAudit.geometricFallbacks\n"
        "          + boundaryAudit.missingFluidNeighborFallbacks << '\\n'\n"
        "      << \"unresolved_links=\" << boundaryAudit.unresolvedLinks << '\\n'\n"
        "      << \"exit_code=\" << (precheckPass ? 0 : 3) << '\\n';",
        "Smooth precheck boundary fields",
    )
    text = replace_once(
        text,
        "  const bool acceptancePass = initialGeometryPass",
        "  const bool analyticAccuracyPass = profile.relativeL2 < profileL2Tolerance\n"
        "    && profile.offsetRelativeToAnalyticMax < offsetRelativeTolerance\n"
        "    && std::abs(relativeError) < kRelativeErrorTolerance;\n\n"
        "  const bool acceptancePass = initialGeometryPass",
        "Smooth analytical gate split",
    )
    text = replace_once(
        text,
        "    && maxCrossFlux <= crossFluxTolerance\n"
        "    && sectionDifference <= sectionTolerance\n"
        "    && profile.relativeL2 < profileL2Tolerance\n"
        "    && profile.offsetRelativeToAnalyticMax < offsetRelativeTolerance\n"
        "    && std::abs(relativeError) < kRelativeErrorTolerance;",
        "    && maxCrossFlux <= crossFluxTolerance\n"
        "    && sectionDifference <= sectionTolerance;",
        "Smooth numerical-only run gate",
    )
    text = replace_once(
        text,
        "    << \"tau=\" << converter.getLatticeRelaxationTime() << '\\n'\n"
        "    << \"descriptor=D3Q19_FORCE\\n\"",
        "    << \"tau=\" << converter.getLatticeRelaxationTime() << '\\n'\n"
        "    << \"rho_phys_kg_m3=\" << rhoPhys << '\\n'\n"
        "    << \"nu_phys_m2_s=\" << nuPhys << '\\n'\n"
        "    << \"nu_lattice=\" << nuPhys * p.dt / (p.dx * p.dx) << '\\n'\n"
        "    << \"a_lattice=\" << p.accelerationY * p.dt * p.dt / p.dx << '\\n'\n"
        "    << \"velocity_conversion_m_s_per_lattice=\" << p.dx / p.dt << '\\n'\n"
        "    << \"descriptor=D3Q19_FORCE\\n\"",
        "Smooth final similarity fields",
    )
    text = replace_once(
        text,
        "    << \"fallback_count=\" << boundaryAudit.geometricFallbacks\n"
        "        + boundaryAudit.missingFluidNeighborFallbacks << '\\n'\n"
        "    << \"material_unchanged=\" << materialUnchanged << '\\n'",
        "    << \"fallback_count=\" << boundaryAudit.geometricFallbacks\n"
        "        + boundaryAudit.missingFluidNeighborFallbacks << '\\n'\n"
        "    << \"unresolved_links=\" << boundaryAudit.unresolvedLinks << '\\n'\n"
        "    << \"material_unchanged=\" << materialUnchanged << '\\n'",
        "Smooth final unresolved field",
    )
    text = replace_once(
        text,
        "    << \"max_density_deviation=\" << maxDensityDeviation << '\\n'\n"
        "    << \"max_Mach=\" << maxMach << '\\n'",
        "    << \"max_density_deviation=\" << maxDensityDeviation << '\\n'\n"
        "    << \"rho_min=\" << final.rhoMin << '\\n'\n"
        "    << \"rho_max=\" << final.rhoMax << '\\n'\n"
        "    << \"max_Mach=\" << maxMach << '\\n'",
        "Smooth final density fields",
    )
    text = replace_once(
        text,
        "    << \"K_relative_error=\" << relativeError << '\\n'",
        "    << \"K_relative_error=\" << relativeError << '\\n'\n"
        "    << \"analytic_accuracy_PASS=\" << analyticAccuracyPass << '\\n'\n"
        "    << \"finite=\" << final.finite << '\\n'",
        "Smooth analytical status",
    )
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if sha256(EX_BASE) != EX_SHA256:
        raise RuntimeError("frozen EX240 source hash changed")
    if sha256(SMOOTH_BASE) != SMOOTH_SHA256:
        raise RuntimeError("frozen Smooth75 source hash changed")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for tag, grid in GRIDS.items():
        (output_dir / f"g2_ex240_dx{tag}.cpp").write_text(generate_ex(grid))
    (output_dir / "g2_smooth75_step3.cpp").write_text(generate_smooth())


if __name__ == "__main__":
    main()
