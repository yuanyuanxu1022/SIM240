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
#include <sstream>
#include <string>

using namespace olb;
using T=double;
using D=descriptors::D3Q19<descriptors::FORCE>;

constexpr T dx=5e-9,dt=1e-11,Lx=240e-9,Ly=240e-9,grooveDepth=100e-9;
constexpr T rhoPhys=1000.,nu=1e-6,mu=rhoPhys*nu,accel=1e5,Aplan=Lx*Ly;
constexpr int overlap=3,shortSteps=100,maxSteps=30000,windowN=1000;
constexpr T mainStdTol=1e-6,mainSpanTol=5e-6,crossAbsTol=1e-12;

struct Measure {
  long long nodes=0; T mass=0,volume=0,maxRhoDev=0,maxULat=0;
  T intU[3]{},meanU[3]{},J[3]{},q1=0,q2=0;
  T pressureMin=std::numeric_limits<T>::max();
  T pressureMax=-std::numeric_limits<T>::max();
  bool finite=true;
};

std::string gapTag(T h)
{
  std::ostringstream s;
  const T nm=h*1e9;
  if(std::abs(nm-std::round(nm))<1e-10) s<<static_cast<int>(std::llround(nm));
  else s<<std::fixed<<std::setprecision(1)<<nm;
  return s.str();
}

int materialAt(const Vector<T,3>& r,T h)
{
  if(r[2]<0) return 2;
  const bool mesa=r[0]<60e-9||r[0]>=180e-9;
  if(r[2]>=(mesa?h:h+grooveDepth)) return 3;
  return 1;
}

template<class GEO>
std::array<long long,4> materialCounts(GEO& geometry)
{
  std::array<long long,4> result{};
  for(int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
    auto& block=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      const int material=block.getMaterial(p);
      if(material>=0&&material<4) ++result[material];
    });
  }
  return result;
}

template<class LAT,class GEO>
Measure measure(LAT& lattice,GEO& geometry,const UnitConverter<T,D>& converter,int drive)
{
  Measure s;
  const int plane1=12;
  const int plane2=drive==0?36:24;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC);
    auto& geo=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      if(geo.getMaterial(p)!=1) return;
      auto cell=block.get(p); T u[3]{}; cell.computeU(u); const T rho=cell.computeRho();
      const T uLat=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      const T pressure=converter.getPhysPressure((rho-1)/descriptors::invCs2<T,D>());
      ++s.nodes; s.mass+=rho*rhoPhys*dx*dx*dx; s.volume+=dx*dx*dx;
      s.maxRhoDev=std::max(s.maxRhoDev,std::abs(rho-1));
      s.maxULat=std::max(s.maxULat,uLat);
      s.pressureMin=std::min(s.pressureMin,pressure);
      s.pressureMax=std::max(s.pressureMax,pressure);
      s.finite&=std::isfinite(rho)&&std::isfinite(uLat)&&std::isfinite(pressure);
      for(int d=0;d<3;++d) {
        const T up=converter.getPhysVelocity(u[d]);
        s.intU[d]+=up*dx*dx*dx;
      }
      const T ud=converter.getPhysVelocity(u[drive]);
      if((drive==0?p[0]:p[1])==plane1) s.q1+=ud*dx*dx;
      if((drive==0?p[0]:p[1])==plane2) s.q2+=ud*dx*dx;
    });
  }
  for(int d=0;d<3;++d) {
    s.meanU[d]=s.intU[d]/s.volume;
    s.J[d]=s.intU[d]/Aplan;
  }
  return s;
}

struct Window {
  std::deque<T> main,cross;
  void add(T a,T b) {
    main.push_back(a); cross.push_back(b);
    if(static_cast<int>(main.size())>windowN) { main.pop_front(); cross.pop_front(); }
  }
  bool full() const { return static_cast<int>(main.size())==windowN; }
  void metrics(T& relStd,T& relSpan,T& crossMax) const {
    const T avg=std::accumulate(main.begin(),main.end(),T{})/main.size(); T ss=0;
    for(T value:main) ss+=(value-avg)*(value-avg);
    relStd=std::sqrt(ss/main.size())/std::abs(avg);
    const auto mm=std::minmax_element(main.begin(),main.end());
    relSpan=(*mm.second-*mm.first)/std::abs(avg);
    crossMax=0; for(T value:cross) crossMax=std::max(crossMax,std::abs(value));
  }
};

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1) { std::cerr<<"single rank required\n"; return 2; }
  if(argc!=3) {
    std::cerr<<"usage: ./sim_ec1xt240_fixed_gap_dns GAP_NM short-x|short-y|x|y\n";
    return 2;
  }
  const T h=std::stod(argv[1])*1e-9;
  const bool allowedGap=std::abs(h-75e-9)<1e-15||std::abs(h-70e-9)<1e-15||std::abs(h-65e-9)<1e-15;
  const std::string mode=argv[2];
  const bool shortRun=mode.rfind("short-",0)==0;
  const int drive=(mode=="x"||mode=="short-x")?0:(mode=="y"||mode=="short-y")?1:-1;
  if(!allowedGap||drive<0) { std::cerr<<"unsupported frozen gap or mode\n"; return 2; }

  const std::string runId="sim_ec1xt240_h"+gapTag(h)+"_dx5_a1e5_"+mode+"_20260909";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)) { std::cerr<<"exists "<<outDir<<'\n'; return 2; }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log"); log<<std::setprecision(17)<<std::boolalpha;

  try {
    const T nominalVolume=Aplan*h+120e-9*Ly*grooveDepth;
    const T href=nominalVolume/Aplan;
    const long long expectedNodes=static_cast<long long>(std::llround(nominalVolume/(dx*dx*dx)));
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,h+grooveDepth+20e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1); cuboids.setPeriodicity({true,true,false});
    HeuristicLoadBalancer<T> load(cuboids); SuperGeometry<T,3> geometry(cuboids,load,overlap);
    for(int iC=0;iC<load.size();++iC) {
      auto& block=geometry.getBlockGeometry(iC);
      block.forCoreSpatialLocations([&](LatticeR<3> p) { block.set(p,materialAt(block.getPhysR(p),h)); });
    }
    geometry.communicate(); geometry.checkForErrors(false); const auto initialMaterials=materialCounts(geometry);

    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nu,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,load);
    dynamics::set<ForcedBGKdynamics>(lattice,geometry,1);
    boundary::set<boundary::BounceBack>(lattice,geometry,2);
    boundary::set<boundary::BounceBack>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator(1),one,zero);
    lattice.iniEquilibrium(geometry,1,one,zero);
    Vector<T,3> force{0,0,0}; force[drive]=accel*dt*dt/dx;
    fields::set<descriptors::FORCE>(lattice,geometry.getMaterialIndicator(1),force);
    lattice.setParameter<descriptors::OMEGA>(converter.getLatticeRelaxationFrequency());
    lattice.initialize();

    SuperVTMwriter3D<T> writer("sim_ec1xt240_h"+gapTag(h)+"_"+mode,overlap);
    SuperGeometryF3D<T> material(geometry); material.getName()="material";
    SuperLatticePhysVelocity3D<T,D> velocity(lattice,converter); velocity.getName()="velocity_m_s";
    SuperLatticePhysPressure3D<T,D> pressure(lattice,converter); pressure.getName()="pressure_Pa";
    writer.addFunctor(material); writer.addFunctor(velocity); writer.addFunctor(pressure);
    writer.createMasterFile(); writer.write(0);

    const Measure initial=measure(lattice,geometry,converter,drive);
    T maxMassDrift=0,maxRhoDeviation=0,maxMach=0;
    Window window; bool converged=false; int finalStep=0;
    T relStd=std::numeric_limits<T>::infinity(),relSpan=relStd,crossMax=relStd;
    std::ofstream csv(outDir/"diagnostics.csv"); csv<<std::setprecision(17)
      <<"step,time_s,fluid_nodes,fluid_volume_m3,fluid_mass_kg,mass_signed_relative,mass_abs_relative,"
        "max_density_deviation,pressure_min_Pa,pressure_max_Pa,mean_ux_m_s,mean_uy_m_s,mean_uz_m_s,"
        "Jx_m2_s,Jy_m2_s,Jz_m2_s,Q_section1_m3_s,Q_section2_m3_s,section_relative_difference,"
        "max_speed_m_s,Re_max_Href,Mach_max,window_main_rel_std,window_main_rel_span,"
        "window_cross_abs_max,finite,material_unchanged\n";
    const int limit=shortRun?shortSteps:maxSteps;
    for(int step=0;step<=limit;++step) {
      if(step) lattice.collideAndStream();
      const Measure state=measure(lattice,geometry,converter,drive);
      const T massRel=(state.mass-initial.mass)/initial.mass;
      maxMassDrift=std::max(maxMassDrift,std::abs(massRel));
      maxRhoDeviation=std::max(maxRhoDeviation,state.maxRhoDev);
      const T speed=converter.getPhysVelocity(state.maxULat);
      const T mach=state.maxULat/std::sqrt(T(1)/3); maxMach=std::max(maxMach,mach);
      const T qDen=std::max(std::abs(state.q1),std::abs(state.q2));
      const T qRel=qDen?std::abs(state.q1-state.q2)/qDen:0;
      window.add(state.J[drive],state.J[1-drive]);
      if(window.full()) window.metrics(relStd,relSpan,crossMax);
      const bool same=materialCounts(geometry)==initialMaterials;
      csv<<step<<','<<step*dt<<','<<state.nodes<<','<<state.volume<<','<<state.mass<<','<<massRel<<','
        <<std::abs(massRel)<<','<<state.maxRhoDev<<','<<state.pressureMin<<','<<state.pressureMax<<','
        <<state.meanU[0]<<','<<state.meanU[1]<<','<<state.meanU[2]<<','<<state.J[0]<<','<<state.J[1]<<','
        <<state.J[2]<<','<<state.q1<<','<<state.q2<<','<<qRel<<','<<speed<<','<<speed*href/nu<<','<<mach<<','
        <<(window.full()?relStd:-1)<<','<<(window.full()?relSpan:-1)<<','<<(window.full()?crossMax:-1)<<','
        <<state.finite<<','<<same<<'\n';
      finalStep=step;
      if(!shortRun&&window.full()&&relStd<=mainStdTol&&relSpan<=mainSpanTol&&crossMax<=crossAbsTol) {
        converged=true; break;
      }
    }

    const Measure final=measure(lattice,geometry,converter,drive); writer.write(finalStep);
    const T qDen=std::max(std::abs(final.q1),std::abs(final.q2));
    const T qRel=qDen?std::abs(final.q1-final.q2)/qDen:0;
    const T maxSpeed=converter.getPhysVelocity(final.maxULat);
    const T mach=final.maxULat/std::sqrt(T(1)/3);
    const bool same=materialCounts(geometry)==initialMaterials;
    const bool geometryPass=initialMaterials[1]==expectedNodes&&std::abs(final.volume-nominalVolume)<1e-30;
    const bool basic=final.finite&&same&&maxMassDrift<=1e-10
      &&maxRhoDeviation<=(shortRun?1e-7:1e-6)&&mach<=.05
      &&final.J[drive]>0&&std::abs(final.J[1-drive])<=crossAbsTol;
    const bool pass=shortRun?(basic&&geometryPass):(basic&&geometryPass&&converged&&qRel<=1e-5);
    const T Kmain=mu*final.J[drive]/(rhoPhys*accel);
    const T Bmain=Kmain/href;
    const T resistanceJ=rhoPhys*accel/final.J[drive];
    const T resistanceU=rhoPhys*accel/final.meanU[drive];

    std::ofstream result(outDir/"result.txt"); result<<std::setprecision(17)<<std::boolalpha
      <<"model=SIM-EC1XT240\nrun_id="<<runId<<"\ngap_nm="<<h*1e9<<"\nmode="<<mode
      <<"\nPASS="<<pass<<"\nconverged="<<converged<<"\nsteps_completed="<<finalStep
      <<"\ndt_s="<<dt<<"\ntau="<<converter.getLatticeRelaxationTime()
      <<"\nforce_lattice="<<force[0]<<','<<force[1]<<','<<force[2]
      <<"\nfluid_nodes="<<final.nodes<<"\nfluid_volume_m3="<<final.volume
      <<"\nnominal_volume_m3="<<nominalVolume<<"\nH_ref_m="<<href
      <<"\nmax_mass_abs_relative="<<maxMassDrift<<"\nmax_density_deviation="<<maxRhoDeviation
      <<"\npressure_range_Pa="<<final.pressureMin<<','<<final.pressureMax
      <<"\nmax_speed_m_s="<<maxSpeed<<"\nRe_max_Href="<<maxSpeed*href/nu<<"\nMach_max="<<mach
      <<"\nmean_u_m_s="<<final.meanU[0]<<','<<final.meanU[1]<<','<<final.meanU[2]
      <<"\nJ_m2_s="<<final.J[0]<<','<<final.J[1]<<','<<final.J[2]
      <<"\nK_main_m3="<<Kmain<<"\nB_main_m2="<<Bmain
      <<"\nR_J_Pa_s_per_m3="<<resistanceJ<<"\nR_U_Pa_s_per_m2="<<resistanceU
      <<"\nQ_sections_m3_s="<<final.q1<<','<<final.q2<<"\nsection_relative_difference="<<qRel
      <<"\nwindow_main_rel_std="<<relStd<<"\nwindow_main_rel_span="<<relSpan
      <<"\nwindow_cross_abs_max="<<crossMax<<"\nmaterial_unchanged="<<same
      <<"\nfinite="<<final.finite<<"\nexit_code="<<(pass?0:3)
      <<"\nexit_reason="<<(pass?(shortRun?"short_test_passed":"steady_converged_and_accepted")
                                  :(converged?"threshold_failure":"maximum_steps_without_convergence"))<<'\n';
    std::ofstream manifest(outDir/"run_manifest.txt"); manifest
      <<"model=SIM-EC1XT240\nrun_id="<<runId<<"\ncommand=mpirun -np 1 ./sim_ec1xt240_fixed_gap_dns "
      <<h*1e9<<' '<<mode<<"\nsource=sim_ec1xt240_fixed_gap_dns.cpp\npressure=SuperLatticePhysPressure3D\n"
      <<"boundary=x_y_periodic_z_fixed_bounceback\ndrive=periodic_body_acceleration\nexit_code="<<(pass?0:3)<<'\n';
    log<<"run_id="<<runId<<"\nPASS="<<pass<<"\nsteps_completed="<<finalStep<<"\nexit_code="<<(pass?0:3)<<'\n';
    std::cout<<runId<<" PASS="<<pass<<" step="<<finalStep<<'\n';
    return pass?0:3;
  } catch(const std::exception& error) {
    log<<"exception="<<error.what()<<"\nexit_code=4\n";
    std::cerr<<error.what()<<'\n'; return 4;
  }
}
