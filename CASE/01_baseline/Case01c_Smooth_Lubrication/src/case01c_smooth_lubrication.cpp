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
constexpr int nx = 48;
constexpr int ny = 48;
constexpr int nz = 15;
constexpr long long expectedFluidNodes = 1LL * nx * ny * nz;
constexpr long long expectedWallLinks = 2LL * nx * ny * 5LL;
constexpr int convergenceWindow = 1000;
constexpr int maximumSteps = 30000;
constexpr T qTolerance = 64.0 * std::numeric_limits<T>::epsilon();
constexpr T relativeStdTolerance = 1.0e-6;
constexpr T relativeSpanTolerance = 5.0e-6;
constexpr T sectionTolerance = 1.0e-5;
constexpr T massTolerance = 1.0e-10;
constexpr T densityTolerance = 1.0e-6;
constexpr T machTolerance = 0.05;
constexpr T crossFluxTolerance = 1.0e-12;
constexpr T profileL2Tolerance = 0.02;
constexpr T jyRelativeErrorTolerance = 0.02;

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

struct BoundaryAudit {
  long long candidateLinks = 0;
  long long validDistanceLinks = 0;
  long long exactHalfwayLinks = 0;
  long long installedLinks = 0;
  long long installedHalfwayLinks = 0;
  long long geometricFallbacks = 0;
  long long missingFluidNeighborFallbacks = 0;
  long long unresolvedLinks = 0;
  T qMin = std::numeric_limits<T>::infinity();
  T qMax = -std::numeric_limits<T>::infinity();
  bool pass = false;
};

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
  T lowerAdjacentUy = 0.0;
  T upperAdjacentUy = 0.0;
  long long lowerAdjacentNodes = 0;
  long long upperAdjacentNodes = 0;
  bool finite = true;
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

class ExactPlanarChannelIndicator final : public IndicatorCuboid3D<T> {
public:
  ExactPlanarChannelIndicator()
    : IndicatorCuboid3D<T>(
        {lx + 4.0 * dx, ly + 4.0 * dx, height},
        {-2.0 * dx, -2.0 * dx, 0.0})
  { }

  bool distance(
    T& distance,
    const Vector<T, 3>& origin,
    const Vector<T, 3>& direction,
    int = -1) override
  {
    if (direction[2] == 0.0) {
      return false;
    }
    const T wallZ = direction[2] < 0.0 ? 0.0 : height;
    const T lambda = (wallZ - origin[2]) / direction[2];
    if (lambda < 0.0 || lambda > 1.0) {
      return false;
    }
    const Vector<T, 3> intersection = origin + lambda * direction;
    if (intersection[0] < -2.0 * dx || intersection[0] > lx + 2.0 * dx
        || intersection[1] < -2.0 * dx || intersection[1] > ly + 2.0 * dx) {
      return false;
    }
    distance = std::abs(lambda) * util::norm<3>(direction);
    return std::isfinite(distance);
  }
};

int wrapPeriodicIndex(int value, int extent)
{
  value %= extent;
  return value < 0 ? value + extent : value;
}

Vector<int, 3> wrapPeriodicXY(Vector<int, 3> latticeR)
{
  latticeR[0] = wrapPeriodicIndex(latticeR[0], nx);
  latticeR[1] = wrapPeriodicIndex(latticeR[1], ny);
  return latticeR;
}

template <typename GEOMETRY>
std::array<long long, 4> countMaterials(GEOMETRY& geometry)
{
  std::array<long long, 4> counts{};
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      const int material = block.getMaterial(latticeR);
      if (material >= 0 && material < static_cast<int>(counts.size())) {
        ++counts[material];
      }
    });
  }
  return counts;
}

template <typename GEOMETRY>
BoundaryAudit auditGeometryLinks(
  GEOMETRY& geometry,
  IndicatorF3D<T>& analyticalBoundary)
{
  BoundaryAudit audit;
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> fluidR) {
      if (block.getMaterial(fluidR) != 1) {
        return;
      }
      const Vector<T, 3> fluidPhysR = block.getPhysR(fluidR);
      for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
        const auto c = descriptors::c<DESCRIPTOR>(iPop);
        const Vector<int, 3> solidR(fluidR + c);
        const int wallMaterial = block.getMaterial(wrapPeriodicXY(solidR));
        if (wallMaterial != 2 && wallMaterial != 3) {
          continue;
        }

        ++audit.candidateLinks;
        const T norm = dx * util::norm<3>(c);
        const Vector<T, 3> direction = dx * c;
        T distance = -1.0;
        T q = -1.0;
        if (analyticalBoundary.distance(
              distance, fluidPhysR.data(), direction, block.getIcGlob())) {
          q = distance / norm;
        }
        if (!(q >= 0.0 && q <= 1.0)) {
          ++audit.geometricFallbacks;
        }
        else {
          ++audit.validDistanceLinks;
          audit.qMin = std::min(audit.qMin, q);
          audit.qMax = std::max(audit.qMax, q);
          if (std::abs(q - 0.5) <= qTolerance) {
            ++audit.exactHalfwayLinks;
          }
        }

        const Vector<int, 3> fluidSideR(fluidR - c);
        if (!block.isInside(fluidSideR) || block.getMaterial(fluidSideR) != 1) {
          ++audit.missingFluidNeighborFallbacks;
        }
      }
    });
  }
  return audit;
}

template <typename LATTICE, typename GEOMETRY>
void auditInstalledDistances(
  LATTICE& lattice,
  GEOMETRY& geometry,
  BoundaryAudit& audit)
{
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      const auto q = block.get(latticeR)
        .template getFieldPointer<descriptors::BOUZIDI_DISTANCE>();
      for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
        if (q[iPop] > 0.0) {
          ++audit.installedLinks;
          if (std::abs(q[iPop] - 0.5) <= qTolerance) {
            ++audit.installedHalfwayLinks;
          }
          else {
            ++audit.unresolvedLinks;
          }
        }
      }
    });
  }

  audit.pass = audit.candidateLinks == expectedWallLinks
    && audit.validDistanceLinks == expectedWallLinks
    && audit.exactHalfwayLinks == expectedWallLinks
    && audit.installedLinks == expectedWallLinks
    && audit.installedHalfwayLinks == expectedWallLinks
    && audit.geometricFallbacks == 0
    && audit.missingFluidNeighborFallbacks == 0
    && audit.unresolvedLinks == 0
    && std::abs(audit.qMin - 0.5) <= qTolerance
    && std::abs(audit.qMax - 0.5) <= qTolerance;
}

void writeBoundaryAudit(
  const std::filesystem::path& path,
  const BoundaryAudit& audit,
  bool geometryPass)
{
  std::ofstream out(path);
  out << std::setprecision(17) << std::boolalpha
      << "geometry_PASS=" << geometryPass << '\n'
      << "q_audit_PASS=" << audit.pass << '\n'
      << "theoretical_candidate_links=" << expectedWallLinks << '\n'
      << "candidate_links=" << audit.candidateLinks << '\n'
      << "valid_distance_links=" << audit.validDistanceLinks << '\n'
      << "q_min=" << audit.qMin << '\n'
      << "q_max=" << audit.qMax << '\n'
      << "q_tolerance=" << qTolerance << '\n'
      << "q_equal_0p5_count=" << audit.exactHalfwayLinks << '\n'
      << "installed_links=" << audit.installedLinks << '\n'
      << "installed_q_equal_0p5_count=" << audit.installedHalfwayLinks << '\n'
      << "geometric_fallback_count=" << audit.geometricFallbacks << '\n'
      << "missing_fluid_neighbor_fallback_count="
      << audit.missingFluidNeighborFallbacks << '\n'
      << "unresolved_link_count=" << audit.unresolvedLinks << '\n';
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
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      auto cell = block.get(latticeR);
      T uLat[3]{};
      cell.computeU(uLat);
      const T rho = cell.computeRho();
      const T speedLat = std::sqrt(
        uLat[0] * uLat[0] + uLat[1] * uLat[1] + uLat[2] * uLat[2]);
      const T z = blockGeometry.getPhysR(latticeR)[2];

      ++value.fluidNodes;
      value.fluidVolume += cellVolume;
      value.fluidMass += rho * rhoPhys * cellVolume;
      value.maxDensityDeviation = std::max(
        value.maxDensityDeviation, std::abs(rho - 1.0));
      value.maxLatticeSpeed = std::max(value.maxLatticeSpeed, speedLat);
      value.finite = value.finite && std::isfinite(rho) && std::isfinite(speedLat);

      for (int iD = 0; iD < 3; ++iD) {
        const T uPhys = converter.getPhysVelocity(uLat[iD]);
        value.integratedVelocity[iD] += uPhys * cellVolume;
        value.finite = value.finite && std::isfinite(uPhys);
      }
      const T uy = converter.getPhysVelocity(uLat[1]);
      if (latticeR[1] == sectionIndex1) {
        value.sectionQ1 += uy * cellArea;
      }
      if (latticeR[1] == sectionIndex2) {
        value.sectionQ2 += uy * cellArea;
      }
      if (std::abs(z - 0.5 * dx) <= qTolerance * dx) {
        value.lowerAdjacentUy += uy;
        ++value.lowerAdjacentNodes;
      }
      if (std::abs(z - (height - 0.5 * dx)) <= qTolerance * dx) {
        value.upperAdjacentUy += uy;
        ++value.upperAdjacentNodes;
      }
    });
  }

  for (int iD = 0; iD < 3; ++iD) {
    value.meanVelocity[iD] = value.integratedVelocity[iD] / value.fluidVolume;
    value.fluxJ[iD] = value.integratedVelocity[iD] / areaPlan;
  }
  if (value.lowerAdjacentNodes > 0 && value.upperAdjacentNodes > 0) {
    value.lowerAdjacentUy /= value.lowerAdjacentNodes;
    value.upperAdjacentUy /= value.upperAdjacentNodes;
  }
  else {
    value.finite = false;
  }
  return value;
}

struct ProfileResult {
  T relativeL2 = 0.0;
  T offsetMean = 0.0;
  T offsetSpan = 0.0;
  T offsetSampleStd = 0.0;
};

template <typename LATTICE, typename GEOMETRY>
ProfileResult writeVelocityProfile(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  const std::filesystem::path& path)
{
  std::array<T, nz> sums{};
  std::array<long long, nz> counts{};
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      const T z = blockGeometry.getPhysR(latticeR)[2];
      const int iz = static_cast<int>(std::llround(z / dx - 0.5));
      if (iz < 0 || iz >= nz) {
        return;
      }
      T uLat[3]{};
      block.get(latticeR).computeU(uLat);
      sums[iz] += converter.getPhysVelocity(uLat[1]);
      ++counts[iz];
    });
  }

  ProfileResult result;
  std::array<T, nz> offsets{};
  T numerator = 0.0;
  T denominator = 0.0;
  std::ofstream out(path);
  out << std::setprecision(17)
      << "z_m,z_nm,u_LBM_m_s,u_theory_m_s,difference_m_s,point_relative_error\n";
  for (int iz = 0; iz < nz; ++iz) {
    const T z = (iz + 0.5) * dx;
    const T numerical = sums[iz] / counts[iz];
    const T analytic = rhoPhys * accelerationY * z * (height - z) / (2.0 * muPhys);
    offsets[iz] = numerical - analytic;
    numerator += offsets[iz] * offsets[iz];
    denominator += analytic * analytic;
    out << z << ',' << z * 1.0e9 << ',' << numerical << ',' << analytic
        << ',' << offsets[iz] << ',' << offsets[iz] / analytic << '\n';
  }
  result.relativeL2 = std::sqrt(numerator / denominator);
  result.offsetMean = std::accumulate(offsets.begin(), offsets.end(), T{}) / nz;
  const auto extrema = std::minmax_element(offsets.begin(), offsets.end());
  result.offsetSpan = *extrema.second - *extrema.first;
  T squared = 0.0;
  for (T value : offsets) {
    squared += (value - result.offsetMean) * (value - result.offsetMean);
  }
  result.offsetSampleStd = std::sqrt(squared / (nz - 1));
  return result;
}

} // namespace

int main(int argc, char* argv[])
{
  initialize(&argc, &argv);
  std::cout << std::setprecision(17) << std::boolalpha;
  if (argc != 3 || (std::string(argv[1]) != "precheck"
                   && std::string(argv[1]) != "steady")) {
    std::cerr << "usage: case01_bouzidi_steady precheck|steady OUTPUT_DIRECTORY\n";
    return 2;
  }
  if (singleton::mpi().getSize() != 1) {
    std::cerr << "Case01-Bouzidi steady validation requires one MPI rank\n";
    return 2;
  }

  const std::string mode(argv[1]);
  const std::filesystem::path outputDirectory(argv[2]);
  if (!std::filesystem::exists(outputDirectory / "run_manifest.txt")) {
    std::cerr << "pre-run run_manifest.txt is required\n";
    return 2;
  }
  if (std::filesystem::exists(outputDirectory / "result.txt")) {
    std::cerr << "refusing to overwrite existing result\n";
    return 2;
  }
  singleton::directories().setOutputDir((outputDirectory.string() + "/").c_str());

  const T expectedFluidVolume = lx * ly * height;
  const T analyticMeanVelocity = rhoPhys * accelerationY * height * height / (12.0 * muPhys);
  const T analyticJy = rhoPhys * accelerationY * std::pow(height, 3) / (12.0 * muPhys);
  const T analyticKyy = std::pow(height, 3) / 12.0;
  const T analyticByy = height * height / 12.0;
  const T analyticRj = 12.0 * muPhys / std::pow(height, 3);

  IndicatorCuboid3D<T> domain(
    {lx - dx, ly - dx, height + 20.0e-9},
    {dx / 2.0, dx / 2.0, -dx / 2.0});
  CuboidDecomposition<T, 3> cuboids(domain, dx, 1);
  cuboids.setPeriodicity({true, true, false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T, 3> geometry(cuboids, loadBalancer, overlap);
  geometry.setWriteIncrementalVTK(false);
  for (int iC = 0; iC < loadBalancer.size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      block.set(latticeR, materialAt(block.getPhysR(latticeR)));
    });
  }
  geometry.rename(0, 0);
  geometry.communicate();
  const bool geometryErrors = geometry.checkForErrors(false);
  const auto initialMaterials = countMaterials(geometry);
  const bool geometryPass = !geometryErrors
    && initialMaterials[1] == expectedFluidNodes;

  UnitConverter<T, DESCRIPTOR> converter(dx, dt, lx, 1.0, nuPhys, rhoPhys);
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);
  ExactPlanarChannelIndicator analyticalChannel;
  BoundaryAudit boundaryAudit = auditGeometryLinks(geometry, analyticalChannel);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 2, analyticalChannel);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 3, analyticalChannel);
  auditInstalledDistances(lattice, geometry, boundaryAudit);
  writeBoundaryAudit(
    outputDirectory / "boundary_audit.txt", boundaryAudit, geometryPass);

  const bool precheckPass = geometryPass && boundaryAudit.pass;
  if (mode == "precheck") {
    std::ofstream result(outputDirectory / "result.txt");
    result << std::setprecision(17) << std::boolalpha
      << "run_scope=Case01c_Smooth_Lubrication_precheck\n"
      << "formal_simulation=false\n"
      << "collide_and_stream_calls=0\n"
      << "geometry_PASS=" << geometryPass << '\n'
      << "material_0_count=" << initialMaterials[0] << '\n'
      << "material_1_fluid_count=" << initialMaterials[1] << '\n'
      << "material_2_lower_wall_count=" << initialMaterials[2] << '\n'
      << "material_3_upper_wall_count=" << initialMaterials[3] << '\n'
      << "expected_fluid_count=" << expectedFluidNodes << '\n'
      << "q_audit_PASS=" << boundaryAudit.pass << '\n'
      << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
      << "installed_links=" << boundaryAudit.installedLinks << '\n'
      << "q_min=" << boundaryAudit.qMin << '\n'
      << "q_max=" << boundaryAudit.qMax << '\n'
      << "geometric_fallback_count=" << boundaryAudit.geometricFallbacks << '\n'
      << "missing_fluid_neighbor_fallback_count="
      << boundaryAudit.missingFluidNeighborFallbacks << '\n'
      << "exit_code=" << (precheckPass ? 0 : 3) << '\n';
    std::cout << "precheck_PASS=" << precheckPass
              << " geometry_PASS=" << geometryPass
              << " q_audit_PASS=" << boundaryAudit.pass
              << " candidate_links=" << boundaryAudit.candidateLinks
              << " installed_links=" << boundaryAudit.installedLinks
              << " fallback_count="
              << boundaryAudit.geometricFallbacks
                   + boundaryAudit.missingFluidNeighborFallbacks << '\n';
    return precheckPass ? 0 : 3;
  }

  if (!precheckPass) {
    std::cerr << "steady run blocked by geometry or q precheck\n";
    return 3;
  }

  AnalyticalConst3D<T, T> one(1.0);
  AnalyticalConst3D<T, T> zeroVelocity(0.0, 0.0, 0.0);
  lattice.defineRhoU(geometry.getMaterialIndicator(1), one, zeroVelocity);
  lattice.iniEquilibrium(geometry, 1, one, zeroVelocity);
  Vector<T, 3> force{0.0, accelerationY * dt * dt / dx, 0.0};
  fields::set<descriptors::FORCE>(
    lattice, geometry.getMaterialIndicator(1), force);
  lattice.setParameter<descriptors::OMEGA>(
    converter.getLatticeRelaxationFrequency());
  lattice.initialize();

  const Measurement initial = measure(lattice, geometry, converter);
  const bool initialGeometryPass = geometryPass
    && initial.fluidNodes == expectedFluidNodes
    && std::abs(initial.fluidVolume - expectedFluidVolume) <= 1.0e-32;

  std::ofstream diagnostics(outputDirectory / "diagnostics.csv");
  diagnostics << std::setprecision(17)
    << "step,time_s,fluid_nodes,fluid_volume_m3,fluid_mass_kg,mean_rho_kg_m3,mass_signed_relative,mass_abs_relative,"
       "max_density_deviation_step,max_density_deviation_so_far,mean_ux_m_s,mean_uy_m_s,mean_uz_m_s,"
       "Jx_m2_s,Jy_m2_s,Jz_m2_s,RJ_Pa_s_per_m3,RJ_defined,Q_section1_m3_s,Q_section2_m3_s,"
       "section_relative_difference,max_speed_m_s,Mach_step,Mach_max_so_far,window_rel_std_sample,"
       "window_rel_span,cross_flux_max_so_far,lower_wall_adjacent_uy_m_s,"
       "upper_wall_adjacent_uy_m_s,finite\n";

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
    const T sectionDenominator = std::max(
      std::abs(state.sectionQ1), std::abs(state.sectionQ2));
    const T sectionDifference = sectionDenominator > 0.0
      ? std::abs(state.sectionQ1 - state.sectionQ2) / sectionDenominator : 0.0;
    const T crossFlux = std::max(std::abs(state.fluxJ[0]), std::abs(state.fluxJ[2]));
    const bool rjDefined = state.fluxJ[1] > 0.0;
    const T rj = rjDefined ? rhoPhys * accelerationY / state.fluxJ[1] : 0.0;

    maxMassRelativeDrift = std::max(maxMassRelativeDrift, std::abs(massRelative));
    maxDensityDeviation = std::max(maxDensityDeviation, state.maxDensityDeviation);
    maxMach = std::max(maxMach, mach);
    maxCrossFlux = std::max(maxCrossFlux, crossFlux);
    window.add(state.fluxJ[1]);
    if (window.full()) {
      window.metrics(windowRelativeStd, windowRelativeSpan);
    }

    diagnostics << step << ',' << step * dt << ',' << state.fluidNodes << ','
      << state.fluidVolume << ',' << state.fluidMass << ','
      << state.fluidMass / state.fluidVolume << ',' << massRelative << ','
      << std::abs(massRelative) << ',' << state.maxDensityDeviation << ','
      << maxDensityDeviation << ',' << state.meanVelocity[0] << ','
      << state.meanVelocity[1] << ',' << state.meanVelocity[2] << ','
      << state.fluxJ[0] << ',' << state.fluxJ[1] << ',' << state.fluxJ[2] << ','
      << rj << ',' << rjDefined << ',' << state.sectionQ1 << ',' << state.sectionQ2 << ','
      << sectionDifference << ',' << maxSpeed << ',' << mach << ',' << maxMach << ','
      << (window.full() ? windowRelativeStd : -1.0) << ','
      << (window.full() ? windowRelativeSpan : -1.0) << ',' << maxCrossFlux << ','
      << state.lowerAdjacentUy << ',' << state.upperAdjacentUy << ','
      << state.finite << '\n';

    const bool windowPass = window.full()
      && windowRelativeStd <= relativeStdTolerance
      && windowRelativeSpan <= relativeSpanTolerance;
    const bool diagnosticPass = state.finite
      && maxMassRelativeDrift <= massTolerance
      && maxDensityDeviation <= densityTolerance
      && maxMach <= machTolerance
      && maxCrossFlux <= crossFluxTolerance
      && sectionDifference <= sectionTolerance;
    return windowPass && diagnosticPass;
  };

  record(0, initial);
  std::cout << "run_scope=Case01c_Smooth_Lubrication_dx5_tau1p7\n"
            << "maximum_steps=" << maximumSteps
            << " convergence_window=" << convergenceWindow << '\n';
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
  const T sectionDenominator = std::max(
    std::abs(final.sectionQ1), std::abs(final.sectionQ2));
  const T sectionDifference = sectionDenominator > 0.0
    ? std::abs(final.sectionQ1 - final.sectionQ2) / sectionDenominator : 0.0;
  const T finalMach = final.maxLatticeSpeed / std::sqrt(T(1.0 / 3.0));
  const T finalMaxSpeed = converter.getPhysVelocity(final.maxLatticeSpeed);
  const T numericalJy = final.fluxJ[1];
  const T numericalKyy = muPhys * numericalJy / (rhoPhys * accelerationY);
  const T numericalByy = numericalKyy / height;
  const T numericalRj = rhoPhys * accelerationY / numericalJy;
  const T jyRelativeError = (numericalJy - analyticJy) / analyticJy;
  const T rjRelativeError = (numericalRj - analyticRj) / analyticRj;
  const ProfileResult profile = writeVelocityProfile(
    lattice, geometry, converter, outputDirectory / "velocity_profile.csv");

  const bool acceptancePass = initialGeometryPass
    && boundaryAudit.pass
    && materialUnchanged
    && final.finite
    && converged
    && maxMassRelativeDrift <= massTolerance
    && maxDensityDeviation <= densityTolerance
    && maxMach <= machTolerance
    && maxCrossFlux <= crossFluxTolerance
    && sectionDifference <= sectionTolerance
    && profile.relativeL2 <= profileL2Tolerance
    && std::abs(jyRelativeError) <= jyRelativeErrorTolerance;

  std::ofstream result(outputDirectory / "result.txt");
  result << std::setprecision(17) << std::boolalpha
    << "run_scope=Case01c_Smooth_Lubrication_dx5_tau1p7\n"
    << "formal_simulation=true\n"
    << "PASS=" << acceptancePass << '\n'
    << "converged=" << converged << '\n'
    << "normal_exit_planned=" << acceptancePass << '\n'
    << "stop_reason=" << (converged ? "frozen_window_converged" : "maximum_steps_without_convergence") << '\n'
    << "steps_completed=" << finalStep << '\n'
    << "geometry_PASS=" << initialGeometryPass << '\n'
    << "q_audit_PASS=" << boundaryAudit.pass << '\n'
    << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
    << "installed_links=" << boundaryAudit.installedLinks << '\n'
    << "fallback_count=" << boundaryAudit.geometricFallbacks
        + boundaryAudit.missingFluidNeighborFallbacks << '\n'
    << "Lx_m=" << lx << '\n'
    << "Ly_m=" << ly << '\n'
    << "H_m=" << height << '\n'
    << "dx_m=" << dx << '\n'
    << "dt_s=" << dt << '\n'
    << "tau=" << converter.getLatticeRelaxationTime() << '\n'
    << "descriptor=D3Q19_FORCE\n"
    << "collision=ForcedBGK\n"
    << "wall_boundary=Bouzidi_exact_planar\n"
    << "acceleration_y_m_s2=" << accelerationY << '\n'
    << "force_lattice=0," << accelerationY * dt * dt / dx << ",0\n"
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
    << "section_flux_relative_difference=" << sectionDifference << '\n'
    << "window_rel_std_sample=" << windowRelativeStd << '\n'
    << "window_rel_span=" << windowRelativeSpan << '\n'
    << "mean_uy_m_s=" << final.meanVelocity[1] << '\n'
    << "lower_wall_adjacent_uy_m_s=" << final.lowerAdjacentUy << '\n'
    << "upper_wall_adjacent_uy_m_s=" << final.upperAdjacentUy << '\n'
    << "J_LBM_m2_s=" << numericalJy << '\n'
    << "J_Reynolds_m2_s=" << analyticJy << '\n'
    << "R_LBM_Pa_s_per_m3=" << numericalRj << '\n'
    << "R_Reynolds_Pa_s_per_m3=" << analyticRj << '\n'
    << "relative_error_R=" << rjRelativeError << '\n'
    << "Jy_m2_s=" << numericalJy << '\n'
    << "Kyy_m3=" << numericalKyy << '\n'
    << "Byy_m2=" << numericalByy << '\n'
    << "RJ_Pa_s_per_m3=" << numericalRj << '\n'
    << "analytic_mean_uy_m_s=" << analyticMeanVelocity << '\n'
    << "analytic_Jy_m2_s=" << analyticJy << '\n'
    << "analytic_Kyy_m3=" << analyticKyy << '\n'
    << "analytic_Byy_m2=" << analyticByy << '\n'
    << "analytic_RJ_Pa_s_per_m3=" << analyticRj << '\n'
    << "Jy_relative_error=" << jyRelativeError << '\n'
    << "RJ_relative_error=" << rjRelativeError << '\n'
    << "velocity_profile_L2_relative_error=" << profile.relativeL2 << '\n'
    << "velocity_offset_mean_m_s=" << profile.offsetMean << '\n'
    << "velocity_offset_span_m_s=" << profile.offsetSpan << '\n'
    << "velocity_offset_sample_std_m_s=" << profile.offsetSampleStd << '\n'
    << "exit_code=" << (acceptancePass ? 0 : 3) << '\n';

  std::cout << "PASS=" << acceptancePass
            << " converged=" << converged
            << " steps=" << finalStep
            << " Jy_m2_s=" << numericalJy
            << " Jy_relative_error=" << jyRelativeError
            << " velocity_L2=" << profile.relativeL2
            << " max_mass_abs_relative=" << maxMassRelativeDrift << '\n';
  return acceptancePass ? 0 : 3;
}

