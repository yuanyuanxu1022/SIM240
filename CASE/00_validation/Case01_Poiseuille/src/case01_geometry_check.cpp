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

// ---- 物理尺度与流体参数（SI 单位）----
// 每个 lattice 节点在真实空间代表 dx=5 nm；dt 是一个 lattice 时间步对应的物理时间。
constexpr T dx = 5.0e-9;
constexpr T dt = 1.0e-11;
// x/y 为平面内周期方向，z 为上下固壁之间的流体高度。
constexpr T width = 240.0e-9;
constexpr T length = 240.0e-9;
constexpr T height = 75.0e-9;
constexpr T rhoPhys = 1000.0;
constexpr T nuPhys = 1.0e-6;
// 对 material 1（流体）施加的物理加速度，方向在后面指定为 +y。
constexpr T acceleration = 1.0e5;
// OpenLB super-geometry 的 communication overlap 层数；不是物理流体厚度。
constexpr int overlap = 3;

// 根据格点的物理 z 坐标赋予材料编号。
// material 1: 流体；material 2: 下基底；material 3: 上固壁。
// 固体节点中心位于真实壁面外侧，真实壁面由 halfway bounce-back 位于流体/固体节点中点。
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
  // 遍历所有核心格点，统计每种 material 的节点数，用于后续几何审计。
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
  // 初始化 OpenLB/MPI 环境；本 Gate 明确要求只使用一个 MPI rank。
  initialize(&argc, &argv);

  if (argc != 2) {
    std::cerr << "usage: case01_geometry_check OUTPUT_FILE\n";
    return 2;
  }
  if (singleton::mpi().getSize() != 1) {
    std::cerr << "Gate 0 geometry check requires one MPI rank\n";
    return 2;
  }

  // 物理尺寸转换为格点数：240/5=48，75/5=15，故预期流体节点数为 48*48*15。
  const int nx = static_cast<int>(std::llround(width / dx));
  const int ny = static_cast<int>(std::llround(length / dx));
  const int nzFluid = static_cast<int>(std::llround(height / dx));
  const long long expectedFluidNodes =
    static_cast<long long>(nx) * ny * nzFluid;
  const T expectedFluidVolume = width * length * height;

  // 建立含上下固体节点的计算 cuboid。
  // 起点为 (dx/2, dx/2, -dx/2)，因此流体首层中心在 z=+dx/2、
  // 下固体首层中心在 z=-dx/2；两者中点 z=0 才是真实下壁面。
  IndicatorCuboid3D<T> domain(
    {width - dx, length - dx, height + 20.0e-9},
    {dx / 2.0, dx / 2.0, -dx / 2.0});
  CuboidDecomposition<T, 3> cuboids(domain, dx, 1);
  // x/y 严格周期：从一侧离开会从另一侧进入；z 不周期，因为上下需要真实固壁。
  cuboids.setPeriodicity({true, true, false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T, 3> geometry(cuboids, loadBalancer, overlap);

  // geometry 是“地图”：先给每个格点标记流体或固体，尚未进行 LBM 时间推进。
  for (int iC = 0; iC < loadBalancer.size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticePosition) {
      block.set(latticePosition, materialAt(block.getPhysR(latticePosition)));
    });
  }
  geometry.communicate();
  geometry.checkForErrors(false);
  const auto materialCounts = countMaterials(geometry);

  // UnitConverter 负责物理单位与 lattice 单位互换；它由 dx、dt、黏性和密度给出 tau/omega。
  UnitConverter<T, DESCRIPTOR> converter(
    dx, dt, width, 1.0, nuPhys, rhoPhys);
  // lattice 是“物理求解器”：在已标记的 geometry 上存放并演化 LBM population。
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  // material 1 使用受体力驱动的 BGK 碰撞；material 2/3 为固定无滑移反弹壁面。
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);
  boundary::set<boundary::BounceBack>(lattice, geometry, 2);
  boundary::set<boundary::BounceBack>(lattice, geometry, 3);

  // 初始化所有流体节点：lattice density rho=1，速度 u=(0,0,0)。
  // rho=1 是无量纲 lattice 密度，不是把物理水密度改成 1 kg/m^3。
  AnalyticalConst3D<T, T> one(1.0);
  AnalyticalConst3D<T, T> zeroVelocity(0.0, 0.0, 0.0);
  lattice.defineRhoU(geometry.getMaterialIndicator(1), one, zeroVelocity);
  lattice.iniEquilibrium(geometry, 1, one, zeroVelocity);

  // 物理加速度换算为 lattice 体力：a_LB=a_phys*dt^2/dx。
  // force[0/1/2] 分别对应 x/y/z；此处只在 +y 方向施加体力。
  Vector<T, 3> force{0.0, 0.0, 0.0};
  force[1] = acceleration * dt * dt / dx;
  fields::set<descriptors::FORCE>(
    lattice, geometry.getMaterialIndicator(1), force);
  lattice.setParameter<descriptors::OMEGA>(
    converter.getLatticeRelaxationFrequency());
  lattice.initialize();

  // 以下只审计“初始化是否正确”，没有调用 lattice.collideAndStream()，所以尚未模拟流动。
  const T actualFluidVolume = materialCounts[1] * dx * dx * dx;
  const T tau = converter.getLatticeRelaxationTime();
  // 几何门槛：流体节点数和体积正确，且上下固壁确实存在。
  const bool geometryPass =
    materialCounts[1] == expectedFluidNodes
    && materialCounts[2] > 0
    && materialCounts[3] > 0
    && std::abs(actualFluidVolume - expectedFluidVolume) <= 1.0e-32;
  // 单位换算门槛：本冻结配置要求 tau=1.7，且 +y lattice 体力为 2e-9。
  const bool converterPass =
    std::abs(tau - 1.7) <= 1.0e-12
    && std::abs(force[1] - 2.0e-9) <= 1.0e-20;
  const bool pass = geometryPass && converterPass;

  std::ofstream output(argv[1]);
  if (!output) {
    std::cerr << "cannot open Gate 0 output file\n";
    return 4;
  }
  // 将审计证据写入文本；PASS 仅代表初始化通过，不代表 Poiseuille 流动已验证。
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
