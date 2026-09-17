#include <olb.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <typeinfo>
#include <vector>

using namespace olb;

using T = double;
using D = descriptors::D3Q19<descriptors::BOUZIDI_DISTANCE,
                             descriptors::BOUZIDI_VELOCITY>;

constexpr T dx = 5e-9;
constexpr T dt = 1e-11;
constexpr T Lx = 240e-9;
constexpr T Ly = 240e-9;
constexpr T grooveDepth = 100e-9;
constexpr T rhoPhys = 1000.;
constexpr T nuPhys = 1e-6;
constexpr int overlap = 3;
constexpr int trajectorySteps = 10000;
constexpr int lastStep = 170;

class PeriodicXOutside final : public IndicatorF3D<T> {
public:
  PeriodicXOutside()
  {
    this->_myMin = {-1e9, -1e9, -1e9};
    this->_myMax = { 1e9,  1e9,  1e9};
    this->getName() = "PeriodicXOutside";
  }

  bool operator()(bool output[1], const T r[3]) override
  {
    const T eps = dx*1e-6;
    output[0] = r[1] < dx/2-eps || r[1] > Ly-dx/2+eps
             || r[2] < -dx/2-eps || r[2] > 192.5e-9+eps;
    return true;
  }
};

T smooth5(T s)
{
  s = std::clamp(s, T(0), T(1));
  return 10*s*s*s - 15*s*s*s*s + 6*s*s*s*s*s;
}

T dSmooth5(T s)
{
  s = std::clamp(s, T(0), T(1));
  return 30*s*s*(1-s)*(1-s);
}

T hAt(int step, bool moving)
{
  return moving ? 75e-9 - 10e-9*smooth5(T(step)/trajectorySteps) : 75e-9;
}

T wallSpeed(int step, bool moving)
{
  return moving ? -10e-9/(trajectorySteps*dt)
                    * dSmooth5((T(step)-T(0.5))/trajectorySteps)
                : 0;
}

bool isPunch(T x, T z, T h)
{
  return z >= ((x < 60e-9 || x >= 180e-9) ? h : h+grooveDepth);
}

int materialAt(const Vector<T,3>& r)
{
  if (r[2] < 0) {
    return 2;
  }
  if (isPunch(r[0], r[2], 75e-9)) {
    return 3;
  }
  if (r[1] < dx) {
    return 4;
  }
  if (r[1] > Ly-dx) {
    return 5;
  }
  return 1;
}

template <typename LATTICE, typename GEOMETRY>
std::array<int,3> updateLinks(LATTICE& lattice, GEOMETRY& geometry, T h, T uWall)
{
  int active = 0;
  int invalid = 0;
  int dualCells = 0;
  for (int iC=0; iC<lattice.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      auto cell = block.get(p);
      for (int iPop=0; iPop<D::q; ++iPop) {
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(iPop, -1);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(iPop, 0);
      }
      const int material = blockGeometry.getMaterial(p);
      if (material!=1 && material!=4 && material!=5) {
        return;
      }
      const auto r = blockGeometry.getPhysR(p);
      bool any = false;
      for (int iPop=1; iPop<D::q; ++iPop) {
        const auto c = descriptors::c<D>(iPop);
        const int solidMaterial = blockGeometry.getMaterial(p+c);
        if (solidMaterial!=2 && solidMaterial!=3) {
          continue;
        }
        T q = .5;
        T velocityCoefficient = 0;
        if (solidMaterial==3) {
          T lo=0, hi=1;
          for (int i=0; i<50; ++i) {
            const T alpha = (lo+hi)/2;
            if (isPunch(r[0]+alpha*dx*c[0], r[2]+alpha*dx*c[2], h)) {
              hi=alpha;
            } else {
              lo=alpha;
            }
          }
          q = (lo+hi)/2;
          velocityCoefficient = c[2]*uWall*dt/dx;
        }
        if (q<0 || q>1) {
          ++invalid;
        } else {
          cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(iPop,q);
          cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(iPop,
                                                                         velocityCoefficient);
          ++active;
          any=true;
        }
      }
      if (any && (material==4 || material==5)) {
        ++dualCells;
      }
    });
  }
  lattice.communicate();
  return {active,invalid,dualCells};
}

struct TracePoint {
  const char* name;
  LatticeR<3> p;
};

constexpr std::array<TracePoint,6> tracePoints {{
  {"dual",              {0,0,15}},
  {"first_alarm",       {0,0,14}},
  {"dual_y_interior",   {0,1,15}},
  {"alarm_y_interior",  {0,1,14}},
  {"dual_z_solid",      {0,0,16}},
  {"dual_x_periodic",   {47,0,15}}
}};

template <typename BLOCK, typename BLOCK_GEOMETRY>
void writeSnapshot(std::ofstream& out, BLOCK& block, BLOCK_GEOMETRY& geometry,
                   int step, const char* stage, const TracePoint& point)
{
  const auto p = point.p;
  auto cell = block.get(p);
  const int material = geometry.getMaterial(p);

  T rhoBoundary = cell.computeRho();
  T uBoundary[3] { };
  cell.computeU(uBoundary);

  T rhoDirect = 1;
  T jDirect[3] { };
  std::array<T,D::q> populations { };
  std::array<T,D::q> q { };
  std::array<T,D::q> velocityCoefficient { };
  for (int iPop=0; iPop<D::q; ++iPop) {
    populations[iPop] = cell[iPop];
    rhoDirect += populations[iPop];
    const auto c = descriptors::c<D>(iPop);
    for (int iD=0; iD<3; ++iD) {
      jDirect[iD] += populations[iPop]*c[iD];
    }
    q[iPop] = cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(iPop);
    velocityCoefficient[iPop] =
      cell.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(iPop);
  }
  T uDirect[3] {jDirect[0]/rhoDirect,jDirect[1]/rhoDirect,jDirect[2]/rhoDirect};
  const T speedBoundary = std::sqrt(uBoundary[0]*uBoundary[0]
                                  + uBoundary[1]*uBoundary[1]
                                  + uBoundary[2]*uBoundary[2]);
  const T speedDirect = std::sqrt(uDirect[0]*uDirect[0]
                                + uDirect[1]*uDirect[1]
                                + uDirect[2]*uDirect[2]);

  out << step << ',' << stage << ',' << point.name << ','
      << p[0] << ',' << p[1] << ',' << p[2] << ',' << material << ','
      << rhoBoundary << ',' << uBoundary[0] << ',' << uBoundary[1] << ','
      << uBoundary[2] << ',' << speedBoundary/std::sqrt(T(1)/3) << ','
      << rhoDirect << ',' << uDirect[0] << ',' << uDirect[1] << ','
      << uDirect[2] << ',' << speedDirect/std::sqrt(T(1)/3);
  for (T value : populations) out << ',' << value;
  for (T value : q) out << ',' << value;
  for (T value : velocityCoefficient) out << ',' << value;
  out << '\n';
}

void writeSnapshotHeader(std::ofstream& out)
{
  out << "step,stage,cell_name,ix,iy,iz,material,"
      << "rho_boundary_momenta,ux_boundary_momenta,uy_boundary_momenta,"
      << "uz_boundary_momenta,Mach_boundary_momenta,"
      << "rho_direct_shifted,ux_direct_shifted,uy_direct_shifted,"
      << "uz_direct_shifted,Mach_direct_shifted";
  for (int i=0; i<D::q; ++i) out << ",f" << i;
  for (int i=0; i<D::q; ++i) out << ",q" << i;
  for (int i=0; i<D::q; ++i) out << ",bouzidi_velocity_coeff" << i;
  out << '\n';
}

template <typename BLOCK, typename BLOCK_GEOMETRY>
void writeTopology(std::ofstream& out, BLOCK& block, BLOCK_GEOMETRY& geometry,
                   int step, const TracePoint& point)
{
  auto cell = block.get(point.p);
  const int currentMaterial = geometry.getMaterial(point.p);
  for (int iPop=0; iPop<D::q; ++iPop) {
    const auto c = descriptors::c<D>(iPop);
    const auto neighbor = point.p+c;
    out << step << ',' << point.name << ',' << point.p[0] << ',' << point.p[1]
        << ',' << point.p[2] << ',' << currentMaterial << ',' << iPop << ','
        << c[0] << ',' << c[1] << ',' << c[2] << ','
        << descriptors::opposite<D>(iPop) << ','
        << neighbor[0] << ',' << neighbor[1] << ',' << neighbor[2] << ','
        << geometry.getMaterial(neighbor) << ','
        << cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(iPop)
        << ','
        << cell.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(iPop)
        << '\n';
  }
}

int run(bool moving)
{
  const std::string label = moving ? "C" : "B";
  const std::string runId = "operator_population_trace_"+label+"_20260907";
  const auto outDir = std::filesystem::path("output")/runId;
  if (std::filesystem::exists(outDir)) {
    std::cerr << "Refusing to overwrite " << outDir << '\n';
    return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());

  IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},
                              {dx/2,dx/2,-dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);
  cuboids.setPeriodicity({true,false,false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  for (int iC=0; iC<loadBalancer.size(); ++iC) {
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    blockGeometry.forCoreSpatialLocations([&](LatticeR<3> p) {
      blockGeometry.set(p,materialAt(blockGeometry.getPhysR(p)));
    });
  }
  geometry.communicate();

  SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
  UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
  SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
  dynamics::set<BGKdynamics>(lattice,geometry,1);
  boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
  dynamics::set<NoDynamics>(lattice,geometry,2);
  dynamics::set<NoDynamics>(lattice,geometry,3);
  AnalyticalConst3D<T,T> one(1);
  AnalyticalConst3D<T,T> zero(0,0,0);
  lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
  for (int material : {1,4,5}) {
    lattice.iniEquilibrium(geometry,material,one,zero);
  }
  lattice.addPostProcessor<stage::PostStream>(
    meta::id<BouzidiVelocityPostProcessor>{});
  lattice.initialize();

  std::ofstream trace(outDir/"per_operator_population_trace.csv");
  trace << std::setprecision(17);
  writeSnapshotHeader(trace);
  std::ofstream topology(outDir/"d3q19_topology_step157.csv");
  topology << std::setprecision(17)
           << "step,cell_name,ix,iy,iz,current_material,direction,cx,cy,cz,"
           << "opposite,neighbor_ix,neighbor_iy,neighbor_iz,neighbor_material,q,"
           << "bouzidi_velocity_coefficient\n";

  auto& block = lattice.getBlock(0);
  auto& blockGeometry = geometry.getBlockGeometry(0);
  for (int step=1; step<=lastStep; ++step) {
    const auto linkCounts = updateLinks(lattice,geometry,hAt(step,moving),
                                        wallSpeed(step,moving));
    if (linkCounts[1] != 0) {
      std::cerr << "invalid q at step " << step << '\n';
      return 3;
    }
    if (step>=145) {
      for (const auto& point : tracePoints) {
        writeSnapshot(trace,block,blockGeometry,step,"pre_collision",point);
      }
    }

    // Exact public SuperLattice collision path: PreCollide processors/custom
    // tasks, block collision, then PostCollide communication/processors.
    lattice.collide();
    if (step>=145) {
      for (const auto& point : tracePoints) {
        writeSnapshot(trace,block,blockGeometry,step,
                      "post_LP_reconstruction_and_collision",point);
      }
    }

    // Split SuperLattice::AndStream so the state immediately after the block
    // stream can be captured before PostStream (moving Bouzidi) overwrites.
    for (int iC=0; iC<loadBalancer.size(); ++iC) {
      lattice.getBlock(iC).stream();
    }
    if (step>=145) {
      for (const auto& point : tracePoints) {
        writeSnapshot(trace,block,blockGeometry,step,
                      "post_stream_pre_PostStream",point);
      }
    }

    lattice.executePostProcessors(stage::PostStream{});
    if (step>=145) {
      for (const auto& point : tracePoints) {
        writeSnapshot(trace,block,blockGeometry,step,
                      "post_moving_Bouzidi_PostStream",point);
      }
    }
    lattice.executeCustomTasks(stage::PostStream{});
    lattice.getCommunicator(stage::PostPostProcess{}).communicate();
    if (step>=145) {
      for (const auto& point : tracePoints) {
        writeSnapshot(trace,block,blockGeometry,step,
                      "post_overlap_sync",point);
      }
    }
    if (step==157) {
      writeTopology(topology,block,blockGeometry,step,tracePoints[0]);
      writeTopology(topology,block,blockGeometry,step,tracePoints[1]);
    }
  }

  std::ofstream record(outDir/"run_record.txt");
  record << "run_id=" << runId << '\n'
         << "command=./explicit_piston_operator_population_trace " << label << '\n'
         << "exit_code=0\n"
         << "exit_reason=targeted_operator_trace_completed\n"
         << "steps=" << lastStep << '\n'
         << "trace_window=145..170\n"
         << "material_conversion_enabled=false\n";
  return 0;
}

int main(int argc, char** argv)
{
  initialize(&argc,&argv);
  if (singleton::mpi().getSize()!=1 || argc!=2) {
    return 2;
  }
  const char which = argv[1][0];
  if (which!='B' && which!='C') {
    return 2;
  }
  return run(which=='C');
}
