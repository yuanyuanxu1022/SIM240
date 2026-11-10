#include "alpha_ch.h"
#include "grid.h"
#include <algorithm>
#include <bit>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <string>
#include <zlib.h>

using namespace olb;using namespace olb::descriptors;
using T=double;
using NSD=D3Q19<RHO,NABLARHO,FORCE,EXTERNAL_FORCE,TAU_EFF>;
using CHD=D3Q19<FORCE,SOURCE,SOURCE_OLD,PHIWETTING,VELOCITY,OLD_PHIU,STATISTIC,CHEM_POTENTIAL,BOUNDARY,sim240::CH_ALPHA>;
using Both=Case<names::NavierStokes,Lattice<T,NSD>,names::Component1,Lattice<T,CHD>>;
using NSDyn=MultiPhaseIncompressibleBGKdynamics<T,NSD>;
using CHDyn=sim240::AlphaCHDynamics<T,CHD>;
using Mixture=LinearTauViscosity;
constexpr T pi=3.14159265358979323846,sigma=2.0833333333333333e-5,width=4.,beta=6.25e-5,kappa=1.25e-4,mobility=1./6.;
constexpr int N=64;
constexpr T dtSI=1.0416666666666667e-13;
const std::string fieldNames="\"phi\",\"mu\",\"source\",\"source_old\",\"ux\",\"uy\",\"uz\",\"jx\",\"jy\",\"jz\",\"Fx\",\"Fy\",\"Fz\",\"p_h\",\"rho\",\"tau\"";
using Ledger=std::map<std::string,long double>;
struct Config {std::string id;bool equal=false,constantMu=false;T rhoGas()const{return equal?1.:.0012;}};
struct Frame {
 std::vector<T> phi,mu,source,sold,rho,tau,p;
 std::array<std::vector<T>,3> u,j,force;
 explicit Frame(std::size_t n):phi(n),mu(n),source(n),sold(n),rho(n),tau(n),p(n){
  for(auto* v:{&u,&j,&force})for(auto& a:*v)a.resize(n);
 }
 Vec velocity(int i)const{return {u[0][i],u[1][i],u[2][i]};}
 Vec rawJ(int i)const{return {j[0][i],j[1][i],j[2][i]};}
 Vec F(int i)const{return {force[0][i],force[1][i],force[2][i]};}
 Vec cut(int i)const{Vec v{};for(int a=0;a<3;++a){T raw=j[a][i]/rho[i];v[a]=rho[i]*((std::abs(raw)<1e-15?0.:raw)-raw);}return v;}
};
template<class Fun>void each(Both& tc,const Grid& g,Fun fun){
 auto& ns=tc.getLattice(names::NavierStokes{});auto& ch=tc.getLattice(names::Component1{});std::size_t count=0;
 for(int b=0;b<ns.getLoadBalancer().size();++b){auto& nb=ns.getBlock(b);auto& hb=ch.getBlock(b);auto& geo=tc.getGeometry().getBlockGeometry(b);
  nb.forCoreSpatialLocations([&](LatticeR<3> r){if(geo.getMaterial(r)!=1)throw std::runtime_error("nonfluid core");
   auto pos=geo.getPhysR(r);int x=std::llround(pos[0]),y=std::llround(pos[1]),z=std::llround(pos[2]);
   if(x<0||x>=g.n||y<0||y>=g.n||z<0||z>=g.n)throw std::runtime_error("periodic coordinate outside 0..N-1");
   auto nc=nb.get(r);auto hc=hb.get(r);fun(nc,hc,x,y,z,g.index(x,y,z));++count;});
 }
 if(count!=g.size)throw std::runtime_error("core count mismatch");
}
void refreshChemical(Both& tc,const Grid& grid,const Config& cfg){
 auto& ch=tc.getLattice(names::Component1{});
 each(tc,grid,[&](auto&,auto& h,int,int,int,int){T phi=h.computeRho();T rho=1+(cfg.rhoGas()-1)*phi;
  if(!std::isfinite(phi)||!std::isfinite(rho)||rho<=0)throw std::runtime_error("nonpositive density BEFORE coupling division; no clipping");
  h.template setField<STATISTIC>(phi);h.template setField<PHIWETTING>(phi);
  if(cfg.constantMu)h.template setField<CHEM_POTENTIAL>(0.);
 });
 ch.getCommunicator(stage::PreCoupling()).communicate();
 if(!cfg.constantMu)ch.executePostProcessors(stage::ChemPotCalc());
 ch.getCommunicator(stage::PreCoupling()).communicate();
}
void collect(Both& tc,const Grid& grid,Frame& f){
 each(tc,grid,[&](auto& n,auto& h,int,int,int,int i){
  f.phi[i]=h.computeRho();f.mu[i]=h.template getField<CHEM_POTENTIAL>();f.source[i]=h.template getField<SOURCE>();f.sold[i]=h.template getField<SOURCE_OLD>();
  f.rho[i]=n.template getField<RHO>();f.tau[i]=n.template getField<TAU_EFF>();f.p[i]=n.computeRho();
  if(f.rho[i]<=0)throw std::runtime_error("nonpositive current rho");
  T u[3]{};n.computeU(u);auto acceleration=n.template getField<FORCE>();
  for(int a=0;a<3;++a){f.u[a][i]=u[a];f.force[a][i]=f.rho[i]*acceleration[a];f.j[a][i]=0;for(int q=0;q<19;++q)f.j[a][i]+=c<NSD>(q,a)*n[q];}
 });
}
T initialize(Both& tc,const Grid& grid,const Config& cfg){
 auto& ns=tc.getLattice(names::NavierStokes{});auto& ch=tc.getLattice(names::Component1{});auto bulk=tc.getGeometry().getMaterialIndicator(1);
 ns.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,NSD>>(N,1.,T(N),0.,1./6.,1.);ch.setUnitConverter(ns.getUnitConverter());
 dynamics::set<olb::CSE<NSDyn>>(ns,bulk);dynamics::set<olb::CSE<CHDyn>>(ch,bulk);
 ns.setParameter<OMEGA>(1.);ch.setParameter<OMEGA>(1.);
 ch.addPostProcessor<stage::ChemPotCalc>(meta::id<ChemPotentialPhaseFieldProcessor>());
 ch.setParameter<SCALAR>(sigma);ch.setParameter<INTERFACE_WIDTH>(width);ch.setParameter<ADDEND>(0.);
 auto& comm=ch.getCommunicator(stage::PreCoupling());comm.requestOverlap(2);comm.requestField<STATISTIC>();comm.requestField<PHIWETTING>();comm.requestField<CHEM_POTENTIAL>();comm.exchangeRequests();
 auto& cp=tc.setCouplingOperator("Coupling",WellBalancedCahnHilliardPostProcessor<Mixture>{},names::NavierStokes{},ns,names::Component1{},ch);
 cp.restrictTo(bulk);cp.setParameter<Mixture::RHOS>({1.,cfg.rhoGas()});cp.setParameter<Mixture::TAUS>({1.,1.25});
 AnalyticalConst3D<T,T> zero(0.),one(1.),half(.5),vel(0.,0.,0.);
 fields::set<RHO>(ns,bulk,one);fields::set<TAU_EFF>(ns,bulk,one);fields::set<FORCE>(ns,bulk,vel);fields::set<NABLARHO>(ns,bulk,vel);
 fields::set<EXTERNAL_FORCE>(ns,bulk,vel);fields::set<BODY_FORCE>(ns,bulk,vel);
 fields::set<sim240::CH_ALPHA>(ch,bulk,one);fields::set<CHEM_POTENTIAL>(ch,bulk,zero);fields::set<SOURCE>(ch,bulk,zero);fields::set<SOURCE_OLD>(ch,bulk,zero);
 fields::set<BOUNDARY>(ch,bulk,zero);fields::set<VELOCITY>(ch,bulk,vel);fields::set<OLD_PHIU>(ch,bulk,vel);
 ch.iniEquilibrium(bulk,half,vel);ns.iniEquilibrium(bulk,zero,vel);ch.initialize();ns.initialize();
 auto profile=[&](int x,int y,int z,T a0){T yphase=2*pi*y/N,zphase=2*pi*z/N;
  T corr=(std::sin(yphase+.37)*std::cos(zphase+.19)+.25*std::cos(2*yphase+.23))/2.5;
  return .5*(1+std::tanh(2*(std::abs(T(x)-N/2.)-(a0+corr))/width));};
 T lo=14.,hi=18.;
 for(int k=0;k<60;++k){T a=(lo+hi)/2;long double amount=0;grid.each([&](int x,int y,int z,int){amount+=profile(x,y,z,a);});
  if(amount/grid.size>.5)lo=a;else hi=a;}
 T a0=(lo+hi)/2;
 each(tc,grid,[&](auto& n,auto& h,int x,int y,int z,int){T phi=profile(x,y,z,a0);n.template setField<RHO>(1+(cfg.rhoGas()-1)*phi);n.template setField<TAU_EFF>(1+.25*phi);
  for(int i=0;i<19;++i){n[i]=0;h[i]=(i==0?phi:0.)-t<T,CHD>(i);}
 });
 refreshChemical(tc,grid,cfg);
 each(tc,grid,[&](auto&,auto& h,int,int,int,int){T phi=h.computeRho(),mu=h.template getField<CHEM_POTENTIAL>();
  for(int i=0;i<19;++i){T w=t<T,CHD>(i);h[i]=(i==0?phi-(1-w)*mu:w*mu)-w;}
 });
 refreshChemical(tc,grid,cfg);tc.getOperator("Coupling").apply();
 // A single explicitly recorded startup rule: S_old=S0 and SOURCE=S0.
 each(tc,grid,[&](auto&,auto& h,int,int,int,int){h.template setField<SOURCE>(h.template getField<SOURCE_OLD>());});
 return a0*2.5;
}
Ledger statistics(Both& tc,const Grid& grid,const Config& cfg,const Frame& f){
 Ledger s;T phiMin=1e9,phiMax=-1e9,rhoMin=1e9,rhoMax=-1e9,pMin=1e9,pMax=-1e9;bool finite=true;
 grid.each([&](int x,int y,int z,int i){T phi=f.phi[i],rho=f.rho[i];Vec grad=grid.grad(f.phi,x,y,z),gm=grid.grad(f.mu,x,y,z),u=f.velocity(i),force=f.F(i),cut=f.cut(i);
  T lp=grid.lap(f.phi,x,y,z),lm=grid.lap(f.mu,x,y,z);T muExpected=cfg.constantMu?0.:4*beta*phi*(phi-1)*(phi-.5)-kappa*lp;
  T div=0,strain2=0;T du[3][3]{};
  for(int a=0;a<3;++a){auto gu=grid.grad(f.u[a],x,y,z);for(int b=0;b<3;++b)du[a][b]=gu[b];div+=du[a][a];}
  for(int a=0;a<3;++a)for(int b=0;b<3;++b)strain2+=std::pow(.5*(du[a][b]+du[b][a]),2);
  s["phase_sum"]+=phi;s["liquid_sum"]+=1-phi;s["mass_sum"]+=rho;s["source_sum"]+=f.source[i];s["S_sum"]+=f.sold[i];s["phi_div_u_sum"]+=phi*div;
  s["free_energy"]+=beta*phi*phi*(phi-1)*(phi-1)-.5*kappa*phi*lp;
  s["link_dissipation"]-=mobility*f.mu[i]*lm;s["kinetic_energy"]+=.5*rho*dot(u,u);
  s["viscous_gradient_dissipation"]+=2*rho*(f.tau[i]-.5)/3*strain2;
  s["capillary_power"]+=dot(u,force);s["instant_advection_work"]-=f.mu[i]*f.sold[i];s["AB_advection_work"]-=f.mu[i]*f.source[i];
  s["conditional_mass_diffusion_kinetic_term"]-=.5*dot(u,u)*(cfg.rhoGas()-1)*mobility*lm;
  s["mass_diffusion_flux_max"]=std::max(s["mass_diffusion_flux_max"],(long double)(std::abs(cfg.rhoGas()-1)*mobility*norm(gm)));
  s["Mach_max"]=std::max(s["Mach_max"],(long double)(norm(u)*std::sqrt(3.)));
  s["grad_mu_max"]=std::max(s["grad_mu_max"],(long double)norm(gm));s["div_u_max"]=std::max(s["div_u_max"],(long double)std::abs(div));s["div_u_square_sum"]+=(long double)div*div;
  s["mu_constitutive_max_error"]=std::max(s["mu_constitutive_max_error"],(long double)std::abs(f.mu[i]-muExpected));
  s["S_local_max_error"]=std::max(s["S_local_max_error"],(long double)std::abs(f.sold[i]-dot(u,grad)));
  s["rho_mapping_max_error"]=std::max(s["rho_mapping_max_error"],(long double)std::abs(rho-(1+(cfg.rhoGas()-1)*phi)));
  s["tau_mapping_max_error"]=std::max(s["tau_mapping_max_error"],(long double)std::abs(f.tau[i]-(1+.25*phi)));
  phiMin=std::min(phiMin,phi);phiMax=std::max(phiMax,phi);rhoMin=std::min(rhoMin,rho);rhoMax=std::max(rhoMax,rho);pMin=std::min(pMin,f.p[i]);pMax=std::max(pMax,f.p[i]);
  for(int a=0;a<3;++a){std::string suffix=std::to_string(a);s["raw_J"+suffix]+=f.j[a][i];s["physical_P"+suffix]+=rho*u[a];s["force_sum"+suffix]+=force[a];s["raw_cut_sum"+suffix]+=cut[a];s["omega_cut_sum"+suffix]+=cut[a]/f.tau[i];
   s["force_local_max_error"]=std::max(s["force_local_max_error"],(long double)std::abs(force[a]+phi*gm[a]));
   finite&=std::isfinite(u[a])&&std::isfinite(force[a])&&std::isfinite(f.j[a][i]);}
  finite&=std::isfinite(phi)&&std::isfinite(rho)&&std::isfinite(f.mu[i])&&std::isfinite(f.p[i])&&std::isfinite(f.source[i])&&std::isfinite(f.sold[i])&&std::isfinite(f.tau[i]);
 });
 each(tc,grid,[&](auto& n,auto& h,int,int,int,int){for(int i=0;i<19;++i)finite&=std::isfinite(n[i])&&std::isfinite(h[i]);
  s["alpha_max_error"]=std::max(s["alpha_max_error"],(long double)std::abs(h.template getField<sim240::CH_ALPHA>()-1));});
 s["phi_min"]=phiMin;s["phi_max"]=phiMax;s["rho_min"]=rhoMin;s["rho_max"]=rhoMax;s["p_h_min"]=pMin;s["p_h_max"]=pMax;
 s["finite"]=finite;s["nodes"]=grid.size;s["gradient_integration_by_parts_residual_per_node"]=(s["S_sum"]+s["phi_div_u_sum"])/grid.size;
 s["semidiscrete_capillary_advection_exchange"]=s["capillary_power"]+s["instant_advection_work"];
 return s;
}
void dump(const Frame& f,const Grid& grid,const std::filesystem::path& path){
 static_assert(std::endian::native==std::endian::little);std::vector<T> data(grid.size*16);
 for(std::size_t i=0;i<grid.size;++i){T* p=data.data()+16*i;p[0]=f.phi[i];p[1]=f.mu[i];p[2]=f.source[i];p[3]=f.sold[i];
  for(int a=0;a<3;++a){p[4+a]=f.u[a][i];p[7+a]=f.j[a][i];p[10+a]=f.force[a][i];}p[13]=f.p[i];p[14]=f.rho[i];p[15]=f.tau[i];}
 gzFile file=gzopen(path.c_str(),"wb1");if(!file)throw std::runtime_error("cannot create gzip frame");
 const auto bytes=data.size()*sizeof(T);int written=gzwrite(file,data.data(),static_cast<unsigned>(bytes));int code=gzclose(file);
 if(written!=static_cast<int>(bytes)||code!=Z_OK)throw std::runtime_error("incomplete gzip frame");
}
Ledger step(Both& tc,const Grid& grid,const Config& cfg,const Frame& old,Frame& next,const Ledger& before){
 auto& ns=tc.getLattice(names::NavierStokes{});auto& ch=tc.getLattice(names::Component1{});
 std::vector<T> postNS(grid.size*19),postCH(grid.size*19);Ledger delta;
 each(tc,grid,[&](auto& n,auto& h,int,int,int,int p){T rho=old.rho[p],omega=1/old.tau[p];Vec raw=old.rawJ(p),force=old.F(p);T u[3]{};auto gr=n.template getField<NABLARHO>();T u2=0,ug=0,sumMoving=0;
  for(int a=0;a<3;++a){T v=raw[a]/rho;u[a]=(std::abs(v)<1e-15?0.:v)+force[a]/(2*rho);u2+=u[a]*u[a];ug+=u[a]*gr[a];}
  for(int q=1;q<19;++q)sumMoving+=n[q];T pressure=(sumMoving+.5*ug-.5*rho*u2)/2;
  delta["pressure_recovery_max_error"]=std::max(delta["pressure_recovery_max_error"],(long double)std::abs(pressure-old.p[p]));
  for(int i=0;i<19;++i){T w=t<T,NSD>(i),cu=0,cf=0,cg=0,cc=0;
   for(int a=0;a<3;++a){int ci=c<NSD>(i,a);cu+=ci*u[a];cf+=ci*force[a]/rho;cg+=ci*gr[a];cc+=ci*ci;}
   T eq=i==0?3*pressure*(w-1)-1.5*rho*w*u2:3*w*(pressure+rho*(cu+1.5*cu*cu-.5*u2));
   postNS[19*p+i]=(1-omega)*n[i]+omega*eq+(1-.5*omega)*3*w*(rho*cf+cu*cg);
   postCH[19*p+i]=(i==0?old.phi[p]-(1-w)*old.mu[p]:w*old.mu[p])-w+w*(-2.5+1.5*cc)*old.source[p];
  }
 });
 ns.collide();ch.collide();
 each(tc,grid,[&](auto& n,auto& h,int,int,int,int p){for(int i=0;i<19;++i){
  delta["NS_collision_population_max_error"]=std::max(delta["NS_collision_population_max_error"],(long double)std::abs(n[i]-postNS[19*p+i]));
  delta["CH_collision_population_max_error"]=std::max(delta["CH_collision_population_max_error"],(long double)std::abs(h[i]-postCH[19*p+i]));
  postNS[19*p+i]=n[i];postCH[19*p+i]=h[i];}
 });
 ns.AndStream();ch.AndStream();
 long double work=0,sourceWork=0;
 each(tc,grid,[&](auto& n,auto& h,int x,int y,int z,int p){T sourceContribution=0;
  for(int i=0;i<19;++i){int other=grid.neighbor(x,y,z,i,-1);T cc=0;for(int a=0;a<3;++a)cc+=c<CHD>(i,a)*c<CHD>(i,a);
   sourceContribution+=t<T,CHD>(i)*(-2.5+1.5*cc)*old.source[other];
   delta["NS_stream_population_max_error"]=std::max(delta["NS_stream_population_max_error"],(long double)std::abs(n[i]-postNS[19*other+i]));
   delta["CH_stream_population_max_error"]=std::max(delta["CH_stream_population_max_error"],(long double)std::abs(h[i]-postCH[19*other+i]));
  }
  T change=h.computeRho()-old.phi[p];T predicted=mobility*grid.lap(old.mu,x,y,z)+sourceContribution;
  delta["CH_point_update_max_error"]=std::max(delta["CH_point_update_max_error"],(long double)std::abs(change-predicted));
  work+=(long double)old.mu[p]*change;sourceWork+=(long double)old.mu[p]*sourceContribution;
 });
 refreshChemical(tc,grid,cfg);tc.getOperator("Coupling").apply();collect(tc,grid,next);auto after=statistics(tc,grid,cfg,next);
 delta["phase_budget_residual_per_node"]=(after["phase_sum"]-before.at("phase_sum")+before.at("source_sum"))/grid.size;
 delta["source_migration_work"]=sourceWork;delta["chemical_work_on_actual_delta_phi"]=work;
 delta["energy_time_remainder"]=after["free_energy"]-before.at("free_energy")-work;
 delta["energy_balance_residual_per_node"]=(after["free_energy"]-before.at("free_energy")+before.at("link_dissipation")-sourceWork-delta["energy_time_remainder"])/grid.size;
 delta["source_migration_correction_work"]=sourceWork-before.at("AB_advection_work");
 delta["kinetic_diagnostic_remainder"]=after["kinetic_energy"]-before.at("kinetic_energy")-before.at("capillary_power")+before.at("viscous_gradient_dissipation");
 for(int a=0;a<3;++a){std::string suffix=std::to_string(a);
  delta["raw_momentum_residual_per_node_"+suffix]=(after["raw_J"+suffix]-before.at("raw_J"+suffix)-before.at("force_sum"+suffix)-before.at("omega_cut_sum"+suffix))/grid.size;
  delta["physical_momentum_residual_per_node_"+suffix]=(after["physical_P"+suffix]-before.at("physical_P"+suffix)-.5*(after["force_sum"+suffix]+before.at("force_sum"+suffix))-before.at("omega_cut_sum"+suffix)-after["raw_cut_sum"+suffix]+before.at("raw_cut_sum"+suffix))/grid.size;
 }
 grid.each([&](int,int,int,int p){delta["AB_source_max_error"]=std::max(delta["AB_source_max_error"],(long double)std::abs(next.source[p]-(1.5*next.sold[p]-.5*old.sold[p])));});
 for(const auto& [key,value]:delta)after[key]=value;return after;
}
int run(const Config& cfg,const std::filesystem::path& out,bool initOnly){
 if(std::filesystem::exists(out))throw std::runtime_error("refusing existing output");std::filesystem::create_directories(out/"frames");singleton::directories().setOutputDir(out.string()+"/");
 auto started=std::chrono::steady_clock::now();Grid grid(N);IndicatorCuboid3D<T> domain({T(N-1),T(N-1),T(N-1)},{0,0,0});Mesh<T,3> mesh(domain,1.,1);mesh.setOverlap(3);mesh.getCuboidDecomposition().setPeriodicity({true,true,true});
 Both::ParametersD parameters;Both tc(parameters,mesh);tc.getGeometry().rename(0,1);tc.getGeometry().innerClean();tc.getGeometry().checkForErrors(false);
 T a0=initialize(tc,grid,cfg);Frame current(grid.size);collect(tc,grid,current);auto first=statistics(tc,grid,cfg,current);auto s=first;
 std::ofstream config(out/"config.json");config<<std::setprecision(17)<<"{\"case_id\":\""<<cfg.id<<"\",\"N\":64,\"steps\":"<<(initOnly?0:64)<<",\"nominal_steps\":64,\"alpha\":1,\"tau_CH\":1,\"dt_SI\":"<<dtSI<<",\"sigma\":"<<sigma<<",\"width\":4,\"beta\":"<<beta<<",\"kappa\":"<<kappa<<",\"rhos\":[1,"<<cfg.rhoGas()<<"],\"taus\":[1,1.25],\"a0_nm\":"<<a0<<",\"constant_mu_zero\":"<<(cfg.constantMu?"true":"false")<<",\"MPI_ranks\":1,\"CH_CSE_optimized\":false,\"NS_CSE_optimized\":"<<(dynamics::is_cse_optimized_v<NSDyn>?"true":"false")<<"}\n";config.close();
 std::ofstream schema(out/"frame_schema.json");schema<<"{\"dtype\":\"<f8\",\"shape\":[64,64,64,16],\"order\":\"C\",\"columns\":["<<fieldNames<<"],\"coordinates\":\"0..63 each axis; multiply by2.5nm\",\"time_layer\":\"after chemical refresh and exactly one coupling; source is for next collision\",\"named_snapshot_steps\":[0,1,16,32,64]}\n";schema.close();
 const std::vector<std::string> extra={"NS_collision_population_max_error","CH_collision_population_max_error","NS_stream_population_max_error","CH_stream_population_max_error","CH_point_update_max_error","pressure_recovery_max_error","phase_budget_residual_per_node","source_migration_work","chemical_work_on_actual_delta_phi","energy_time_remainder","energy_balance_residual_per_node","source_migration_correction_work","kinetic_diagnostic_remainder","AB_source_max_error"};
 for(auto key:extra)s[key]=0;for(int a=0;a<3;++a){s["raw_momentum_residual_per_node_"+std::to_string(a)]=0;s["physical_momentum_residual_per_node_"+std::to_string(a)]=0;}
 s["phase_relative_drift"]=0;s["liquid_relative_drift"]=0;s["mass_relative_drift"]=0;s["step"]=0;
 std::vector<std::string> keys;for(auto& [k,v]:s)keys.push_back(k);
 std::ofstream history(out/"history.csv");history<<std::setprecision(20);for(std::size_t i=0;i<keys.size();++i)history<<(i?",":"")<<keys[i];history<<'\n';
 int completed=0;bool safe=true;long double peakQ=0,peakMass=0,peakMach=0;int peakQstep=0,peakMassStep=0;
 for(int it=0;it<=(initOnly?0:64);++it){
  if(it){Frame previous=current;auto before=s;s=step(tc,grid,cfg,previous,current,before);}
  s["step"]=it;s["phase_relative_drift"]=(s["phase_sum"]-first.at("phase_sum"))/first.at("phase_sum");
  s["liquid_relative_drift"]=(s["liquid_sum"]-first.at("liquid_sum"))/first.at("liquid_sum");s["mass_relative_drift"]=(s["mass_sum"]-first.at("mass_sum"))/first.at("mass_sum");
  if(std::abs(s["phase_relative_drift"])>peakQ){peakQ=std::abs(s["phase_relative_drift"]);peakQstep=it;}if(std::abs(s["mass_relative_drift"])>peakMass){peakMass=std::abs(s["mass_relative_drift"]);peakMassStep=it;}peakMach=std::max(peakMach,s["Mach_max"]);
  for(std::size_t i=0;i<keys.size();++i)history<<(i?",":"")<<s.at(keys[i]);history<<'\n';history.flush();
  dump(current,grid,out/"frames"/("step_"+std::to_string(it)+".bin.gz"));
  completed=it;safe=s["finite"]==1&&s["rho_min"]>0&&s["Mach_max"]<.05;
  std::cout<<"step="<<it<<" phase_drift="<<s["phase_relative_drift"]<<" Mach="<<s["Mach_max"]<<"\n";
  if(!safe)break;
 }
 auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
 std::ofstream result(out/"result.json");result<<std::setprecision(20)<<"{\"requested_steps\":"<<(initOnly?0:64)<<",\"completed_steps\":"<<completed<<",\"NS_collide_calls\":"<<completed<<",\"CH_collide_calls\":"<<completed<<",\"safe\":"<<(safe?"true":"false")<<",\"wall_seconds\":"<<elapsed<<",\"phase_max_absolute_relative_drift\":"<<peakQ<<",\"phase_peak_step\":"<<peakQstep<<",\"mass_max_absolute_relative_drift\":"<<peakMass<<",\"mass_peak_step\":"<<peakMassStep<<",\"maximum_Mach\":"<<peakMach<<",\"NUMERICAL_GATE\":\"NOT_EVALUATED\",\"RESULT_PASS\":\"NOT_EVALUATED\",\"geometry_PASS\":\"NOT_EVALUATED\"}\n";
 return safe&&completed==(initOnly?0:64)?0:4;
}
int main(int argc,char** argv){
 try{
  if(argc==2&&std::string(argv[1])=="--describe"){std::cout<<"C coarse only:4 fixed N64/64-step cases; --initialize-only has zero collide/stream; every-step 16-field gzip evidence; no K or equilibrium claim\n";return 0;}
  if(argc!=3&&argc!=4)throw std::runtime_error("usage: coupled_check C_frozen_id new_output [--initialize-only]");
  std::string id=argv[1];bool init=argc==4;if(init&&std::string(argv[3])!="--initialize-only")throw std::runtime_error("unknown option");
  Config cfg;bool found=false;for(bool equal:{true,false})for(bool zero:{true,false}){std::string candidate=std::string("C_")+(equal?"equal":"target")+(zero?"_mu0":"_constitutive");if(id==candidate){cfg={id,equal,zero};found=true;}}
  if(!found)throw std::runtime_error("invalid frozen C case ID");
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)throw std::runtime_error("single MPI rank only");
  static_assert(!dynamics::is_cse_optimized_v<CHDyn>);return run(cfg,std::filesystem::absolute(argv[2]),init);
 }catch(const std::exception& e){std::cerr<<"C_DIAGNOSTIC_ERROR: "<<e.what()<<'\n';return 3;}
}
