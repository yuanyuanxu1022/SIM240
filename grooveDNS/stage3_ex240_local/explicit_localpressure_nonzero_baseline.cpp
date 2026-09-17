#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

constexpr int baselineN=16;
constexpr T baselineLength=(baselineN-1)*dx;
constexpr T imposedDeltaRho=2e-6;

class PeriodicXZOutside final : public IndicatorF3D<T> {
public:
  PeriodicXZOutside()
  {
    this->_myMin={-1e9,-1e9,-1e9};this->_myMax={1e9,1e9,1e9};
    this->getName()="PeriodicXZOutside";
  }
  bool operator()(bool output[1],const T r[3]) override
  {
    const T eps=dx*1e-6;
    output[0]=r[1]<dx/2-eps||r[1]>baselineLength+dx/2+eps;
    return true;
  }
};

class LinearBaselineRho final : public AnalyticalF3D<T,T> {
public:
  LinearBaselineRho():AnalyticalF3D<T,T>(1){this->getName()="LinearBaselineRho";}
  bool operator()(T out[1],const T r[3]) override
  {
    out[0]=1+imposedDeltaRho/T(2)-imposedDeltaRho*r[1]/baselineLength;
    return true;
  }
};

struct BaselineStats {
  T mass=0,rhoMin=1e300,rhoMax=-1e300,maxU=0,lowOut=0,highOut=0;
  bool finite=true;
};

template<class L,class G>
BaselineStats baselineStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter)
{
  BaselineStats s;
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    const int m=g.getMaterial(p);if(m!=1&&m!=4&&m!=5)return;
    auto cell=block.get(p);T u[3]{};cell.computeU(u);const T rho=cell.computeRho();
    const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
    s.mass+=rho*rhoPhys*dx*dx*dx;s.rhoMin=std::min(s.rhoMin,rho);
    s.rhoMax=std::max(s.rhoMax,rho);s.maxU=std::max(s.maxU,speed);
    s.finite&=std::isfinite(rho)&&std::isfinite(speed);
    for(int i=0;i<D::q;++i)s.finite&=std::isfinite(cell[i]);
    const T uy=converter.getPhysVelocity(u[1]);
    if(m==4)s.lowOut-=rho*rhoPhys*uy*dx*dx;
    if(m==5)s.highOut+=rho*rhoPhys*uy*dx*dx;
  });
  return s;
}

int runLocalPressureNonzero()
{
  const std::string runId="localpressure_fixed_nonzero_flow_650_20260907";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"Refusing to overwrite\n";return 2;}
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());

  IndicatorCuboid3D<T> domain({baselineLength,baselineLength,baselineLength},
                              {dx/2,dx/2,dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,true});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    g.set(p,p[1]==0?4:(p[1]==baselineN-1?5:1));
  });
  geometry.communicate();
  SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXZOutside,geometry);
  UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
  SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
  dynamics::set<BGKdynamics>(lattice,geometry,1);
  boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
  LinearBaselineRho rhoProfile;AnalyticalConst3D<T,T> zero(0,0,0);
  lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),rhoProfile,zero);
  for(int m:{1,4,5})lattice.iniEquilibrium(geometry,m,rhoProfile,zero);
  lattice.initialize();
  AnalyticalConst3D<T,T> rhoLow(1+imposedDeltaRho/T(2));
  AnalyticalConst3D<T,T> rhoHigh(1-imposedDeltaRho/T(2));
  lattice.defineRho(geometry,4,rhoLow);lattice.defineRho(geometry,5,rhoHigh);
  lattice.communicate();

  std::ofstream csv(outDir/"diagnostics.csv");csv<<std::setprecision(17)
    <<"step,time_s,mass_kg,mass_relative_change,low_outward_flux_kg_s,"
      "high_outward_flux_kg_s,net_outward_flux_kg_s,cumulative_outward_mass_kg,"
      "mass_balance_residual_kg,relative_mass_balance_residual,rho_min,rho_max,"
      "max_speed_lattice,max_speed_m_s,max_Mach,finite\n";
  BaselineStats initial=baselineStats(lattice,geometry,converter),previous=initial,current=initial;
  T cumulative=0,maxMach=0,minRho=1e300,maxRho=-1e300,maxResidual=0;
  int firstMach=-1,firstRho=-1,firstNonfinite=-1;
  for(int step=0;step<=650;++step){
    if(step)lattice.collideAndStream();
    current=baselineStats(lattice,geometry,converter);
    if(step)cumulative+=T(.5)*((previous.lowOut+previous.highOut)
                              +(current.lowOut+current.highOut))*dt;
    const T residual=current.mass-initial.mass+cumulative;
    const T mach=current.maxU/std::sqrt(T(1)/3);
    maxMach=std::max(maxMach,mach);minRho=std::min(minRho,current.rhoMin);
    maxRho=std::max(maxRho,current.rhoMax);
    maxResidual=std::max(maxResidual,std::abs(residual/initial.mass));
    if(firstMach<0&&mach>.01)firstMach=step;
    if(firstRho<0&&(current.rhoMin<.99||current.rhoMax>1.01))firstRho=step;
    if(firstNonfinite<0&&!current.finite)firstNonfinite=step;
    csv<<step<<','<<step*dt<<','<<current.mass<<','
       <<(current.mass-initial.mass)/initial.mass<<','<<current.lowOut<<','
       <<current.highOut<<','<<(current.lowOut+current.highOut)<<','<<cumulative
       <<','<<residual<<','<<residual/initial.mass<<','<<current.rhoMin<<','
       <<current.rhoMax<<','<<current.maxU<<','<<converter.getPhysVelocity(current.maxU)
       <<','<<mach<<','<<current.finite<<'\n';
    previous=current;if(!current.finite)break;
  }
  const T finalResidual=current.mass-initial.mass+cumulative;
  const bool nonzero=std::abs(current.lowOut)+std::abs(current.highOut)>0;
  const bool pass=current.finite&&firstMach<0&&firstRho<0&&nonzero
                 &&maxResidual<=1e-5;
  std::ofstream result(outDir/"result.txt");result<<std::setprecision(17)<<std::boolalpha
    <<"run_id="<<runId<<"\nPASS="<<pass<<"\nsteps_completed=650\n"
    <<"delta_rho="<<imposedDeltaRho<<"\nperiodicity=x,z\nopen_direction=y\n"
    <<"domain_nodes="<<baselineN<<','<<baselineN<<','<<baselineN<<"\n"
    <<"max_Mach="<<maxMach<<"\nfirst_Mach_over_0.01_step="<<firstMach
    <<"\nrho_range="<<minRho<<','<<maxRho
    <<"\nfirst_rho_outside_0.99_1.01_step="<<firstRho
    <<"\nfirst_nonfinite_step="<<firstNonfinite
    <<"\nfinal_low_outward_flux_kg_s="<<current.lowOut
    <<"\nfinal_high_outward_flux_kg_s="<<current.highOut
    <<"\nfinal_net_outward_flux_kg_s="<<(current.lowOut+current.highOut)
    <<"\ninitial_mass_kg="<<initial.mass<<"\nfinal_mass_kg="<<current.mass
    <<"\nfinal_relative_mass_balance_residual="<<finalResidual/initial.mass
    <<"\nmax_abs_relative_mass_balance_residual="<<maxResidual
    <<"\nexit_code="<<(pass?0:3)<<"\nexit_reason="
    <<(pass?"all_frozen_nonzero_flow_checks_passed":"one_or_more_frozen_checks_failed")
    <<'\n';
  std::ofstream record(outDir/"run_record.txt");record
    <<"run_id="<<runId<<"\ncommand=./explicit_localpressure_nonzero_baseline\n"
    <<"source=explicit_localpressure_nonzero_baseline.cpp\nsteps=650\n"
    <<"acceptance=maxMach<=0.01,rho in [0.99,1.01],finite,nonzero flow,"
      "max_abs_relative_mass_residual<=1e-5\n"
    <<"exit_code="<<(pass?0:3)<<'\n';
  return pass?0:3;
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)return 2;
  return runLocalPressureNonzero();
}
