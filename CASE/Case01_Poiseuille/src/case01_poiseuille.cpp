#include <olb.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <string>
#include <vector>

using namespace olb;

using T = double;
using DESCRIPTOR = descriptors::D3Q19<descriptors::FORCE>;

namespace {

constexpr T dx = 5.0e-9;
constexpr T dt = 1.0e-11;
constexpr T lx = 240.0e-9;
constexpr T ly = 240.0e-9;
constexpr T height = 75.0e-9;
constexpr T rhoPhys = 1000.0;
constexpr T nuPhys = 1.0e-6;
constexpr T muPhys = rhoPhys * nuPhys;
constexpr T accelerationY = 1.0e5;
constexpr T areaPlan = lx * ly;
constexpr int overlap = 3;
constexpr int convergenceWindow = 1000;
constexpr int maximumSteps = 30000;
constexpr T relativeStdTolerance = 1.0e-6;
constexpr T relativeSpanTolerance = 5.0e-6;
constexpr T sectionTolerance = 1.0e-5;
constexpr T massTolerance = 1.0e-10;
constexpr T densityTolerance = 1.0e-6;
constexpr T machTolerance = 0.05;
constexpr T crossFluxTolerance = 1.0e-12;
constexpr T profileL2Tolerance = 0.02;
constexpr T jyRelativeErrorTolerance = 0.02;

struct Measurement {
  long long fluidNodes = 0;
  T fluidVolume = 0.0;
  T fluidMass = 0.0;
  T maxDensityDeviation = 0.0;
  T maxLatticeSpeed = 0.0;
  std::array<T, 3> integratedVelocity{};
  std::array<T, 3> meanVelocity{};
  std::array<T, 3> fluxJ{};
  T sectionQ1 = 0.0;
  T sectionQ2 = 0.0;
  bool finite = true;
};

struct FluxWindow {
  std::deque<T> values;

  void add(T value)
  {
    values.push_back(value);
    if (static_cast<int>(values.size()) > convergenceWindow) {
      values.pop_front();
    }
  }

  bool full() const
  {
    return static_cast<int>(values.size()) == convergenceWindow;
  }

  void metrics(T& relativeStd, T& relativeSpan) const
  {
    const T mean = std::accumulate(values.begin(), values.end(), T{}) / values.size();
    T squared = 0.0;
    for (T value : values) {
      squared += (value - mean) * (value - mean);
    }
    const T sampleStd = std::sqrt(squared / (values.size() - 1));
    const auto extrema = std::minmax_element(values.begin(), values.end());
    relativeStd = sampleStd / std::abs(mean);
    relativeSpan = (*extrema.second - *extrema.first) / std::abs(mean);
  }
};

int materialAt(const Vector<T, 3>& position)
{
  if (position[2] < 0.0) {
    return 2;
  }
  if (position[2] >= height) {
    return 3;
  }
  return 1;
}

template <typename GEOMETRY>
std::array<long long, 4> countMaterials(GEOMETRY& geometry)
{
  std::array<long long, 4> counts{};
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticePosition) {
      const int material = block.getMaterial(latticePosition);
      if (material >= 0 && material < static_cast<int>(counts.size())) {
        ++counts[material];
      }
    });
  }
  return counts;
}

template <typename LATTICE, typename GEOMETRY>
Measurement measure(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter)
{
  Measurement value;
  constexpr int sectionIndex1 = 12;
  constexpr int sectionIndex2 = 36;
  const T cellVolume = dx * dx * dx;
  const T cellArea = dx * dx;

  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < lattice.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticePosition) {
      if (blockGeometry.getMaterial(latticePosition) != 1) {
        return;
      }

      auto cell = block.get(latticePosition);
      T latticeVelocity[3]{};
      cell.computeU(latticeVelocity);
      const T rho = cell.computeRho();
      const T latticeSpeed = std::sqrt(
        latticeVelocity[0] * latticeVelocity[0]
        + latticeVelocity[1] * latticeVelocity[1]
        + latticeVelocity[2] * latticeVelocity[2]);

      ++value.fluidNodes;
      value.fluidVolume += cellVolume;
      value.fluidMass += rho * rhoPhys * cellVolume;
      value.maxDensityDeviation = std::max(value.maxDensityDeviation, std::abs(rho - 1.0));
      value.maxLatticeSpeed = std::max(value.maxLatticeSpeed, latticeSpeed);
      value.finite = value.finite && std::isfinite(rho) && std::isfinite(latticeSpeed);

      for (int direction = 0; direction < 3; ++direction) {
        const T physicalVelocity = converter.getPhysVelocity(latticeVelocity[direction]);
        value.integratedVelocity[direction] += physicalVelocity * cellVolume;
        value.finite = value.finite && std::isfinite(physicalVelocity);
      }

      const T physicalUy = converter.getPhysVelocity(latticeVelocity[1]);
      if (latticePosition[1] == sectionIndex1) {
        value.sectionQ1 += physicalUy * cellArea;
      }
      if (latticePosition[1] == sectionIndex2) {
        value.sectionQ2 += physicalUy * cellArea;
      }
    });
  }

  for (int direction = 0; direction < 3; ++direction) {
    value.meanVelocity[direction] = value.integratedVelocity[direction] / value.fluidVolume;
    value.fluxJ[direction] = value.integratedVelocity[direction] / areaPlan;
  }
  return value;
}

template <typename LATTICE, typename GEOMETRY>
T writeVelocityProfile(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  const std::filesystem::path& outputPath)
{
  const int nz = static_cast<int>(std::llround(height / dx));
  std::vector<T> velocitySum(nz, 0.0);
  std::vector<long long> counts(nz, 0);

  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < lattice.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticePosition) {
      if (blockGeometry.getMaterial(latticePosition) != 1) {
        return;
      }
      const T z = blockGeometry.getPhysR(latticePosition)[2];
      const int iz = static_cast<int>(std::llround(z / dx - 0.5));
      if (iz < 0 || iz >= nz) {
        return;
      }
      T latticeVelocity[3]{};
      block.get(latticePosition).computeU(latticeVelocity);
      velocitySum[iz] += converter.getPhysVelocity(latticeVelocity[1]);
      ++counts[iz];
    });
  }

  std::ofstream profile(outputPath);
  profile << std::setprecision(17)
          << "z_m,z_nm,u_y_numerical_m_s,u_y_analytic_m_s,point_relative_error\n";
  T numerator = 0.0;
  T denominator = 0.0;
  for (int iz = 0; iz < nz; ++iz) {
    const T z = (iz + 0.5) * dx;
    const T numerical = velocitySum[iz] / counts[iz];
    const T analytic = rhoPhys * accelerationY * z * (height - z) / (2.0 * muPhys);
    const T pointError = (numerical - analytic) / analytic;
    numerator += (numerical - analytic) * (numerical - analytic);
    denominator += analytic * analytic;
    profile << z << ',' << z * 1.0e9 << ',' << numerical << ',' << analytic << ',' << pointError << '\n';
  }
  return std::sqrt(numerator / denominator);
}

template <typename LATTICE, typename GEOMETRY>
void writeVtk(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  int step,
  bool createMaster)
{
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  SuperVTMwriter3D<T> writer("case01_poiseuille", overlap);
  SuperGeometryF3D<T> material(geometry);
  material.getName() = "material";
  SuperLatticePhysVelocity3D<T, DESCRIPTOR> velocity(lattice, converter);
  velocity.getName() = "velocity_m_s";
  SuperLatticePhysPressure3D<T, DESCRIPTOR> pressure(lattice, converter);
  pressure.getName() = "pressure_Pa";
  writer.addFunctor(material);
  writer.addFunctor(velocity);
  writer.addFunctor(pressure);
  if (createMaster) {
    writer.createMasterFile();
  }
  writer.write(step);
}

} // namespace

int main(int argc, char* argv[])
{
  initialize(&argc, &argv);
  std::cout << std::setprecision(17) << std::boolalpha;

  if (argc != 2) {
    std::cerr << "usage: case01_poiseuille OUTPUT_DIRECTORY\n";
    return 2;
  }
  if (singleton::mpi().getSize() != 1) {
    std::cerr << "Gate 1 frozen protocol requires exactly one MPI rank\n";
    return 2;
  }

  const std::filesystem::path outputDirectory(argv[1]);
  if (!std::filesystem::exists(outputDirectory / "run_manifest.txt")) {
    std::cerr << "pre-run run_manifest.txt is required\n";
    return 2;
  }
  if (std::filesystem::exists(outputDirectory / "diagnostics.csv")) {
    std::cerr << "refusing to overwrite an existing formal run\n";
    return 2;
  }
  singleton::directories().setOutputDir((outputDirectory.string() + "/").c_str());

  const int nx = static_cast<int>(std::llround(lx / dx));
  const int ny = static_cast<int>(std::llround(ly / dx));
  const int nz = static_cast<int>(std::llround(height / dx));
  const long long expectedFluidNodes = static_cast<long long>(nx) * ny * nz;
  const T expectedFluidVolume = lx * ly * height;
  const T analyticMeanVelocity = rhoPhys * accelerationY * height * height / (12.0 * muPhys);
  const T analyticJy = rhoPhys * accelerationY * height * height * height / (12.0 * muPhys);
  const T analyticKyy = height * height * height / 12.0;
  const T analyticByy = height * height / 12.0;
  const T analyticResistance = 12.0 * muPhys / (height * height * height);

  IndicatorCuboid3D<T> domain(
    {lx - dx, ly - dx, height + 20.0e-9},
    {dx / 2.0, dx / 2.0, -dx / 2.0});
  CuboidDecomposition<T, 3> cuboids(domain, dx, 1);
  cuboids.setPeriodicity({true, true, false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T, 3> geometry(cuboids, loadBalancer, overlap);

  for (int iC = 0; iC < loadBalancer.size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticePosition) {
      block.set(latticePosition, materialAt(block.getPhysR(latticePosition)));
    });
  }
  geometry.communicate();
  geometry.checkForErrors(false);
  const auto initialMaterials = countMaterials(geometry);

  UnitConverter<T, DESCRIPTOR> converter(dx, dt, lx, 1.0, nuPhys, rhoPhys);
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);
  boundary::set<boundary::BounceBack>(lattice, geometry, 2);
  boundary::set<boundary::BounceBack>(lattice, geometry, 3);

  AnalyticalConst3D<T, T> one(1.0);
  AnalyticalConst3D<T, T> zeroVelocity(0.0, 0.0, 0.0);
  lattice.defineRhoU(geometry.getMaterialIndicator(1), one, zeroVelocity);
  lattice.iniEquilibrium(geometry, 1, one, zeroVelocity);
  Vector<T, 3> force{0.0, accelerationY * dt * dt / dx, 0.0};
  fields::set<descriptors::FORCE>(lattice, geometry.getMaterialIndicator(1), force);
  lattice.setParameter<descriptors::OMEGA>(converter.getLatticeRelaxationFrequency());
  lattice.initialize();

  writeVtk(lattice, geometry, converter, 0, true);
  const Measurement initial = measure(lattice, geometry, converter);
  const bool initialGeometryPass =
    initialMaterials[1] == expectedFluidNodes
    && std::abs(initial.fluidVolume - expectedFluidVolume) <= 1.0e-32;

  std::ofstream diagnostics(outputDirectory / "diagnostics.csv");
  diagnostics << std::setprecision(17)
    << "step,time_s,fluid_nodes,fluid_volume_m3,fluid_mass_kg,mass_signed_relative,mass_abs_relative,"
       "max_density_deviation_step,max_density_deviation_so_far,mean_ux_m_s,mean_uy_m_s,mean_uz_m_s,"
       "Jx_m2_s,Jy_m2_s,Jz_m2_s,RJ_Pa_s_per_m3,RJ_defined,Q_section1_m3_s,Q_section2_m3_s,"
       "section_relative_difference,max_speed_m_s,Mach_step,Mach_max_so_far,window_rel_std_sample,"
       "window_rel_span,cross_flux_max_so_far,finite\n";

  FluxWindow window;
  T maxMassRelativeDrift = 0.0;
  T maxDensityDeviation = 0.0;
  T maxMach = 0.0;
  T maxCrossFlux = 0.0;
  T windowRelativeStd = std::numeric_limits<T>::infinity();
  T windowRelativeSpan = std::numeric_limits<T>::infinity();
  bool converged = false;
  int finalStep = 0;

  auto record = [&](int step, const Measurement& state) {
    const T massRelative = (state.fluidMass - initial.fluidMass) / initial.fluidMass;
    const T mach = state.maxLatticeSpeed / std::sqrt(T(1.0 / 3.0));
    const T maxSpeed = converter.getPhysVelocity(state.maxLatticeSpeed);
    const T sectionDenominator = std::max(std::abs(state.sectionQ1), std::abs(state.sectionQ2));
    const T sectionDifference = sectionDenominator > 0.0
      ? std::abs(state.sectionQ1 - state.sectionQ2) / sectionDenominator : 0.0;
    const T crossFlux = std::max(std::abs(state.fluxJ[0]), std::abs(state.fluxJ[2]));
    const bool resistanceDefined = state.fluxJ[1] > 0.0;
    const T resistance = resistanceDefined ? rhoPhys * accelerationY / state.fluxJ[1] : 0.0;

    maxMassRelativeDrift = std::max(maxMassRelativeDrift, std::abs(massRelative));
    maxDensityDeviation = std::max(maxDensityDeviation, state.maxDensityDeviation);
    maxMach = std::max(maxMach, mach);
    maxCrossFlux = std::max(maxCrossFlux, crossFlux);
    window.add(state.fluxJ[1]);
    if (window.full()) {
      window.metrics(windowRelativeStd, windowRelativeSpan);
    }

    diagnostics << step << ',' << step * dt << ',' << state.fluidNodes << ',' << state.fluidVolume << ','
      << state.fluidMass << ',' << massRelative << ',' << std::abs(massRelative) << ','
      << state.maxDensityDeviation << ',' << maxDensityDeviation << ','
      << state.meanVelocity[0] << ',' << state.meanVelocity[1] << ',' << state.meanVelocity[2] << ','
      << state.fluxJ[0] << ',' << state.fluxJ[1] << ',' << state.fluxJ[2] << ','
      << resistance << ',' << resistanceDefined << ',' << state.sectionQ1 << ',' << state.sectionQ2 << ','
      << sectionDifference << ',' << maxSpeed << ',' << mach << ',' << maxMach << ','
      << (window.full() ? windowRelativeStd : -1.0) << ','
      << (window.full() ? windowRelativeSpan : -1.0) << ',' << maxCrossFlux << ',' << state.finite << '\n';

    const bool windowPass = window.full()
      && windowRelativeStd <= relativeStdTolerance
      && windowRelativeSpan <= relativeSpanTolerance;
    const bool diagnosticsPass = state.finite
      && maxMassRelativeDrift <= massTolerance
      && maxDensityDeviation <= densityTolerance
      && maxMach <= machTolerance
      && maxCrossFlux <= crossFluxTolerance
      && sectionDifference <= sectionTolerance;
    return windowPass && diagnosticsPass;
  };

  record(0, initial);
  std::cout << "run_scope=Gate1_Case01_dx5_a1e5_only\n"
            << "maximum_steps=" << maximumSteps << " convergence_window=" << convergenceWindow << '\n';

  for (int step = 1; step <= maximumSteps; ++step) {
    lattice.collideAndStream();
    const Measurement state = measure(lattice, geometry, converter);
    converged = record(step, state);
    finalStep = step;
    if (step % 1000 == 0 || converged) {
      std::cout << "step=" << step << " Jy_m2_s=" << state.fluxJ[1]
                << " window_rel_std=" << windowRelativeStd
                << " window_rel_span=" << windowRelativeSpan
                << " converged=" << converged << '\n';
    }
    if (converged) {
      break;
    }
  }
  diagnostics.close();

  const Measurement final = measure(lattice, geometry, converter);
  const auto finalMaterials = countMaterials(geometry);
  const bool materialUnchanged = finalMaterials == initialMaterials;
  const T finalMassRelative = (final.fluidMass - initial.fluidMass) / initial.fluidMass;
  const T sectionDenominator = std::max(std::abs(final.sectionQ1), std::abs(final.sectionQ2));
  const T sectionRelativeDifference = sectionDenominator > 0.0
    ? std::abs(final.sectionQ1 - final.sectionQ2) / sectionDenominator : 0.0;
  const T finalMach = final.maxLatticeSpeed / std::sqrt(T(1.0 / 3.0));
  const T finalMaxSpeed = converter.getPhysVelocity(final.maxLatticeSpeed);
  const T numericalJy = final.fluxJ[1];
  const T numericalKyy = muPhys * numericalJy / (rhoPhys * accelerationY);
  const T numericalByy = numericalKyy / height;
  const T numericalResistance = rhoPhys * accelerationY / numericalJy;
  const T jyRelativeError = (numericalJy - analyticJy) / analyticJy;
  const T resistanceRelativeError = (numericalResistance - analyticResistance) / analyticResistance;
  const T profileL2RelativeError = writeVelocityProfile(
    lattice, geometry, converter, outputDirectory / "velocity_profile.csv");

  writeVtk(lattice, geometry, converter, finalStep, false);

  const bool acceptancePass = initialGeometryPass
    && materialUnchanged
    && final.finite
    && converged
    && maxMassRelativeDrift <= massTolerance
    && maxDensityDeviation <= densityTolerance
    && maxMach <= machTolerance
    && maxCrossFlux <= crossFluxTolerance
    && sectionRelativeDifference <= sectionTolerance
    && profileL2RelativeError <= profileL2Tolerance
    && std::abs(jyRelativeError) <= jyRelativeErrorTolerance;

  std::ofstream result(outputDirectory / "result.txt");
  result << std::setprecision(17) << std::boolalpha
    << "run_scope=Gate1_Case01_dx5_a1e5_only\n"
    << "PASS=" << acceptancePass << '\n'
    << "converged=" << converged << '\n'
    << "normal_exit_planned=" << acceptancePass << '\n'
    << "stop_reason=" << (converged ? "frozen_window_converged" : "maximum_steps_without_convergence") << '\n'
    << "steps_completed=" << finalStep << '\n'
    << "Lx_m=" << lx << '\n'
    << "Ly_m=" << ly << '\n'
    << "H_m=" << height << '\n'
    << "dx_m=" << dx << '\n'
    << "dt_s=" << dt << '\n'
    << "tau=" << converter.getLatticeRelaxationTime() << '\n'
    << "descriptor=D3Q19_FORCE\n"
    << "collision=ForcedBGK\n"
    << "acceleration_y_m_s2=" << accelerationY << '\n'
    << "force_lattice=0," << force[1] << ",0\n"
    << "fluid_nodes=" << final.fluidNodes << '\n'
    << "fluid_volume_m3=" << final.fluidVolume << '\n'
    << "material_unchanged=" << materialUnchanged << '\n'
    << "max_mass_abs_relative=" << maxMassRelativeDrift << '\n'
    << "final_mass_signed_relative=" << finalMassRelative << '\n'
    << "max_density_deviation=" << maxDensityDeviation << '\n'
    << "max_speed_m_s=" << finalMaxSpeed << '\n'
    << "max_Mach=" << maxMach << '\n'
    << "final_Mach=" << finalMach << '\n'
    << "max_cross_flux_m2_s=" << maxCrossFlux << '\n'
    << "Q_section1_m3_s=" << final.sectionQ1 << '\n'
    << "Q_section2_m3_s=" << final.sectionQ2 << '\n'
    << "section_flux_relative_difference=" << sectionRelativeDifference << '\n'
    << "window_rel_std_sample=" << windowRelativeStd << '\n'
    << "window_rel_span=" << windowRelativeSpan << '\n'
    << "mean_uy_m_s=" << final.meanVelocity[1] << '\n'
    << "Jy_m2_s=" << numericalJy << '\n'
    << "Kyy_m3=" << numericalKyy << '\n'
    << "Byy_m2=" << numericalByy << '\n'
    << "RJ_Pa_s_per_m3=" << numericalResistance << '\n'
    << "analytic_mean_uy_m_s=" << analyticMeanVelocity << '\n'
    << "analytic_Jy_m2_s=" << analyticJy << '\n'
    << "analytic_Kyy_m3=" << analyticKyy << '\n'
    << "analytic_Byy_m2=" << analyticByy << '\n'
    << "analytic_RJ_Pa_s_per_m3=" << analyticResistance << '\n'
    << "Jy_relative_error=" << jyRelativeError << '\n'
    << "RJ_relative_error=" << resistanceRelativeError << '\n'
    << "velocity_profile_L2_relative_error=" << profileL2RelativeError << '\n'
    << "exit_code=" << (acceptancePass ? 0 : 3) << '\n';
  result.close();

  std::cout << "PASS=" << acceptancePass << " steps_completed=" << finalStep
            << " Jy_m2_s=" << numericalJy << " RJ_Pa_s_per_m3=" << numericalResistance
            << " profile_L2_relative_error=" << profileL2RelativeError << '\n';
  return acceptancePass ? 0 : 3;
}
