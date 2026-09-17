#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <map>

constexpr T zeroMachTolerance=1e-12;
constexpr T zeroRhoTolerance=1e-12;
constexpr T zeroMassResidualTolerance=1e-12;
constexpr T movingMassResidualLimit=1e-3;
constexpr T z1DeltaRho=2e-6;
constexpr int z1N=16;
constexpr T z1Length=(z1N-1)*dx;
constexpr T sepLy=280e-9;
constexpr int sepNy=56;
constexpr T sepMovingY0=20e-9,sepMovingY1=260e-9;

int zhWrapX(int ix)
{
  int wrapped=ix%48;return wrapped<0?wrapped+48:wrapped;
}

template<class G>
std::array<int,2> zhMarkPeriodicPressureIntersections(G& geometry)
{
  std::array<int,2> marked{};
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    const int m=g.getMaterial(p);if(m!=4&&m!=5)return;
    bool touches=false;
    for(int i=1;i<D::q;++i){
      auto n=p+descriptors::c<D>(i);
      if(n[0]<0||n[0]>=48)n[0]=zhWrapX(n[0]);
      const int sm=g.getMaterial(n);touches|=sm==2||sm==3;
    }
    if(touches){g.set(p,m==4?6:7);++marked[m==4?0:1];}
  });
  geometry.communicate();return marked;
}

template<class L,class G>
std::array<int,4> zhUpdatePeriodicLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,recovered=0,falseSolid=0;
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p){
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i){
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
    }
    if(!isFluidMaterial(g.getMaterial(p)))return;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i){
      const auto c=descriptors::c<D>(i);auto raw=p+c,mapped=raw;
      const bool crosses=raw[0]<0||raw[0]>=48;
      if(crosses)mapped[0]=zhWrapX(raw[0]);
      const int rawM=g.getMaterial(raw),sm=crosses?g.getMaterial(mapped):rawM;
      if(crosses&&(sm==2||sm==3)&&rawM!=2&&rawM!=3)++recovered;
      if(crosses&&(rawM==2||rawM==3)&&sm!=2&&sm!=3)++falseSolid;
      if(sm!=2&&sm!=3)continue;
      T q=.5,velocityCoefficient=0;
      if(sm==3){
        T lo=0,hi=1;
        for(int k=0;k<50;++k){
          const T a=(lo+hi)/2;
          T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;
          if(punch(x,r[2]+a*dx*c[2],h))hi=a;else lo=a;
        }
        q=(lo+hi)/2;velocityCoefficient=c[2]*uWall*dt/dx;
      }
      if(!(q>=0&&q<=1))++invalid;
      else{
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,
                                                                       velocityCoefficient);
        ++active;
      }
    }
  });
  lattice.communicate();return{active,invalid,recovered,falseSolid};
}

template<class B,class G>
void zhWriteCell(std::ofstream& out,B& block,G& g,int step,const char* name,
                 LatticeR<3> p)
{
  auto cell=block.get(p);T u[3]{};cell.computeU(u);
  out<<step<<','<<name<<','<<p[0]<<','<<p[1]<<','<<p[2]<<','<<g.getMaterial(p)
     <<','<<cell.computeRho()<<','<<u[0]<<','<<u[1]<<','<<u[2]<<','
     <<std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2])/std::sqrt(T(1)/3);
  for(int i=0;i<D::q;++i)out<<','<<cell[i];
  out<<'\n';
}

void zhWriteCellHeader(std::ofstream& out)
{
  out<<"step,cell_name,ix,iy,iz,material,rho,ux,uy,uz,Mach";
  for(int i=0;i<D::q;++i)out<<",f"<<i;
  out<<'\n';
}

template<class L,class G>
void setAllZouHePressure(L& lattice,G& geometry,SuperIndicatorFfromIndicatorF3D<T>& outside,
                        bool hasIntersectionLabels)
{
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
  if(hasIntersectionLabels){
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(6),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(7),geometry.getMaterialIndicator(1),outside);
  }
}

int runOriginalZouHe(bool moving,bool preserveIntersectionPatch)
{
  const std::string label=moving?(preserveIntersectionPatch?"Cpatch":"Cnopatch"):"Z0";
  const std::string runId=moving
    ?(preserveIntersectionPatch?"zouhe_pressure_Cpatch_650_20260908":
                                "zouhe_pressure_Cnopatch_650_20260908")
    :"zouhe_pressure_Z0_zero_fixed_650_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"Refusing to overwrite "<<outDir<<'\n';return 2;}
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  try{
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});
    geometry.communicate();
    std::array<int,2> marked{};
    if(preserveIntersectionPatch)marked=zhMarkPeriodicPressureIntersections(geometry);
    const auto initialCounts=materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    setAllZouHePressure(lattice,geometry,outside,preserveIntersectionPatch);
    dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
    for(int m:{1,4,5,6,7})lattice.iniEquilibrium(geometry,m,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();
    for(int m:{4,5,6,7})lattice.defineRho(geometry,m,one);
    lattice.communicate();

    std::ofstream csv(outDir/"diagnostics.csv");csv<<std::setprecision(17)
      <<"step,time_s,h_nm,wall_speed_m_s,active_links,invalid_links,"
        "periodic_links_recovered,false_periodic_solid_links,fluid_nodes,mass_kg,"
        "mass_relative_change,low_outward_flux_kg_s,high_outward_flux_kg_s,"
        "net_outward_flux_kg_s,cumulative_outward_mass_kg,mass_balance_residual_kg,"
        "relative_mass_balance_residual,rho_min,rho_max,max_speed_m_s,max_Mach,"
        "max_ix,max_iy,max_iz,max_material,finite,material_conversions\n";
    std::ofstream hist(outDir/"tracked_cells.csv");hist<<std::setprecision(17);zhWriteCellHeader(hist);
    auto& block=lattice.getBlock(0);
    Stats initial=computeStats(lattice,geometry,converter),previous=initial,current=initial;
    T cumulative=0,maxMach=0,minRho=1e300,maxRho=-1e300,maxResidual=0,globalMaxU=0;
    int firstMach=-1,firstRho=-1,firstNonfinite=-1,maxInvalid=0,maxFalse=0;
    int globalIx=0,globalIy=0,globalIz=0,globalMaterial=0;
    for(int step=0;step<=650;++step){
      const auto links=zhUpdatePeriodicLinks(lattice,geometry,hAt(step,moving),wallSpeed(step,moving));
      maxInvalid=std::max(maxInvalid,links[1]);maxFalse=std::max(maxFalse,links[3]);
      if(step)lattice.collideAndStream();
      current=computeStats(lattice,geometry,converter);
      if(step)cumulative+=T(.5)*((previous.lowOut+previous.highOut)
                                +(current.lowOut+current.highOut))*dt;
      const T residual=current.mass-initial.mass+cumulative;
      const T mach=current.maxU/std::sqrt(T(1)/3);
      maxMach=std::max(maxMach,mach);minRho=std::min(minRho,current.rhoMin);
      maxRho=std::max(maxRho,current.rhoMax);
      maxResidual=std::max(maxResidual,std::abs(residual/initial.mass));
      if(current.maxU>globalMaxU){globalMaxU=current.maxU;globalIx=current.maxIx;
        globalIy=current.maxIy;globalIz=current.maxIz;globalMaterial=current.maxMaterial;}
      if(firstMach<0&&mach>machLimit)firstMach=step;
      if(firstRho<0&&(current.rhoMin<rhoMinLimit||current.rhoMax>rhoMaxLimit))firstRho=step;
      if(firstNonfinite<0&&!current.finite)firstNonfinite=step;
      csv<<step<<','<<step*dt<<','<<hAt(step,moving)*1e9<<','<<wallSpeed(step,moving)
         <<','<<links[0]<<','<<links[1]<<','<<links[2]<<','<<links[3]<<','
         <<current.fluidNodes<<','<<current.mass<<','<<(current.mass-initial.mass)/initial.mass
         <<','<<current.lowOut<<','<<current.highOut<<','<<(current.lowOut+current.highOut)
         <<','<<cumulative<<','<<residual<<','<<residual/initial.mass<<','
         <<current.rhoMin<<','<<current.rhoMax<<','<<converter.getPhysVelocity(current.maxU)
         <<','<<mach<<','<<current.maxIx<<','<<current.maxIy<<','<<current.maxIz<<','
         <<current.maxMaterial<<','<<current.finite<<",0\n";
      zhWriteCell(hist,block,g,step,"cell_0_0_13",{0,0,13});
      zhWriteCell(hist,block,g,step,"cell_0_0_14",{0,0,14});
      zhWriteCell(hist,block,g,step,"cell_0_0_15",{0,0,15});
      zhWriteCell(hist,block,g,step,"cell_0_1_15",{0,1,15});
      previous=current;if(!current.finite)break;
    }
    const T finalResidual=current.mass-initial.mass+cumulative;
    const bool materialUnchanged=materialCounts(geometry)==initialCounts;
    const bool zeroPass=!moving&&current.finite&&maxMach<=zeroMachTolerance
      &&std::max(std::abs(minRho-1),std::abs(maxRho-1))<=zeroRhoTolerance
      &&maxResidual<=zeroMassResidualTolerance&&maxInvalid==0&&maxFalse==0
      &&materialUnchanged;
    const bool movingPass=moving&&current.finite&&firstMach<0&&firstRho<0
      &&maxResidual<=movingMassResidualLimit&&cumulative>0&&maxInvalid==0&&maxFalse==0
      &&materialUnchanged;
    const bool pass=zeroPass||movingPass;
    std::ofstream result(outDir/"result.txt");result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\ncase="<<label<<"\nPASS="<<pass
      <<"\npressure_boundary=ZouHePressure\nintersection_patch_preserved="
      <<preserveIntersectionPatch<<"\nsteps_completed="<<(firstNonfinite<0?650:firstNonfinite)
      <<"\nintersection_low_cells="<<marked[0]<<"\nintersection_high_cells="<<marked[1]
      <<"\nmax_Mach="<<maxMach<<"\nfirst_Mach_over_0.05_step="<<firstMach
      <<"\nrho_range="<<minRho<<','<<maxRho
      <<"\nfirst_rho_outside_0.8_1.2_step="<<firstRho
      <<"\nfirst_nonfinite_step="<<firstNonfinite
      <<"\nmax_speed_m_s="<<converter.getPhysVelocity(globalMaxU)
      <<"\nmax_speed_location="<<globalIx<<','<<globalIy<<','<<globalIz
      <<"\nmax_speed_material="<<globalMaterial
      <<"\ninitial_mass_kg="<<initial.mass<<"\nfinal_mass_kg="<<current.mass
      <<"\nlow_outward_flux_final_kg_s="<<current.lowOut
      <<"\nhigh_outward_flux_final_kg_s="<<current.highOut
      <<"\ncumulative_outward_mass_kg="<<cumulative
      <<"\nfinal_relative_mass_balance_residual="<<finalResidual/initial.mass
      <<"\nmax_abs_relative_mass_balance_residual="<<maxResidual
      <<"\nmax_invalid_links="<<maxInvalid<<"\nmax_false_periodic_solid_links="<<maxFalse
      <<"\nmaterial_conversions=0\nmaterial_field_unchanged="<<materialUnchanged
      <<"\nexit_code="<<(pass?0:3)<<'\n';
    std::ofstream record(outDir/"run_record.txt");record
      <<"run_id="<<runId<<"\ncommand=./explicit_piston_zouhe_pressure_candidate "<<label
      <<"\nsteps=650\nmaterial_conversion_enabled=false\nexit_code="<<(pass?0:3)<<'\n';
    return pass?0:3;
  }catch(const std::exception& e){
    std::ofstream failure(outDir/"failure.txt");failure<<e.what()<<'\n';
    std::cerr<<e.what()<<'\n';return 4;
  }
}

class Z1Outside final : public IndicatorF3D<T> {
public:
  Z1Outside(){this->_myMin={-1e9,-1e9,-1e9};this->_myMax={1e9,1e9,1e9};
    this->getName()="Z1Outside";}
  bool operator()(bool out[1],const T r[3]) override
  {
    const T eps=dx*1e-6;out[0]=r[1]<dx/2-eps||r[1]>z1Length+dx/2+eps;return true;
  }
};

class Z1Rho final : public AnalyticalF3D<T,T> {
public:
  Z1Rho():AnalyticalF3D<T,T>(1){this->getName()="Z1Rho";}
  bool operator()(T out[1],const T r[3]) override
  {out[0]=1+z1DeltaRho/T(2)-z1DeltaRho*r[1]/z1Length;return true;}
};

struct Z1Stats {T mass=0,rhoMin=1e300,rhoMax=-1e300,maxU=0,lowOut=0,highOut=0;bool finite=true;};

template<class L,class G>
Z1Stats computeZ1(L& lattice,G& geometry,const UnitConverter<T,D>& converter)
{
  Z1Stats s;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
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
  });return s;
}

int runZ1(bool useZouHe)
{
  const std::string runId=useZouHe
    ? "zouhe_pressure_Z1_nonzero_fixed_650_20260908"
    : "localpressure_fixed_nonzero_profile_650_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"Refusing to overwrite\n";return 2;}
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  IndicatorCuboid3D<T> domain({z1Length,z1Length,z1Length},{dx/2,dx/2,dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,true});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,p[1]==0?4:(p[1]==z1N-1?5:1));});
  geometry.communicate();SuperIndicatorFfromIndicatorF3D<T> outside(new Z1Outside,geometry);
  UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
  SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);dynamics::set<BGKdynamics>(lattice,geometry,1);
  if(useZouHe){
    setAllZouHePressure(lattice,geometry,outside,false);
  }else{
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
  }
  Z1Rho rhoProfile;AnalyticalConst3D<T,T> zero(0,0,0);
  lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),rhoProfile,zero);
  for(int m:{1,4,5})lattice.iniEquilibrium(geometry,m,rhoProfile,zero);
  lattice.initialize();AnalyticalConst3D<T,T> rhoLow(1+z1DeltaRho/T(2)),rhoHigh(1-z1DeltaRho/T(2));
  lattice.defineRho(geometry,4,rhoLow);lattice.defineRho(geometry,5,rhoHigh);lattice.communicate();
  std::ofstream csv(outDir/"diagnostics.csv");csv<<std::setprecision(17)
    <<"step,time_s,mass_kg,mass_relative_change,low_outward_flux_kg_s,"
      "high_outward_flux_kg_s,net_outward_flux_kg_s,cumulative_outward_mass_kg,"
      "mass_balance_residual_kg,relative_mass_balance_residual,rho_min,rho_max,"
      "max_speed_lattice,max_speed_m_s,max_Mach,finite\n";
  Z1Stats initial=computeZ1(lattice,geometry,converter),previous=initial,current=initial;
  T cumulative=0,maxMach=0,minRho=1e300,maxRho=-1e300,maxResidual=0;
  int firstMach=-1,firstRho=-1,firstNonfinite=-1;
  for(int step=0;step<=650;++step){
    if(step)lattice.collideAndStream();
    current=computeZ1(lattice,geometry,converter);
    if(step)cumulative+=T(.5)*((previous.lowOut+previous.highOut)
                              +(current.lowOut+current.highOut))*dt;
    const T residual=current.mass-initial.mass+cumulative;
    const T mach=current.maxU/std::sqrt(T(1)/3);
    maxMach=std::max(maxMach,mach);minRho=std::min(minRho,current.rhoMin);
    maxRho=std::max(maxRho,current.rhoMax);maxResidual=std::max(maxResidual,std::abs(residual/initial.mass));
    if(firstMach<0&&mach>.01)firstMach=step;
    if(firstRho<0&&(current.rhoMin<.99||current.rhoMax>1.01))firstRho=step;
    if(firstNonfinite<0&&!current.finite)firstNonfinite=step;
    csv<<step<<','<<step*dt<<','<<current.mass<<','<<(current.mass-initial.mass)/initial.mass
       <<','<<current.lowOut<<','<<current.highOut<<','<<(current.lowOut+current.highOut)
       <<','<<cumulative<<','<<residual<<','<<residual/initial.mass<<','<<current.rhoMin
       <<','<<current.rhoMax<<','<<current.maxU<<','<<converter.getPhysVelocity(current.maxU)
       <<','<<mach<<','<<current.finite<<'\n';previous=current;if(!current.finite)break;
  }
  std::ofstream profile(outDir/"velocity_profile_final.csv");profile<<std::setprecision(17)
    <<"iy,y_nm,mean_rho,mean_uy_lattice,mean_uy_m_s\n";
  auto& block=lattice.getBlock(0);
  for(int iy=0;iy<z1N;++iy){
    T sr=0,su=0;int n=0;
    for(int ix=0;ix<z1N;++ix)for(int iz=0;iz<z1N;++iz){
      auto cell=block.get({ix,iy,iz});T u[3]{};cell.computeU(u);sr+=cell.computeRho();su+=u[1];++n;
    }
    profile<<iy<<','<<(iy*dx+dx/2)*1e9<<','<<sr/n<<','<<su/n<<','
           <<converter.getPhysVelocity(su/n)<<'\n';
  }
  const T finalResidual=current.mass-initial.mass+cumulative;
  const bool nonzero=std::abs(current.lowOut)+std::abs(current.highOut)>0;
  const bool pass=current.finite&&firstMach<0&&firstRho<0&&nonzero&&maxResidual<=1e-5;
  std::ofstream result(outDir/"result.txt");result<<std::setprecision(17)<<std::boolalpha
    <<"run_id="<<runId<<"\nPASS="<<pass<<"\npressure_boundary="
    <<(useZouHe?"ZouHePressure":"LocalPressure")<<"\nsteps_completed=650"
    <<"\ndelta_rho="<<z1DeltaRho<<"\nmax_Mach="<<maxMach
    <<"\nfirst_Mach_over_0.01_step="<<firstMach<<"\nrho_range="<<minRho<<','<<maxRho
    <<"\nfirst_rho_outside_0.99_1.01_step="<<firstRho
    <<"\nfirst_nonfinite_step="<<firstNonfinite
    <<"\nfinal_low_outward_flux_kg_s="<<current.lowOut
    <<"\nfinal_high_outward_flux_kg_s="<<current.highOut
    <<"\nfinal_net_outward_flux_kg_s="<<(current.lowOut+current.highOut)
    <<"\ninitial_mass_kg="<<initial.mass<<"\nfinal_mass_kg="<<current.mass
    <<"\nfinal_relative_mass_balance_residual="<<finalResidual/initial.mass
    <<"\nmax_abs_relative_mass_balance_residual="<<maxResidual
    <<"\nexit_code="<<(pass?0:3)<<'\n';
  std::ofstream record(outDir/"run_record.txt");record
    <<"run_id="<<runId<<"\ncommand=./explicit_piston_zouhe_pressure_candidate "
    <<(useZouHe?"Z1":"Z1LP")<<'\n'
    <<"steps=650\nexit_code="<<(pass?0:3)<<'\n';return pass?0:3;
}

class SepOutside final : public IndicatorF3D<T> {
public:
  SepOutside(){this->_myMin={-1e9,-1e9,-1e9};this->_myMax={1e9,1e9,1e9};
    this->getName()="SepOutside";}
  bool operator()(bool out[1],const T r[3]) override
  {
    const T eps=dx*1e-6;out[0]=r[1]<dx/2-eps||r[1]>sepLy-dx/2+eps
      ||r[2]<-dx/2-eps||r[2]>192.5e-9+eps;return true;
  }
};

bool sepMovingFootprint(T y){return y>=sepMovingY0&&y<sepMovingY1;}
bool sepPunch(T x,T y,T z,T h){return sepMovingFootprint(y)&&punch(x,z,h);}
int sepMaterialAt(const Vector<T,3>& r)
{
  if(r[2]<0)return 2;
  if(punch(r[0],r[2],75e-9))return sepMovingFootprint(r[1])?3:8;
  if(r[1]<dx)return 4;
  if(r[1]>sepLy-dx)return 5;
  return 1;
}
bool sepFluid(int m){return m==1||m==4||m==5||m==6||m==7;}

template<class G>
std::array<int,2> markSepIntersections(G& geometry)
{
  std::array<int,2> marked{};auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    const int m=g.getMaterial(p);if(m!=4&&m!=5)return;bool touches=false;
    for(int i=1;i<D::q;++i){auto n=p+descriptors::c<D>(i);if(n[0]<0||n[0]>=48)n[0]=zhWrapX(n[0]);
      const int sm=g.getMaterial(n);touches|=sm==2||sm==3||sm==8;}
    if(touches){g.set(p,m==4?6:7);++marked[m==4?0:1];}
  });geometry.communicate();return marked;
}

struct SepLinkCount {int active=0,moving=0,invalid=0,dual=0,minDistance=100000;};
template<class L,class G>
SepLinkCount updateSepLinks(L& lattice,G& geometry,T h,T uWall)
{
  SepLinkCount s;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p){
    auto cell=block.get(p);for(int i=0;i<D::q;++i){
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);}
    const int m=g.getMaterial(p);if(!sepFluid(m))return;bool ownsMoving=false;const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i){const auto c=descriptors::c<D>(i);auto n=p+c;
      if(n[0]<0||n[0]>=48)n[0]=zhWrapX(n[0]);
      const int sm=g.getMaterial(n);
      if(sm!=2&&sm!=3&&sm!=8)continue;
      T q=.5,vc=0;
      if(sm==3){T lo=0,hi=1;for(int k=0;k<50;++k){const T a=(lo+hi)/2;
          T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;
          if(sepPunch(x,r[1]+a*dx*c[1],r[2]+a*dx*c[2],h))hi=a;else lo=a;}
        q=(lo+hi)/2;vc=c[2]*uWall*dt/dx;ownsMoving=true;++s.moving;}
      if(!(q>=0&&q<=1))++s.invalid;else{cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,vc);++s.active;}}
    if(ownsMoving){s.minDistance=std::min(s.minDistance,std::min(p[1],sepNy-1-p[1]));
      if(m==4||m==5||m==6||m==7)++s.dual;}
  });lattice.communicate();return s;
}

struct SepStats {T mass=0,rhoMin=1e300,rhoMax=-1e300,maxU=0,lowOut=0,highOut=0;
  int ix=0,iy=0,iz=0,material=0;bool finite=true;};
template<class L,class G>
SepStats computeSep(L& lattice,G& geometry,const UnitConverter<T,D>& converter)
{
  SepStats s;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){const int m=g.getMaterial(p);if(!sepFluid(m))return;
    auto cell=block.get(p);T u[3]{};cell.computeU(u);const T rho=cell.computeRho();
    const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);s.mass+=rho*rhoPhys*dx*dx*dx;
    s.rhoMin=std::min(s.rhoMin,rho);s.rhoMax=std::max(s.rhoMax,rho);
    if(speed>s.maxU){s.maxU=speed;s.ix=p[0];s.iy=p[1];s.iz=p[2];s.material=m;}
    s.finite&=std::isfinite(rho)&&std::isfinite(speed);for(int i=0;i<D::q;++i)s.finite&=std::isfinite(cell[i]);
    const T uy=converter.getPhysVelocity(u[1]);if(m==4||m==6)s.lowOut-=rho*rhoPhys*uy*dx*dx;
    if(m==5||m==7)s.highOut+=rho*rhoPhys*uy*dx*dx;});return s;
}

int runSeparatedZouHe()
{
  const std::string runId="zouhe_pressure_separated_moving_650_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"Refusing to overwrite\n";return 2;}
  std::filesystem::create_directories(outDir);singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  IndicatorCuboid3D<T> domain({Lx-dx,sepLy-dx,195e-9},{dx/2,dx/2,-dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  auto& g=geometry.getBlockGeometry(0);g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,sepMaterialAt(g.getPhysR(p)));});
  geometry.communicate();const auto marked=markSepIntersections(geometry);
  std::array<long long,9> initialCounts{};g.forCoreSpatialLocations([&](LatticeR<3> p){const int m=g.getMaterial(p);if(m>=0&&m<9)++initialCounts[m];});
  SuperIndicatorFfromIndicatorF3D<T> outside(new SepOutside,geometry);
  UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
  dynamics::set<BGKdynamics>(lattice,geometry,1);setAllZouHePressure(lattice,geometry,outside,true);
  dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);dynamics::set<NoDynamics>(lattice,geometry,8);
  AnalyticalConst3D<T,T> one(1),zero(0,0,0);lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
  for(int m:{1,4,5,6,7})lattice.iniEquilibrium(geometry,m,one,zero);
  lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});lattice.initialize();
  for(int m:{4,5,6,7})lattice.defineRho(geometry,m,one);
  lattice.communicate();
  std::ofstream csv(outDir/"diagnostics.csv");csv<<std::setprecision(17)
    <<"step,time_s,h_nm,wall_speed_m_s,active_links,moving_links,invalid_links,pressure_moving_dual,"
      "min_pressure_distance,mass_kg,mass_relative_change,low_outward_flux_kg_s,high_outward_flux_kg_s,"
      "net_outward_flux_kg_s,cumulative_outward_mass_kg,mass_balance_residual_kg,relative_mass_balance_residual,"
      "rho_min,rho_max,max_speed_m_s,max_Mach,max_ix,max_iy,max_iz,max_material,finite,material_conversions\n";
  std::ofstream hist(outDir/"tracked_cells.csv");hist<<std::setprecision(17);zhWriteCellHeader(hist);
  auto& block=lattice.getBlock(0);SepStats initial=computeSep(lattice,geometry,converter),previous=initial,current=initial;
  T cumulative=0,maxMach=0,minRho=1e300,maxRho=-1e300,maxResidual=0,globalU=0;
  int firstMach=-1,firstRho=-1,firstNonfinite=-1,maxInvalid=0,maxDual=0,minDistance=100000;
  int gx=0,gy=0,gz=0,gm=0;
  for(int step=0;step<=650;++step){const auto links=updateSepLinks(lattice,geometry,hAt(step,true),wallSpeed(step,true));
    maxInvalid=std::max(maxInvalid,links.invalid);maxDual=std::max(maxDual,links.dual);minDistance=std::min(minDistance,links.minDistance);
    if(step)lattice.collideAndStream();
    current=computeSep(lattice,geometry,converter);
    if(step)cumulative+=T(.5)*((previous.lowOut+previous.highOut)+(current.lowOut+current.highOut))*dt;
    const T residual=current.mass-initial.mass+cumulative,mach=current.maxU/std::sqrt(T(1)/3);
    maxMach=std::max(maxMach,mach);minRho=std::min(minRho,current.rhoMin);maxRho=std::max(maxRho,current.rhoMax);
    maxResidual=std::max(maxResidual,std::abs(residual/initial.mass));if(current.maxU>globalU){globalU=current.maxU;
      gx=current.ix;gy=current.iy;gz=current.iz;gm=current.material;}if(firstMach<0&&mach>machLimit)firstMach=step;
    if(firstRho<0&&(current.rhoMin<rhoMinLimit||current.rhoMax>rhoMaxLimit))firstRho=step;
    if(firstNonfinite<0&&!current.finite)firstNonfinite=step;
    csv<<step<<','<<step*dt<<','<<hAt(step,true)*1e9<<','<<wallSpeed(step,true)<<','<<links.active<<','<<links.moving
       <<','<<links.invalid<<','<<links.dual<<','<<links.minDistance<<','<<current.mass<<','<<(current.mass-initial.mass)/initial.mass
       <<','<<current.lowOut<<','<<current.highOut<<','<<(current.lowOut+current.highOut)<<','<<cumulative<<','<<residual<<','
       <<residual/initial.mass<<','<<current.rhoMin<<','<<current.rhoMax<<','<<converter.getPhysVelocity(current.maxU)<<','<<mach
       <<','<<current.ix<<','<<current.iy<<','<<current.iz<<','<<current.material<<','<<current.finite<<",0\n";
    zhWriteCell(hist,block,g,step,"pressure_0_0_13",{0,0,13});zhWriteCell(hist,block,g,step,"buffer_0_1_13",{0,1,13});
    zhWriteCell(hist,block,g,step,"buffer_0_2_13",{0,2,13});zhWriteCell(hist,block,g,step,"moving_link_0_3_13",{0,3,13});
    previous=current;if(!current.finite)break;}
  std::array<long long,9> finalCounts{};g.forCoreSpatialLocations([&](LatticeR<3> p){const int m=g.getMaterial(p);if(m>=0&&m<9)++finalCounts[m];});
  const bool unchanged=finalCounts==initialCounts;const bool pass=current.finite&&firstMach<0&&firstRho<0&&maxInvalid==0
    &&maxDual==0&&maxResidual<=movingMassResidualLimit&&cumulative>0&&unchanged;
  std::ofstream result(outDir/"result.txt");result<<std::setprecision(17)<<std::boolalpha
    <<"run_id="<<runId<<"\nPASS="<<pass<<"\npressure_boundary=ZouHePressure\nsteps_completed="<<(firstNonfinite<0?650:firstNonfinite)
    <<"\nintersection_low_cells="<<marked[0]<<"\nintersection_high_cells="<<marked[1]
    <<"\nmin_lattice_index_distance_pressure_to_moving_link="<<minDistance<<"\npressure_moving_dual_cells_max="<<maxDual
    <<"\nmax_Mach="<<maxMach<<"\nfirst_Mach_over_0.05_step="<<firstMach<<"\nrho_range="<<minRho<<','<<maxRho
    <<"\nfirst_rho_outside_0.8_1.2_step="<<firstRho<<"\nfirst_nonfinite_step="<<firstNonfinite
    <<"\nmax_speed_m_s="<<converter.getPhysVelocity(globalU)<<"\nmax_speed_location="<<gx<<','<<gy<<','<<gz
    <<"\nmax_speed_material="<<gm<<"\ninitial_mass_kg="<<initial.mass<<"\nfinal_mass_kg="<<current.mass
    <<"\nfinal_low_outward_flux_kg_s="<<current.lowOut<<"\nfinal_high_outward_flux_kg_s="<<current.highOut
    <<"\ncumulative_outward_mass_kg="<<cumulative<<"\nmax_abs_relative_mass_balance_residual="<<maxResidual
    <<"\nmax_invalid_links="<<maxInvalid<<"\nmaterial_conversions=0\nmaterial_field_unchanged="<<unchanged
    <<"\nexit_code="<<(pass?0:3)<<'\n';
  std::ofstream record(outDir/"run_record.txt");record<<"run_id="<<runId
    <<"\ncommand=./explicit_piston_zouhe_pressure_candidate S\nsteps=650\nexit_code="<<(pass?0:3)<<'\n';return pass?0:3;
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1||argc!=2)return 2;
  const std::string mode=argv[1];
  if(mode=="Z0")return runOriginalZouHe(false,true);
  if(mode=="Z1")return runZ1(true);
  if(mode=="Z1LP")return runZ1(false);
  if(mode=="S")return runSeparatedZouHe();
  if(mode=="Cpatch")return runOriginalZouHe(true,true);
  if(mode=="Cnopatch")return runOriginalZouHe(true,false);
  return 2;
}
