#include <olb.h>

#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

using namespace olb;

using T = double;
using DESCRIPTOR = descriptors::D3Q19<descriptors::FORCE>;

namespace {

constexpr T dx = 5.0e-9;
constexpr T dt = 1.0e-11;
constexpr T width = 240.0e-9;
constexpr T length = 240.0e-9;
constexpr T height = 75.0e-9;
constexpr T rhoPhys = 1000.0;
constexpr T nuPhys = 1.0e-6;
constexpr T acceleration = 1.0e5;
constexpr int overlap = 3;

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

} // namespace

int main(int argc, char* argv[])
{
  initialize(&argc, &argv);

  if (argc != 2) {
    std::cerr << "usage: case01_geometry_check OUTPUT_FILE\n";
    return 2;
  }
  if (singleton::mpi().getSize() != 1) {
    std::cerr << "Gate 0 geometry check requires one MPI rank\n";
    return 2;
  }

  const int nx = static_cast<int>(std::llround(width / dx));
  const int ny = static_cast<int>(std::llround(length / dx));
  const int nzFluid = static_cast<int>(std::llround(height / dx));
  const long long expectedFluidNodes =
    static_cast<long long>(nx) * ny * nzFluid;
  const T expectedFluidVolume = width * length * height;

  IndicatorCuboid3D<T> domain(
    {width - dx, length - dx, height + 20.0e-9},
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
  const auto materialCounts = countMaterials(geometry);

  UnitConverter<T, DESCRIPTOR> converter(
    dx, dt, width, 1.0, nuPhys, rhoPhys);
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);
  boundary::set<boundary::BounceBack>(lattice, geometry, 2);
  boundary::set<boundary::BounceBack>(lattice, geometry, 3);

  AnalyticalConst3D<T, T> one(1.0);
  AnalyticalConst3D<T, T> zeroVelocity(0.0, 0.0, 0.0);
  lattice.defineRhoU(geometry.getMaterialIndicator(1), one, zeroVelocity);
  lattice.iniEquilibrium(geometry, 1, one, zeroVelocity);

  Vector<T, 3> force{0.0, 0.0, 0.0};
  force[1] = acceleration * dt * dt / dx;
  fields::set<descriptors::FORCE>(
    lattice, geometry.getMaterialIndicator(1), force);
  lattice.setParameter<descriptors::OMEGA>(
    converter.getLatticeRelaxationFrequency());
  lattice.initialize();

  const T actualFluidVolume = materialCounts[1] * dx * dx * dx;
  const T tau = converter.getLatticeRelaxationTime();
  const bool geometryPass =
    materialCounts[1] == expectedFluidNodes
    && materialCounts[2] > 0
    && materialCounts[3] > 0
    && std::abs(actualFluidVolume - expectedFluidVolume) <= 1.0e-32;
  const bool converterPass =
    std::abs(tau - 1.7) <= 1.0e-12
    && std::abs(force[1] - 2.0e-9) <= 1.0e-20;
  const bool pass = geometryPass && converterPass;

  std::ofstream output(argv[1]);
  if (!output) {
    std::cerr << "cannot open Gate 0 output file\n";
    return 4;
  }
  output << std::setprecision(17) << std::boolalpha
         << "gate=0\n"
         << "scope=geometry_material_and_lattice_initialization_only\n"
         << "PASS=" << pass << '\n'
         << "normal_exit_planned=" << pass << '\n'
         << "collide_and_stream_calls=0\n"
         << "formal_simulation_started=false\n"
         << "openlb_version_macro=" << OLB_VERSION << '\n'
         << "nx=" << nx << '\n'
         << "ny=" << ny << '\n'
         << "nz_fluid=" << nzFluid << '\n'
         << "material_0_nodes=" << materialCounts[0] << '\n'
         << "material_1_fluid_nodes=" << materialCounts[1] << '\n'
         << "material_2_substrate_nodes=" << materialCounts[2] << '\n'
         << "material_3_upper_wall_nodes=" << materialCounts[3] << '\n'
         << "expected_fluid_nodes=" << expectedFluidNodes << '\n'
         << "fluid_volume_m3=" << actualFluidVolume << '\n'
         << "expected_fluid_volume_m3=" << expectedFluidVolume << '\n'
         << "periodic_x=true\n"
         << "periodic_y=true\n"
         << "periodic_z=false\n"
         << "z_boundary=fixed_halfway_bounce_back\n"
         << "descriptor=D3Q19_FORCE\n"
         << "collision=ForcedBGK\n"
         << "dx_m=" << dx << '\n'
         << "dt_s=" << dt << '\n'
         << "tau=" << tau << '\n'
         << "omega=" << converter.getLatticeRelaxationFrequency() << '\n'
         << "acceleration_m_s2=" << acceleration << '\n'
         << "force_lattice=" << force[0] << ',' << force[1] << ',' << force[2] << '\n'
         << "geometry_pass=" << geometryPass << '\n'
         << "converter_pass=" << converterPass << '\n'
         << "exit_code=" << (pass ? 0 : 3) << '\n';

  std::cout << "Gate0 Case01 geometry/material initialization PASS="
            << std::boolalpha << pass
            << " fluid_nodes=" << materialCounts[1]
            << " collideAndStream=0\n";
  return pass ? 0 : 3;
}
