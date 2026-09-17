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

constexpr T dx=5e-9,dt=1e-11,h=65e-9,grooveDepth=100e-9;
constexpr T rhoPhys=1000.,nu=1e-6,mu=rhoPhys*nu,accel=1e5;
constexpr int overlap=3,shortSteps=100,maxSteps=30000,windowN=1000;
constexpr T mainStdTol=1e-6,mainSpanTol=5e-6,crossAbsTol=1e-12;

struct GeometrySpec {
  int angle{},nx{},ny{},phasePeriod{},mesaHalf{};
  T lx{},ly{},normalPitch{},grooveWidth{};
};

GeometrySpec geometrySpec(int angle)
{
  if(angle==0||angle==90) return {angle,48,48,48,12,240e-9,240e-9,240e-9,120e-9};
  if(angle==45) {
    const T normalPixel=dx/std::sqrt(T(2));
    return {angle,68,68,68,17,340e-9,340e-9,68*normalPixel,34*normalPixel};
  }
  throw std::invalid_argument("angle must be 0, 45 or 90");
}

int positiveModulo(int value,int period)
{
  const int result=value%period;
  return result<0?result+period:result;
}

int materialAt(const LatticeR<3>& p,const GeometrySpec& spec)
{
  if(p[2]<0) return 2;
  int phase=0;
  if(spec.angle==0) phase=positiveModulo(p[0],spec.phasePeriod);
  else if(spec.angle==90) phase=positiveModulo(p[1],spec.phasePeriod);
  else phase=positiveModulo(p[0]-p[1],spec.phasePeriod);
  const bool mesa=phase<spec.mesaHalf||phase>=spec.phasePeriod-spec.mesaHalf;
  const T z=(p[2]-.5)*dx;
  if(z>=(mesa?h:h+grooveDepth)) return 3;
  return z<0?2:1;
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

struct Measure {
  long long nodes{}; T mass{},volume{},maxRhoDev{},maxULat{};
  T intU[3]{},meanU[3]{},J[3]{},q1{},q2{};
  T pressureMin=std::numeric_limits<T>::max();
  T pressureMax=-std::numeric_limits<T>::max();
  bool finite=true;
};

template<class LAT,class GEO>
Measure measure(LAT& lattice,GEO& geometry,const UnitConverter<T,D>& converter,
                const GeometrySpec& spec,int drive)
{
  Measure s; const T areaPlan=spec.lx*spec.ly;
  const int plane1=(drive==0?spec.nx:spec.ny)/4;
  const int plane2=3*(drive==0?spec.nx:spec.ny)/4;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC); auto& geo=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      if(geo.getMaterial(p)!=1) return;
      auto cell=block.get(p); T u[3]{}; cell.computeU(u); const T rho=cell.computeRho();
      const T uLat=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      const T pressure=converter.getPhysPressure((rho-1)/descriptors::invCs2<T,D>());
      ++s.nodes; s.mass+=rho*rhoPhys*dx*dx*dx; s.volume+=dx*dx*dx;
      s.maxRhoDev=std::max(s.maxRhoDev,std::abs(rho-1)); s.maxULat=std::max(s.maxULat,uLat);
      s.pressureMin=std::min(s.pressureMin,pressure); s.pressureMax=std::max(s.pressureMax,pressure);
      s.finite&=std::isfinite(rho)&&std::isfinite(uLat)&&std::isfinite(pressure);
      for(int d=0;d<3;++d) s.intU[d]+=converter.getPhysVelocity(u[d])*dx*dx*dx;
      const T ud=converter.getPhysVelocity(u[drive]);
      if((drive==0?p[0]:p[1])==plane1) s.q1+=ud*dx*dx;
      if((drive==0?p[0]:p[1])==plane2) s.q2+=ud*dx*dx;
    });
  }
  for(int d=0;d<3;++d) { s.meanU[d]=s.intU[d]/s.volume; s.J[d]=s.intU[d]/areaPlan; }
  return s;
}

struct SeriesWindow {
  std::deque<T> values;
  void add(T value) { values.push_back(value); if(static_cast<int>(values.size())>windowN) values.pop_front(); }
  bool full() const { return static_cast<int>(values.size())==windowN; }
  void metrics(T& relStd,T& relSpan,T& absMax) const {
    const T avg=std::accumulate(values.begin(),values.end(),T{})/values.size(); T ss=0; absMax=0;
    for(T value:values) { ss+=(value-avg)*(value-avg); absMax=std::max(absMax,std::abs(value)); }
    relStd=std::sqrt(ss/values.size())/std::abs(avg);
    const auto mm=std::minmax_element(values.begin(),values.end());
    relSpan=(*mm.second-*mm.first)/std::abs(avg);
  }
};

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1) { std::cerr<<"single rank required\n"; return 2; }
  if(argc!=3) { std::cerr<<"usage: ./sim_ec1xt240_directional_dns ANGLE short-x|short-y|x|y\n"; return 2; }
  const int angle=std::stoi(argv[1]); GeometrySpec spec;
  try { spec=geometrySpec(angle); } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 2; }
  const std::string mode=argv[2]; const bool shortRun=mode.rfind("short-",0)==0;
  const int drive=(mode=="x"||mode=="short-x")?0:(mode=="y"||mode=="short-y")?1:-1;
  if(drive<0) return 2;
  const std::string runId="sim_ec1xt240_angle"+std::to_string(angle)+"_h65_dx5_a1e5_"+mode+"_20260909";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)) { std::cerr<<"exists "<<outDir<<'\n'; return 2; }
  std::filesystem::create_directories(outDir); singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log"); log<<std::setprecision(17)<<std::boolalpha;

  try {
    const T areaPlan=spec.lx*spec.ly,href=h+grooveDepth/T(2),nominalVolume=areaPlan*href;
    const long long expectedNodes=static_cast<long long>(spec.nx)*spec.ny*23;
    IndicatorCuboid3D<T> domain({spec.lx-dx,spec.ly-dx,h+grooveDepth+20e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1); cuboids.setPeriodicity({true,true,false});
    HeuristicLoadBalancer<T> load(cuboids); SuperGeometry<T,3> geometry(cuboids,load,overlap);
    for(int iC=0;iC<load.size();++iC) {
      auto& block=geometry.getBlockGeometry(iC);
      block.forCoreSpatialLocations([&](LatticeR<3> p) { block.set(p,materialAt(p,spec)); });
    }
    geometry.communicate(); geometry.checkForErrors(false); const auto initialMaterials=materialCounts(geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nu,rhoPhys); SuperLattice<T,D> lattice(converter,cuboids,load);
    dynamics::set<ForcedBGKdynamics>(lattice,geometry,1);
    boundary::set<boundary::BounceBack>(lattice,geometry,2);
    boundary::set<boundary::BounceBack>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0); lattice.defineRhoU(geometry.getMaterialIndicator(1),one,zero);
    lattice.iniEquilibrium(geometry,1,one,zero); Vector<T,3> force{0,0,0}; force[drive]=accel*dt*dt/dx;
    fields::set<descriptors::FORCE>(lattice,geometry.getMaterialIndicator(1),force);
    lattice.setParameter<descriptors::OMEGA>(converter.getLatticeRelaxationFrequency()); lattice.initialize();

    SuperVTMwriter3D<T> writer("sim_ec1xt240_angle"+std::to_string(angle)+"_"+mode,overlap);
    SuperGeometryF3D<T> material(geometry); material.getName()="material";
    SuperLatticePhysVelocity3D<T,D> velocity(lattice,converter); velocity.getName()="velocity_m_s";
    SuperLatticePhysPressure3D<T,D> pressure(lattice,converter); pressure.getName()="pressure_Pa";
    writer.addFunctor(material); writer.addFunctor(velocity); writer.addFunctor(pressure); writer.createMasterFile(); writer.write(0);

    const Measure initial=measure(lattice,geometry,converter,spec,drive); T maxMass=0,maxRho=0,maxMach=0;
    SeriesWindow mainWindow,crossWindow; bool converged=false; int finalStep=0;
    T mainStd=INFINITY,mainSpan=INFINITY,mainAbs=INFINITY,crossStd=INFINITY,crossSpan=INFINITY,crossAbs=INFINITY;
    std::ofstream csv(outDir/"diagnostics.csv"); csv<<std::setprecision(17)
      <<"step,time_s,fluid_nodes,fluid_volume_m3,fluid_mass_kg,mass_abs_relative,max_density_deviation,"
        "pressure_min_Pa,pressure_max_Pa,mean_ux_m_s,mean_uy_m_s,mean_uz_m_s,Jx_m2_s,Jy_m2_s,Jz_m2_s,"
        "Q_section1_m3_s,Q_section2_m3_s,section_relative_difference,max_speed_m_s,Re_max_Href,Mach_max,"
        "main_rel_std,main_rel_span,cross_rel_std,cross_rel_span,cross_abs_max,finite,material_unchanged\n";
    const int limit=shortRun?shortSteps:maxSteps;
    for(int step=0;step<=limit;++step) {
      if(step) lattice.collideAndStream();
      const Measure state=measure(lattice,geometry,converter,spec,drive);
      const T massRel=std::abs((state.mass-initial.mass)/initial.mass); maxMass=std::max(maxMass,massRel);
      maxRho=std::max(maxRho,state.maxRhoDev); const T maxSpeed=converter.getPhysVelocity(state.maxULat);
      const T mach=state.maxULat/std::sqrt(T(1)/3); maxMach=std::max(maxMach,mach);
      const int crossDirection=1-drive; mainWindow.add(state.J[drive]); crossWindow.add(state.J[crossDirection]);
      if(mainWindow.full()) { mainWindow.metrics(mainStd,mainSpan,mainAbs); crossWindow.metrics(crossStd,crossSpan,crossAbs); }
      const T qDen=std::max(std::abs(state.q1),std::abs(state.q2)); const T qRel=qDen?std::abs(state.q1-state.q2)/qDen:0;
      const bool same=materialCounts(geometry)==initialMaterials;
      csv<<step<<','<<step*dt<<','<<state.nodes<<','<<state.volume<<','<<state.mass<<','<<massRel<<','<<state.maxRhoDev
        <<','<<state.pressureMin<<','<<state.pressureMax<<','<<state.meanU[0]<<','<<state.meanU[1]<<','<<state.meanU[2]
        <<','<<state.J[0]<<','<<state.J[1]<<','<<state.J[2]<<','<<state.q1<<','<<state.q2<<','<<qRel<<','<<maxSpeed
        <<','<<maxSpeed*href/nu<<','<<mach<<','<<(mainWindow.full()?mainStd:-1)<<','<<(mainWindow.full()?mainSpan:-1)
        <<','<<(mainWindow.full()?crossStd:-1)<<','<<(mainWindow.full()?crossSpan:-1)<<','<<(mainWindow.full()?crossAbs:-1)
        <<','<<state.finite<<','<<same<<'\n';
      finalStep=step;
      const bool crossSteady=angle==45?(crossStd<=mainStdTol&&crossSpan<=mainSpanTol):crossAbs<=crossAbsTol;
      if(!shortRun&&mainWindow.full()&&mainStd<=mainStdTol&&mainSpan<=mainSpanTol&&crossSteady) { converged=true; break; }
    }

    const Measure final=measure(lattice,geometry,converter,spec,drive); writer.write(finalStep);
    const T qDen=std::max(std::abs(final.q1),std::abs(final.q2)); const T qRel=qDen?std::abs(final.q1-final.q2)/qDen:0;
    const T maxSpeed=converter.getPhysVelocity(final.maxULat),mach=final.maxULat/std::sqrt(T(1)/3);
    const bool same=materialCounts(geometry)==initialMaterials;
    const bool geometryPass=initialMaterials[1]==expectedNodes&&std::abs(final.volume-nominalVolume)<1e-30;
    const T crossJ=final.J[1-drive];
    const bool crossPhysicalPass=angle==45?(crossJ>0):std::abs(crossJ)<=crossAbsTol;
    const bool basic=final.finite&&same&&maxMass<=1e-10&&maxRho<=(shortRun?1e-7:1e-6)
      &&mach<=.05&&final.J[drive]>0&&crossPhysicalPass;
    const bool pass=shortRun?(basic&&geometryPass):(basic&&geometryPass&&converged&&qRel<=1e-5);
    const T Kx=mu*final.J[0]/(rhoPhys*accel),Ky=mu*final.J[1]/(rhoPhys*accel);
    const T resistance=rhoPhys*accel/final.J[drive],flowRate=(final.q1+final.q2)/2;

    std::ofstream result(outDir/"result.txt"); result<<std::setprecision(17)<<std::boolalpha
      <<"model=SIM-EC1XT240\nrun_id="<<runId<<"\nangle_deg="<<angle<<"\nmode="<<mode<<"\nPASS="<<pass
      <<"\nconverged="<<converged<<"\nsteps_completed="<<finalStep<<"\nnx_ny="<<spec.nx<<','<<spec.ny
      <<"\nLx_Ly_m="<<spec.lx<<','<<spec.ly<<"\nnormal_pitch_nm="<<spec.normalPitch*1e9
      <<"\ngroove_width_nm="<<spec.grooveWidth*1e9<<"\ngap_nm=65\ndt_s="<<dt
      <<"\ntau="<<converter.getLatticeRelaxationTime()<<"\nforce_lattice="<<force[0]<<','<<force[1]<<','<<force[2]
      <<"\nfluid_nodes="<<final.nodes<<"\nfluid_volume_m3="<<final.volume<<"\nnominal_volume_m3="<<nominalVolume
      <<"\nmax_mass_abs_relative="<<maxMass<<"\nmax_density_deviation="<<maxRho
      <<"\npressure_range_Pa="<<final.pressureMin<<','<<final.pressureMax<<"\nmax_speed_m_s="<<maxSpeed
      <<"\nRe_max_Href="<<maxSpeed*href/nu<<"\nMach_max="<<mach
      <<"\nmean_u_m_s="<<final.meanU[0]<<','<<final.meanU[1]<<','<<final.meanU[2]
      <<"\nJ_m2_s="<<final.J[0]<<','<<final.J[1]<<','<<final.J[2]
      <<"\nK_response_column_m3="<<Kx<<','<<Ky<<"\nflow_rate_mean_m3_s="<<flowRate
      <<"\nR_main_Pa_s_per_m3="<<resistance<<"\nQ_sections_m3_s="<<final.q1<<','<<final.q2
      <<"\nsection_relative_difference="<<qRel<<"\nmain_rel_std="<<mainStd<<"\nmain_rel_span="<<mainSpan
      <<"\ncross_rel_std="<<crossStd<<"\ncross_rel_span="<<crossSpan<<"\ncross_abs_max="<<crossAbs
      <<"\nmaterial_unchanged="<<same<<"\nfinite="<<final.finite<<"\nexit_code="<<(pass?0:3)
      <<"\nexit_reason="<<(pass?(shortRun?"short_test_passed":"steady_converged_and_accepted")
                                  :(converged?"threshold_failure":"maximum_steps_without_convergence"))<<'\n';
    std::ofstream manifest(outDir/"run_manifest.txt"); manifest
      <<"model=SIM-EC1XT240\nrun_id="<<runId<<"\ncommand=mpirun -np 1 ./sim_ec1xt240_directional_dns "
      <<angle<<' '<<mode<<"\nangle_reference=current_groove_axis_y\nboundary=x_y_periodic_z_fixed_bounceback\n"
      <<"pressure=SuperLatticePhysPressure3D\nexit_code="<<(pass?0:3)<<'\n';
    log<<"run_id="<<runId<<"\nPASS="<<pass<<"\nsteps_completed="<<finalStep<<"\nexit_code="<<(pass?0:3)<<'\n';
    std::cout<<runId<<" PASS="<<pass<<" step="<<finalStep<<'\n'; return pass?0:3;
  } catch(const std::exception& error) {
    log<<"exception="<<error.what()<<"\nexit_code=4\n"; std::cerr<<error.what()<<'\n'; return 4;
  }
}
