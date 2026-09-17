#include <olb.h>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

using namespace olb;
using T = double;
using DESCRIPTOR = descriptors::D3Q19<>;

constexpr T dx=5e-9, dt=1e-11, nu=1e-6, rhoPhys=1000.;
constexpr T Lx=240e-9, Ly=240e-9, h=75e-9, grooveDepth=100e-9;
constexpr T zCoreMin=-dx/2, zCoreMax=192.5e-9;
constexpr int overlap=3, steps=100;

// Outside of the non-periodic physical core.  x is deliberately ignored:
// x padding is a periodic image, while y and z padding are genuinely outside.
class PeriodicXOutside final : public IndicatorF3D<T> {
public:
  PeriodicXOutside() {
    this->_myMin = {-std::numeric_limits<T>::max(),-std::numeric_limits<T>::max(),-std::numeric_limits<T>::max()};
    this->_myMax = { std::numeric_limits<T>::max(), std::numeric_limits<T>::max(), std::numeric_limits<T>::max()};
    this->getName() = "PeriodicXOutside";
  }
  bool operator()(bool output[1], const T input[3]) override {
    const T eps=dx*1e-6;
    output[0] = input[1] < dx/2-eps || input[1] > Ly-dx/2+eps
             || input[2] < zCoreMin-eps || input[2] > zCoreMax+eps;
    return true;
  }
};

struct Stats {
  long long nodes=0;
  T massLattice=0, maxULattice=0, rhoMin=std::numeric_limits<T>::max(), rhoMax=-std::numeric_limits<T>::max();
  T lowOutKgS=0, highOutKgS=0;
  bool finite=true;
};

int materialAt(const Vector<T,3>& r) {
  const T x=r[0], y=r[1], z=r[2];
  if (z < 0) return 2;
  const bool mesa = x < 60e-9 || x >= 180e-9;
  if (z >= (mesa ? h : h+grooveDepth)) return 3;
  if (y < dx) return 4;
  if (y > Ly-dx) return 5;
  return 1;
}

template<class LAT,class GEO>
Stats sample(LAT& lat,GEO& geo,const UnitConverter<T,DESCRIPTOR>& converter) {
  Stats s;
  for(int iC=0;iC<lat.getLoadBalancer().size();++iC) {
    auto& block=lat.getBlock(iC); auto& bg=geo.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      const int m=bg.getMaterial(p); if(m!=1&&m!=4&&m!=5) return;
      auto cell=block.get(p); T u[3]{}; cell.computeU(u); const T rho=cell.computeRho();
      const T umag=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      s.nodes++; s.massLattice+=rho; s.maxULattice=std::max(s.maxULattice,umag);
      s.rhoMin=std::min(s.rhoMin,rho); s.rhoMax=std::max(s.rhoMax,rho);
      s.finite = s.finite && std::isfinite(rho) && std::isfinite(umag);
      // Cell-centred quadrature on each pressure plane; outward signs differ.
      const T uyPhys=converter.getPhysVelocity(u[1]);
      if(m==4) s.lowOutKgS += -rho*rhoPhys*uyPhys*dx*dx;
      if(m==5) s.highOutKgS += rho*rhoPhys*uyPhys*dx*dx;
    });
  }
  return s;
}

template<class GEO>
std::array<long long,8> auditNormals(GEO& geo, SuperIndicatorF3D<T>& outside,
                                     const std::filesystem::path& file) {
  // total, correct, zero, wrong, omitted, wall-overlap, seam, x-padding-misclassified
  std::array<long long,8> c{};
  std::ofstream out(file);
  out << "x_nm,y_nm,z_nm,material,type,nx,ny,nz,xm,xp,ym,yp,zm,zp,expected_ny,status\n";
  for(int iC=0;iC<geo.getLoadBalancer().size();++iC) {
    auto& bg=geo.getBlockGeometry(iC);
    auto fluidSuper=geo.getMaterialIndicator(1);
    auto& fluid=fluidSuper->getBlockIndicatorF(iC);
    auto& outBlock=outside.getBlockIndicatorF(iC);
    bg.forCoreSpatialLocations([&](LatticeR<3> p) {
      const int m=bg.getMaterial(p); if(m!=4&&m!=5) return; c[0]++;
      const auto [type,n]=computeBoundaryTypeAndNormal(fluid,outBlock,p);
      const int expected=m==4?-1:1;
      const bool zero=n==Vector<int,3>{0,0,0};
      const bool correct=type==DiscreteNormalType::Flat && n==Vector<int,3>{0,expected,0};
      if(correct)c[1]++; else if(zero)c[2]++; else c[3]++;
      const auto r=bg.getPhysR(p);
      const bool seam=r[0] < dx || r[0] > Lx-dx; if(seam)c[6]++;
      bool xOutM=false,xOutP=false; int im[4]={iC,p[0]-1,p[1],p[2]},ip[4]={iC,p[0]+1,p[1],p[2]};
      outside(&xOutM,im); outside(&xOutP,ip); if(xOutM||xOutP)c[7]++;
      const int xm=bg.getMaterial(p+Vector<int,3>{-1,0,0}), xp=bg.getMaterial(p+Vector<int,3>{1,0,0});
      const int ym=bg.getMaterial(p+Vector<int,3>{0,-1,0}), yp=bg.getMaterial(p+Vector<int,3>{0,1,0});
      const int zm=bg.getMaterial(p+Vector<int,3>{0,0,-1}), zp=bg.getMaterial(p+Vector<int,3>{0,0,1});
      if(m==2||m==3)c[5]++;
      out<<r[0]*1e9<<","<<r[1]*1e9<<","<<r[2]*1e9<<","<<m<<","<<int(type)<<","<<n[0]<<","<<n[1]<<","<<n[2]<<","<<xm<<","<<xp<<","<<ym<<","<<yp<<","<<zm<<","<<zp<<","<<expected<<","<<(correct?"correct":"invalid")<<"\n";
    });
  }
  c[4]=2400-c[0];
  return c;
}

template<class GEO>
std::array<long long,6> materialCounts(GEO& geo) {
  std::array<long long,6> n{};
  for(int iC=0;iC<geo.getLoadBalancer().size();++iC) {
    auto& bg=geo.getBlockGeometry(iC);
    bg.forCoreSpatialLocations([&](LatticeR<3> p){int m=bg.getMaterial(p);if(m>=0&&m<6)n[m]++;});
  }
  return n;
}

int main(int argc,char** argv) {
  initialize(&argc,&argv);
  const std::string run="open_drain_fixed_h75_periodic_outside_20260907";
  const auto out=std::filesystem::path("output")/run;
  if(singleton::mpi().getSize()!=1) { std::cerr<<"single rank required\n"; return 2; }
  if(std::filesystem::exists(out)) { std::cerr<<"output exists: "<<out<<"\n"; return 2; }
  std::filesystem::create_directories(out);
  singleton::directories().setOutputDir((out.string()+"/").c_str());
  std::ofstream log(out/"integration.log");
  log<<std::boolalpha<<std::setprecision(16);
  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1); cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> load(cuboids); SuperGeometry<T,3> geo(cuboids,load,overlap);
    for(int iC=0;iC<load.size();++iC) { auto& bg=geo.getBlockGeometry(iC); bg.forCoreSpatialLocations([&](LatticeR<3> p){bg.set(p,materialAt(bg.getPhysR(p)));}); }
    geo.communicate(); geo.checkForErrors(false);
    const auto materials0=materialCounts(geo);

    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geo);
    const auto audit=auditNormals(geo,outside,out/"pressure_node_diagnostic.csv");
    std::ofstream ai(out/"initialization_audit.txt");
    ai<<"expected_pressure_nodes=2400\nobserved_pressure_nodes="<<audit[0]<<"\ncorrect_normals="<<audit[1]
      <<"\nzero_normals="<<audit[2]<<"\nwrong_or_conflicting_normals="<<audit[3]<<"\nomitted="<<audit[4]
      <<"\nsolid_nodes_overwritten_by_pressure="<<audit[5]<<"\npressure_nodes_at_x_seam="<<audit[6]
      <<"\nx_periodic_padding_classified_outside="<<audit[7]<<"\noverlap_cells="<<overlap
      <<"\ngeometry_communicated_before_audit=true\nx_periodicity=true\ny_periodicity=false\nz_periodicity=false\n";
    if(audit[0]!=2400||audit[1]!=2400||audit[2]||audit[3]||audit[4]||audit[5]||audit[7])
      throw std::runtime_error("pressure-node normal audit failed");

    UnitConverter<T,DESCRIPTOR> converter(dx,dt,240e-9,1.,nu,rhoPhys);
    SuperLattice<T,DESCRIPTOR> lat(converter,cuboids,load);
    dynamics::set<BGKdynamics>(lat,geo,1);
    boundary::set<T,DESCRIPTOR,boundary::LocalPressure<T,DESCRIPTOR,BGKdynamics<T,DESCRIPTOR>>>(lat,geo.getMaterialIndicator(4),geo.getMaterialIndicator(1),outside);
    boundary::set<T,DESCRIPTOR,boundary::LocalPressure<T,DESCRIPTOR,BGKdynamics<T,DESCRIPTOR>>>(lat,geo.getMaterialIndicator(5),geo.getMaterialIndicator(1),outside);
    boundary::set<boundary::BounceBack>(lat,geo,2);
    boundary::set<boundary::BounceBack>(lat,geo,3);
    AnalyticalConst3D<T,T> one(1),zeroU(0,0,0);
    lat.defineRhoU(geo.getMaterialIndicator({1,4,5}),one,zeroU);
    for(int m:{1,4,5})lat.iniEquilibrium(geo,m,one,zeroU);
    lat.initialize();

    SuperVTMwriter3D<T> writer("periodic_pressure_baseline",overlap);
    SuperGeometryF3D<T> material(geo); material.getName()="material";
    SuperLatticePhysVelocity3D<T,DESCRIPTOR> velocity(lat,converter); velocity.getName()="velocity_m_per_s";
    writer.addFunctor(material); writer.addFunctor(velocity); writer.createMasterFile(); writer.write(0);

    const Stats initial=sample(lat,geo,converter); Stats previous=initial,final=initial;
    const T massScale=rhoPhys*dx*dx*dx, mass0=initial.massLattice*massScale;
    T cumulativeOut=0;
    std::ofstream csv(out/"baseline_statistics.csv");
    csv<<"step,time_s,fluid_nodes,domain_mass_kg,relative_mass_change,low_outward_mass_flux_kg_s,high_outward_mass_flux_kg_s,net_outward_mass_flux_kg_s,cumulative_outward_mass_kg,mass_balance_residual_kg,relative_mass_balance_residual,max_speed_m_s,rho_min_lattice,rho_max_lattice,finite,material_unchanged\n"<<std::setprecision(16);
    for(int step=0;step<=steps;++step) {
      if(step)lat.collideAndStream();
      final=sample(lat,geo,converter);
      if(step) cumulativeOut += .5*((previous.lowOutKgS+previous.highOutKgS)+(final.lowOutKgS+final.highOutKgS))*dt;
      const T mass=final.massLattice*massScale, residual=mass-mass0+cumulativeOut;
      const bool unchanged=materialCounts(geo)==materials0;
      csv<<step<<","<<step*dt<<","<<final.nodes<<","<<mass<<","<<(mass-mass0)/mass0<<","<<final.lowOutKgS<<","<<final.highOutKgS<<","<<(final.lowOutKgS+final.highOutKgS)<<","<<cumulativeOut<<","<<residual<<","<<residual/mass0<<","<<converter.getPhysVelocity(final.maxULattice)<<","<<final.rhoMin<<","<<final.rhoMax<<","<<final.finite<<","<<unchanged<<"\n";
      previous=final;
    }
    writer.write(steps);
    const T mass=final.massLattice*massScale, residual=mass-mass0+cumulativeOut;
    const bool passFinite=final.finite, passU=converter.getPhysVelocity(final.maxULattice)<=1e-14;
    const bool passRho=final.rhoMin>=1.-1e-12&&final.rhoMax<=1.+1e-12;
    const bool passMass=std::abs((mass-mass0)/mass0)<=1e-13;
    const bool passBalance=std::abs(residual/mass0)<=1e-13;
    const bool passMaterial=materialCounts(geo)==materials0;
    const bool pass=passFinite&&passU&&passRho&&passMass&&passBalance&&passMaterial;
    log<<"OpenLB_version="<<OLB_VERSION<<"\nrun_id="<<run<<"\nsteps_completed="<<steps
       <<"\ndt_s="<<dt<<"\ntau="<<converter.getLatticeRelaxationTime()<<"\npressure_node_audit_pass=true"
       <<"\nfluid_nodes="<<final.nodes<<"\ninitial_mass_kg="<<mass0<<"\nfinal_mass_kg="<<mass
       <<"\nrelative_mass_change="<<(mass-mass0)/mass0<<"\nlow_outward_flux_kg_s="<<final.lowOutKgS
       <<"\nhigh_outward_flux_kg_s="<<final.highOutKgS<<"\ncumulative_outward_mass_kg="<<cumulativeOut
       <<"\nmass_balance_residual_kg="<<residual<<"\nrelative_mass_balance_residual="<<residual/mass0
       <<"\nmax_speed_m_s="<<converter.getPhysVelocity(final.maxULattice)<<"\nrho_range="<<final.rhoMin<<","<<final.rhoMax
       <<"\nfinite="<<final.finite<<"\nmaterial_unchanged="<<passMaterial<<"\npass_finite="<<passFinite
       <<"\npass_velocity="<<passU<<"\npass_density="<<passRho<<"\npass_mass="<<passMass
       <<"\npass_mass_balance="<<passBalance<<"\nPASS="<<pass<<"\nexit_code="<<(pass?0:3)<<"\n";
    std::ofstream record(out/"run_record.txt");
    record<<"run_id="<<run<<"\ncommand=./periodic_pressure_baseline\nsteps=100\nh_nm=75\ndx_nm=5\nperiodicity=x:true,y:false,z:false\ny_boundary=equal-reference-pressure\ninitial_velocity=0\nbody_force=0\nexit_reason="<<(pass?"completed_thresholds_passed":"completed_thresholds_failed")<<"\nexit_code="<<(pass?0:3)<<"\n";
    std::cout<<"completed "<<run<<" PASS="<<std::boolalpha<<pass<<"\n";
    return pass?0:3;
  } catch(const std::exception& e) {
    log<<"exception="<<e.what()<<"\nsteps_completed=0\nexit_code=4\n";
    std::ofstream record(out/"run_record.txt"); record<<"run_id="<<run<<"\ncommand=./periodic_pressure_baseline\nexit_reason=exception\nexit_code=4\nexception="<<e.what()<<"\n";
    std::cerr<<e.what()<<"\n"; return 4;
  }
}
