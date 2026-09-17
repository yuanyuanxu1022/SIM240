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

namespace {

using T = double;
using DESCRIPTOR = descriptors::D3Q19<descriptors::FORCE>;

constexpr T dx = 2.5e-9;
constexpr T tau = 1.0;
constexpr T rhoPhys = 1000.0;
constexpr T nuPhys = 1.0e-6;
constexpr T muPhys = rhoPhys * nuPhys;
constexpr T acceleration = 1.0e5;
constexpr T lx = 240.0e-9;
constexpr T ly = 240.0e-9;
constexpr T mesaGap = 75.0e-9;
constexpr T grooveDepth = 100.0e-9;
constexpr T grooveStart = 60.0e-9;
constexpr T grooveEnd = 180.0e-9;
constexpr T areaPlan = lx * ly;
constexpr T nominalVolume = areaPlan * mesaGap
  + (grooveEnd - grooveStart) * ly * grooveDepth;
constexpr T referenceHeight = nominalVolume / areaPlan;
constexpr T smoothK0 = mesaGap * mesaGap * mesaGap / 12.0;
constexpr T dt = (tau - 0.5) * dx * dx / (3.0 * nuPhys);
constexpr int nx = 96;
constexpr int ny = 96;
constexpr int overlap = 3;
constexpr int convergenceWindow = 1000;
constexpr int maximumSteps = 60000;
constexpr T relativeStdTolerance = 1.0e-6;
constexpr T relativeSpanTolerance = 5.0e-6;
constexpr T massTolerance = 1.0e-10;
constexpr T densityTolerance = 1.0e-6;
constexpr T machTolerance = 0.05;
constexpr T sectionTolerance = 1.0e-5;
constexpr T crossFluxTolerance = 1.0e-12;
constexpr T qTolerance = 1.0e-10;
constexpr T volumeRoundoffTolerance = 1.0e-10;

struct Parameters {
  std::string mode;
  std::string caseId;
  std::string directionName;
  int drive = -1;
  std::filesystem::path outputDirectory;
};

struct BoundaryAudit {
  long long candidateLinks = 0;
  long long validDistanceLinks = 0;
  long long installedLinks = 0;
  long long geometricFallbacks = 0;
  long long missingFluidNeighbourFallbacks = 0;
  long long unresolvedLinks = 0;
  T qMin = std::numeric_limits<T>::infinity();
  T qMax = -std::numeric_limits<T>::infinity();
  T installedQMin = std::numeric_limits<T>::infinity();
  T installedQMax = -std::numeric_limits<T>::infinity();
  bool pass = false;
};

struct Measurement {
  long long fluidNodes = 0;
  T volume = 0.0;
  T mass = 0.0;
  T densityIntegral = 0.0;
  T maxDensityDeviation = 0.0;
  T maxLatticeSpeed = 0.0;
  T pressureMin = std::numeric_limits<T>::infinity();
  T pressureMax = -std::numeric_limits<T>::infinity();
  std::array<T, 3> integratedVelocity{};
  std::array<T, 3> meanVelocity{};
  std::array<T, 3> fluxJ{};
  T sectionQ1 = 0.0;
  T sectionQ2 = 0.0;
  bool finite = true;
};

struct FluxWindow {
  std::deque<T> main;
  std::deque<T> cross;

  void add(T mainValue, T crossValue)
  {
    main.push_back(mainValue);
    cross.push_back(crossValue);
    if (static_cast<int>(main.size()) > convergenceWindow) {
      main.pop_front();
      cross.pop_front();
    }
  }

  bool full() const
  {
    return static_cast<int>(main.size()) == convergenceWindow;
  }

  void metrics(T& relativeStd, T& relativeSpan, T& crossMaximum) const
  {
    const T mean = std::accumulate(main.begin(), main.end(), T{}) / main.size();
    T squared = 0.0;
    for (T value : main) {
      squared += (value - mean) * (value - mean);
    }
    relativeStd = std::sqrt(squared / (main.size() - 1)) / std::abs(mean);
    const auto extrema = std::minmax_element(main.begin(), main.end());
    relativeSpan = (*extrema.second - *extrema.first) / std::abs(mean);
    crossMaximum = 0.0;
    for (T value : cross) {
      crossMaximum = std::max(crossMaximum, std::abs(value));
    }
  }
};

Parameters parseParameters(int argc, char* argv[])
{
  if (argc != 4) {
    throw std::runtime_error("usage: executable precheck|steady P|T OUTPUT_DIRECTORY");
  }
  Parameters p;
  p.mode = argv[1];
  const std::string direction = argv[2];
  p.outputDirectory = argv[3];
  if (p.mode != "precheck" && p.mode != "steady") {
    throw std::runtime_error("mode must be precheck or steady");
  }
  if (direction == "P") {
    p.caseId = "G2-P";
    p.directionName = "parallel";
    p.drive = 1;
  }
  else if (direction == "T") {
    p.caseId = "G2-T";
    p.directionName = "perpendicular";
    p.drive = 0;
  }
  else {
    throw std::runtime_error("direction must be P (parallel/y) or T (perpendicular/x)");
  }
  return p;
}

T wrapX(T x)
{
  x = std::fmod(x, lx);
  return x < 0.0 ? x + lx : x;
}

bool inGroove(T x)
{
  const T wrapped = wrapX(x);
  return wrapped >= grooveStart && wrapped < grooveEnd;
}

T upperWall(T x)
{
  return inGroove(x) ? mesaGap + grooveDepth : mesaGap;
}

int materialAt(const Vector<T, 3>& position)
{
  if (position[2] < 0.0) {
    return 2;
  }
  if (position[2] >= upperWall(position[0])) {
    return 3;
  }
  return 1;
}

class ExactEX240FluidIndicator final : public IndicatorCuboid3D<T> {
public:
  ExactEX240FluidIndicator()
    : IndicatorCuboid3D<T>(
        {lx + 4.0 * dx, ly + 4.0 * dx, mesaGap + grooveDepth},
        {-2.0 * dx, -2.0 * dx, 0.0})
  { }

  bool distance(
    T& distance,
    const Vector<T, 3>& origin,
    const Vector<T, 3>& direction,
    int = -1) override
  {
    T best = std::numeric_limits<T>::infinity();
    const T epsilon = 1.0e-12;
    auto accept = [&](T lambda) {
      if (lambda >= -epsilon && lambda <= 1.0 + epsilon) {
        best = std::min(best, std::max(T{}, lambda));
      }
    };

    if (direction[2] < 0.0) {
      accept((0.0 - origin[2]) / direction[2]);
    }
    if (direction[2] > 0.0) {
      for (T wallZ : {mesaGap, mesaGap + grooveDepth}) {
        const T lambda = (wallZ - origin[2]) / direction[2];
        if (lambda < -epsilon || lambda > 1.0 + epsilon) {
          continue;
        }
        const T xHit = origin[0] + lambda * direction[0];
        const bool horizontalExists = wallZ == mesaGap ? !inGroove(xHit) : inGroove(xHit);
        if (horizontalExists) {
          accept(lambda);
        }
      }
    }

    if (direction[0] != 0.0) {
      for (int image = -1; image <= 1; ++image) {
        for (T wallX : {grooveStart + image * lx, grooveEnd + image * lx}) {
          const T lambda = (wallX - origin[0]) / direction[0];
          if (lambda < -epsilon || lambda > 1.0 + epsilon) {
            continue;
          }
          const T zHit = origin[2] + lambda * direction[2];
          if (zHit >= mesaGap - epsilon
              && zHit <= mesaGap + grooveDepth + epsilon) {
            accept(lambda);
          }
        }
      }
    }

    if (!std::isfinite(best)) {
      return false;
    }
    // All EX240 walls are exactly halfway between the adjacent fluid and
    // solid nodes.  Snap round-off-sized deviations to the exact analytical
    // intersection so OpenLB selects its q <= 0.5 Bouzidi branch consistently.
    if (std::abs(best - 0.5) <= qTolerance) {
      best = 0.5;
    }
    distance = best * util::norm<3>(direction);
    return std::isfinite(distance);
  }
};

int wrapIndex(int value, int extent)
{
  value %= extent;
  return value < 0 ? value + extent : value;
}

Vector<int, 3> wrapPeriodicXY(Vector<int, 3> latticeR)
{
  latticeR[0] = wrapIndex(latticeR[0], nx);
  latticeR[1] = wrapIndex(latticeR[1], ny);
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
      const Vector<T, 3> origin = block.getPhysR(fluidR);
      for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
        const auto c = descriptors::c<DESCRIPTOR>(iPop);
        const Vector<int, 3> solidR(fluidR + c);
        const int material = block.getMaterial(wrapPeriodicXY(solidR));
        if (material != 2 && material != 3) {
          continue;
        }
        ++audit.candidateLinks;
        const Vector<T, 3> ray = dx * c;
        const T norm = util::norm<3>(ray);
        T wallDistance = -1.0;
        T q = -1.0;
        if (analyticalBoundary.distance(
              wallDistance, origin.data(), ray, block.getIcGlob())) {
          q = wallDistance / norm;
        }
        if (!(q > 0.0 && q <= 1.0 + qTolerance)) {
          ++audit.geometricFallbacks;
        }
        else {
          ++audit.validDistanceLinks;
          audit.qMin = std::min(audit.qMin, q);
          audit.qMax = std::max(audit.qMax, q);
        }
        // OpenLB reads the second fluid-side node only in the q > 0.5
        // Bouzidi branch.  Counting it for q <= 0.5 incorrectly flags
        // concave step-corner links that use the local q <= 0.5 formula.
        if (q > 0.5) {
          const Vector<int, 3> fluidSideR(fluidR - c);
          if (!block.isInside(fluidSideR)
              || block.getMaterial(wrapPeriodicXY(fluidSideR)) != 1) {
            ++audit.missingFluidNeighbourFallbacks;
          }
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
      const auto distances = block.get(latticeR)
        .template getFieldPointer<descriptors::BOUZIDI_DISTANCE>();
      for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
        if (distances[iPop] > 0.0) {
          ++audit.installedLinks;
          audit.installedQMin = std::min(audit.installedQMin, distances[iPop]);
          audit.installedQMax = std::max(audit.installedQMax, distances[iPop]);
          if (distances[iPop] > 1.0 + qTolerance) {
            ++audit.unresolvedLinks;
          }
        }
      }
    });
  }
  audit.pass = audit.candidateLinks > 0
    && audit.validDistanceLinks == audit.candidateLinks
    && audit.installedLinks == audit.candidateLinks
    && audit.geometricFallbacks == 0
    && audit.missingFluidNeighbourFallbacks == 0
    && audit.unresolvedLinks == 0
    && std::abs(audit.installedQMin - audit.qMin) <= qTolerance
    && std::abs(audit.installedQMax - audit.qMax) <= qTolerance;
}

void writeBoundaryAudit(
  const std::filesystem::path& path,
  const BoundaryAudit& audit,
  const std::array<long long, 4>& materials,
  bool geometryPass)
{
  std::ofstream out(path);
  out << std::setprecision(17) << std::boolalpha
      << "geometry_PASS=" << geometryPass << '\n'
      << "q_audit_PASS=" << audit.pass << '\n'
      << "material_0=" << materials[0] << '\n'
      << "material_1=" << materials[1] << '\n'
      << "material_2=" << materials[2] << '\n'
      << "material_3=" << materials[3] << '\n'
      << "candidate_links=" << audit.candidateLinks << '\n'
      << "valid_distance_links=" << audit.validDistanceLinks << '\n'
      << "installed_links=" << audit.installedLinks << '\n'
      << "q_min=" << audit.qMin << '\n'
      << "q_max=" << audit.qMax << '\n'
      << "installed_q_min=" << audit.installedQMin << '\n'
      << "installed_q_max=" << audit.installedQMax << '\n'
      << "geometric_fallback_count=" << audit.geometricFallbacks << '\n'
      << "missing_fluid_neighbour_fallback_count="
      << audit.missingFluidNeighbourFallbacks << '\n'
      << "unresolved_link_count=" << audit.unresolvedLinks << '\n';
}

template <typename LATTICE, typename GEOMETRY>
Measurement measure(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  int drive)
{
  Measurement value;
  const int section1 = drive == 0 ? nx / 8 : ny / 4;
  const int section2 = drive == 0 ? nx / 2 : 3 * ny / 4;
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
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
      const T pressure = converter.getPhysPressure(
        (rho - 1.0) / descriptors::invCs2<T, DESCRIPTOR>());
      ++value.fluidNodes;
      value.volume += dx * dx * dx;
      value.mass += rho * rhoPhys * dx * dx * dx;
      value.densityIntegral += rho * dx * dx * dx;
      value.maxDensityDeviation = std::max(
        value.maxDensityDeviation, std::abs(rho - 1.0));
      value.maxLatticeSpeed = std::max(value.maxLatticeSpeed, speedLat);
      value.pressureMin = std::min(value.pressureMin, pressure);
      value.pressureMax = std::max(value.pressureMax, pressure);
      value.finite = value.finite && std::isfinite(rho)
        && std::isfinite(speedLat) && std::isfinite(pressure);
      for (int iD = 0; iD < 3; ++iD) {
        const T uPhys = converter.getPhysVelocity(uLat[iD]);
        value.integratedVelocity[iD] += uPhys * dx * dx * dx;
        value.finite = value.finite && std::isfinite(uPhys);
      }
      const T mainVelocity = converter.getPhysVelocity(uLat[drive]);
      const int coordinate = drive == 0 ? latticeR[0] : latticeR[1];
      if (coordinate == section1) {
        value.sectionQ1 += mainVelocity * dx * dx;
      }
      if (coordinate == section2) {
        value.sectionQ2 += mainVelocity * dx * dx;
      }
    });
  }
  for (int iD = 0; iD < 3; ++iD) {
    value.meanVelocity[iD] = value.integratedVelocity[iD] / value.volume;
    value.fluxJ[iD] = value.integratedVelocity[iD] / areaPlan;
  }
  return value;
}

template <typename LATTICE, typename GEOMETRY>
void writeFinalProfiles(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  const Parameters& p)
{
  const int slices = p.drive == 0 ? nx : ny;
  std::vector<T> rhoSum(slices, 0.0);
  std::vector<T> pressureSum(slices, 0.0);
  std::vector<T> velocitySum(slices, 0.0);
  std::vector<T> phiSum(slices, 0.0);
  std::vector<long long> counts(slices, 0);
  std::ofstream field(p.outputDirectory / "field_slice.csv");
  field << std::setprecision(17)
        << "x,z,ux,uy,uz,speed,rho,pressure,Phi,material\n";

  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    BlockLatticePhysDissipation3D<T, DESCRIPTOR> dissipation(block, converter);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      auto cell = block.get(latticeR);
      T uLat[3]{};
      cell.computeU(uLat);
      const T rho = cell.computeRho();
      const T pressure = converter.getPhysPressure(
        (rho - 1.0) / descriptors::invCs2<T, DESCRIPTOR>());
      std::array<T, 3> velocity{};
      T speedSquared = 0.0;
      for (int iD = 0; iD < 3; ++iD) {
        velocity[iD] = converter.getPhysVelocity(uLat[iD]);
        speedSquared += velocity[iD] * velocity[iD];
      }
      int input[3]{latticeR[0], latticeR[1], latticeR[2]};
      T epsilon[1]{};
      dissipation(epsilon, input);
      const T phi = rhoPhys * epsilon[0];
      const int slice = p.drive == 0 ? latticeR[0] : latticeR[1];
      rhoSum[slice] += rho;
      pressureSum[slice] += pressure;
      velocitySum[slice] += velocity[p.drive];
      phiSum[slice] += phi;
      ++counts[slice];

      if (latticeR[1] == ny / 2) {
        const Vector<T, 3> position = blockGeometry.getPhysR(latticeR);
        field << position[0] << ',' << position[2] << ','
              << velocity[0] << ',' << velocity[1] << ',' << velocity[2] << ','
              << std::sqrt(speedSquared) << ',' << rho << ',' << pressure << ','
              << phi << ",1\n";
      }
    });
  }

  std::ofstream pressure(p.outputDirectory / "pressure_profile.csv");
  std::ofstream velocity(p.outputDirectory / "velocity_profile.csv");
  std::ofstream energy(p.outputDirectory / "energy_dissipation.csv");
  pressure << std::setprecision(17) << "position,rho,pressure\n";
  velocity << std::setprecision(17) << "position,velocity\n";
  energy << std::setprecision(17) << "position,Phi\n";
  for (int i = 0; i < slices; ++i) {
    if (counts[i] == 0) {
      continue;
    }
    const T position = (i + 0.5) * dx;
    pressure << position << ',' << rhoSum[i] / counts[i] << ','
             << pressureSum[i] / counts[i] << '\n';
    velocity << position << ',' << velocitySum[i] / counts[i] << '\n';
    energy << position << ',' << phiSum[i] / counts[i] << '\n';
  }
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
    std::cerr << "G2 requires exactly one MPI rank\n";
    return 2;
  }
  if (!std::filesystem::exists(p.outputDirectory / "run_manifest.txt")) {
    std::cerr << "pre-run manifest is required\n";
    return 2;
  }
  if (std::filesystem::exists(p.outputDirectory / "result.txt")) {
    std::cerr << "refusing to overwrite existing result\n";
    return 2;
  }
  singleton::directories().setOutputDir((p.outputDirectory.string() + "/").c_str());

  const T domainTop = mesaGap + grooveDepth + 4.0 * dx;
  IndicatorCuboid3D<T> domain(
    {lx - dx, ly - dx, domainTop},
    {0.5 * dx, 0.5 * dx, -0.5 * dx});
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
  constexpr long long expectedFluidNodes = 460800;
  const bool geometryPass = !geometryErrors
    && initialMaterials[1] == expectedFluidNodes;

  UnitConverter<T, DESCRIPTOR> converter(dx, dt, lx, 1.0, nuPhys, rhoPhys);
  const bool converterPass = std::abs(converter.getLatticeRelaxationTime() - tau) <= 1.0e-12;
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);
  ExactEX240FluidIndicator exactGeometry;
  BoundaryAudit boundaryAudit = auditGeometryLinks(geometry, exactGeometry);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 2, exactGeometry);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 3, exactGeometry);
  auditInstalledDistances(lattice, geometry, boundaryAudit);
  writeBoundaryAudit(
    p.outputDirectory / "boundary_audit.txt",
    boundaryAudit,
    initialMaterials,
    geometryPass);

  const bool precheckPass = geometryPass && converterPass && boundaryAudit.pass;
  if (p.mode == "precheck") {
    std::ofstream result(p.outputDirectory / "result.txt");
    result << std::setprecision(17) << std::boolalpha
           << "case=" << p.caseId << '\n'
           << "direction=" << p.directionName << '\n'
           << "formal_simulation=false\n"
           << "collide_and_stream_calls=0\n"
           << "geometry_PASS=" << geometryPass << '\n'
           << "converter_PASS=" << converterPass << '\n'
           << "q_audit_PASS=" << boundaryAudit.pass << '\n'
           << "fluid_nodes=" << initialMaterials[1] << '\n'
           << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
           << "installed_links=" << boundaryAudit.installedLinks << '\n'
           << "q_min=" << boundaryAudit.qMin << '\n'
           << "q_max=" << boundaryAudit.qMax << '\n'
           << "fallback_count="
           << boundaryAudit.geometricFallbacks
                + boundaryAudit.missingFluidNeighbourFallbacks << '\n'
           << "exit_code=" << (precheckPass ? 0 : 3) << '\n';
    std::cout << "precheck_PASS=" << precheckPass
              << " links=" << boundaryAudit.installedLinks
              << " q=[" << boundaryAudit.qMin << ',' << boundaryAudit.qMax << "]\n";
    return precheckPass ? 0 : 3;
  }

  if (!precheckPass) {
    std::cerr << "steady run blocked by geometry/converter/boundary precheck\n";
    return 3;
  }

  AnalyticalConst3D<T, T> one(1.0);
  AnalyticalConst3D<T, T> zeroVelocity(0.0, 0.0, 0.0);
  lattice.defineRhoU(geometry.getMaterialIndicator(1), one, zeroVelocity);
  lattice.iniEquilibrium(geometry, 1, one, zeroVelocity);
  Vector<T, 3> force{0.0, 0.0, 0.0};
  force[p.drive] = acceleration * dt * dt / dx;
  fields::set<descriptors::FORCE>(
    lattice, geometry.getMaterialIndicator(1), force);
  lattice.setParameter<descriptors::OMEGA>(
    converter.getLatticeRelaxationFrequency());
  lattice.initialize();

  SuperVTMwriter3D<T> writer("g2_ex240_" + p.directionName, overlap);
  SuperGeometryF3D<T> material(geometry);
  material.getName() = "material";
  SuperLatticePhysVelocity3D<T, DESCRIPTOR> velocity(lattice, converter);
  velocity.getName() = "velocity_m_s";
  SuperLatticePhysPressure3D<T, DESCRIPTOR> pressure(lattice, converter);
  pressure.getName() = "pressure_Pa";
  SuperLatticePhysDissipation3D<T, DESCRIPTOR> dissipation(lattice, converter);
  dissipation.getName() = "dissipation_m2_s3";
  writer.addFunctor(material);
  writer.addFunctor(velocity);
  writer.addFunctor(pressure);
  writer.addFunctor(dissipation);
  writer.createMasterFile();
  writer.write(0);

  const Measurement initial = measure(lattice, geometry, converter, p.drive);
  const bool initialVolumePass = initial.fluidNodes == expectedFluidNodes
    && std::abs(initial.volume - nominalVolume) / nominalVolume
         <= volumeRoundoffTolerance;
  std::ofstream diagnostics(p.outputDirectory / "diagnostics.csv");
  diagnostics << std::setprecision(17)
    << "step,J,rho,Mach,mass,time_s,mass_error,max_density_deviation,"
       "Jx,Jy,Jz,Q_section1,Q_section2,section_relative_difference,"
       "pressure_min,pressure_max,window_rel_std,window_rel_span,"
       "window_cross_abs_max,finite\n";

  FluxWindow window;
  T maxMassError = 0.0;
  T maxDensityDeviation = 0.0;
  T maxMach = 0.0;
  T windowStd = std::numeric_limits<T>::infinity();
  T windowSpan = std::numeric_limits<T>::infinity();
  T windowCross = std::numeric_limits<T>::infinity();
  bool converged = false;
  int finalStep = 0;

  for (int step = 0; step <= maximumSteps; ++step) {
    if (step > 0) {
      lattice.collideAndStream();
    }
    const Measurement state = measure(lattice, geometry, converter, p.drive);
    const T massError = (state.mass - initial.mass) / initial.mass;
    const T mach = state.maxLatticeSpeed / std::sqrt(T(1.0 / 3.0));
    const T sectionDenominator = std::max(
      std::abs(state.sectionQ1), std::abs(state.sectionQ2));
    const T sectionDifference = sectionDenominator > 0.0
      ? std::abs(state.sectionQ1 - state.sectionQ2) / sectionDenominator : 0.0;
    const int crossDirection = 1 - p.drive;
    window.add(state.fluxJ[p.drive], state.fluxJ[crossDirection]);
    if (window.full()) {
      window.metrics(windowStd, windowSpan, windowCross);
    }
    maxMassError = std::max(maxMassError, std::abs(massError));
    maxDensityDeviation = std::max(
      maxDensityDeviation, state.maxDensityDeviation);
    maxMach = std::max(maxMach, mach);
    diagnostics << step << ',' << state.fluxJ[p.drive] << ','
                << state.densityIntegral / state.volume << ',' << mach << ','
                << state.mass << ',' << step * dt << ',' << massError << ','
                << state.maxDensityDeviation << ',' << state.fluxJ[0] << ','
                << state.fluxJ[1] << ',' << state.fluxJ[2] << ','
                << state.sectionQ1 << ',' << state.sectionQ2 << ','
                << sectionDifference << ',' << state.pressureMin << ','
                << state.pressureMax << ','
                << (window.full() ? windowStd : -1.0) << ','
                << (window.full() ? windowSpan : -1.0) << ','
                << (window.full() ? windowCross : -1.0) << ','
                << state.finite << '\n';
    finalStep = step;
    if (window.full()
        && windowStd <= relativeStdTolerance
        && windowSpan <= relativeSpanTolerance
        && windowCross <= crossFluxTolerance) {
      converged = true;
      break;
    }
  }

  const Measurement final = measure(lattice, geometry, converter, p.drive);
  writer.write(finalStep);
  writeFinalProfiles(lattice, geometry, converter, p);
  const auto finalMaterials = countMaterials(geometry);
  const bool materialUnchanged = finalMaterials == initialMaterials;
  const T sectionDenominator = std::max(
    std::abs(final.sectionQ1), std::abs(final.sectionQ2));
  const T sectionDifference = sectionDenominator > 0.0
    ? std::abs(final.sectionQ1 - final.sectionQ2) / sectionDenominator : 0.0;
  const T mainJ = final.fluxJ[p.drive];
  const T effectiveK = muPhys * mainJ / (rhoPhys * acceleration);
  const T resistance = rhoPhys * acceleration / mainJ;
  const bool pass = initialVolumePass
    && boundaryAudit.pass
    && materialUnchanged
    && final.finite
    && converged
    && maxMassError < massTolerance
    && maxDensityDeviation <= densityTolerance
    && maxMach < machTolerance
    && windowCross <= crossFluxTolerance
    && sectionDifference <= sectionTolerance
    && mainJ > 0.0;

  std::ofstream summary(p.outputDirectory / "result_summary.csv");
  summary << std::setprecision(17)
          << "Case,direction,dx,tau,force,J,Keff,R_eff,Mach,mass_error\n"
          << p.caseId << ',' << p.directionName << ',' << dx << ',' << tau << ','
          << acceleration << ',' << mainJ << ',' << effectiveK << ','
          << resistance << ',' << maxMach << ',' << maxMassError << '\n';

  std::ofstream result(p.outputDirectory / "result.txt");
  result << std::setprecision(17) << std::boolalpha
         << "case=" << p.caseId << '\n'
         << "direction=" << p.directionName << '\n'
         << "PASS=" << pass << '\n'
         << "converged=" << converged << '\n'
         << "steps_completed=" << finalStep << '\n'
         << "Lx_m=" << lx << '\n'
         << "Ly_m=" << ly << '\n'
         << "mesa_gap_m=" << mesaGap << '\n'
         << "groove_depth_m=" << grooveDepth << '\n'
         << "groove_width_m=" << grooveEnd - grooveStart << '\n'
         << "H_ref_m=" << referenceHeight << '\n'
         << "dx_m=" << dx << '\n'
         << "dt_s=" << dt << '\n'
         << "tau=" << converter.getLatticeRelaxationTime() << '\n'
         << "descriptor=D3Q19_FORCE\n"
         << "collision=ForcedBGK\n"
         << "wall_boundary=Bouzidi_zero_velocity_exact_EX240\n"
         << "periodicity=x_y\n"
         << "acceleration_m_s2=" << acceleration << '\n'
         << "force_lattice=" << force[0] << ',' << force[1] << ',' << force[2] << '\n'
         << "fluid_nodes=" << final.fluidNodes << '\n'
         << "fluid_volume_m3=" << final.volume << '\n'
         << "nominal_volume_m3=" << nominalVolume << '\n'
         << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
         << "installed_links=" << boundaryAudit.installedLinks << '\n'
         << "q_min=" << boundaryAudit.qMin << '\n'
         << "q_max=" << boundaryAudit.qMax << '\n'
         << "fallback_count="
         << boundaryAudit.geometricFallbacks
              + boundaryAudit.missingFluidNeighbourFallbacks << '\n'
         << "unresolved_links=" << boundaryAudit.unresolvedLinks << '\n'
         << "max_mass_abs_relative=" << maxMassError << '\n'
         << "max_density_deviation=" << maxDensityDeviation << '\n'
         << "max_Mach=" << maxMach << '\n'
         << "pressure_range_Pa=" << final.pressureMin << ',' << final.pressureMax << '\n'
         << "J_vector_m2_s=" << final.fluxJ[0] << ',' << final.fluxJ[1] << ','
         << final.fluxJ[2] << '\n'
         << "J_main_m2_s=" << mainJ << '\n'
         << "Keff_m3=" << effectiveK << '\n'
         << "K0_smooth_h75_m3=" << smoothK0 << '\n'
         << "Keff_over_K0=" << effectiveK / smoothK0 << '\n'
         << "R_eff_Pa_s_per_m3=" << resistance << '\n'
         << "Q_sections_m3_s=" << final.sectionQ1 << ',' << final.sectionQ2 << '\n'
         << "section_relative_difference=" << sectionDifference << '\n'
         << "window_main_rel_std=" << windowStd << '\n'
         << "window_main_rel_span=" << windowSpan << '\n'
         << "window_cross_abs_max=" << windowCross << '\n'
         << "material_unchanged=" << materialUnchanged << '\n'
         << "finite=" << final.finite << '\n'
         << "exit_code=" << (pass ? 0 : 3) << '\n';
  std::cout << "case=" << p.caseId << " PASS=" << pass
            << " step=" << finalStep << " J=" << mainJ
            << " Keff=" << effectiveK << '\n';
  return pass ? 0 : 3;
}
