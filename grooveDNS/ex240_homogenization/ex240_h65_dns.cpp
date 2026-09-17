#include <olb.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <string>

using namespace olb;
using T=double;
using D=descriptors::D3Q19<descriptors::FORCE>;

constexpr T dx=5e-9,dt=1e-11,Lx=240e-9,Ly=240e-9,h=65e-9,dg=100e-9;
constexpr T rhoP=1000.,nu=1e-6,mu=rhoP*nu,accel=1e5,Aplan=Lx*Ly;
constexpr T Vnom=Aplan*h+120e-9*Ly*dg,Href=Vnom/Aplan;
constexpr int overlap=3,shortSteps=100,maxSteps=30000,windowN=1000;
constexpr T mainStdTol=1e-6,mainSpanTol=5e-6,crossAbsTol=1e-12;

struct Measure {
 long long n=0; T mass=0,volume=0,maxRhoDev=0,maxULat=0;
 T intU[3]{},meanU[3]{},J[3]{},q1=0,q2=0; bool finite=true;
};

int matAt(const Vector<T,3>& r){
 const T x=r[0],z=r[2]; if(z<0)return 2;
 const bool mesa=x<60e-9||x>=180e-9;
 if(z>=(mesa?h:h+dg)) return 3;
 return 1;
}

template<class GEO> std::array<long long,4> matCounts(GEO& geo){
 std::array<long long,4> n{}; for(int c=0;c<geo.getLoadBalancer().size();++c){auto&g=geo.getBlockGeometry(c);g.forCoreSpatialLocations([&](LatticeR<3>p){int m=g.getMaterial(p);if(m>=0&&m<4)n[m]++;});}return n;
}

template<class LAT,class GEO> Measure measure(LAT&lat,GEO&geo,const UnitConverter<T,D>&cv,int drive){
 Measure s; const int p1=drive==0?12:12,p2=drive==0?36:24; // x=62.5/182.5 or y=62.5/122.5 nm
 for(int c=0;c<lat.getLoadBalancer().size();++c){auto&b=lat.getBlock(c);auto&g=geo.getBlockGeometry(c);b.forCoreSpatialLocations([&](LatticeR<3>p){
  if(g.getMaterial(p)!=1) return;
  auto cell=b.get(p);T u[3]{};cell.computeU(u);T r=cell.computeRho();
  s.n++;s.mass+=r*rhoP*dx*dx*dx;s.volume+=dx*dx*dx;s.maxRhoDev=std::max(s.maxRhoDev,std::abs(r-1));
  T ul=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);s.maxULat=std::max(s.maxULat,ul);s.finite&=std::isfinite(r)&&std::isfinite(ul);
  for(int d=0;d<3;++d){T up=cv.getPhysVelocity(u[d]);s.intU[d]+=up*dx*dx*dx;}
  const T ud=cv.getPhysVelocity(u[drive]);if((drive==0?p[0]:p[1])==p1)s.q1+=ud*dx*dx;if((drive==0?p[0]:p[1])==p2)s.q2+=ud*dx*dx;
 });}
 for(int d=0;d<3;++d){s.meanU[d]=s.intU[d]/s.volume;s.J[d]=s.intU[d]/Aplan;}return s;
}

struct Window {std::deque<T> main,cross;void add(T a,T b){main.push_back(a);cross.push_back(b);if((int)main.size()>windowN){main.pop_front();cross.pop_front();}}
 bool full()const{return (int)main.size()==windowN;} void metrics(T&relStd,T&relSpan,T&crossMax)const{T avg=std::accumulate(main.begin(),main.end(),T{})/main.size(),ss=0;for(T x:main)ss+=(x-avg)*(x-avg);relStd=std::sqrt(ss/main.size())/std::abs(avg);auto mm=std::minmax_element(main.begin(),main.end());relSpan=(*mm.second-*mm.first)/std::abs(avg);crossMax=0;for(T x:cross)crossMax=std::max(crossMax,std::abs(x));}}
;

int main(int argc,char**argv){
 initialize(&argc,&argv);if(singleton::mpi().getSize()!=1){std::cerr<<"single rank required\n";return 2;}
 if(argc<2){std::cerr<<"usage: ./ex240_h65_dns short-x|short-y|x|y\n";return 2;}
 std::string mode=argv[1];bool shortRun=mode.rfind("short-",0)==0;int drive=(mode=="x"||mode=="short-x")?0:(mode=="y"||mode=="short-y")?1:-1;if(drive<0)return 2;
 std::string run="ex240_h65_dx5_a1e5_"+mode+"_20260907";auto out=std::filesystem::path("output")/run;if(std::filesystem::exists(out)){std::cerr<<"exists "<<out<<"\n";return 2;}std::filesystem::create_directories(out);singleton::directories().setOutputDir((out.string()+"/").c_str());
 std::ofstream log(out/"run.log");log<<std::setprecision(16)<<std::boolalpha;
 try{
  IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,h+dg+20e-9},{dx/2,dx/2,-dx/2});CuboidDecomposition<T,3> cub(domain,dx,1);cub.setPeriodicity({true,true,false});HeuristicLoadBalancer<T> load(cub);SuperGeometry<T,3> geo(cub,load,overlap);
  for(int c=0;c<load.size();++c){auto&g=geo.getBlockGeometry(c);g.forCoreSpatialLocations([&](LatticeR<3>p){g.set(p,matAt(g.getPhysR(p)));});}geo.communicate();geo.checkForErrors(false);auto mats0=matCounts(geo);
  UnitConverter<T,D> cv(dx,dt,240e-9,1.,nu,rhoP);SuperLattice<T,D> lat(cv,cub,load);dynamics::set<ForcedBGKdynamics>(lat,geo,1);boundary::set<boundary::BounceBack>(lat,geo,2);boundary::set<boundary::BounceBack>(lat,geo,3);
  AnalyticalConst3D<T,T> one(1),zero(0,0,0);lat.defineRhoU(geo.getMaterialIndicator(1),one,zero);lat.iniEquilibrium(geo,1,one,zero);Vector<T,3> force{0,0,0};force[drive]=accel*dt*dt/dx;fields::set<descriptors::FORCE>(lat,geo.getMaterialIndicator(1),force);lat.setParameter<descriptors::OMEGA>(cv.getLatticeRelaxationFrequency());lat.initialize();
  SuperVTMwriter3D<T> wr("ex240_h65_"+mode,overlap);SuperGeometryF3D<T> gm(geo);gm.getName()="material";SuperLatticePhysVelocity3D<T,D> vel(lat,cv);vel.getName()="velocity_m_s";wr.addFunctor(gm);wr.addFunctor(vel);wr.createMasterFile();wr.write(0);
  auto s0=measure(lat,geo,cv,drive);T maxMass=0,maxRho=0,maxMach=0;Window win;bool converged=false;int finalStep=0;T rs=std::numeric_limits<T>::infinity(),span=rs,crossMax=rs;
  std::ofstream csv(out/"diagnostics.csv");csv<<"step,time_s,fluid_nodes,fluid_volume_m3,fluid_mass_kg,mass_signed_relative,mass_abs_relative,max_density_deviation,mean_ux_m_s,mean_uy_m_s,mean_uz_m_s,Jx_m2_s,Jy_m2_s,Jz_m2_s,Q_section1_m3_s,Q_section2_m3_s,section_relative_difference,max_speed_m_s,Re_max_Href,Mach_max,window_main_rel_std,window_main_rel_span,window_cross_abs_max,finite,material_unchanged\n"<<std::setprecision(16);
  int limit=shortRun?shortSteps:maxSteps;for(int step=0;step<=limit;++step){if(step)lat.collideAndStream();auto s=measure(lat,geo,cv,drive);T rel=(s.mass-s0.mass)/s0.mass;maxMass=std::max(maxMass,std::abs(rel));maxRho=std::max(maxRho,s.maxRhoDev);T u=cv.getPhysVelocity(s.maxULat),mach=s.maxULat/std::sqrt(1./3.);maxMach=std::max(maxMach,mach);T qden=std::max(std::abs(s.q1),std::abs(s.q2)),qrel=qden?std::abs(s.q1-s.q2)/qden:0;win.add(s.J[drive],s.J[1-drive]);if(win.full())win.metrics(rs,span,crossMax);bool same=matCounts(geo)==mats0;
   csv<<step<<","<<step*dt<<","<<s.n<<","<<s.volume<<","<<s.mass<<","<<rel<<","<<std::abs(rel)<<","<<s.maxRhoDev<<","<<s.meanU[0]<<","<<s.meanU[1]<<","<<s.meanU[2]<<","<<s.J[0]<<","<<s.J[1]<<","<<s.J[2]<<","<<s.q1<<","<<s.q2<<","<<qrel<<","<<u<<","<<u*Href/nu<<","<<mach<<","<<(win.full()?rs:-1)<<","<<(win.full()?span:-1)<<","<<(win.full()?crossMax:-1)<<","<<s.finite<<","<<same<<"\n";
   finalStep=step;if(!shortRun&&win.full()&&rs<=mainStdTol&&span<=mainSpanTol&&crossMax<=crossAbsTol){converged=true;break;}
  }
  auto sf=measure(lat,geo,cv,drive);wr.write(finalStep);T qden=std::max(std::abs(sf.q1),std::abs(sf.q2)),qrel=qden?std::abs(sf.q1-sf.q2)/qden:0;T umax=cv.getPhysVelocity(sf.maxULat);T mach=sf.maxULat/std::sqrt(1./3.);bool same=matCounts(geo)==mats0;
  bool geometryPass=mats0[1]==52992&&std::abs(sf.volume-Vnom)<1e-30;bool basic=sf.finite&&same&&maxMass<=1e-10&&maxRho<=(shortRun?1e-7:1e-6)&&mach<=.05&&sf.J[drive]>0&&std::abs(sf.J[1-drive])<=crossAbsTol;bool pass=shortRun?(basic&&geometryPass):(basic&&geometryPass&&converged&&qrel<=1e-5);
  T Kx=mu*sf.J[0]/(rhoP*accel),Ky=mu*sf.J[1]/(rhoP*accel);
  std::ofstream result(out/"result.txt");result<<std::setprecision(16)<<std::boolalpha<<"run_id="<<run<<"\nmode="<<mode<<"\nPASS="<<pass<<"\nconverged="<<converged<<"\nsteps_completed="<<finalStep<<"\ndt_s="<<dt<<"\ntau="<<cv.getLatticeRelaxationTime()<<"\nforce_lattice="<<force[0]<<","<<force[1]<<","<<force[2]<<"\nfluid_nodes="<<sf.n<<"\nfluid_volume_m3="<<sf.volume<<"\nnominal_volume_m3="<<Vnom<<"\nmax_mass_abs_relative="<<maxMass<<"\nmax_density_deviation="<<maxRho<<"\nmax_speed_m_s="<<umax<<"\nRe_max_Href="<<umax*Href/nu<<"\nMach_max="<<mach<<"\nmean_u_m_s="<<sf.meanU[0]<<","<<sf.meanU[1]<<","<<sf.meanU[2]<<"\nJ_m2_s="<<sf.J[0]<<","<<sf.J[1]<<","<<sf.J[2]<<"\nK_m3="<<Kx<<","<<Ky<<"\nB_m2="<<Kx/Href<<","<<Ky/Href<<"\nQ_sections_m3_s="<<sf.q1<<","<<sf.q2<<"\nsection_relative_difference="<<qrel<<"\nwindow_main_rel_std="<<rs<<"\nwindow_main_rel_span="<<span<<"\nwindow_cross_abs_max="<<crossMax<<"\nmaterial_unchanged="<<same<<"\nfinite="<<sf.finite<<"\nexit_code="<<(pass?0:3)<<"\nexit_reason="<<(pass?(shortRun?"short_test_passed":"steady_converged_and_accepted"):(converged?"threshold_failure":"maximum_steps_without_convergence"))<<"\n";
  log<<"run_id="<<run<<"\nmode="<<mode<<"\nsteps_completed="<<finalStep<<"\nPASS="<<pass<<"\nexit_code="<<(pass?0:3)<<"\n";std::ofstream rec(out/"run_record.txt");rec<<"run_id="<<run<<"\ncommand=./ex240_h65_dns "<<mode<<"\nexit_code="<<(pass?0:3)<<"\n";std::cout<<run<<" PASS="<<pass<<" step="<<finalStep<<"\n";return pass?0:3;
 }catch(const std::exception&e){log<<"exception="<<e.what()<<"\nexit_code=4\n";std::cerr<<e.what()<<"\n";return 4;}
}
