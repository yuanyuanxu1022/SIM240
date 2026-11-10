#include "dimension_corrected_ch.h"
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

using namespace olb;
using namespace olb::descriptors;
using T=double;
using D=D3Q19<FORCE,SOURCE,SOURCE_OLD,PHIWETTING,VELOCITY,OLD_PHIU,STATISTIC,CHEM_POTENTIAL,BOUNDARY>;
using TestCase=Case<names::Component1,Lattice<T,D>>;
constexpr T pi=3.14159265358979323846, amplitude=.05, speed=.008;
struct InitialPhase : AnalyticalF3D<T,T> {
  int n;
  explicit InitialPhase(int size):AnalyticalF3D<T,T>(1),n(size) {}
  bool operator()(T output[], const T input[]) override {
    output[0]=.5;
    for(int a=0;a<3;++a) output[0]+=amplitude/3*std::cos(2*pi*input[a]/n);
    return true;
  }
};

// Snapshot all core phi values before any neighbor gradient, then synchronize halos.
// This reproduces the coupling's D3Q19 gradient and AB source construction,
// with prescribed constant u and intentionally zero chemical potential.
void updateSource(TestCase& c, bool first) {
  auto& h=c.getLattice(names::Component1{});
  for(int b=0;b<h.getLoadBalancer().size();++b) {
    auto& block=h.getBlock(b);
    block.forCoreSpatialLocations([&](LatticeR<3> r) {
      auto cell=block.get(r);
      cell.template setField<STATISTIC>(cell.computeRho());
    });
  }
  h.getCommunicator(stage::PreCoupling()).communicate();
  for(int b=0;b<h.getLoadBalancer().size();++b) {
    auto& block=h.getBlock(b);
    block.forCoreSpatialLocations([&](LatticeR<3> r) {
      auto cell=block.get(r);
      Vector<T,3> grad{};
      for(int i=0;i<D::q;++i) {
        const T phi=cell.neighbor(descriptors::c<D>(i)).template getFieldComponent<STATISTIC>(0);
        grad+=phi*descriptors::c<D>(i)*descriptors::t<T,D>(i)*descriptors::invCs2<T,D>();
      }
      const auto u=cell.template getField<VELOCITY>();
      T s=0;
      for(int a=0;a<3;++a) s+=u[a]*grad[a];
      const T old=first?s:cell.template getField<SOURCE_OLD>();
      cell.template setField<SOURCE>(1.5*s-.5*old);
      cell.template setField<SOURCE_OLD>(s);
    });
  }
}

struct Stats {
  long long nodes=0;
  T sum=0,min=1e9,max=-1e9,error=0,norm=0,sourceSum=0;
  std::array<T,3> real{},imag{};
  bool finite=true;
};
Stats measure(TestCase& c,int n,int t,const std::array<T,3>& u,const std::filesystem::path& dump={}) {
  Stats s;
  std::ofstream out;
  if(!dump.empty()) {
    out.open(dump);out<<std::setprecision(17)<<"x,y,z,phi,exact_phi\n";
    if(!out) throw std::runtime_error("cannot open field output");
  }
  auto& h=c.getLattice(names::Component1{});
  for(int b=0;b<h.getLoadBalancer().size();++b) {
    auto& block=h.getBlock(b);auto& g=c.getGeometry().getBlockGeometry(b);
    block.forCoreSpatialLocations([&](LatticeR<3> r) {
      if(g.getMaterial(r)!=1) throw std::runtime_error("non-fluid core node");
      auto cell=block.get(r);const auto x=g.getPhysR(r);
      const T phi=cell.computeRho();T exact=.5;
      for(int a=0;a<3;++a) {
        const T phase=2*pi*x[a]/n;
        exact+=amplitude/3*std::cos(phase-2*pi*u[a]*t/n);
        s.real[a]+=(phi-.5)*std::cos(phase);
        s.imag[a]-=(phi-.5)*std::sin(phase);
      }
      s.sum+=phi;s.min=std::min(s.min,phi);s.max=std::max(s.max,phi);
      s.error+=(phi-exact)*(phi-exact);s.norm+=(exact-.5)*(exact-.5);
      s.sourceSum+=cell.template getField<SOURCE>();++s.nodes;
      s.finite &= std::isfinite(phi)&&std::isfinite(s.sourceSum);
      for(int i=0;i<D::q;++i) s.finite &= std::isfinite(cell[i]);
      if(out.is_open()) out<<x[0]<<','<<x[1]<<','<<x[2]<<','<<phi<<','<<exact<<'\n';
    });
  }
  if(s.nodes!=static_cast<long long>(n)*n*n) throw std::runtime_error("node-count mismatch");
  return s;
}

template<typename Dyn>
int run(int n,std::array<T,3> u,const std::string& variant,const std::string& direction,
        const std::filesystem::path& out,bool initOnly) {
  if(std::filesystem::exists(out)) throw std::runtime_error("refusing to overwrite output");
  std::filesystem::create_directories(out);
  singleton::directories().setOutputDir(out.string()+"/");
  IndicatorCuboid3D<T> domain({T(n-1),T(n-1),T(n-1)},{0,0,0});
  Mesh<T,3> mesh(domain,T(1),1);mesh.setOverlap(3);
  mesh.getCuboidDecomposition().setPeriodicity({true,true,true});
  TestCase::ParametersD parameters;TestCase c(parameters,mesh);
  auto& g=c.getGeometry();g.rename(0,1);g.innerClean();g.checkForErrors(false);
  auto& h=c.getLattice(names::Component1{});
  h.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,D>>(n,1.,T(n),0.,1./6.,1.);
  auto bulk=g.getMaterialIndicator(1);
  // Explicit wrapper: old uses its generated kernel; new falls back to local generic.
  dynamics::set<olb::CSE<Dyn>>(h,bulk);
  h.setParameter<OMEGA>(1.);
  AnalyticalConst3D<T,T> zero(0),vel(u[0],u[1],u[2]);InitialPhase phi(n);
  fields::set<VELOCITY>(h,bulk,vel);fields::set<CHEM_POTENTIAL>(h,bulk,zero);
  fields::set<SOURCE>(h,bulk,zero);fields::set<SOURCE_OLD>(h,bulk,zero);
  h.iniEquilibrium(bulk,phi,vel);
  auto& comm=h.getCommunicator(stage::PreCoupling());
  comm.requestOverlap(1);comm.requestField<STATISTIC>();comm.exchangeRequests();
  h.initialize();h.iniEquilibrium(bulk,phi,vel);
  updateSource(c,true);
  const int steps=initOnly?0:static_cast<int>(std::llround(n/(4*speed)));
  std::ofstream config(out/"config.json");
  config<<std::setprecision(17)<<"{\"N\":"<<n<<",\"steps\":"<<steps
        <<",\"variant\":\""<<variant<<"\",\"direction\":\""<<direction
        <<"\",\"u\":["<<u[0]<<','<<u[1]<<','<<u[2]
        <<"],\"old_cse_optimized\":true,\"new_cse_optimized\":false,\"MPI_ranks\":1,\"tau\":1,\"chemical_potential\":0}\n";
  config.close();
  std::ofstream history(out/"history.csv");
  history<<std::setprecision(17)<<"step,nodes,phase_sum,relative_drift,phi_min,phi_max,fluctuation_L2,source_sum,re_x,im_x,re_y,im_y,re_z,im_z,finite\n";
  const Stats initial=measure(c,n,0,u,out/"initial.csv");
  bool safe=true;int completed=0;
  for(int t=0;t<=steps;++t) {
    if(t) {h.collideAndStream();updateSource(c,false);}
    const auto s=measure(c,n,t,u);
    const T drift=(s.sum-initial.sum)/initial.sum;
    history<<t<<','<<s.nodes<<','<<s.sum<<','<<drift<<','<<s.min<<','<<s.max<<','<<std::sqrt(s.error/s.norm)<<','<<s.sourceSum;
    for(int a=0;a<3;++a) history<<','<<s.real[a]/s.nodes<<','<<s.imag[a]/s.nodes;
    history<<','<<s.finite<<'\n';
    completed=t;
    safe=s.finite&&s.min>=.2&&s.max<=.8&&std::abs(drift)<=1e-6;
    if(!safe) break;
  }
  history.close();
  measure(c,n,completed,u,out/"final.csv");
  std::ofstream result(out/"result.json");
  result<<"{\"completed_steps\":"<<completed<<",\"requested_steps\":"<<steps
        <<",\"safe\":"<<(safe?"true":"false")
        <<",\"NUMERICAL_GATE\":\"NOT_EVALUATED\",\"RESULT_PASS\":\"NOT_EVALUATED\",\"geometry_PASS\":\"NOT_EVALUATED\"}\n";
  return safe?0:4;
}
int main(int argc,char** argv) {
  try {
    if(argc==2&&std::string(argv[1])=="--describe") {
      std::cout<<"D3Q19 prescribed-advection only; N=16,32; tau=1; old/new; x+ x- y+ y- z+ z- xyz+ xyz- zero; --initialize-only has no collideAndStream\n";
      return 0;
    }
    if(argc!=5&&argc!=6) throw std::runtime_error("usage: translation_check old|new 16|32 direction output [--initialize-only]");
    const std::string variant=argv[1],ns=argv[2],direction=argv[3];
    const std::filesystem::path out=std::filesystem::absolute(argv[4]);
    if(variant!="old"&&variant!="new") throw std::runtime_error("invalid variant");
    if(ns!="16"&&ns!="32") throw std::runtime_error("invalid grid");
    const bool initOnly=argc==6;
    if(initOnly&&std::string(argv[5])!="--initialize-only") throw std::runtime_error("invalid option");
    std::array<T,3> u{};
    if(direction!="zero") {
      if(direction!="x+"&&direction!="x-"&&direction!="y+"&&direction!="y-"&&direction!="z+"&&direction!="z-"&&direction!="xyz+"&&direction!="xyz-") throw std::runtime_error("invalid direction");
      const T sign=direction.back()=='+'?1.:-1.;
      for(int a=0;a<3;++a) if(direction.find("xyz"[a])!=std::string::npos) u[a]=sign*speed;
    }
    initialize(&argc,&argv);
    if(singleton::mpi().getSize()!=1) throw std::runtime_error("one MPI rank only");
    using New=sim240::CorrectedDynamics<T,D>;using Old=WellBalancedCahnHilliardBGKdynamics<T,D>;
    static_assert(!dynamics::is_cse_optimized_v<New>);
    static_assert(dynamics::is_cse_optimized_v<Old>);
    return variant=="new"?run<New>(std::stoi(ns),u,variant,direction,out,initOnly)
                         :run<Old>(std::stoi(ns),u,variant,direction,out,initOnly);
  } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 3;}
}
