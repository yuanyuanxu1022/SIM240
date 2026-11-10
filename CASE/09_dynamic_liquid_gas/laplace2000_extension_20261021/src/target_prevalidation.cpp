#include <olb.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <regex>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using namespace olb;
using namespace olb::descriptors;
using namespace olb::names;
using T=double;

using PhaseCase=Case<
  NavierStokes,Lattice<T,D3Q19<RHO,NABLARHO,FORCE,EXTERNAL_FORCE,TAU_EFF>>,
  Component1,Lattice<T,D3Q19<FORCE,SOURCE,SOURCE_OLD,PHIWETTING,VELOCITY,OLD_PHIU,STATISTIC,CHEM_POTENTIAL,BOUNDARY>>
>;
using NSDynamics=MultiPhaseIncompressibleBGKdynamics<T,PhaseCase::descriptor_t_of<NavierStokes>>;
using CHDynamics=WellBalancedCahnHilliardBGKdynamics<T,PhaseCase::descriptor_t_of<Component1>>;
// Backend array entries mean phi=0, phi=1 despite their gas/liquid names.
// This case retains project phi=0 LIQUID, phi=1 GAS.
using MixtureRules=LinearTauViscosity;
using Coupling=WellBalancedCahnHilliardPostProcessor<MixtureRules>;

#include "target_parameters.h"
constexpr T pi=3.14159265358979323846;
template<typename T>
class TanhSpherePhaseF3D final : public AnalyticalF3D<T,T> {
  Vector<T,3> _center; T _radius,_width;
public:
  TanhSpherePhaseF3D(Vector<T,3> center,T radius,T width)
    : AnalyticalF3D<T,T>(1),_center(center),_radius(radius),_width(width) {}
  bool operator()(T output[],const T x[]) override
  {
    const T dist=std::sqrt((x[0]-_center[0])*(x[0]-_center[0])
                          +(x[1]-_center[1])*(x[1]-_center[1])
                          +(x[2]-_center[2])*(x[2]-_center[2]));
    const T d=dist-_radius;
    output[0]=T(.5)*(1+std::tanh(T(2)*d/_width));
    return true;
  }
};

struct Options {
  std::string mode,runId; int steps=0;
};
Options parse(int argc,char** argv) {
  Options o;
  for(int i=1;i<argc;++i) {
    const std::string k=argv[i];
    if(++i>=argc) throw std::runtime_error("missing argument");
    if(k=="--case") o.mode=argv[i];
    else if(k=="--run-id") o.runId=argv[i];
    else if(k=="--steps") o.steps=std::stoi(argv[i]);
    else throw std::runtime_error("unknown argument: "+k);
  }
  if(o.mode!="laplace")
    throw std::runtime_error("this extension permits laplace only");
  if(!std::regex_match(o.runId,std::regex("[A-Za-z0-9][A-Za-z0-9_-]*")))
    throw std::runtime_error("valid unique run-id required");
  if(o.steps!=0 && o.steps!=2000) throw std::runtime_error("extension permits 0-step preparation or exactly 2000 diagnostic steps; no formal validation");
  return o;
}

struct Config {
  int nx,ny,nz; T radius; bool walls,flat,gas;
  T lo=0,hi=0; // benchmark wall normal is local y; maps to project z
};
// Same exact half-cell wall strategy as paper 1; periodic tangential axes
// have no side-wall intersections. Avoid generic indicator ray tolerance.
class ExactFlatWalls final : public IndicatorCuboid3D<T> {
  T lower,upper;
public:
  ExactFlatWalls(const Config& c):IndicatorCuboid3D<T>(
    {T(c.nx)+4,c.hi-c.lo,T(c.nz)+4},{-2,c.lo,-2}),lower(c.lo),upper(c.hi) {}
  bool distance(T& d,const Vector<T,3>& x,const Vector<T,3>& v,int=-1) override {
    if(v[1]==0) return false;
    T t=((v[1]>0?upper:lower)-x[1])/v[1];
    if(t<0 || t>1) return false;
    if(std::abs(t-.5)<1e-12) t=.5;
    d=t*util::norm<3>(v); return true;
  }
};
Mesh<T,3> createMesh(const Config& c) {
  // Indicator endpoints are inclusive: N periodic nodes occupy coordinates 0..N-1.
  IndicatorCuboid3D<T> domain({T(c.nx-1),T(c.walls?c.ny:c.ny-1),T(c.nz-1)},{0,0,0});
  Mesh<T,3> mesh(domain,T(1),1); mesh.setOverlap(3);
  mesh.getCuboidDecomposition().setPeriodicity(c.walls?Vector<bool,3>{true,false,true}:Vector<bool,3>{true,true,true});
  return mesh;
}
void prepareGeometry(PhaseCase& c,Config& cfg) {
  auto& g=c.getGeometry();
  if(cfg.walls) { g.rename(0,2); g.rename(2,1,{0,1,0}); }
  else g.rename(0,1);
  g.innerClean(); g.checkForErrors(false);
  T ymin=1e9,ymax=-1e9;
  auto& ns=c.getLattice(NavierStokes{});
  for(int i=0;i<ns.getLoadBalancer().size();++i) {
    auto& bg=g.getBlockGeometry(i);
    ns.getBlock(i).forCoreSpatialLocations([&](LatticeR<3> r) {
      if(bg.getMaterial(r)==1) { T y=bg.getPhysR(r)[1]; ymin=std::min(ymin,y); ymax=std::max(ymax,y); }
    });
  }
  cfg.lo=ymin-.5; cfg.hi=ymax+.5;
  if(cfg.flat && std::abs(cfg.hi-cfg.lo-30)>1e-12)
    throw std::runtime_error("flat gap must equal 30 lattice cells = 75 nm");
}

void prepareLattice(PhaseCase& c,const Config& cfg) {
  auto& g=c.getGeometry(); auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  using NSD=PhaseCase::descriptor_t_of<NavierStokes>;
  // Solver coordinates are lattice units. SI conversion is explicit in target_parameters.h;
  // this converter is deliberately lattice identity, never used for SI output.
  ns.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,NSD>>(cfg.nx,tauL,T(cfg.nx),T(0),T(1./6.),T(1));
  ch.setUnitConverter(ns.getUnitConverter());
  auto bulk=g.getMaterialIndicator(1);
  dynamics::set<NSDynamics>(ns,bulk); dynamics::set<CHDynamics>(ch,bulk);
  if(cfg.walls) {
    ExactFlatWalls wall(cfg);
    setBouzidiBoundary(ns,g,2,wall); setBouzidiWellBalanced(ch,g,2,wall);
  }
  ch.addPostProcessor<stage::PostStream>(bulk,meta::id<RhoWettingStatistics>());
  auto& cp=c.setCouplingOperator("Coupling",Coupling{},NavierStokes{},ns,Component1{},ch);
  cp.restrictTo(bulk);
  cp.setParameter<MixtureRules::TAUS>({tauL,tauG});
  cp.setParameter<MixtureRules::RHOS>({rhoL,rhoG});
  ch.addPostProcessor<stage::ChemPotCalc>(meta::id<ChemPotentialPhaseFieldProcessor>());
  ns.setParameter<OMEGA>(1/tauL); ch.setParameter<OMEGA>(1/tauPhase);
  ch.setParameter<THETA>(pi/2); ch.setParameter<INTERFACE_WIDTH>(interfaceWidth);
  ch.setParameter<SCALAR>(sigma); ch.setParameter<ADDEND>(T(0));
  auto& comm=ch.getCommunicator(stage::PreCoupling());
  comm.requestOverlap(2); comm.requestField<STATISTIC>();
  comm.requestField<PHIWETTING>(); comm.requestField<CHEM_POTENTIAL>(); comm.exchangeRequests();
}
void syncChemical(PhaseCase& c) {
  auto& ch=c.getLattice(Component1{});
  // iniEquilibrium changes populations, not the STATISTIC cache used by coupling.
  // Refresh from actual populations, without clipping/renormalizing either phase.
  for(int i=0;i<ch.getLoadBalancer().size();++i) {
    auto& g=c.getGeometry().getBlockGeometry(i); auto& h=ch.getBlock(i);
    h.forCoreSpatialLocations([&](LatticeR<3> r) {
      if(g.getMaterial(r)==1) { auto cell=h.get(r); RhoWettingStatistics{}.apply(cell); }
    });
  }
  ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.executePostProcessors(stage::PreCoupling());
  ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.executePostProcessors(stage::ChemPotCalc());
  ch.getCommunicator(stage::PreCoupling()).communicate();
}
void initializeFields(PhaseCase& c,const Config& cfg) {
  auto& g=c.getGeometry(); auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  AnalyticalConst3D<T,T> zero(0),one(1),rhoLiquid(rhoL),rhoGas(rhoG),tauLiquid(tauL),tauGas(tauG),two(2),vel(0,0,0);
  AnalyticalConst3D<T,T> flatPhi(cfg.gas?1:0),drive(cfg.flat?bodyForce:0,0,0);
  const Vector<T,3> center{T(cfg.nx)/2,cfg.walls?cfg.lo:T(cfg.ny)/2,T(cfg.nz)/2};
  TanhSpherePhaseF3D<T> sphere(center,cfg.radius,interfaceWidth);
  AnalyticalF3D<T,T>& phi=cfg.flat?static_cast<AnalyticalF3D<T,T>&>(flatPhi):static_cast<AnalyticalF3D<T,T>&>(sphere);
  AnalyticalIdentity3D<T,T> rho(rhoLiquid+(rhoGas-rhoLiquid)*phi),tau(tauLiquid+(tauGas-tauLiquid)*phi);
  auto all=g.getMaterialIndicator({0,1,2}); auto bulk=g.getMaterialIndicator(1);
  // Initialize fields BEFORE any equilibrium/momentum computation that divides by RHO.
  fields::set<RHO>(ns,all,rho); fields::set<TAU_EFF>(ns,all,tau);
  fields::set<NABLARHO>(ns,all,vel); fields::set<FORCE>(ns,all,vel);
  fields::set<EXTERNAL_FORCE>(ns,all,vel); fields::set<BODY_FORCE>(ns,all,drive);
  fields::set<SOURCE>(ch,all,zero); fields::set<SOURCE_OLD>(ch,all,zero);
  fields::set<VELOCITY>(ch,all,vel); fields::set<OLD_PHIU>(ch,all,vel);
  fields::set<PHIWETTING>(ch,all,phi); fields::set<CHEM_POTENTIAL>(ch,all,zero);
  fields::set<BOUNDARY>(ch,all,zero);
  if(cfg.walls) fields::set<BOUNDARY>(ch,g.getMaterialIndicator(2),two);
  // p_h starts at zero: -phi grad(mu) uses a modified pressure gauge.
  ns.iniEquilibrium(all,zero,vel); ch.iniEquilibrium(all,phi,vel);
  ns.initialize(); ch.initialize();
  fields::set<PHIWETTING>(ch,all,phi); ch.iniEquilibrium(all,phi,vel);
  syncChemical(c); ch.iniEquilibrium(all,phi,vel); syncChemical(c);
  ns.iniEquilibrium(all,zero,vel);
  c.getOperator("Coupling").apply();
}

struct Stats {
  T liquid=0,mass=0,minPhi=1e9,maxPhi=-1e9,minRho=1e9,maxRho=-1e9,maxU=0;
  T mappingError=0,tauError=0,pIn=0,pOut=0,pbIn=0,pbOut=0,muIn=0,muOut=0;
  T sumUx=0,errorSq=0,exactSq=0;
  long long fluid=0,inside=0,outside=0,solid=0;
  bool finite=true;
};
Stats measure(PhaseCase& c,const Config& cfg,const std::filesystem::path& samples={}) {
  Stats s; auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  std::ofstream field;
  if(!samples.empty()) { field.open(samples); field<<std::setprecision(17)<<"x_lu,y_lu,z_lu,phi,rho_lu,tau,p_h_lu,chemical_potential_lu,p_bulk_candidate_lu,ux_lu,uy_lu,uz_lu\n"; }
  for(int i=0;i<ns.getLoadBalancer().size();++i) {
    auto& g=c.getGeometry().getBlockGeometry(i); auto& n=ns.getBlock(i); auto& h=ch.getBlock(i);
    n.forCoreSpatialLocations([&](LatticeR<3> r) {
      if(g.getMaterial(r)==2) { ++s.solid; return; } if(g.getMaterial(r)!=1) return;
      ++s.fluid; auto nc=n.get(r); auto hc=h.get(r); const auto x=g.getPhysR(r);
      const T phi=hc.computeRho(),rho=nc.template getField<RHO>(),tau=nc.template getField<TAU_EFF>();
      const T p=nc.computeRho(),mu=hc.template getField<CHEM_POTENTIAL>();
      const T beta=12*sigma/interfaceWidth,f0=beta*phi*phi*(phi-1)*(phi-1);
      // Bulk limit of Korteweg normal stress, NOT interface pressure tensor.
      const T pb=p+phi*mu-f0;
      T u[3]{}; nc.computeU(u); T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      s.finite &= std::isfinite(phi)&&std::isfinite(rho)&&std::isfinite(p)&&std::isfinite(mu)&&std::isfinite(tau)&&std::isfinite(speed);
      for(int q=0;q<19;++q) s.finite &= std::isfinite(nc[q])&&std::isfinite(hc[q]);
      s.liquid+=1-phi; s.mass+=rho; s.sumUx+=u[0];
      s.minPhi=std::min(s.minPhi,phi); s.maxPhi=std::max(s.maxPhi,phi);
      s.minRho=std::min(s.minRho,rho); s.maxRho=std::max(s.maxRho,rho); s.maxU=std::max(s.maxU,speed);
      s.mappingError=std::max(s.mappingError,std::abs(rho-(rhoL+(rhoG-rhoL)*phi)));
      s.tauError=std::max(s.tauError,std::abs(tau-(tauL+(tauG-tauL)*phi)));
      if(phi<.01) { ++s.inside; s.pIn+=p; s.pbIn+=pb; s.muIn+=mu; }
      if(phi>.99) { ++s.outside; s.pOut+=p; s.pbOut+=pb; s.muOut+=mu; }
      if(cfg.flat) {
        T density=cfg.gas?rhoG:rhoL,nu=((cfg.gas?tauG:tauL)-.5)/3;
        T exact=bodyForce*(x[1]-cfg.lo)*(cfg.hi-x[1])/(2*density*nu);
        s.errorSq+=(u[0]-exact)*(u[0]-exact); s.exactSq+=exact*exact;
      }
      // Midplane data sufficient for interface fits; avoid full-domain CSV overhead.
      if(field.is_open() && std::abs(x[2]-T(cfg.nz)/2)<.25)
        field<<x[0]<<','<<x[1]<<','<<x[2]<<','<<phi<<','<<rho<<','<<tau<<','<<p<<','<<mu<<','<<pb<<','<<u[0]<<','<<u[1]<<','<<u[2]<<'\n';
    });
  }
  if(s.inside) { s.pIn/=s.inside; s.pbIn/=s.inside; s.muIn/=s.inside; }
  else s.pIn=s.pbIn=s.muIn=std::numeric_limits<T>::quiet_NaN();
  if(s.outside) { s.pOut/=s.outside; s.pbOut/=s.outside; s.muOut/=s.outside; }
  else s.pOut=s.pbOut=s.muOut=std::numeric_limits<T>::quiet_NaN();
  return s;
}

bool auditGeometry(PhaseCase& c,const Config& cfg,const std::filesystem::path& path) {
  auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  using D=PhaseCase::descriptor_t_of<NavierStokes>;
  long long candidates=0,installed=0,bad=0,fallback=0,fluid=0;
  T genericQError=0;
  ExactFlatWalls wall(cfg);
  IndicatorCuboid3D<T> genericWall({T(cfg.nx)+4,cfg.hi-cfg.lo,T(cfg.nz)+4},{-2,cfg.lo,-2});
  for(int i=0;i<ns.getLoadBalancer().size();++i) {
    auto& g=c.getGeometry().getBlockGeometry(i); auto& n=ns.getBlock(i); auto& h=ch.getBlock(i);
    n.forCoreSpatialLocations([&](LatticeR<3> r) {
      if(g.getMaterial(r)!=1) return;
      ++fluid;
      for(int q=1;q<19;++q) {
        const auto v=descriptors::c<D>(q);
        const T qn=n.get(r).template getFieldComponent<BOUZIDI_DISTANCE>(q);
        const T qh=h.get(r).template getFieldComponent<BOUZIDI_DISTANCE>(q);
        const bool target=cfg.walls && g.getMaterial(r+v)==2;
        if(qn>=0) ++installed;
        if(target) {
          ++candidates; T dist=-1; auto x=g.getPhysR(r); Vector<T,3> dir{T(v[0]),T(v[1]),T(v[2])};
          const bool found=wall.distance(dist,x.data(),dir.data(),g.getIcGlob());
          const T len=std::sqrt(T(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]));
          T genericDist=-1;
          if(genericWall.distance(genericDist,x.data(),dir.data(),g.getIcGlob()))
            genericQError=std::max(genericQError,std::abs(genericDist/len-.5));
          if(!found || dist<0 || dist>len || g.getMaterial(r-v)!=1) ++fallback;
          if(std::abs(qn-.5)>1e-10 || std::abs(qh-.5)>1e-10 || !found || std::abs(dist/len-.5)>1e-10) ++bad;
        } else if(qn>=0 || qh>=0) ++bad;
      }
    });
  }
  const long long expectedFluid=static_cast<long long>(cfg.nx)*cfg.nz*(cfg.walls?cfg.ny-1:cfg.ny);
  if(fluid!=expectedFluid) ++bad;
  std::ofstream f(path); f<<std::boolalpha<<std::setprecision(17)
    <<"wall_lower_lattice="<<cfg.lo<<"\nwall_upper_lattice="<<cfg.hi
    <<"\ncandidate_links="<<candidates<<"\ninstalled_ns_links="<<installed
    <<"\nbad_ns_or_ch_links="<<bad<<"\nfallback_predicate_count="<<fallback
    <<"\nfluid_nodes="<<fluid<<"\nexpected_fluid_nodes="<<expectedFluid
    <<"\ngeneric_indicator_max_q_deviation_diagnostic="<<genericQError
    <<"\nlink_audit_pass="<<(bad==0&&fallback==0&&candidates==installed)<<'\n';
  return bad==0&&fallback==0&&candidates==installed;
}
// Prevent coupling division by a nonpositive extrapolated density BEFORE applying it.
void requirePositiveDensity(PhaseCase& c) {
  auto& ch=c.getLattice(Component1{});
  for(int i=0;i<ch.getLoadBalancer().size();++i) {
    auto& g=c.getGeometry().getBlockGeometry(i); auto& h=ch.getBlock(i);
    h.forCoreSpatialLocations([&](LatticeR<3> r) {
      if(g.getMaterial(r)!=1) return;
      T phi=h.get(r).computeRho(),rho=rhoL+(rhoG-rhoL)*phi;
      if(!std::isfinite(phi)||!std::isfinite(rho)||rho<=0)
        throw std::runtime_error("nonpositive/nonfinite mixture density before coupling; no clipping");
    });
  }
}
int main(int argc,char** argv) {
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1) { std::cerr<<"single rank only\n"; return 2; }
  try {
    const Options o=parse(argc,argv); bool flat=o.mode=="flat_liquid"||o.mode=="flat_gas";
    Config cfg=flat?Config{16,31,16,0,true,true,o.mode=="flat_gas"}:
      o.mode=="contact"?Config{64,40,64,18,true,false,false}:Config{64,64,64,16,false,false,false};
    const auto out=std::filesystem::path("output")/o.runId;
    if(std::filesystem::exists(out)) throw std::runtime_error("refusing to overwrite run-id");
    std::filesystem::create_directories(out); singleton::directories().setOutputDir((out.string()+"/").c_str());
    PhaseCase::ParametersD parameters; auto mesh=createMesh(cfg); PhaseCase c(parameters,mesh);
    prepareGeometry(c,cfg); prepareLattice(c,cfg);
    const bool geometry=auditGeometry(c,cfg,out/"geometry_audit.txt");
    if(!geometry) throw std::runtime_error("geometry/link audit failed");
    initializeFields(c,cfg);
    std::ofstream csv(out/"history.csv"); csv<<std::setprecision(17)
      <<"step,time_s,liquid_amount_lu3,total_mass_lu,liquid_drift,total_mass_drift,phi_min,phi_max,rho_min,rho_max,max_Mach,max_u_m_s,rho_mapping_error,tau_mapping_error,p_h_inside_minus_outside_Pa,p_bulk_candidate_inside_minus_outside_Pa,mu_inside_Pa,mu_outside_Pa,flux_x_m2_s,velocity_L2_relative_error,finite\n";
    Stats initial=measure(c,cfg,out/"slice_initial.csv");
    bool safe=true; int completed=0;
    for(int step=0;step<=o.steps;++step) {
      if(step) {
        c.getLattice(NavierStokes{}).collideAndStream(); c.getLattice(Component1{}).collideAndStream();
        requirePositiveDensity(c); syncChemical(c); c.getOperator("Coupling").apply();
      }
      Stats s=measure(c,cfg); T ma=std::sqrt(T(3))*s.maxU;
      T ld=initial.liquid>1e-10?(s.liquid-initial.liquid)/initial.liquid:std::numeric_limits<T>::quiet_NaN();
      T md=(s.mass-initial.mass)/initial.mass;
      T q=s.sumUx/(T(cfg.nx)*cfg.nz)*dxSI*velocityScale;
      T l2=s.exactSq>0?std::sqrt(s.errorSq/s.exactSq):std::numeric_limits<T>::quiet_NaN();
      csv<<step<<','<<step*dtSI<<','<<s.liquid<<','<<s.mass<<','<<ld<<','<<md<<','<<s.minPhi<<','<<s.maxPhi<<','<<s.minRho<<','<<s.maxRho<<','<<ma<<','<<s.maxU*velocityScale<<','<<s.mappingError<<','<<s.tauError<<','<<(s.pIn-s.pOut)*pressureScale<<','<<(s.pbIn-s.pbOut)*pressureScale<<','<<s.muIn*pressureScale<<','<<s.muOut*pressureScale<<','<<q<<','<<l2<<','<<s.finite<<'\n';
      if(step>0 && step%250==0) measure(c,cfg,out/("slice_step_"+std::to_string(step)+".csv"));
      completed=step;
      safe=s.finite&&ma<.05&&s.minRho>0&&s.minPhi>=-.05&&s.maxPhi<=1.05&&s.mappingError<1e-10&&s.tauError<1e-10;
      if(!safe) break;
    }
    measure(c,cfg,out/"slice_final.csv");
    std::ofstream f(out/"result.txt"); f<<std::boolalpha<<std::setprecision(17)
      <<"case="<<o.mode<<"\nrun_id="<<o.runId<<"\nsteps_completed="<<completed<<"\nsteps_requested="<<o.steps
      <<"\ninitialization_or_pilot_safe="<<safe<<"\nlink_audit_pass="<<geometry
      <<"\nNUMERICAL_GATE=NOT_EVALUATED\nRESULT_PASS=NOT_EVALUATED\ngeometry_PASS=NOT_EVALUATED\n"
      <<"formal_validation_released=false\nmodel_material_not_GHY=true\n";
    return safe&&completed==o.steps?0:3;
  } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 4; }
}

