#include "dimension_corrected_ch.h"
#include "case_configs.h"
#include <array>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace olb;
using namespace olb::descriptors;
using T=double;
using D=D3Q19<FORCE,SOURCE,SOURCE_OLD,PHIWETTING,VELOCITY,OLD_PHIU,STATISTIC,CHEM_POTENTIAL,BOUNDARY>;
using TestCase=Case<names::Component1,Lattice<T,D>>;
using Dyn=sim240::CorrectedDynamics<T,D>;
constexpr T pi=3.14159265358979323846, sigmaTarget=1.4467592592592595e-5;
struct Grid {
 int n;std::vector<T> phi,mu,source,lapMu,cosine,sine;std::vector<std::array<T,3>> velocity;
 explicit Grid(int size):n(size),phi(n*n*n),mu(phi.size()),source(phi.size()),lapMu(phi.size()),cosine(phi.size()),sine(phi.size()),velocity(phi.size()){}
 int index(int x,int y,int z)const {auto mod=[&](int a){return(a%n+n)%n;};return (mod(x)*n+mod(y))*n+mod(z);}
 int neighbor(int x,int y,int z,int i,int sign=1)const{return index(x+sign*c<D>(i,0),y+sign*c<D>(i,1),z+sign*c<D>(i,2));}
 T lap(const std::vector<T>& f,int x,int y,int z)const{T v=0;int p=index(x,y,z);for(int i=0;i<19;++i)v+=6*t<T,D>(i)*(f[neighbor(x,y,z,i)]-f[p]);return v;}
 std::array<T,3> gradient(const std::vector<T>& f,int x,int y,int z)const{std::array<T,3> v{};for(int i=0;i<19;++i)for(int a=0;a<3;++a)v[a]+=3*t<T,D>(i)*c<D>(i,a)*f[neighbor(x,y,z,i)];return v;}
};
template<class F>void each(TestCase& tc,Grid& grid,F fun){
 auto& h=tc.getLattice(names::Component1{});long count=0;
 for(int b=0;b<h.getLoadBalancer().size();++b){auto& block=h.getBlock(b);auto& geo=tc.getGeometry().getBlockGeometry(b);
  block.forCoreSpatialLocations([&](LatticeR<3> r){if(geo.getMaterial(r)!=1)throw std::runtime_error("nonfluid node");auto pos=geo.getPhysR(r);
   int x=std::llround(pos[0]),y=std::llround(pos[1]),z=std::llround(pos[2]);
   if(x<0||x>=grid.n||y<0||y>=grid.n||z<0||z>=grid.n)throw std::runtime_error("periodic coordinate mismatch");
   auto cell=block.get(r);fun(cell,x,y,z,grid.index(x,y,z));++count;});}
 if(count!=static_cast<long>(grid.phi.size()))throw std::runtime_error("core node count mismatch");
}
void refresh(TestCase& tc,Grid& grid,const Config& cfg,const std::string& fixture){
 auto& h=tc.getLattice(names::Component1{});
 each(tc,grid,[&](auto& cell,int,int,int,int p){grid.phi[p]=cell.computeRho();cell.template setField<STATISTIC>(grid.phi[p]);cell.template setField<PHIWETTING>(grid.phi[p]);});
 h.getCommunicator(stage::PreCoupling()).communicate();
 if(cfg.nonlinear){h.executePostProcessors(stage::ChemPotCalc());}
 else each(tc,grid,[&](auto& cell,int x,int y,int z,int p){T mu=cfg.a*(grid.phi[p]-cfg.center)-cfg.kappa*grid.lap(grid.phi,x,y,z);
  if(fixture=="constant_mu")mu=.003;
  if(fixture=="specified_mu")mu=.002*std::sin(2*pi*x/grid.n+.3)+.001*std::cos(2*pi*(y+z)/grid.n);
  cell.template setField<CHEM_POTENTIAL>(mu);});
 h.getCommunicator(stage::PreCoupling()).communicate();
 each(tc,grid,[&](auto& cell,int,int,int,int p){grid.mu[p]=cell.template getField<CHEM_POTENTIAL>();});
 for(int x=0;x<grid.n;++x)for(int y=0;y<grid.n;++y)for(int z=0;z<grid.n;++z)grid.lapMu[grid.index(x,y,z)]=grid.lap(grid.mu,x,y,z);
}
void populations(TestCase& tc,Grid& grid){
 each(tc,grid,[&](auto& cell,int,int,int,int p){T phi=grid.phi[p],mu=grid.mu[p];
  for(int i=0;i<19;++i){T w=t<T,D>(i);cell[i]=(i==0?phi-(1-w)*mu:w*mu)-w;}});
}
void dump(TestCase& tc,Grid& grid,const std::filesystem::path& file,bool pops){
 std::ofstream f(file);if(!f)throw std::runtime_error("cannot write snapshot");f<<std::setprecision(17)<<"x,y,z,phi,mu,source,source_old,ux,uy,uz";
 if(pops){for(int i=0;i<19;++i)f<<",f"<<i;}f<<'\n';
 each(tc,grid,[&](auto& cell,int x,int y,int z,int){auto u=cell.template getField<VELOCITY>();
  f<<x<<','<<y<<','<<z<<','<<cell.computeRho()<<','<<cell.template getField<CHEM_POTENTIAL>()<<','<<cell.template getField<SOURCE>()<<','<<cell.template getField<SOURCE_OLD>()<<','<<u[0]<<','<<u[1]<<','<<u[2];
  if(pops){for(int i=0;i<19;++i)f<<','<<cell[i];}f<<'\n';});
}
struct Stats {long double sum=0,re=0,im=0,norm=0,h2re=0,h3re=0,energy=0,diss=0;T lo=1e9,hi=-1e9;bool finite=true;};
Stats measure(TestCase&tc,Grid&grid,const Config&cfg){
 Stats s;T beta=3*sigmaTarget;T mobility=(cfg.tau-.5)/3;
 each(tc,grid,[&](auto&cell,int x,int y,int z,int p){T phi=cell.computeRho(),d=phi-cfg.center;
  s.sum+=phi;s.re+=d*grid.cosine[p];s.im-=d*grid.sine[p];s.norm+=d*d;
  T co=grid.cosine[p];s.h2re+=d*(2*co*co-1);s.h3re+=d*(4*co*co*co-3*co);
  s.lo=std::min(s.lo,phi);s.hi=std::max(s.hi,phi);
  T bulk=cfg.nonlinear?beta*phi*phi*(phi-1)*(phi-1):.5*cfg.a*d*d;
  s.energy+=bulk-.5*cfg.kappa*phi*grid.lap(grid.phi,x,y,z);
  s.diss-=mobility*grid.mu[p]*grid.lapMu[p];
  for(int i=0;i<19;++i){s.finite&=std::isfinite(cell[i]);}s.finite&=std::isfinite(phi)&&std::isfinite(grid.mu[p]);});
 return s;
}
void initialModes(TestCase&tc,Grid&grid,const Config&cfg,const std::filesystem::path& out){
 std::array<long double,19> re{},im{};
 each(tc,grid,[&](auto& cell,int,int,int,int p){for(int i=0;i<19;++i){re[i]+=cell[i]*grid.cosine[p];im[i]-=cell[i]*grid.sine[p];}});
 std::ofstream f(out);f<<std::setprecision(20)<<"population,re,im\n";for(int i=0;i<19;++i)f<<i<<','<<re[i]/grid.phi.size()<<','<<im[i]/grid.phi.size()<<'\n';
}
int run(Config cfg,const std::string& fixture,const std::filesystem::path&out,bool initOnly){
 if(std::filesystem::exists(out))throw std::runtime_error("refusing overwrite of existing run directory");
 std::filesystem::create_directories(out);singleton::directories().setOutputDir(out.string()+"/");
 auto started=std::chrono::steady_clock::now();int n=cfg.n;Grid grid(n);
 IndicatorCuboid3D<T> domain({T(n-1),T(n-1),T(n-1)},{0,0,0});Mesh<T,3> mesh(domain,1.,1);mesh.setOverlap(3);mesh.getCuboidDecomposition().setPeriodicity({true,true,true});
 TestCase::ParametersD par;TestCase tc(par,mesh);auto& geo=tc.getGeometry();geo.rename(0,1);geo.innerClean();geo.checkForErrors(false);
 auto& h=tc.getLattice(names::Component1{});auto bulk=geo.getMaterialIndicator(1);
 h.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,D>>(n,1.,T(n),0.,1./6.,1.);
 dynamics::set<olb::CSE<Dyn>>(h,bulk);h.setParameter<OMEGA>(1/cfg.tau);
 h.addPostProcessor<stage::ChemPotCalc>(meta::id<ChemPotentialPhaseFieldProcessor>());
 h.setParameter<SCALAR>(sigmaTarget);h.setParameter<INTERFACE_WIDTH>(4.);h.setParameter<ADDEND>(0.);
 auto& comm=h.getCommunicator(stage::PreCoupling());comm.requestOverlap(2);comm.requestField<STATISTIC>();comm.requestField<PHIWETTING>();comm.requestField<CHEM_POTENTIAL>();comm.exchangeRequests();
 AnalyticalConst3D<T,T> center(cfg.center),zero(0),vel(0,0,0);
 fields::set<SOURCE>(h,bulk,zero);fields::set<SOURCE_OLD>(h,bulk,zero);fields::set<VELOCITY>(h,bulk,vel);fields::set<CHEM_POTENTIAL>(h,bulk,zero);fields::set<BOUNDARY>(h,bulk,zero);
 h.iniEquilibrium(bulk,center,vel);h.initialize();
 std::vector<T> psi(grid.phi.size());
 for(int x=0;x<n;++x)for(int y=0;y<n;++y)for(int z=0;z<n;++z){int p=grid.index(x,y,z);T theta=2*pi*(cfg.mx*x+cfg.my*y+cfg.mz*z)/n;
  grid.cosine[p]=std::cos(theta);grid.sine[p]=std::sin(theta);grid.phi[p]=cfg.center+cfg.amplitude*grid.cosine[p];
  if(!fixture.empty())grid.phi[p]=.35+.08*std::cos(2*pi*x/n+.31)+.04*std::sin(2*pi*y/n+.2)+.02*std::cos(2*pi*(x+y)/n+.7);
  psi[p]=.01*(std::sin(2*pi*x/n+.2)*std::sin(2*pi*y/n+.6)+.17*std::cos(2*pi*(y+z)/n+.5));}
 populations(tc,grid);refresh(tc,grid,cfg,fixture);populations(tc,grid);refresh(tc,grid,cfg,fixture);
 each(tc,grid,[&](auto& cell,int x,int y,int z,int p){auto g=grid.gradient(grid.phi,x,y,z),gp=grid.gradient(psi,x,y,z);std::array<T,3> u{};
  if(fixture=="solenoidal"){u={gp[1],-gp[0],0};}if(fixture=="compressible"){for(int a=0;a<3;++a)u[a]=.01*g[a];}
  T s=0;for(int a=0;a<3;++a)s+=u[a]*g[a];grid.velocity[p]=u;grid.source[p]=s;
  cell.template setField<VELOCITY>(Vector<T,3>{u[0],u[1],u[2]});cell.template setField<SOURCE>(s);cell.template setField<SOURCE_OLD>(s);});
 int steps=initOnly?0:cfg.steps;
 std::ofstream config(out/"config.json");config<<std::setprecision(17)<<"{\"case_id\":\""<<cfg.id<<"\",\"fixture\":\""<<fixture<<"\",\"N\":"<<n<<",\"steps\":"<<steps<<",\"nominal_steps\":"<<cfg.steps<<",\"tau\":"<<cfg.tau<<",\"center\":"<<cfg.center<<",\"amplitude\":"<<cfg.amplitude<<",\"a\":"<<cfg.a<<",\"kappa\":"<<cfg.kappa<<",\"nonlinear\":"<<(cfg.nonlinear?"true":"false")<<",\"mode\":["<<cfg.mx<<','<<cfg.my<<','<<cfg.mz<<"],\"MPI_ranks\":1,\"new_CSE_optimized\":false}\n";config.close();
 dump(tc,grid,out/"initial.csv",!fixture.empty());initialModes(tc,grid,cfg,out/"initial_population_modes.csv");
 if(!fixture.empty()){
  auto before=grid.phi,mu=grid.mu,source=grid.source;long double sumBefore=0,sumAfter=0,sumSource=0;T err=0;
  if(!initOnly){h.collide();dump(tc,grid,out/"post_collision.csv",true);h.AndStream();dump(tc,grid,out/"post_stream.csv",true);
   each(tc,grid,[&](auto&cell,int x,int y,int z,int p){for(int i=0;i<19;++i)if(!std::isfinite(cell[i]))throw std::runtime_error("nonfinite A2 population");T predicted=before[p]+grid.lap(mu,x,y,z)/6;
    for(int i=0;i<19;++i){T cc=0;for(int a=0;a<3;++a)cc+=c<D>(i,a)*c<D>(i,a);predicted+=t<T,D>(i)*(-2.5+1.5*cc)*source[grid.neighbor(x,y,z,i,-1)];}
    err=std::max(err,std::abs(cell.computeRho()-predicted));sumBefore+=before[p];sumAfter+=cell.computeRho();sumSource+=source[p];});
   refresh(tc,grid,cfg,fixture);dump(tc,grid,out/"post_refresh.csv",true);
  }
  std::ofstream f(out/"result.json");f<<std::setprecision(20)<<"{\"requested_steps\":"<<steps<<",\"completed_steps\":"<<steps<<",\"point_update_max_error\":"<<err<<",\"budget_residual_per_node\":"<<(sumAfter-sumBefore+sumSource)/grid.phi.size()<<",\"source_sum\":"<<sumSource<<",\"phase_change\":"<<sumAfter-sumBefore<<",\"acceptance_evaluated\":"<<(initOnly?"false":"true")<<",\"NUMERICAL_GATE\":\"NOT_EVALUATED\",\"RESULT_PASS\":\"NOT_EVALUATED\",\"geometry_PASS\":\"NOT_EVALUATED\"}\n";
  return !initOnly&&(err>1e-12||std::abs((sumAfter-sumBefore+sumSource)/grid.phi.size())>1e-12)?4:0;
 }
 std::vector<std::array<T,2>> reference;
 if(!cfg.nonlinear){std::ifstream f(std::filesystem::path("reference")/(std::string(cfg.id)+".csv"));std::string line;std::getline(f,line);
  while(std::getline(f,line)){std::replace(line.begin(),line.end(),',',' ');std::istringstream s(line);int step;T re,im;if(!(s>>step>>re>>im)||step!=static_cast<int>(reference.size()))throw std::runtime_error("invalid reference row");reference.push_back({re,im});}
  if(reference.size()!=static_cast<size_t>(cfg.steps+1))throw std::runtime_error("missing bound reference curve");}
 auto first=measure(tc,grid,cfg);long double initialSum=first.sum;bool safe=true;int completed=0;
 std::ofstream hist(out/"history.csv");hist<<std::setprecision(20)<<"step,nodes,phase_sum,relative_drift,phi_min,phi_max,mode_re,mode_im,fluctuation_mean_square,harmonic2_re,harmonic3_re,free_energy,link_dissipation,one_step_applicable,one_step_max_error,mu_constitutive_max_error,energy_time_remainder,energy_balance_residual,reference_L2_over_initial_RMS,finite\n";
 T point=0,muErr=0;long double rem=0,balance=0;
 for(int step=0;step<=steps;++step){
  if(step){auto before=grid.phi,oldMu=grid.mu,oldLapMu=grid.lapMu;auto old=measure(tc,grid,cfg);
   h.collideAndStream();point=0;long double work=0;
   each(tc,grid,[&](auto&cell,int,int,int,int p){T delta=cell.computeRho()-before[p];work+=oldMu[p]*delta;if(cfg.tau==1.)point=std::max(point,std::abs(delta-oldLapMu[p]/6));});
   refresh(tc,grid,cfg,fixture);auto now=measure(tc,grid,cfg);rem=now.energy-old.energy-work;balance=now.energy-old.energy+old.diss-rem;
  }
  auto s=measure(tc,grid,cfg);muErr=0;
  if(cfg.nonlinear)each(tc,grid,[&](auto&,int x,int y,int z,int p){T phi=grid.phi[p];T expected=12*sigmaTarget*phi*(phi-1)*(phi-.5)-cfg.kappa*grid.lap(grid.phi,x,y,z);muErr=std::max(muErr,std::abs(expected-grid.mu[p]));});
  long double l2=0;if(!cfg.nonlinear){each(tc,grid,[&](auto&cell,int,int,int,int p){T exact=cfg.center+2*(reference[step][0]*grid.cosine[p]-reference[step][1]*grid.sine[p]);T diff=cell.computeRho()-exact;l2+=diff*diff;});l2=std::sqrt(l2/grid.phi.size())/(cfg.amplitude/std::sqrt(2.));}
  hist<<step<<','<<grid.phi.size()<<','<<s.sum<<','<<(s.sum-initialSum)/initialSum<<','<<s.lo<<','<<s.hi<<','<<s.re/grid.phi.size()<<','<<s.im/grid.phi.size()<<','<<s.norm/grid.phi.size()<<','<<s.h2re/grid.phi.size()<<','<<s.h3re/grid.phi.size()<<','<<s.energy<<','<<s.diss<<','<<(cfg.tau==1.)<<','<<point<<','<<muErr<<','<<rem<<','<<balance<<','<<l2<<','<<s.finite<<'\n';
  if(cfg.nonlinear)dump(tc,grid,out/("field_step_"+std::to_string(step)+".csv"),false);
  completed=step;safe=s.finite&&s.lo>=.05&&s.hi<=.95&&std::abs((s.sum-initialSum)/initialSum)<=1e-6;
  if(!safe)break;
 }
 hist.close();dump(tc,grid,out/"final.csv",false);
 double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
 std::ofstream result(out/"result.json");result<<std::setprecision(17)<<"{\"requested_steps\":"<<steps<<",\"completed_steps\":"<<completed<<",\"safe\":"<<(safe?"true":"false")<<",\"wall_seconds\":"<<elapsed<<",\"NUMERICAL_GATE\":\"NOT_EVALUATED\",\"RESULT_PASS\":\"NOT_EVALUATED\",\"geometry_PASS\":\"NOT_EVALUATED\"}\n";
 return safe&&completed==steps?0:4;
}
int main(int argc,char**argv){
 try{
  if(argc==2&&std::string(argv[1])=="--describe"){std::cout<<"A2 four N8 single steps; B18 periodic CH diffusion cases; --initialize-only has zero streaming; no NS feedback or physical Gate\n";return 0;}
  if(argc!=4&&argc!=5)throw std::runtime_error("usage: ab_check a2|b case_id new_output [--initialize-only]");
  std::string stage=argv[1],id=argv[2];bool initOnly=argc==5;
  if(initOnly&&std::string(argv[4])!="--initialize-only")throw std::runtime_error("unknown option");
  Config cfg{};bool found=false;std::string fixture;
  if(stage=="b")for(auto c:configs)if(id==c.id){cfg=c;found=true;}
  if(stage=="a2"&&(id=="constant_mu"||id=="specified_mu"||id=="solenoidal"||id=="compressible")){fixture=id;cfg={"A2",id=="solenoidal"||id=="compressible",8,1,0,0,1,1.,.35,.08,.1,6*sigmaTarget};found=true;}
  if(!found)throw std::runtime_error("invalid stage or frozen case ID");
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)throw std::runtime_error("only one MPI rank permitted");
  static_assert(!dynamics::is_cse_optimized_v<Dyn>);
  return run(cfg,fixture,std::filesystem::absolute(argv[3]),initOnly);
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 3;}
}
