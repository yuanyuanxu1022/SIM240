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
using MixtureRules=LinearTauViscosity;
using Coupling=WellBalancedCahnHilliardPostProcessor<MixtureRules>;

constexpr T pi=3.1415926535897932384626433832795;
constexpr T tauL=1.,tauG=.8,tauPhase=1.,rhoL=1.,rhoG=1.,sigma=.01,interfaceWidth=4.,targetTheta=100.;

struct Options { std::string mode,runId; int maxSteps=-1,vtkInterval=-1; bool shortRun=false; };

Options parse(int argc,char** argv)
{
  Options o;
  for (int i=1;i<argc;++i) {
    std::string key=argv[i];
    auto value=[&](){ if (++i>=argc) throw std::runtime_error("missing value after "+key); return std::string(argv[i]); };
    if (key=="--case") o.mode=value();
    else if (key=="--run-id") o.runId=value();
    else if (key=="--max-steps") o.maxSteps=std::stoi(value());
    else if (key=="--vtk-interval") o.vtkInterval=std::stoi(value());
    else if (key=="--short") o.shortRun=true;
    else throw std::runtime_error("unknown option "+key);
  }
  if (o.mode!="contact"&&o.mode!="laplace") throw std::runtime_error("--case must be contact or laplace");
  if (!std::regex_match(o.runId,std::regex("[A-Za-z0-9][A-Za-z0-9_-]*"))) throw std::runtime_error("--run-id is required");
  if (o.maxSteps<0) o.maxSteps=o.shortRun?50:(o.mode=="contact"?6000:4000);
  if (o.vtkInterval<0) o.vtkInterval=o.shortRun?50:(o.mode=="contact"?500:400);
  return o;
}

struct Config {
  int nx,ny,nz; T radius; bool walls;
};

Mesh<T,3> createMesh(const Config& c)
{
  IndicatorCuboid3D<T> domain({T(c.nx),T(c.ny),T(c.nz)},{0,0,0});
  Mesh<T,3> mesh(domain,T(1),singleton::mpi().getSize());
  mesh.setOverlap(3);
  mesh.getCuboidDecomposition().setPeriodicity(c.walls?Vector<bool,3>{true,false,true}:Vector<bool,3>{true,true,true});
  return mesh;
}

void prepareGeometry(PhaseCase& c,const Config& cfg)
{
  auto& geometry=c.getGeometry();
  if (cfg.walls) {
    geometry.rename(0,2);
    geometry.rename(2,1,{0,1,0});
  } else geometry.rename(0,1);
  geometry.innerClean(); geometry.checkForErrors(false);
}

void prepareLattice(PhaseCase& c,const Config& cfg)
{
  auto& geometry=c.getGeometry();
  auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  using NSD=PhaseCase::descriptor_t_of<NavierStokes>;
  ns.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,NSD>>(cfg.nx,tauL,T(cfg.nx),T(0),T(1./6.),T(1));
  ch.setUnitConverter(ns.getUnitConverter());
  dynamics::set<NSDynamics>(ns,geometry.getMaterialIndicator({1}));
  dynamics::set<CHDynamics>(ch,geometry.getMaterialIndicator({1}));
  auto bulk=geometry.getMaterialIndicator(1);
  if (cfg.walls) {
    IndicatorCuboid3D<T> wallIndicator({T(cfg.nx)+2,T(cfg.ny)-2,T(cfg.nz)+2},{-1.5,.5,-1.5});
    setBouzidiBoundary(ns,geometry,2,wallIndicator);
    setBouzidiWellBalanced(ch,geometry,2,wallIndicator);
  }
  ch.addPostProcessor<stage::PostStream>(bulk,meta::id<RhoWettingStatistics>());
  auto& coupling=c.setCouplingOperator("Coupling",Coupling{},names::NavierStokes{},ns,names::Component1{},ch);
  coupling.restrictTo(bulk);
  coupling.setParameter<MixtureRules::TAUS>({tauG,tauL});
  coupling.setParameter<MixtureRules::RHOS>({rhoG,rhoL});
  ch.addPostProcessor<stage::ChemPotCalc>(meta::id<ChemPotentialPhaseFieldProcessor>());
  ns.setParameter<OMEGA>(T(1)/tauL); ch.setParameter<OMEGA>(T(1)/tauPhase);
  ch.setParameter<THETA>(pi-targetTheta*pi/T(180));
  ch.setParameter<INTERFACE_WIDTH>(interfaceWidth); ch.setParameter<SCALAR>(sigma);
  auto& communicator=ch.getCommunicator(stage::PreCoupling());
  communicator.requestOverlap(2); communicator.requestField<STATISTIC>();
  communicator.requestField<PHIWETTING>(); communicator.requestField<CHEM_POTENTIAL>(); communicator.exchangeRequests();
}

void initializeFields(PhaseCase& c,const Config& cfg)
{
  auto& geometry=c.getGeometry(); auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  AnalyticalConst3D<T,T> zero(0),one(1),rhoV(rhoG),rhoLiquid(rhoL),
    tauV(tauG),tauLiquid(tauL),zeroVelocity(0,0,0),two(2);
  const Vector<T,3> center=cfg.walls?Vector<T,3>{T(cfg.nx)/2,0,T(cfg.nz)/2}:Vector<T,3>{T(cfg.nx)/2,T(cfg.ny)/2,T(cfg.nz)/2};
  IndicatorSphere3D<T> sphere(center,cfg.radius);
  SmoothIndicatorSphere3D<T,T> smoothSphere(sphere,interfaceWidth/2);
  AnalyticalIdentity3D<T,T> phi(one-smoothSphere);
  AnalyticalIdentity3D<T,T> rho(rhoV+(rhoLiquid-rhoV)*phi);
  AnalyticalIdentity3D<T,T> tau(tauV+(tauLiquid-tauV)*phi);
  auto all=cfg.walls?geometry.getMaterialIndicator({0,1,2}):geometry.getMaterialIndicator({0,1});
  auto bulk=geometry.getMaterialIndicator(1);
  ns.defineRhoU(all,zero,zeroVelocity); ns.iniEquilibrium(all,zero,zeroVelocity);
  ch.defineRhoU(all,phi,zeroVelocity); ch.iniEquilibrium(all,phi,zeroVelocity);
  fields::set<RHO>(ns,all,rho); fields::set<TAU_EFF>(ns,bulk,tau);
  fields::set<EXTERNAL_FORCE>(ns,all,zeroVelocity);
  fields::set<SOURCE>(ch,bulk,zero); fields::set<SOURCE_OLD>(ch,bulk,zero);
  fields::set<PHIWETTING>(ch,bulk,phi); fields::set<CHEM_POTENTIAL>(ch,bulk,zero);
  fields::set<BOUNDARY>(ch,bulk,zero);
  if (cfg.walls) fields::set<BOUNDARY>(ch,geometry.getMaterialIndicator(2),two);
  ch.executePostProcessors(stage::PreCoupling()); ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.executePostProcessors(stage::ChemPotCalc()); ch.getCommunicator(stage::PreCoupling()).communicate();
  ns.initialize(); ch.initialize(); ch.iniEquilibrium(all,phi,zeroVelocity); ch.getCommunicator(stage::PreCoupling()).communicate();
}

struct Sample { T x,y,z,phi,p; };
struct Stats {
  T phaseAmount=0,phiMin=1e9,phiMax=-1e9,rhoMin=1e9,rhoMax=-1e9,maxU=0;
  T pInside=0,pOutside=0; long long nInside=0,nOutside=0,nFluid=0,nWall=0; bool finite=true;
  std::vector<Sample> samples;
};

Stats measure(PhaseCase& c)
{
  Stats s; auto& geometry=c.getGeometry(); auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  for (int iC=0;iC<ns.getLoadBalancer().size();++iC) {
    auto& g=geometry.getBlockGeometry(iC); auto& n=ns.getBlock(iC); auto& h=ch.getBlock(iC);
    n.forCoreSpatialLocations([&](LatticeR<3> r) {
      const int material=g.getMaterial(r); if (material==2) { ++s.nWall; return; } if (material!=1) return; ++s.nFluid;
      auto nc=n.get(r); auto hc=h.get(r); const T phi=hc.computeRho(); const T p=nc.computeRho(); const T rho=nc.template getField<RHO>();
      T u[3]{}; nc.computeU(u); const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      s.finite &= std::isfinite(phi)&&std::isfinite(p)&&std::isfinite(rho)&&std::isfinite(speed);
      for (int q=0;q<19;++q) s.finite &= std::isfinite(nc[q])&&std::isfinite(hc[q]);
      s.phaseAmount+=T(1)-phi; s.phiMin=std::min(s.phiMin,phi); s.phiMax=std::max(s.phiMax,phi);
      s.rhoMin=std::min(s.rhoMin,rho); s.rhoMax=std::max(s.rhoMax,rho); s.maxU=std::max(s.maxU,speed);
      if (phi<T(.1)) { s.pInside+=p; ++s.nInside; } if (phi>T(.9)) { s.pOutside+=p; ++s.nOutside; }
      const auto x=g.getPhysR(r); s.samples.push_back({x[0],x[1],x[2],phi,p});
    });
  }
  if (s.nInside) {
    s.pInside/=s.nInside;
  }
  if (s.nOutside) {
    s.pOutside/=s.nOutside;
  }
  return s;
}

T crossing(std::vector<std::pair<T,T>> line,bool first)
{
  std::sort(line.begin(),line.end()); std::vector<T> roots;
  for (std::size_t i=1;i<line.size();++i) {
    const T a=line[i-1].second-T(.5),b=line[i].second-T(.5);
    if (a==0) roots.push_back(line[i-1].first);
    else if (a*b<0) roots.push_back(line[i-1].first+(line[i].first-line[i-1].first)*(-a)/(b-a));
  }
  if (roots.empty()) {
    return std::numeric_limits<T>::quiet_NaN();
  }
  return first?roots.front():roots.back();
}

T contactAngle(const Stats& s,const Config& cfg)
{
  std::vector<std::pair<T,T>> horizontal,vertical;
  for (const auto& a:s.samples) {
    if (std::abs(a.z-T(cfg.nz)/2)<.25 && std::abs(a.y-T(2))<.25) horizontal.push_back({a.x,a.phi});
    if (std::abs(a.z-T(cfg.nz)/2)<.25 && std::abs(a.x-T(cfg.nx)/2)<.25) vertical.push_back({a.y,a.phi});
  }
  const T x1=crossing(horizontal,true),x2=crossing(horizontal,false),y3=crossing(vertical,false),x3=T(cfg.nx)/2,y12=T(2);
  if (!(std::isfinite(x1)&&std::isfinite(x2)&&std::isfinite(y3)) || std::abs(x2-x1)<1e-12) return std::numeric_limits<T>::quiet_NaN();
  const T s1=x1*x1+y12*y12,s2=x2*x2+y12*y12,s3=x3*x3+y3*y3;
  const T det=x1*y12+x2*y3+x3*y12-(x2*y12+x3*y12+x1*y3);
  if (std::abs(det)<1e-12) return std::numeric_limits<T>::quiet_NaN();
  const T m12=s1*y12+s2*y3+s3*y12-(s2*y12+s3*y12+s1*y3);
  const T m13=s1*x2+s2*x3+s3*x1-(s2*x1+s3*x2+s1*x3);
  const T xc=.5*m12/det,yc=-.5*m13/det,r=std::hypot(x2-xc,y12-yc);
  const T arg=std::clamp(-(yc-T(.5))/r,T(-1),T(1)); return std::acos(arg)*T(180)/pi;
}

void advance(PhaseCase& c)
{
  auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  ns.collideAndStream(); ch.collideAndStream();
  ch.getCommunicator(stage::PreCoupling()).communicate(); ch.executePostProcessors(stage::PreCoupling());
  ch.getCommunicator(stage::PreCoupling()).communicate(); ch.executePostProcessors(stage::ChemPotCalc());
  ch.getCommunicator(stage::PreCoupling()).communicate(); c.getOperator("Coupling").apply();
}

void writeVtk(PhaseCase& c,const std::string& name,int step,bool master)
{
  auto& geometry=c.getGeometry(); auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  using NSD=PhaseCase::descriptor_t_of<NavierStokes>; using CHD=PhaseCase::descriptor_t_of<Component1>;
  ns.setProcessingContext(ProcessingContext::Evaluation); ch.setProcessingContext(ProcessingContext::Evaluation);
  SuperVTMwriter3D<T> writer(name,3); SuperGeometryF3D<T> material(geometry); material.getName()="material";
  SuperLatticeDensity3D<T,NSD> pressure(ns); pressure.getName()="hydrodynamic_pressure_lattice";
  SuperLatticeVelocity3D<T,NSD> velocity(ns); velocity.getName()="velocity_lattice";
  SuperLatticeExternalScalarField3D<T,NSD,RHO> rho(ns); rho.getName()="mixture_density_lattice";
  SuperLatticeField3D<T,CHD,STATISTIC> phi(ch); phi.getName()="phase_field_phi";
  SuperLatticeExternalScalarField3D<T,CHD,CHEM_POTENTIAL> mu(ch); mu.getName()="chemical_potential";
  writer.addFunctor(material); writer.addFunctor(pressure); writer.addFunctor(velocity); writer.addFunctor(rho); writer.addFunctor(phi); writer.addFunctor(mu);
  if (master) {
    writer.createMasterFile();
  }
  writer.write(step);
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv); if (singleton::mpi().getSize()!=1) { std::cerr<<"single rank required\n"; return 2; }
  Options opt; try { opt=parse(argc,argv); } catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 2; }
  const Config cfg=opt.mode=="contact"?Config{64,40,64,18,true}:Config{64,64,64,16,false};
  const auto out=std::filesystem::path("output")/opt.runId; if (std::filesystem::exists(out)) return 2;
  std::filesystem::create_directories(out); singleton::directories().setOutputDir((out.string()+"/").c_str());
  std::ofstream log(out/"run.log"); log<<std::setprecision(17)<<std::boolalpha;
  try {
    PhaseCase::ParametersD parameters; auto mesh=createMesh(cfg); PhaseCase c(parameters,mesh);
    prepareGeometry(c,cfg); prepareLattice(c,cfg); initializeFields(c,cfg);
    const Stats initial=measure(c); const std::string vtkName=opt.mode=="contact"?"phasefield_contact_angle":"phasefield_laplace";
    writeVtk(c,vtkName,0,true);
    std::ofstream csv(out/"history.csv"); csv<<std::setprecision(17)
      <<"step,time_lattice,phase_amount,phase_amount_relative_drift,phi_min,phi_max,rho_min,rho_max,max_velocity_lattice,max_Mach,contact_angle_deg,pressure_inside_lattice,pressure_outside_lattice,delta_pressure_lattice,laplace_expected_lattice,laplace_relative_error,finite\n";
    T maxMassDrift=0,maxMach=0,phiMinAll=initial.phiMin,phiMaxAll=initial.phiMax,rhoMinAll=initial.rhoMin,rhoMaxAll=initial.rhoMax;
    std::vector<T> recentAngles,recentDp; bool allFinite=true; int finalStep=0;
    for (int step=0;step<=opt.maxSteps;++step) {
      if (step) {
        advance(c);
      }
      const Stats s=measure(c);
      const T drift=(s.phaseAmount-initial.phaseAmount)/initial.phaseAmount;
      const T mach=s.maxU/std::sqrt(T(1)/3),angle=cfg.walls?contactAngle(s,cfg):std::numeric_limits<T>::quiet_NaN();
      const T dp=std::abs(s.pInside-s.pOutside),expected=T(2)*sigma/cfg.radius,err=(dp-expected)/expected;
      maxMassDrift=std::max(maxMassDrift,std::abs(drift)); maxMach=std::max(maxMach,mach); phiMinAll=std::min(phiMinAll,s.phiMin); phiMaxAll=std::max(phiMaxAll,s.phiMax); rhoMinAll=std::min(rhoMinAll,s.rhoMin); rhoMaxAll=std::max(rhoMaxAll,s.rhoMax); allFinite=allFinite&&s.finite;
      csv<<step<<','<<step<<','<<s.phaseAmount<<','<<drift<<','<<s.phiMin<<','<<s.phiMax<<','<<s.rhoMin<<','<<s.rhoMax<<','<<s.maxU<<','<<mach<<','<<angle<<','<<s.pInside<<','<<s.pOutside<<','<<dp<<','<<expected<<','<<err<<','<<s.finite<<'\n';
      if (step%opt.vtkInterval==0&&step) { writeVtk(c,vtkName,step,false); if (std::isfinite(angle)) recentAngles.push_back(angle); recentDp.push_back(dp); }
      finalStep=step; if (!s.finite||mach>T(.05)||s.rhoMin<T(.8)||s.rhoMax>T(1.2)||s.phiMin<T(-.1)||s.phiMax>T(1.1)) break;
    }
    const Stats final=measure(c); if (finalStep%opt.vtkInterval) writeVtk(c,vtkName,finalStep,false);
    const T angle=cfg.walls?contactAngle(final,cfg):std::numeric_limits<T>::quiet_NaN(); const T dp=std::abs(final.pInside-final.pOutside),expected=T(2)*sigma/cfg.radius;
    auto tailRange=[](const std::vector<T>& v) { if (v.empty()) return std::numeric_limits<T>::infinity(); auto b=v.end()-std::min<std::size_t>(5,v.size()); return *std::max_element(b,v.end())-*std::min_element(b,v.end()); };
    const T angleRange=tailRange(recentAngles),dpRange=tailRange(recentDp),dpStability=dp>0?dpRange/dp:std::numeric_limits<T>::infinity();
    const bool basicStable=finalStep==opt.maxSteps&&allFinite&&maxMach<=T(.05)
      &&rhoMinAll>=T(.8)&&rhoMaxAll<=T(1.2)&&phiMinAll>=T(-.1)&&phiMaxAll<=T(1.1);
    const bool formalStable=basicStable&&phiMinAll>=T(-.05)&&phiMaxAll<=T(1.05)
      &&maxMassDrift<=T(1e-3);
    const bool stable=opt.shortRun?basicStable:formalStable;
    const bool physical=cfg.walls?(std::isfinite(angle)&&std::abs(angle-targetTheta)<=T(5)&&angleRange<=T(2)):(std::abs(dp-expected)/expected<=T(.15)&&dpStability<=T(.05));
    const bool pass=stable&&(opt.shortRun||physical);
    std::ofstream result(out/"result.txt"); result<<std::setprecision(17)<<std::boolalpha
      <<"PASS="<<pass<<"\nstable="<<stable<<"\nphysical_validation_pass="<<physical<<"\nsteps_completed="<<finalStep
      <<"\nmax_phase_amount_relative_drift="<<maxMassDrift<<"\nphi_range="<<phiMinAll<<','<<phiMaxAll<<"\nrho_range="<<rhoMinAll<<','<<rhoMaxAll<<"\nmax_Mach="<<maxMach
      <<"\ninput_contact_angle_deg="<<targetTheta<<"\nmeasured_contact_angle_deg="<<angle<<"\nlast_five_contact_angle_range_deg="<<angleRange
      <<"\nfinal_delta_pressure_lattice="<<dp<<"\nlaplace_expected_lattice="<<expected<<"\nlaplace_relative_error="<<std::abs(dp-expected)/expected<<"\nlast_five_delta_pressure_relative_range="<<dpStability
      <<"\nfinite="<<allFinite<<"\nexit_code="<<(pass?0:3)<<'\n';
    std::ofstream params(out/"parameters.txt"); params<<std::setprecision(17)
      <<"case="<<opt.mode<<"\nmodel=well_balanced_cahn_hilliard\ndimensions_lattice="<<cfg.nx<<','<<cfg.ny<<','<<cfg.nz<<"\nradius_lattice="<<cfg.radius
      <<"\ntau_liquid="<<tauL<<"\ntau_gas="<<tauG<<"\ntau_phase="<<tauPhase<<"\nrho_liquid_lattice="<<rhoL<<"\nrho_gas_lattice="<<rhoG<<"\nsurface_tension_lattice="<<sigma<<"\ninterface_width_lattice="<<interfaceWidth<<"\ninput_contact_angle_deg="<<targetTheta<<"\n";
    std::ofstream manifest(out/"run_manifest.txt"); manifest<<"run_id="<<opt.runId<<"\ncase="<<opt.mode<<"\ncommand=mpirun -np 1 ./phasefield_minimal_validation --case "<<opt.mode<<" --run-id "<<opt.runId<<" --max-steps "<<opt.maxSteps<<" --vtk-interval "<<opt.vtkInterval<<(opt.shortRun?" --short":"")<<"\nopenlb_head=882924a9cfc8dcdf82909e39530789cb6f5ebcc4\nexit_code="<<(pass?0:3)<<'\n';
    log<<"PASS="<<pass<<" stable="<<stable<<" physical="<<physical<<" step="<<finalStep<<" maxMach="<<maxMach<<" massDrift="<<maxMassDrift<<'\n';
    std::cout<<opt.runId<<" PASS="<<pass<<" step="<<finalStep<<'\n'; return pass?0:3;
  } catch (const std::exception& e) { log<<"exception="<<e.what()<<'\n'; std::cerr<<e.what()<<'\n'; return 4; }
}
