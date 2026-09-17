#include <olb.h>
#include "../case.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>

using namespace olb;

namespace {

struct Options {
  std::string runId = "stage2_bxx_formal";
  std::size_t steps = 20000;
  bool massAudit = true;
};

Options parseOptions(int argc, char** argv) {
  Options options;
  for (int i = 1; i < argc; ++i) {
    const std::string arg(argv[i]);
    if (arg == "--run-id" && i + 1 < argc) {
      options.runId = argv[++i];
    } else if (arg == "--steps" && i + 1 < argc) {
      options.steps = std::stoull(argv[++i]);
    } else if (arg == "--mass-audit" && i + 1 < argc) {
      options.massAudit = std::stoi(argv[++i]) != 0;
    }
  }
  if (options.runId.empty() || options.runId.find('/') != std::string::npos) {
    throw std::runtime_error("run-id must be a non-empty directory name");
  }
  if (options.steps == 0 || options.steps > 20000) {
    throw std::runtime_error("steps must be in [1,20000]");
  }
  return options;
}

bool isFinite(double value) {
  return std::isfinite(value);
}

} // namespace

int main(int argc, char** argv) {
  initialize(&argc, &argv);
  const Options options = parseOptions(argc, argv);

  MyCase::ParametersD params;
  setDefaultParameters(params);
  params.fromCLI(argc, argv);
  params.set<parameters::CHECK_BXX>(1);

  const std::filesystem::path outputDir = std::filesystem::path("runs") / options.runId;
  std::filesystem::create_directories(outputDir);
  singleton::directories().setOutputDir(outputDir.string() + "/");

  Mesh mesh = createMesh(params);
  MyCase myCase(params, mesh);
  prepareGeometry(myCase);
  prepareLattice(myCase);
  setInitialValues(myCase);

  using T = MyCase::value_t;
  auto& lattice = myCase.getLattice(NavierStokes{});
  auto& geometry = myCase.getGeometry();
  auto& converter = lattice.getUnitConverter();

  const double dx = converter.getPhysDeltaX();
  const double dt = converter.getPhysDeltaT();
  const double rhoPhys = converter.getPhysDensity();
  const double nu = converter.getPhysViscosity();
  const double ax = params.get<parameters::BODY_FORCE_ACCEL_X>();
  const double wall = params.get<parameters::WALL_WIDTH>();
  const double groove = params.get<parameters::GROOVE_WIDTH>();
  const int nGrooves = params.get<parameters::NUM_GROOVES>();
  const double height = params.get<parameters::CHANNEL_HEIGHT>();
  const double ly = params.get<parameters::DOMAIN_LY>();
  const double lx = (nGrooves + 1) * wall + nGrooves * groove;
  const double areaCell = lx * height;
  const double dV = dx * dx * dx;
  const double velocityFactor = converter.getConversionFactorVelocity();
  const double forceExpected[3] = {ax * dt * dt / dx, 0., 0.};
  const double planeX[2] = {wall + 0.5 * groove, 2. * wall + 1.5 * groove};

  double forceMin[3] = {
      std::numeric_limits<double>::infinity(), std::numeric_limits<double>::infinity(),
      std::numeric_limits<double>::infinity()};
  double forceMax[3] = {
      -std::numeric_limits<double>::infinity(), -std::numeric_limits<double>::infinity(),
      -std::numeric_limits<double>::infinity()};
  std::size_t initialFluidNodes = 0;
  for (int iC = 0; iC < lattice.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](auto iX, auto iY, auto iZ) {
      if (blockGeometry.getMaterial(iX, iY, iZ) != 1) return;
      const auto force = block.get({iX, iY, iZ}).template getField<descriptors::FORCE>();
      ++initialFluidNodes;
      for (int d = 0; d < 3; ++d) {
        forceMin[d] = std::min(forceMin[d], static_cast<double>(force[d]));
        forceMax[d] = std::max(forceMax[d], static_cast<double>(force[d]));
      }
    });
  }
  bool forceAuditPass = initialFluidNodes > 0;
  for (int d = 0; d < 3; ++d) {
    forceAuditPass = forceAuditPass && isFinite(forceMin[d]) && isFinite(forceMax[d])
      && std::abs(forceMin[d] - forceExpected[d]) <= 1e-15 * std::max(1., std::abs(forceExpected[d]))
      && std::abs(forceMax[d] - forceExpected[d]) <= 1e-15 * std::max(1., std::abs(forceExpected[d]));
  }
  if (!forceAuditPass) {
    throw std::runtime_error("actual lattice force field is not strictly +x");
  }

  std::ofstream csv(outputDir / "blocking_diagnostic.csv");
  csv << std::scientific << std::setprecision(16);
  csv << "step,time_s,fluid_nodes,fluid_volume_m3,fluid_mass_kg,fluid_mass_signed_rel,"
         "fluid_mass_abs_rel,max_density_deviation,volume_mean_ux_m_s,max_abs_ux_m_s,"
         "Qx_legacy_m3_s,qx_legacy_m_s,Bxx_numerical_residual_m2,"
         "Qx_plane_groove1_m3_s,Qx_plane_groove2_m3_s,nonfinite_count,all_finite\n";

  double initialMass = 0.;
  double maxMassAbsRel = 0.;
  double maxDensityDeviationAll = 0.;
  std::size_t totalNonfinite = 0;
  double finalQx = 0., finalQxPlane0 = 0., finalQxPlane1 = 0.;
  double finalQxLegacy = 0., finalQxLegacySuperficial = 0., finalBxx = 0.;
  double finalMeanUx = 0., finalMaxAbsUx = 0.;

  for (std::size_t step = 0; step < options.steps; ++step) {
    lattice.collideAndStream();
    lattice.setProcessingContext(ProcessingContext::Evaluation);

    double mass = 0., sumUx = 0., maxAbsUx = 0., maxDensityDeviation = 0.;
    double planeFlux[2] = {0., 0.};
    std::size_t fluidNodes = 0, nonfiniteCount = 0;
    for (int iC = 0; iC < lattice.getLoadBalancer().size(); ++iC) {
      auto& block = lattice.getBlock(iC);
      auto& blockGeometry = geometry.getBlockGeometry(iC);
      block.forCoreSpatialLocations([&](auto iX, auto iY, auto iZ) {
        if (blockGeometry.getMaterial(iX, iY, iZ) != 1) return;
        auto cell = block.get({iX, iY, iZ});
        double u[3] = {0., 0., 0.};
        cell.computeU(u);
        const double ux = u[0] * velocityFactor;
        const double rho = cell.computeRho();
        ++fluidNodes;
        if (!isFinite(ux) || !isFinite(u[1]) || !isFinite(u[2]) || !isFinite(rho)) {
          ++nonfiniteCount;
          return;
        }
        sumUx += ux;
        maxAbsUx = std::max(maxAbsUx, std::abs(ux));
        if (options.massAudit) {
          mass += rho * rhoPhys * dV;
          maxDensityDeviation = std::max(maxDensityDeviation, std::abs(rho - 1.));
        }
        const auto phys = blockGeometry.getPhysR({iX, iY, iZ});
        // y is periodic and stores both y=0 and y=Ly. A physical x-normal plane
        // should count that periodic point once, so exclude only the known y=Ly image.
        if (phys[1] < ly - 0.25 * dx) {
          for (int p = 0; p < 2; ++p) {
            if (std::abs(phys[0] - planeX[p]) < 0.25 * dx) planeFlux[p] += ux * dx * dx;
          }
        }
      });
    }

    if (!options.massAudit) mass = std::numeric_limits<double>::quiet_NaN();
    if (step == 0 && options.massAudit) initialMass = mass;
    const double signedMassRel = options.massAudit ? (mass - initialMass) / initialMass : std::numeric_limits<double>::quiet_NaN();
    const double massAbsRel = std::abs(signedMassRel);
    const double meanUx = sumUx / static_cast<double>(fluidNodes);
    const double volumeIntegralUx = sumUx * dV;
    // Exact legacy definition retained for reproduction. This is a y-normalized
    // volume integral, not an x-normal section flux.
    const double QxLegacy = volumeIntegralUx / (ly + dx);
    const double qxLegacy = QxLegacy / areaCell;
    const double BxxResidual = rhoPhys * nu * qxLegacy / (rhoPhys * ax);
    const double derived[] = {meanUx, maxAbsUx, QxLegacy, qxLegacy, BxxResidual, planeFlux[0], planeFlux[1]};
    for (double value : derived) if (!isFinite(value)) ++nonfiniteCount;
    totalNonfinite += nonfiniteCount;
    if (options.massAudit) {
      maxMassAbsRel = std::max(maxMassAbsRel, massAbsRel);
      maxDensityDeviationAll = std::max(maxDensityDeviationAll, maxDensityDeviation);
    }

    csv << step << ',' << step * dt << ',' << fluidNodes << ',' << fluidNodes * dV << ','
        << mass << ',' << signedMassRel << ',' << massAbsRel << ',' << maxDensityDeviation << ','
        << meanUx << ',' << maxAbsUx << ',' << QxLegacy << ',' << qxLegacy << ',' << BxxResidual << ','
        << planeFlux[0] << ',' << planeFlux[1] << ',' << nonfiniteCount << ',' << (nonfiniteCount == 0 ? 1 : 0) << '\n';

    finalMeanUx = meanUx;
    finalMaxAbsUx = maxAbsUx;
    finalQxLegacy = QxLegacy;
    finalQxLegacySuperficial = qxLegacy;
    finalBxx = BxxResidual;
    finalQxPlane0 = planeFlux[0];
    finalQxPlane1 = planeFlux[1];
    finalQx = QxLegacy;
    if (step % 500 == 0 || step + 1 == options.steps) {
      std::cout << "[stage2Audit] step=" << step << " t=" << step * dt
                << " meanUx=" << meanUx << " maxAbsUx=" << maxAbsUx
                << " qxLegacy=" << qxLegacy << " nonfinite=" << nonfiniteCount << std::endl;
    }
  }
  csv.close();

  const double qxTolerance = 1e-13;
  std::ofstream summary(outputDir / "run_summary.txt");
  summary << std::scientific << std::setprecision(16);
  summary << "run_id=" << options.runId << '\n';
  summary << "requested_steps=" << options.steps << '\n';
  summary << "completed_steps=" << options.steps << '\n';
  summary << "mass_audit=" << options.massAudit << '\n';
  summary << "force_audit_pass=" << forceAuditPass << '\n';
  summary << "lattice_force_x=" << forceMin[0] << '\n';
  summary << "lattice_force_y=" << forceMin[1] << '\n';
  summary << "lattice_force_z=" << forceMin[2] << '\n';
  summary << "body_accel_x_m_s2=" << ax << '\n';
  summary << "body_accel_y_applied_m_s2=0\nbody_accel_z_applied_m_s2=0\n";
  summary << "final_volume_mean_ux_m_s=" << finalMeanUx << '\n';
  summary << "final_max_abs_ux_m_s=" << finalMaxAbsUx << '\n';
  summary << "final_Qx_legacy_m3_s=" << finalQx << '\n';
  summary << "final_qx_legacy_m_s=" << finalQxLegacySuperficial << '\n';
  summary << "final_Bxx_numerical_residual_m2=" << finalBxx << '\n';
  summary << "final_Qx_plane_groove1_m3_s=" << finalQxPlane0 << '\n';
  summary << "final_Qx_plane_groove2_m3_s=" << finalQxPlane1 << '\n';
  summary << "max_fluid_mass_abs_relative_drift=" << maxMassAbsRel << '\n';
  summary << "max_fluid_density_deviation=" << maxDensityDeviationAll << '\n';
  summary << "total_nonfinite_count=" << totalNonfinite << '\n';
  summary << "qx_tolerance_m_s=" << qxTolerance << '\n';
  summary << "final_qx_pass=" << (std::abs(finalQxLegacySuperficial) < qxTolerance) << '\n';
  summary << "end_reason=fixed_step_limit_completed\n";
  summary.close();

  if (totalNonfinite != 0) return 3;
  return 0;
}
