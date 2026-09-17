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
#include <stdexcept>
#include <string>
#include <vector>

using namespace olb;

using T = double;
using DESCRIPTOR = descriptors::D3Q19<descriptors::FORCE>;

namespace {

constexpr T lx = 240.0e-9;
constexpr T ly = 240.0e-9;
constexpr T height = 75.0e-9;
constexpr T rhoPhys = 1000.0;
constexpr T nuPhys = 1.0e-6;
constexpr T muPhys = rhoPhys * nuPhys;
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
constexpr T kRelativeErrorTolerance = 0.02;
// Summing O(10^5) cell volumes in double precision accumulates round-off.
// This is a bookkeeping check, not a physical mass-conservation gate.
constexpr T geometryVolumeRoundoffTolerance = 1.0e-10;
constexpr T offsetRelativeTolerance = 0.02;
constexpr T qTolerance = 64.0 * std::numeric_limits<T>::epsilon();

struct Parameters {
  std::string mode;
  std::filesystem::path outputDirectory;
  T dx = 0.0;
  T tau = 0.0;
  T accelerationY = 0.0;
  T dt = 0.0;
  int nx = 0;
  int ny = 0;
  int nz = 0;
  T firstFluidZ = 0.0;
  T lastFluidZ = 0.0;
  long long expectedFluidNodes = 0;
  long long expectedWallLinks = 0;
};

Parameters parseParameters(int argc, char* argv[])
{
  if (argc != 6) {
    throw std::runtime_error(
      "usage: g1_poiseuille_bouzidi_validation precheck|steady "
      "OUTPUT_DIRECTORY DX_NM TAU ACCELERATION_M_S2");
  }
  Parameters p;
  p.mode = argv[1];
  if (p.mode != "precheck" && p.mode != "steady") {
    throw std::runtime_error("mode must be precheck or steady");
  }
  p.outputDirectory = argv[2];
  p.dx = std::stod(argv[3]) * 1.0e-9;
  p.tau = std::stod(argv[4]);
  p.accelerationY = std::stod(argv[5]);
  if (!(p.dx > 0.0) || !(p.tau > 0.5) || !(p.accelerationY > 0.0)) {
    throw std::runtime_error("dx, tau and acceleration must be positive; tau must exceed 0.5");
  }
  p.nx = static_cast<int>(std::llround(lx / p.dx));
  p.ny = static_cast<int>(std::llround(ly / p.dx));
  p.nz = static_cast<int>(std::llround(height / p.dx));
  if (p.nx < 2 || p.ny < 2 || p.nz < 2
      || std::abs(p.nx * p.dx - lx) > 1.0e-12 * lx
      || std::abs(p.ny * p.dx - ly) > 1.0e-12 * ly) {
    throw std::runtime_error("dx must exactly divide Lx=Ly=240 nm and resolve the channel");
  }

  // Keep physical viscosity and the requested tau fixed during grid studies.
  // tau = 0.5 + 3*nu*dt/dx^2 for D3Q19 with cs^2=1/3.
  p.dt = (p.tau - 0.5) * p.dx * p.dx / (3.0 * nuPhys);
  p.firstFluidZ = 0.5 * (height - (p.nz - 1) * p.dx);
  p.lastFluidZ = p.firstFluidZ + (p.nz - 1) * p.dx;
  if (!(p.firstFluidZ > 0.0) || !(p.lastFluidZ < height)) {
    throw std::runtime_error("symmetric cell-centre placement failed for requested dx");
  }
  p.expectedFluidNodes = 1LL * p.nx * p.ny * p.nz;
  p.expectedWallLinks = 2LL * p.nx * p.ny * 5LL;
  return p;
}

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
  long long installedLinks = 0;
  long long geometricFallbacks = 0;
  long long missingFluidNeighborFallbacks = 0;
  long long unresolvedLinks = 0;
  T qMin = std::numeric_limits<T>::infinity();
  T qMax = -std::numeric_limits<T>::infinity();
  T installedQMin = std::numeric_limits<T>::infinity();
  T installedQMax = -std::numeric_limits<T>::infinity();
  bool pass = false;
};

struct Measurement {
  long long fluidNodes = 0;
  T fluidVolume = 0.0;
  T fluidMass = 0.0;
  T densityIntegral = 0.0;
  T maxDensityDeviation = 0.0;
  T maxLatticeSpeed = 0.0;
  std::array<T, 3> integratedVelocity{};
  std::array<T, 3> meanVelocity{};
  std::array<T, 3> fluxJ{};
  T meanRho = 0.0;
  T sectionQ1 = 0.0;
  T sectionQ2 = 0.0;
  bool finite = true;
};

struct ProfileResult {
  T relativeL2 = 0.0;
  T offsetMean = 0.0;
  T offsetSpan = 0.0;
  T offsetRelativeToAnalyticMax = 0.0;
};

T layerThickness(T z, const Parameters& p)
{
  const T lower = std::max(T{}, z - 0.5 * p.dx);
  const T upper = std::min(height, z + 0.5 * p.dx);
  return std::max(T{}, upper - lower);
}

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
  explicit ExactPlanarChannelIndicator(const Parameters& p)
    : IndicatorCuboid3D<T>(
        {lx + 4.0 * p.dx, ly + 4.0 * p.dx, height},
        {-2.0 * p.dx, -2.0 * p.dx, 0.0}),
      _dx(p.dx)
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
    if (intersection[0] < -2.0 * _dx || intersection[0] > lx + 2.0 * _dx
        || intersection[1] < -2.0 * _dx || intersection[1] > ly + 2.0 * _dx) {
      return false;
    }
    distance = std::abs(lambda) * util::norm<3>(direction);
    return std::isfinite(distance);
  }

private:
  T _dx;
};

int wrapPeriodicIndex(int value, int extent)
{
  value %= extent;
  return value < 0 ? value + extent : value;
}

Vector<int, 3> wrapPeriodicXY(Vector<int, 3> latticeR, const Parameters& p)
{
  latticeR[0] = wrapPeriodicIndex(latticeR[0], p.nx);
  latticeR[1] = wrapPeriodicIndex(latticeR[1], p.ny);
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
  IndicatorF3D<T>& analyticalBoundary,
  const Parameters& p)
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
        const int wallMaterial = block.getMaterial(wrapPeriodicXY(solidR, p));
        if (wallMaterial != 2 && wallMaterial != 3) {
          continue;
        }

        ++audit.candidateLinks;
        const T norm = p.dx * util::norm<3>(c);
        const Vector<T, 3> direction = p.dx * c;
        T distance = -1.0;
        T q = -1.0;
        if (analyticalBoundary.distance(
              distance, fluidPhysR.data(), direction, block.getIcGlob())) {
          q = distance / norm;
        }
        if (!(q > 0.0 && q <= 1.0 + qTolerance)) {
          ++audit.geometricFallbacks;
        }
        else {
          ++audit.validDistanceLinks;
          audit.qMin = std::min(audit.qMin, q);
          audit.qMax = std::max(audit.qMax, q);
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
  BoundaryAudit& audit,
  const Parameters& p)
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
          audit.installedQMin = std::min(audit.installedQMin, q[iPop]);
          audit.installedQMax = std::max(audit.installedQMax, q[iPop]);
          if (q[iPop] > 1.0 + qTolerance) {
            ++audit.unresolvedLinks;
          }
        }
      }
    });
  }

  audit.pass = audit.candidateLinks == p.expectedWallLinks
    && audit.validDistanceLinks == p.expectedWallLinks
    && audit.installedLinks == p.expectedWallLinks
    && audit.geometricFallbacks == 0
    && audit.missingFluidNeighborFallbacks == 0
    && audit.unresolvedLinks == 0
    && std::abs(audit.installedQMin - audit.qMin) <= qTolerance
    && std::abs(audit.installedQMax - audit.qMax) <= qTolerance;
}

void writeBoundaryAudit(
  const std::filesystem::path& path,
  const BoundaryAudit& audit,
  const Parameters& p,
  bool geometryPass)
{
  std::ofstream out(path);
  out << std::setprecision(17) << std::boolalpha
      << "geometry_PASS=" << geometryPass << '\n'
      << "q_audit_PASS=" << audit.pass << '\n'
      << "theoretical_candidate_links=" << p.expectedWallLinks << '\n'
      << "candidate_links=" << audit.candidateLinks << '\n'
      << "valid_distance_links=" << audit.validDistanceLinks << '\n'
      << "installed_links=" << audit.installedLinks << '\n'
      << "q_min=" << audit.qMin << '\n'
      << "q_max=" << audit.qMax << '\n'
      << "installed_q_min=" << audit.installedQMin << '\n'
      << "installed_q_max=" << audit.installedQMax << '\n'
      << "geometric_fallback_count=" << audit.geometricFallbacks << '\n'
      << "missing_fluid_neighbor_fallback_count="
      << audit.missingFluidNeighborFallbacks << '\n'
      << "unresolved_link_count=" << audit.unresolvedLinks << '\n';
}

template <typename LATTICE, typename GEOMETRY>
Measurement measure(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  const Parameters& p)
{
  Measurement value;
  const int sectionIndex1 = p.ny / 4;
  const int sectionIndex2 = 3 * p.ny / 4;

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
      const T dz = layerThickness(z, p);
      const T cellVolume = p.dx * p.dx * dz;
      const T sectionArea = p.dx * dz;

      ++value.fluidNodes;
      value.fluidVolume += cellVolume;
      value.fluidMass += rho * rhoPhys * cellVolume;
      value.densityIntegral += rho * cellVolume;
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
        value.sectionQ1 += uy * sectionArea;
      }
      if (latticeR[1] == sectionIndex2) {
        value.sectionQ2 += uy * sectionArea;
      }
    });
  }

  for (int iD = 0; iD < 3; ++iD) {
    value.meanVelocity[iD] = value.integratedVelocity[iD] / value.fluidVolume;
    value.fluxJ[iD] = value.integratedVelocity[iD] / areaPlan;
  }
  value.meanRho = value.densityIntegral / value.fluidVolume;
  return value;
}

template <typename LATTICE, typename GEOMETRY>
ProfileResult writeVelocityProfile(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  const Parameters& p,
  const std::filesystem::path& path)
{
  std::vector<T> sums(p.nz, 0.0);
  std::vector<long long> counts(p.nz, 0);
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      const T z = blockGeometry.getPhysR(latticeR)[2];
      const int iz = static_cast<int>(std::llround((z - p.firstFluidZ) / p.dx));
      if (iz < 0 || iz >= p.nz) {
        return;
      }
      T uLat[3]{};
      block.get(latticeR).computeU(uLat);
      sums[iz] += converter.getPhysVelocity(uLat[1]);
      ++counts[iz];
    });
  }

  ProfileResult result;
  T numerator = 0.0;
  T denominator = 0.0;
  T offsetWeighted = 0.0;
  T weightSum = 0.0;
  T offsetMin = std::numeric_limits<T>::infinity();
  T offsetMax = -std::numeric_limits<T>::infinity();
  T analyticMax = 0.0;
  std::ofstream out(path);
  out << std::setprecision(17) << "z,u_LBM,u_analytic,error\n";
  for (int iz = 0; iz < p.nz; ++iz) {
    const T z = p.firstFluidZ + iz * p.dx;
    const T numerical = sums[iz] / counts[iz];
    const T analytic = rhoPhys * p.accelerationY * z * (height - z) / (2.0 * muPhys);
    const T offset = numerical - analytic;
    const T dz = layerThickness(z, p);
    numerator += dz * offset * offset;
    denominator += dz * analytic * analytic;
    offsetWeighted += dz * offset;
    weightSum += dz;
    offsetMin = std::min(offsetMin, offset);
    offsetMax = std::max(offsetMax, offset);
    analyticMax = std::max(analyticMax, std::abs(analytic));
    out << z << ',' << numerical << ',' << analytic << ',' << offset << '\n';
  }
  result.relativeL2 = std::sqrt(numerator / denominator);
  result.offsetMean = offsetWeighted / weightSum;
  result.offsetSpan = offsetMax - offsetMin;
  result.offsetRelativeToAnalyticMax = std::abs(result.offsetMean) / analyticMax;
  return result;
}

} // namespace

int main(int argc, char* argv[])
{
  initialize(&argc, &argv);
  std::cout << std::setprecision(17) << std::boolalpha;

  Parameters p;
  try {
    p = parseParameters(argc, argv);
  }
  catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
  if (singleton::mpi().getSize() != 1) {
    std::cerr << "G1-V2 requires exactly one MPI rank\n";
    return 2;
  }
  if (!std::filesystem::exists(p.outputDirectory / "run_manifest.txt")) {
    std::cerr << "pre-run run_manifest.txt is required\n";
    return 2;
  }
  if (std::filesystem::exists(p.outputDirectory / "result.txt")) {
    std::cerr << "refusing to overwrite an existing result\n";
    return 2;
  }
  singleton::directories().setOutputDir((p.outputDirectory.string() + "/").c_str());

  const T zOrigin = p.firstFluidZ - p.dx;
  const T zUpper = p.lastFluidZ + p.dx;
  IndicatorCuboid3D<T> domain(
    {lx - p.dx, ly - p.dx, zUpper - zOrigin},
    {p.dx / 2.0, p.dx / 2.0, zOrigin});
  CuboidDecomposition<T, 3> cuboids(domain, p.dx, 1);
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
    && initialMaterials[1] == p.expectedFluidNodes;

  UnitConverter<T, DESCRIPTOR> converter(p.dx, p.dt, lx, 1.0, nuPhys, rhoPhys);
  const bool converterPass = std::abs(converter.getLatticeRelaxationTime() - p.tau) <= 1.0e-12;
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);
  ExactPlanarChannelIndicator analyticalChannel(p);
  BoundaryAudit boundaryAudit = auditGeometryLinks(geometry, analyticalChannel, p);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 2, analyticalChannel);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 3, analyticalChannel);
  auditInstalledDistances(lattice, geometry, boundaryAudit, p);
  writeBoundaryAudit(
    p.outputDirectory / "boundary_audit.txt", boundaryAudit, p, geometryPass);

  const bool precheckPass = geometryPass && converterPass && boundaryAudit.pass;
  if (p.mode == "precheck") {
    std::ofstream result(p.outputDirectory / "result.txt");
    result << std::setprecision(17) << std::boolalpha
      << "run_scope=G1_V2_precheck\n"
      << "formal_simulation=false\n"
      << "collide_and_stream_calls=0\n"
      << "geometry_PASS=" << geometryPass << '\n'
      << "converter_PASS=" << converterPass << '\n'
      << "q_audit_PASS=" << boundaryAudit.pass << '\n'
      << "dx_m=" << p.dx << '\n'
      << "dt_s=" << p.dt << '\n'
      << "tau=" << converter.getLatticeRelaxationTime() << '\n'
      << "q_min=" << boundaryAudit.qMin << '\n'
      << "q_max=" << boundaryAudit.qMax << '\n'
      << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
      << "installed_links=" << boundaryAudit.installedLinks << '\n'
      << "exit_code=" << (precheckPass ? 0 : 3) << '\n';
    std::cout << "precheck_PASS=" << precheckPass
              << " geometry_PASS=" << geometryPass
              << " q_audit_PASS=" << boundaryAudit.pass
              << " q_min=" << boundaryAudit.qMin
              << " q_max=" << boundaryAudit.qMax << '\n';
    return precheckPass ? 0 : 3;
  }

  if (!precheckPass) {
    std::cerr << "steady run blocked by geometry, converter or boundary precheck\n";
    return 3;
  }

  AnalyticalConst3D<T, T> one(1.0);
  AnalyticalConst3D<T, T> zeroVelocity(0.0, 0.0, 0.0);
  lattice.defineRhoU(geometry.getMaterialIndicator(1), one, zeroVelocity);
  lattice.iniEquilibrium(geometry, 1, one, zeroVelocity);
  Vector<T, 3> force{0.0, p.accelerationY * p.dt * p.dt / p.dx, 0.0};
  fields::set<descriptors::FORCE>(
    lattice, geometry.getMaterialIndicator(1), force);
  lattice.setParameter<descriptors::OMEGA>(
    converter.getLatticeRelaxationFrequency());
  lattice.initialize();

  const Measurement initial = measure(lattice, geometry, converter, p);
  const T expectedFluidVolume = lx * ly * height;
  const bool initialGeometryPass = initial.fluidNodes == p.expectedFluidNodes
    && std::abs(initial.fluidVolume - expectedFluidVolume) / expectedFluidVolume
         <= geometryVolumeRoundoffTolerance;

  std::ofstream diagnostics(p.outputDirectory / "diagnostics.csv");
  diagnostics << std::setprecision(17)
    << "step,J,rho,Mach,mass,time_s,mass_error,max_density_deviation,"
       "Jx,Jz,Q_section1,Q_section2,section_relative_difference,"
       "window_rel_std,window_rel_span,finite\n";

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
    const T sectionDenominator = std::max(
      std::abs(state.sectionQ1), std::abs(state.sectionQ2));
    const T sectionDifference = sectionDenominator > 0.0
      ? std::abs(state.sectionQ1 - state.sectionQ2) / sectionDenominator : 0.0;
    const T crossFlux = std::max(std::abs(state.fluxJ[0]), std::abs(state.fluxJ[2]));
    maxMassRelativeDrift = std::max(maxMassRelativeDrift, std::abs(massRelative));
    maxDensityDeviation = std::max(maxDensityDeviation, state.maxDensityDeviation);
    maxMach = std::max(maxMach, mach);
    maxCrossFlux = std::max(maxCrossFlux, crossFlux);
    window.add(state.fluxJ[1]);
    if (window.full()) {
      window.metrics(windowRelativeStd, windowRelativeSpan);
    }

    diagnostics << step << ',' << state.fluxJ[1] << ',' << state.meanRho << ','
      << mach << ',' << state.fluidMass << ',' << step * p.dt << ','
      << massRelative << ',' << state.maxDensityDeviation << ','
      << state.fluxJ[0] << ',' << state.fluxJ[2] << ','
      << state.sectionQ1 << ',' << state.sectionQ2 << ',' << sectionDifference << ','
      << (window.full() ? windowRelativeStd : -1.0) << ','
      << (window.full() ? windowRelativeSpan : -1.0) << ',' << state.finite << '\n';

    const bool windowPass = window.full()
      && windowRelativeStd <= relativeStdTolerance
      && windowRelativeSpan <= relativeSpanTolerance;
    const bool diagnosticPass = state.finite
      && maxMassRelativeDrift < massTolerance
      && maxDensityDeviation <= densityTolerance
      && maxMach < machTolerance
      && maxCrossFlux <= crossFluxTolerance
      && sectionDifference <= sectionTolerance;
    return windowPass && diagnosticPass;
  };

  record(0, initial);
  std::cout << "run_scope=G1_V2_Bouzidi_Poiseuille"
            << " dx_nm=" << p.dx * 1.0e9
            << " dt_s=" << p.dt
            << " tau=" << p.tau
            << " acceleration=" << p.accelerationY << '\n';
  for (int step = 1; step <= maximumSteps; ++step) {
    lattice.collideAndStream();
    const Measurement state = measure(lattice, geometry, converter, p);
    converged = record(step, state);
    finalStep = step;
    if (step % 1000 == 0 || converged) {
      std::cout << "step=" << step << " J=" << state.fluxJ[1]
                << " window_rel_std=" << windowRelativeStd
                << " window_rel_span=" << windowRelativeSpan
                << " converged=" << converged << '\n';
    }
    if (converged) {
      break;
    }
  }
  diagnostics.close();

  const Measurement final = measure(lattice, geometry, converter, p);
  const auto finalMaterials = countMaterials(geometry);
  const bool materialUnchanged = finalMaterials == initialMaterials;
  const T finalMassRelative = (final.fluidMass - initial.fluidMass) / initial.fluidMass;
  const T sectionDenominator = std::max(
    std::abs(final.sectionQ1), std::abs(final.sectionQ2));
  const T sectionDifference = sectionDenominator > 0.0
    ? std::abs(final.sectionQ1 - final.sectionQ2) / sectionDenominator : 0.0;
  const T finalMach = final.maxLatticeSpeed / std::sqrt(T(1.0 / 3.0));
  const T numericalJ = final.fluxJ[1];
  const T numericalK = muPhys * numericalJ / (rhoPhys * p.accelerationY);
  const T analyticJ = rhoPhys * p.accelerationY * std::pow(height, 3) / (12.0 * muPhys);
  const T analyticK = std::pow(height, 3) / 12.0;
  const T relativeError = (numericalK - analyticK) / analyticK;
  const ProfileResult profile = writeVelocityProfile(
    lattice, geometry, converter, p, p.outputDirectory / "velocity_profile.csv");

  const bool acceptancePass = initialGeometryPass
    && boundaryAudit.pass
    && materialUnchanged
    && final.finite
    && converged
    && maxMassRelativeDrift < massTolerance
    && maxDensityDeviation <= densityTolerance
    && maxMach < machTolerance
    && maxCrossFlux <= crossFluxTolerance
    && sectionDifference <= sectionTolerance
    && profile.relativeL2 < profileL2Tolerance
    && profile.offsetRelativeToAnalyticMax < offsetRelativeTolerance
    && std::abs(relativeError) < kRelativeErrorTolerance;

  std::ofstream summary(p.outputDirectory / "result_summary.csv");
  summary << std::setprecision(17)
          << "dx,tau,force,J,K_LBM,K_theory,relative_error\n"
          << p.dx << ',' << p.tau << ',' << p.accelerationY << ','
          << numericalJ << ',' << numericalK << ',' << analyticK << ','
          << relativeError << '\n';

  std::ofstream result(p.outputDirectory / "result.txt");
  result << std::setprecision(17) << std::boolalpha
    << "run_scope=G1_V2_Bouzidi_Poiseuille\n"
    << "formal_simulation=true\n"
    << "PASS=" << acceptancePass << '\n'
    << "converged=" << converged << '\n'
    << "stop_reason=" << (converged ? "frozen_window_converged" : "maximum_steps") << '\n'
    << "steps_completed=" << finalStep << '\n'
    << "geometry_PASS=" << initialGeometryPass << '\n'
    << "q_audit_PASS=" << boundaryAudit.pass << '\n'
    << "Lx_m=" << lx << '\n'
    << "Ly_m=" << ly << '\n'
    << "H_m=" << height << '\n'
    << "dx_m=" << p.dx << '\n'
    << "dt_s=" << p.dt << '\n'
    << "tau=" << converter.getLatticeRelaxationTime() << '\n'
    << "descriptor=D3Q19_FORCE\n"
    << "collision=ForcedBGK\n"
    << "wall_boundary=Bouzidi_exact_planar\n"
    << "acceleration_y_m_s2=" << p.accelerationY << '\n'
    << "force_lattice=0," << force[1] << ",0\n"
    << "fluid_nodes=" << final.fluidNodes << '\n'
    << "fluid_volume_m3=" << final.fluidVolume << '\n'
    << "q_min=" << boundaryAudit.qMin << '\n'
    << "q_max=" << boundaryAudit.qMax << '\n'
    << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
    << "installed_links=" << boundaryAudit.installedLinks << '\n'
    << "fallback_count=" << boundaryAudit.geometricFallbacks
        + boundaryAudit.missingFluidNeighborFallbacks << '\n'
    << "material_unchanged=" << materialUnchanged << '\n'
    << "max_mass_abs_relative=" << maxMassRelativeDrift << '\n'
    << "final_mass_signed_relative=" << finalMassRelative << '\n'
    << "max_density_deviation=" << maxDensityDeviation << '\n'
    << "max_Mach=" << maxMach << '\n'
    << "final_Mach=" << finalMach << '\n'
    << "max_cross_flux_m2_s=" << maxCrossFlux << '\n'
    << "section_flux_relative_difference=" << sectionDifference << '\n'
    << "window_rel_std_sample=" << windowRelativeStd << '\n'
    << "window_rel_span=" << windowRelativeSpan << '\n'
    << "J_m2_s=" << numericalJ << '\n'
    << "analytic_J_m2_s=" << analyticJ << '\n'
    << "K_LBM_m3=" << numericalK << '\n'
    << "K_theory_m3=" << analyticK << '\n'
    << "K_relative_error=" << relativeError << '\n'
    << "velocity_profile_L2_relative_error=" << profile.relativeL2 << '\n'
    << "velocity_offset_mean_m_s=" << profile.offsetMean << '\n'
    << "velocity_offset_span_m_s=" << profile.offsetSpan << '\n'
    << "velocity_offset_relative_to_analytic_max="
    << profile.offsetRelativeToAnalyticMax << '\n'
    << "exit_code=" << (acceptancePass ? 0 : 3) << '\n';

  std::cout << "PASS=" << acceptancePass
            << " converged=" << converged
            << " steps=" << finalStep
            << " J=" << numericalJ
            << " K_relative_error=" << relativeError
            << " velocity_L2=" << profile.relativeL2
            << " offset_relative=" << profile.offsetRelativeToAnalyticMax
            << " max_mass_error=" << maxMassRelativeDrift << '\n';
  return acceptancePass ? 0 : 3;
}
