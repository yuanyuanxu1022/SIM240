#include <olb.h>

#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
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
constexpr int shortTestSteps = 20;
constexpr int nx = static_cast<int>(lx / dx + 0.5);
constexpr int ny = static_cast<int>(ly / dx + 0.5);
constexpr long long expectedWallLinks = 2LL * nx * ny * 5LL;
constexpr T qTolerance = 64.0 * std::numeric_limits<T>::epsilon();

struct BoundaryAudit {
  long long expectedLinks = expectedWallLinks;
  long long candidateLinks = 0;
  long long validDistanceLinks = 0;
  long long exactHalfwayLinks = 0;
  long long geometricFallbacks = 0;
  long long missingFluidNeighborFallbacks = 0;
  long long installedLinks = 0;
  long long installedHalfwayLinks = 0;
  T qMin = std::numeric_limits<T>::infinity();
  T qMax = -std::numeric_limits<T>::infinity();
};

struct DirectionAudit {
  long long expectedLinks = 0;
  long long periodicSeamLinks = 0;
  long long preSyncMissingCandidates = 0;
  long long preSyncMissingFluidNeighbors = 0;
  long long candidateLinks = 0;
  long long validDistanceLinks = 0;
  long long installedLinks = 0;
  long long installedHalfwayLinks = 0;
  long long geometricFallbacks = 0;
  long long missingFluidNeighborFallbacks = 0;
  long long unresolvedAnomalies = 0;
};

struct LinkRecord {
  int wallMaterial = 0;
  int iPop = 0;
  int oppositePop = 0;
  Vector<int, 3> c{};
  Vector<int, 3> fluidR{};
  Vector<int, 3> solidRawR{};
  Vector<int, 3> solidWrappedR{};
  Vector<int, 3> fluidSideRawR{};
  Vector<int, 3> fluidSideWrappedR{};
  int solidRawMaterial = 0;
  int solidWrappedMaterial = 0;
  int fluidSideRawMaterial = 0;
  int fluidSideWrappedMaterial = 0;
  bool periodicSeam = false;
  bool distanceValid = false;
  T rawQ = -1.0;
  T installedQ = -1.0;
  bool geometricFallback = false;
  bool missingFluidNeighborFallback = false;
};

struct FlowMeasurement {
  long long fluidNodes = 0;
  T fluidVolume = 0.0;
  T fluidMass = 0.0;
  T maxDensityDeviation = 0.0;
  T maxLatticeSpeed = 0.0;
  T integratedUy = 0.0;
  T jy = 0.0;
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

bool crossesPeriodicSeam(const Vector<int, 3>& latticeR)
{
  return latticeR[0] < 0 || latticeR[0] >= nx
      || latticeR[1] < 0 || latticeR[1] >= ny;
}

void writeLinkRecord(
  std::ofstream& out,
  const std::string& phase,
  const std::string& reason,
  bool resolved,
  const LinkRecord& record)
{
  out << phase << ',' << reason << ',' << resolved << ','
      << record.wallMaterial << ',' << record.fluidR[0] << ','
      << record.fluidR[1] << ',' << record.fluidR[2] << ','
      << record.iPop << ',' << record.oppositePop << ','
      << record.c[0] << ',' << record.c[1] << ',' << record.c[2] << ','
      << record.solidRawR[0] << ',' << record.solidRawR[1] << ','
      << record.solidRawR[2] << ',' << record.solidRawMaterial << ','
      << record.solidWrappedR[0] << ',' << record.solidWrappedR[1] << ','
      << record.solidWrappedR[2] << ',' << record.solidWrappedMaterial << ','
      << record.fluidSideRawR[0] << ',' << record.fluidSideRawR[1] << ','
      << record.fluidSideRawR[2] << ',' << record.fluidSideRawMaterial << ','
      << record.fluidSideWrappedR[0] << ',' << record.fluidSideWrappedR[1] << ','
      << record.fluidSideWrappedR[2] << ',' << record.fluidSideWrappedMaterial << ','
      << record.periodicSeam << ',' << record.distanceValid << ','
      << record.rawQ << ',' << record.installedQ << '\n';
}

template <typename GEOMETRY>
void auditPreSyncPeriodicPadding(
  GEOMETRY& geometry,
  std::array<DirectionAudit, DESCRIPTOR::q>& directions,
  std::ofstream& anomalies)
{
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> fluidR) {
      if (block.getMaterial(fluidR) != 1) {
        return;
      }
      for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
        const auto c = descriptors::c<DESCRIPTOR>(iPop);
        if (c[2] == 0) {
          continue;
        }
        const Vector<int, 3> solidRawR(fluidR + c);
        const Vector<int, 3> solidWrappedR = wrapPeriodicXY(solidRawR);
        const int solidWrappedMaterial = block.getMaterial(solidWrappedR);
        if (solidWrappedMaterial != 2 && solidWrappedMaterial != 3) {
          continue;
        }

        auto& summary = directions[iPop];
        ++summary.expectedLinks;
        const Vector<int, 3> fluidSideRawR(fluidR - c);
        const Vector<int, 3> fluidSideWrappedR = wrapPeriodicXY(fluidSideRawR);
        const bool seam = crossesPeriodicSeam(solidRawR)
          || crossesPeriodicSeam(fluidSideRawR);
        summary.periodicSeamLinks += seam;

        LinkRecord record;
        record.wallMaterial = solidWrappedMaterial;
        record.iPop = iPop;
        record.oppositePop = descriptors::opposite<DESCRIPTOR>(iPop);
        record.c = c;
        record.fluidR = fluidR;
        record.solidRawR = solidRawR;
        record.solidWrappedR = solidWrappedR;
        record.fluidSideRawR = fluidSideRawR;
        record.fluidSideWrappedR = fluidSideWrappedR;
        record.solidRawMaterial = block.getMaterial(solidRawR);
        record.solidWrappedMaterial = solidWrappedMaterial;
        record.fluidSideRawMaterial = block.getMaterial(fluidSideRawR);
        record.fluidSideWrappedMaterial = block.getMaterial(fluidSideWrappedR);
        record.periodicSeam = seam;

        if (record.solidRawMaterial != solidWrappedMaterial) {
          ++summary.preSyncMissingCandidates;
          writeLinkRecord(anomalies, "pre_sync", "missing_candidate_periodic_padding", true, record);
        }
        else if (record.fluidSideRawMaterial != 1
                 && record.fluidSideWrappedMaterial == 1) {
          ++summary.preSyncMissingFluidNeighbors;
          writeLinkRecord(anomalies, "pre_sync", "missing_fluid_neighbor_periodic_padding", true, record);
        }
      }
    });
  }
}

template <typename GEOMETRY>
BoundaryAudit auditGeometryLinks(
  GEOMETRY& geometry,
  IndicatorF3D<T>& analyticalBoundary,
  std::array<DirectionAudit, DESCRIPTOR::q>& directions,
  std::vector<LinkRecord>& records)
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
        const Vector<int, 3> solidWrappedR = wrapPeriodicXY(solidR);
        const int neighborMaterial = block.getMaterial(solidWrappedR);
        if (neighborMaterial != 2 && neighborMaterial != 3) {
          continue;
        }

        ++audit.candidateLinks;
        ++directions[iPop].candidateLinks;
        const T norm = dx * util::norm<3>(c);
        const Vector<T, 3> direction = dx * c;
        T distance = -1.0;
        const bool distanceSuccess = analyticalBoundary.distance(
          distance, fluidPhysR.data(), direction, block.getIcGlob());
        const T rawQ = distanceSuccess ? distance / norm : -1.0;
        const bool geometricFallback = !(rawQ >= 0.0 && rawQ <= 1.0);
        T effectiveQ = rawQ;
        if (geometricFallback) {
          ++audit.geometricFallbacks;
          ++directions[iPop].geometricFallbacks;
          effectiveQ = 0.5;
        }
        else {
          ++audit.validDistanceLinks;
          ++directions[iPop].validDistanceLinks;
        }

        const Vector<int, 3> fluidSideR(fluidR - c);
        const Vector<int, 3> fluidSideWrappedR = wrapPeriodicXY(fluidSideR);
        if (!block.isInside(fluidSideR) || block.getMaterial(fluidSideR) != 1) {
          ++audit.missingFluidNeighborFallbacks;
          ++directions[iPop].missingFluidNeighborFallbacks;
          effectiveQ = 0.5;
        }
        if (std::abs(effectiveQ - 0.5) <= qTolerance) {
          ++audit.exactHalfwayLinks;
        }
        audit.qMin = std::min(audit.qMin, rawQ);
        audit.qMax = std::max(audit.qMax, rawQ);

        LinkRecord record;
        record.wallMaterial = neighborMaterial;
        record.iPop = iPop;
        record.oppositePop = descriptors::opposite<DESCRIPTOR>(iPop);
        record.c = c;
        record.fluidR = fluidR;
        record.solidRawR = solidR;
        record.solidWrappedR = solidWrappedR;
        record.fluidSideRawR = fluidSideR;
        record.fluidSideWrappedR = fluidSideWrappedR;
        record.solidRawMaterial = block.getMaterial(solidR);
        record.solidWrappedMaterial = block.getMaterial(solidWrappedR);
        record.fluidSideRawMaterial = block.getMaterial(fluidSideR);
        record.fluidSideWrappedMaterial = block.getMaterial(fluidSideWrappedR);
        record.periodicSeam = crossesPeriodicSeam(solidR)
          || crossesPeriodicSeam(fluidSideR);
        record.distanceValid = !geometricFallback;
        record.rawQ = rawQ;
        record.geometricFallback = geometricFallback;
        record.missingFluidNeighborFallback = !block.isInside(fluidSideR)
          || block.getMaterial(fluidSideR) != 1;
        records.push_back(record);
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
  std::array<DirectionAudit, DESCRIPTOR::q>& directions,
  std::vector<LinkRecord>& records,
  std::ofstream& anomalies)
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
          ++directions[iPop].installedLinks;
          if (std::abs(q[iPop] - 0.5) <= qTolerance) {
            ++audit.installedHalfwayLinks;
            ++directions[iPop].installedHalfwayLinks;
          }
        }
      }
    });
  }

  for (auto& record : records) {
    auto& block = lattice.getBlock(0);
    record.installedQ = block.get(record.fluidR)
      .template getFieldPointer<descriptors::BOUZIDI_DISTANCE>()[record.iPop];
    const bool anomaly = record.geometricFallback
      || record.missingFluidNeighborFallback
      || record.installedQ <= 0.0
      || std::abs(record.rawQ - 0.5) > qTolerance
      || std::abs(record.installedQ - 0.5) > qTolerance;
    if (anomaly) {
      ++directions[record.iPop].unresolvedAnomalies;
      writeLinkRecord(anomalies, "post_install", "unresolved_boundary_link", false, record);
    }
  }
}

void writeDirectionSummary(
  const std::filesystem::path& outputPath,
  const std::array<DirectionAudit, DESCRIPTOR::q>& directions)
{
  std::ofstream out(outputPath);
  out << "iPop,opposite_iPop,cx,cy,cz,expected_links,periodic_seam_links,"
         "pre_sync_missing_candidates,pre_sync_missing_fluid_neighbors,"
         "candidate_links,valid_distance_links,installed_links,installed_halfway_links,"
         "geometric_fallbacks,missing_fluid_neighbor_fallbacks,unresolved_anomalies\n";
  for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
    const auto c = descriptors::c<DESCRIPTOR>(iPop);
    if (c[2] == 0) {
      continue;
    }
    const auto& value = directions[iPop];
    out << iPop << ',' << descriptors::opposite<DESCRIPTOR>(iPop) << ','
        << c[0] << ',' << c[1] << ',' << c[2] << ','
        << value.expectedLinks << ',' << value.periodicSeamLinks << ','
        << value.preSyncMissingCandidates << ','
        << value.preSyncMissingFluidNeighbors << ','
        << value.candidateLinks << ',' << value.validDistanceLinks << ','
        << value.installedLinks << ',' << value.installedHalfwayLinks << ','
        << value.geometricFallbacks << ','
        << value.missingFluidNeighborFallbacks << ','
        << value.unresolvedAnomalies << '\n';
  }
}

template <typename LATTICE, typename GEOMETRY>
FlowMeasurement measure(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter)
{
  FlowMeasurement value;
  const T cellVolume = dx * dx * dx;
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
      const T uy = converter.getPhysVelocity(uLat[1]);
      const T z = blockGeometry.getPhysR(latticeR)[2];

      ++value.fluidNodes;
      value.fluidVolume += cellVolume;
      value.fluidMass += rho * rhoPhys * cellVolume;
      value.integratedUy += uy * cellVolume;
      value.maxDensityDeviation = std::max(
        value.maxDensityDeviation, std::abs(rho - 1.0));
      value.maxLatticeSpeed = std::max(value.maxLatticeSpeed, speedLat);
      value.finite = value.finite && std::isfinite(rho)
        && std::isfinite(speedLat) && std::isfinite(uy);

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
  value.jy = value.integratedUy / areaPlan;
  value.lowerAdjacentUy /= value.lowerAdjacentNodes;
  value.upperAdjacentUy /= value.upperAdjacentNodes;
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
      velocitySum[iz] += converter.getPhysVelocity(uLat[1]);
      ++counts[iz];
    });
  }

  T numerator = 0.0;
  T denominator = 0.0;
  std::ofstream profile(outputPath);
  profile << std::setprecision(17)
          << "z_m,z_nm,u_y_short_test_m_s,u_y_steady_analytic_m_s,point_relative_error\n";
  for (int iz = 0; iz < nz; ++iz) {
    const T z = (iz + 0.5) * dx;
    const T numerical = velocitySum[iz] / counts[iz];
    const T analytic = rhoPhys * accelerationY * z * (height - z) / (2.0 * muPhys);
    const T error = (numerical - analytic) / analytic;
    numerator += (numerical - analytic) * (numerical - analytic);
    denominator += analytic * analytic;
    profile << z << ',' << z * 1.0e9 << ',' << numerical << ','
            << analytic << ',' << error << '\n';
  }
  return std::sqrt(numerator / denominator);
}

} // namespace

int main(int argc, char* argv[])
{
  initialize(&argc, &argv);
  std::cout << std::setprecision(17) << std::boolalpha;
  if (argc != 2) {
    std::cerr << "usage: case01_bouzidi_short_test OUTPUT_DIRECTORY\n";
    return 2;
  }
  if (singleton::mpi().getSize() != 1) {
    std::cerr << "Case01-Bouzidi short test requires exactly one MPI rank\n";
    return 2;
  }

  const std::filesystem::path outputDirectory(argv[1]);
  if (!std::filesystem::exists(outputDirectory / "run_manifest.txt")) {
    std::cerr << "pre-run run_manifest.txt is required\n";
    return 2;
  }
  if (std::filesystem::exists(outputDirectory / "result.txt")) {
    std::cerr << "refusing to overwrite an existing short test\n";
    return 2;
  }
  singleton::directories().setOutputDir((outputDirectory.string() + "/").c_str());

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

  std::array<DirectionAudit, DESCRIPTOR::q> directionAudit{};
  std::ofstream anomalies(outputDirectory / "boundary_anomalies.csv");
  anomalies << std::setprecision(17) << std::boolalpha
    << "phase,reason,resolved,wall_material,fluid_x,fluid_y,fluid_z,iPop,opposite_iPop,"
       "cx,cy,cz,solid_raw_x,solid_raw_y,solid_raw_z,solid_raw_material,"
       "solid_wrapped_x,solid_wrapped_y,solid_wrapped_z,solid_wrapped_material,"
       "fluid_side_raw_x,fluid_side_raw_y,fluid_side_raw_z,fluid_side_raw_material,"
       "fluid_side_wrapped_x,fluid_side_wrapped_y,fluid_side_wrapped_z,"
       "fluid_side_wrapped_material,periodic_seam,distance_valid,raw_q,installed_q\n";
  auditPreSyncPeriodicPadding(geometry, directionAudit, anomalies);

  // Direct BlockGeometry::set does not mark SuperGeometry communication as
  // needed. This no-op public operation marks the MATERIAL field dirty so the
  // following call fills periodic x/y padding from the physical core.
  geometry.rename(0, 0);
  geometry.communicate();
  geometry.checkForErrors(false);

  UnitConverter<T, DESCRIPTOR> converter(dx, dt, lx, 1.0, nuPhys, rhoPhys);
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);

  ExactPlanarChannelIndicator analyticalChannel;
  std::vector<LinkRecord> linkRecords;
  linkRecords.reserve(expectedWallLinks);
  BoundaryAudit boundaryAudit = auditGeometryLinks(
    geometry, analyticalChannel, directionAudit, linkRecords);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 2, analyticalChannel);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 3, analyticalChannel);
  auditInstalledDistances(
    lattice, geometry, boundaryAudit, directionAudit, linkRecords, anomalies);
  anomalies.close();
  writeDirectionSummary(
    outputDirectory / "boundary_direction_summary.csv", directionAudit);

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

  const FlowMeasurement initial = measure(lattice, geometry, converter);
  std::ofstream history(outputDirectory / "diagnostics.csv");
  history << std::setprecision(17)
          << "step,time_s,Jy_m2_s,RJ_Pa_s_per_m3,RJ_defined,lower_wall_adjacent_uy_m_s,"
             "upper_wall_adjacent_uy_m_s,max_Mach,max_density_deviation,fluid_mass_kg,"
             "fluid_mass_signed_relative,finite\n";

  FlowMeasurement state = initial;
  for (int step = 0; step <= shortTestSteps; ++step) {
    if (step > 0) {
      lattice.collideAndStream();
      state = measure(lattice, geometry, converter);
    }
    const bool rjDefined = state.jy > 0.0;
    const T rj = rjDefined ? rhoPhys * accelerationY / state.jy : 0.0;
    const T mach = state.maxLatticeSpeed / std::sqrt(T(1.0 / 3.0));
    const T massRelative = (state.fluidMass - initial.fluidMass) / initial.fluidMass;
    history << step << ',' << step * dt << ',' << state.jy << ',' << rj << ','
            << rjDefined << ',' << state.lowerAdjacentUy << ','
            << state.upperAdjacentUy << ',' << mach << ','
            << state.maxDensityDeviation << ',' << state.fluidMass << ','
            << massRelative << ',' << state.finite << '\n';
  }
  history.close();

  const T analyticJy = rhoPhys * accelerationY * std::pow(height, 3) / (12.0 * muPhys);
  const T analyticRj = 12.0 * muPhys / std::pow(height, 3);
  const T numericalRj = rhoPhys * accelerationY / state.jy;
  const T jyRelativeError = (state.jy - analyticJy) / analyticJy;
  const T rjRelativeError = (numericalRj - analyticRj) / analyticRj;
  const T profileL2RelativeError = writeVelocityProfile(
    lattice, geometry, converter, outputDirectory / "velocity_profile.csv");
  const long long fallbackCount = boundaryAudit.geometricFallbacks
    + boundaryAudit.missingFluidNeighborFallbacks;
  long long unresolvedAnomalies = 0;
  long long preSyncMissingCandidates = 0;
  long long preSyncMissingFluidNeighbors = 0;
  for (const auto& value : directionAudit) {
    unresolvedAnomalies += value.unresolvedAnomalies;
    preSyncMissingCandidates += value.preSyncMissingCandidates;
    preSyncMissingFluidNeighbors += value.preSyncMissingFluidNeighbors;
  }
  const bool qAuditPass = boundaryAudit.expectedLinks == expectedWallLinks
    && boundaryAudit.candidateLinks == expectedWallLinks
    && boundaryAudit.validDistanceLinks == expectedWallLinks
    && boundaryAudit.installedLinks == boundaryAudit.candidateLinks
    && boundaryAudit.installedHalfwayLinks == boundaryAudit.candidateLinks
    && fallbackCount == 0
    && unresolvedAnomalies == 0
    && std::abs(boundaryAudit.qMin - 0.5) <= qTolerance
    && std::abs(boundaryAudit.qMax - 0.5) <= qTolerance;

  std::ofstream boundaryFile(outputDirectory / "boundary_audit.txt");
  boundaryFile << std::setprecision(17) << std::boolalpha
    << "q_audit_PASS=" << qAuditPass << '\n'
    << "theoretical_candidate_links=" << expectedWallLinks << '\n'
    << "theoretical_derivation=2_walls_x_48_x_48_fluid_nodes_x_5_D3Q19_wall_directions\n"
    << "q_tolerance=" << qTolerance << '\n'
    << "q_tolerance_basis=64_x_double_machine_epsilon\n"
    << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
    << "valid_distance_links=" << boundaryAudit.validDistanceLinks << '\n'
    << "q_min=" << boundaryAudit.qMin << '\n'
    << "q_max=" << boundaryAudit.qMax << '\n'
    << "q_equal_0p5_count=" << boundaryAudit.exactHalfwayLinks << '\n'
    << "installed_links=" << boundaryAudit.installedLinks << '\n'
    << "installed_q_equal_0p5_count=" << boundaryAudit.installedHalfwayLinks << '\n'
    << "geometric_fallback_count=" << boundaryAudit.geometricFallbacks << '\n'
    << "missing_fluid_neighbor_fallback_count="
    << boundaryAudit.missingFluidNeighborFallbacks << '\n'
    << "fallback_count=" << fallbackCount << '\n'
    << "unresolved_anomaly_count=" << unresolvedAnomalies << '\n'
    << "pre_sync_missing_candidate_periodic_padding_count="
    << preSyncMissingCandidates << '\n'
    << "pre_sync_missing_fluid_neighbor_periodic_padding_count="
    << preSyncMissingFluidNeighbors << '\n'
    << "pre_sync_anomalies_resolved_by_material_overlap_sync="
    << (preSyncMissingCandidates == 384
        && preSyncMissingFluidNeighbors == 384) << '\n';
  boundaryFile.close();

  std::ofstream result(outputDirectory / "result.txt");
  result << std::setprecision(17) << std::boolalpha
    << "run_scope=Case01_Bouzidi_code_integration_short_test\n"
    << "formal_simulation=false\n"
    << "steady_state_claim=false\n"
    << "short_test_steps=" << shortTestSteps << '\n'
    << "D3Q19_FORCE=true\n"
    << "collision=ForcedBGK\n"
    << "dx_m=" << dx << '\n'
    << "dt_s=" << dt << '\n'
    << "tau=" << converter.getLatticeRelaxationTime() << '\n'
    << "acceleration_y_m_s2=" << accelerationY << '\n'
    << "q_audit_PASS=" << qAuditPass << '\n'
    << "theoretical_candidate_links=" << expectedWallLinks << '\n'
    << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
    << "installed_links=" << boundaryAudit.installedLinks << '\n'
    << "q_min=" << boundaryAudit.qMin << '\n'
    << "q_max=" << boundaryAudit.qMax << '\n'
    << "q_tolerance=" << qTolerance << '\n'
    << "q_equal_0p5_count=" << boundaryAudit.exactHalfwayLinks << '\n'
    << "fallback_count=" << fallbackCount << '\n'
    << "unresolved_anomaly_count=" << unresolvedAnomalies << '\n'
    << "lower_wall_adjacent_uy_m_s=" << state.lowerAdjacentUy << '\n'
    << "upper_wall_adjacent_uy_m_s=" << state.upperAdjacentUy << '\n'
    << "Jy_short_test_m2_s=" << state.jy << '\n'
    << "RJ_short_test_Pa_s_per_m3=" << numericalRj << '\n'
    << "analytic_steady_Jy_m2_s=" << analyticJy << '\n'
    << "analytic_steady_RJ_Pa_s_per_m3=" << analyticRj << '\n'
    << "Jy_relative_error_vs_steady_analytic=" << jyRelativeError << '\n'
    << "RJ_relative_error_vs_steady_analytic=" << rjRelativeError << '\n'
    << "velocity_profile_L2_relative_error_vs_steady_analytic="
    << profileL2RelativeError << '\n'
    << "analytical_error_interpretation=TRANSIENT_SHORT_TEST_ONLY_NOT_ACCEPTANCE\n"
    << "finite=" << state.finite << '\n'
    << "exit_code=" << (qAuditPass && state.finite ? 0 : 3) << '\n';
  result.close();

  std::cout << "q_audit_PASS=" << qAuditPass
            << " q_min=" << boundaryAudit.qMin
            << " q_max=" << boundaryAudit.qMax
            << " q_equal_0p5_count=" << boundaryAudit.exactHalfwayLinks
            << " fallback_count=" << fallbackCount << '\n'
            << "short_test_steps=" << shortTestSteps
            << " Jy_m2_s=" << state.jy
            << " RJ_Pa_s_per_m3=" << numericalRj
            << " profile_L2_vs_steady=" << profileL2RelativeError << '\n';
  return qAuditPass && state.finite ? 0 : 3;
}
