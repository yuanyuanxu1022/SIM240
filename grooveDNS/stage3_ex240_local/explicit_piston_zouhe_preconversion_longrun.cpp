#define main boundary_intersection_fix_embedded_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <sstream>

constexpr int lrLongSteps=2000;
constexpr int lrRegressionSteps=650;
constexpr T lrMassResidualLimit=1e-3;

int lrWrapX(int ix)
{
  const int wrapped=ix%48;return wrapped<0?wrapped+48:wrapped;
}

template<class L,class G>
std::array<int,4> lrUpdatePeriodicLinks(L& lattice,G& geometry,T h,T uWall)
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
      if(crosses)mapped[0]=lrWrapX(raw[0]);
      const int rawMaterial=g.getMaterial(raw);
      const int solidMaterial=crosses?g.getMaterial(mapped):rawMaterial;
      if(crosses&&(solidMaterial==2||solidMaterial==3)
         &&rawMaterial!=2&&rawMaterial!=3)++recovered;
      if(crosses&&(rawMaterial==2||rawMaterial==3)
         &&solidMaterial!=2&&solidMaterial!=3)++falseSolid;
      if(solidMaterial!=2&&solidMaterial!=3)continue;
      T q=.5,velocityCoefficient=0;
      if(solidMaterial==3){
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
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(
          i,velocityCoefficient);
        ++active;
      }
    }
  });
  lattice.communicate();return{active,invalid,recovered,falseSolid};
}

template<class L,class G>
void lrSetAllZouHePressure(L& lattice,G& geometry,
                           SuperIndicatorFfromIndicatorF3D<T>& outside)
{
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
}

struct LRStats {
  long long fluidNodes=0;
  T mass=0,rhoMin=1e300,rhoMax=-1e300,maxULattice=0;
  T maxUx=0,maxUy=0,maxUz=0,lowOut=0,highOut=0;
  int maxIx=0,maxIy=0,maxIz=0,maxMaterial=0;
  bool finite=true;
};

template<class L,class G>
LRStats lrComputeStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter)
{
  LRStats s;
  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    const int material=g.getMaterial(p);
    if(!isFluidMaterial(material))return;
    auto cell=block.get(p);
    T u[3]{};cell.computeU(u);
    const T rho=cell.computeRho();
    const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
    ++s.fluidNodes;s.mass+=rho*rhoPhys*dx*dx*dx;
    s.rhoMin=std::min(s.rhoMin,rho);s.rhoMax=std::max(s.rhoMax,rho);
    if(speed>s.maxULattice){
      s.maxULattice=speed;s.maxUx=u[0];s.maxUy=u[1];s.maxUz=u[2];
      s.maxIx=p[0];s.maxIy=p[1];s.maxIz=p[2];s.maxMaterial=material;
    }
    s.finite&=std::isfinite(rho)&&std::isfinite(speed);
    for(int i=0;i<D::q;++i)s.finite&=std::isfinite(cell[i]);
    const T uyPhys=converter.getPhysVelocity(u[1]);
    if(material==4)s.lowOut-=rho*rhoPhys*uyPhys*dx*dx;
    if(material==5)s.highOut+=rho*rhoPhys*uyPhys*dx*dx;
  });
  return s;
}

template<class G>
long long lrMaterialChangeCount(G& geometry)
{
  long long changed=0;
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    if(g.getMaterial(p)!=materialAt(g.getPhysR(p)))++changed;
  });
  return changed;
}

template<class G>
std::array<long long,4> lrPressureAudit(G& geometry,
                                        SuperIndicatorFfromIndicatorF3D<T>& outside)
{
  std::array<long long,4> audit{};
  auto fluid=geometry.getMaterialIndicator(1);
  auto& g=geometry.getBlockGeometry(0);
  auto& fluidBlock=fluid->getBlockIndicatorF(0);
  auto& outsideBlock=outside.getBlockIndicatorF(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    const int m=g.getMaterial(p);if(m!=4&&m!=5)return;
    ++audit[0];
    const auto [type,normal]=computeBoundaryTypeAndNormal(fluidBlock,outsideBlock,p);
    const Vector<int,3> expected{0,m==4?-1:1,0};
    if(type==DiscreteNormalType::Flat&&normal==expected)++audit[1];
    else if(normal==Vector<int,3>{0,0,0})++audit[2];
    else ++audit[3];
  });
  return audit;
}

template<class B,class G>
void lrWriteWatch(std::ofstream& out,B& block,G& g,int step,const char* name,
                  LatticeR<3> p)
{
  auto cell=block.get(p);T u[3]{};cell.computeU(u);
  const T mach=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2])/std::sqrt(T(1)/3);
  out<<step<<','<<name<<','<<p[0]<<','<<p[1]<<','<<p[2]<<','<<g.getMaterial(p)
     <<','<<cell[3]<<','<<cell[8]<<','<<cell[17]<<','<<cell.computeRho()
     <<','<<u[0]<<','<<u[1]<<','<<u[2]<<','<<mach<<'\n';
}

int lrRun(bool regression)
{
  const int totalSteps=regression?lrRegressionSteps:lrLongSteps;
  const std::string runId=regression
    ? "zouhe_preconversion_nopatch_regression650_20260908"
    : "zouhe_preconversion_longrun2000_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){
    std::cerr<<"Refusing to overwrite "<<outDir<<'\n';return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log");log<<std::setprecision(17)<<std::boolalpha;
  try{
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});
    geometry.communicate();
    const auto initialCounts=materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    const auto pressureAudit=lrPressureAudit(geometry,outside);
    if(pressureAudit!=std::array<long long,4>{2400,2400,0,0})
      throw std::runtime_error("pressure normal audit failed");

    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    lrSetAllZouHePressure(lattice,geometry,outside);
    dynamics::set<NoDynamics>(lattice,geometry,2);
    dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for(int m:{1,4,5})lattice.iniEquilibrium(geometry,m,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();
    lattice.defineRho(geometry,4,one);lattice.defineRho(geometry,5,one);
    lattice.communicate();

    SuperVTMwriter3D<T> writer("preconversion_longrun_fields",overlap);
    SuperGeometryF3D<T> materialField(geometry);materialField.getName()="material";
    SuperLatticePhysVelocity3D<T,D> velocityField(lattice,converter);
    velocityField.getName()="velocity_m_s";
    writer.addFunctor(materialField);writer.addFunctor(velocityField);
    writer.createMasterFile();writer.write(0);

    std::ofstream history(outDir/"preconversion_longrun_global_history.csv");
    history<<std::setprecision(17)
      <<"step,physical_time_s,piston_position_nm,total_displacement_nm,wall_velocity_m_s,"
        "phase,min_rho,max_rho,max_velocity_m_s,max_velocity_x_m_s,max_velocity_y_m_s,"
        "max_velocity_z_m_s,max_velocity_cell,max_Mach,max_Mach_cell,total_fluid_mass_kg,"
        "cumulative_in_mass_kg,cumulative_out_mass_kg,raw_mass_balance_residual_kg,"
        "relative_mass_balance_residual,low_outward_flux_kg_s,high_outward_flux_kg_s,"
        "outlet_flux_kg_s,illegal_link_count,false_periodic_solid_link_count,"
        "material_conversion_count,material_change_count,number_of_fluid_cells,"
        "active_links,periodic_links_recovered,finite\n";
    std::ofstream watch(outDir/"preconversion_longrun_population_watch.csv");
    watch<<std::setprecision(17)
      <<"step,cell,ix,iy,iz,material,f3,f8,f17,rho,ux,uy,uz,Mach\n";

    auto& block=lattice.getBlock(0);
    LRStats initial=lrComputeStats(lattice,geometry,converter),previous=initial,current=initial;
    T cumulativeIn=0,cumulativeOut=0,maxAbsResidual=0,maxMach=0;
    T globalRhoMin=1e300,globalRhoMax=-1e300,globalMaxSpeed=0;
    T minLowFlux=1e300,maxLowFlux=-1e300,minHighFlux=1e300,maxHighFlux=-1e300;
    int maxMachStep=0,maxMachIx=0,maxMachIy=0,maxMachIz=0;
    int maxSpeedStep=0,maxSpeedIx=0,maxSpeedIy=0,maxSpeedIz=0;
    int maxInvalid=0,maxFalse=0,maxMaterialChanges=0,stepsCompleted=0;
    std::string stopReason="completed_requested_observation";
    bool thresholdPass=true;

    for(int step=0;step<=totalSteps;++step){
      const T h=hAt(step,true),uWall=wallSpeed(step,true);
      const auto links=lrUpdatePeriodicLinks(lattice,geometry,h,uWall);
      if(step)lattice.collideAndStream();
      current=lrComputeStats(lattice,geometry,converter);
      const T previousOut=std::max(previous.lowOut,T(0))+std::max(previous.highOut,T(0));
      const T previousIn=std::max(-previous.lowOut,T(0))+std::max(-previous.highOut,T(0));
      const T currentOut=std::max(current.lowOut,T(0))+std::max(current.highOut,T(0));
      const T currentIn=std::max(-current.lowOut,T(0))+std::max(-current.highOut,T(0));
      if(step){
        cumulativeOut+=T(.5)*(previousOut+currentOut)*dt;
        cumulativeIn+=T(.5)*(previousIn+currentIn)*dt;
      }
      const T residual=current.mass-initial.mass+cumulativeOut-cumulativeIn;
      const T relativeResidual=residual/initial.mass;
      const T mach=current.maxULattice/std::sqrt(T(1)/3);
      const long long materialChanges=lrMaterialChangeCount(geometry);
      const int illegal=links[1]+links[3];
      maxAbsResidual=std::max(maxAbsResidual,std::abs(relativeResidual));
      globalRhoMin=std::min(globalRhoMin,current.rhoMin);
      globalRhoMax=std::max(globalRhoMax,current.rhoMax);
      maxInvalid=std::max(maxInvalid,links[1]);maxFalse=std::max(maxFalse,links[3]);
      maxMaterialChanges=std::max<long long>(maxMaterialChanges,materialChanges);
      minLowFlux=std::min(minLowFlux,current.lowOut);maxLowFlux=std::max(maxLowFlux,current.lowOut);
      minHighFlux=std::min(minHighFlux,current.highOut);maxHighFlux=std::max(maxHighFlux,current.highOut);
      if(mach>maxMach){maxMach=mach;maxMachStep=step;maxMachIx=current.maxIx;
        maxMachIy=current.maxIy;maxMachIz=current.maxIz;}
      if(current.maxULattice>globalMaxSpeed){globalMaxSpeed=current.maxULattice;
        maxSpeedStep=step;maxSpeedIx=current.maxIx;maxSpeedIy=current.maxIy;maxSpeedIz=current.maxIz;}

      const T uxPhys=converter.getPhysVelocity(current.maxUx);
      const T uyPhys=converter.getPhysVelocity(current.maxUy);
      const T uzPhys=converter.getPhysVelocity(current.maxUz);
      history<<step<<','<<step*dt<<','<<h*1e9<<','<<(75e-9-h)*1e9<<','<<uWall<<','
        <<(step==0?"initial":"moving")<<','<<current.rhoMin<<','<<current.rhoMax<<','
        <<converter.getPhysVelocity(current.maxULattice)<<','<<uxPhys<<','<<uyPhys<<','<<uzPhys
        <<",\"("<<current.maxIx<<';'<<current.maxIy<<';'<<current.maxIz<<")\","<<mach
        <<",\"("<<current.maxIx<<';'<<current.maxIy<<';'<<current.maxIz<<")\","<<current.mass
        <<','<<cumulativeIn<<','<<cumulativeOut<<','<<residual<<','<<relativeResidual<<','
        <<current.lowOut<<','<<current.highOut<<','<<(current.lowOut+current.highOut)<<','
        <<illegal<<','<<links[3]<<",0,"<<materialChanges<<','<<current.fluidNodes<<','
        <<links[0]<<','<<links[2]<<','<<current.finite<<'\n';
      lrWriteWatch(watch,block,g,step,"cell_0_0_13",{0,0,13});
      lrWriteWatch(watch,block,g,step,"cell_0_0_14",{0,0,14});
      lrWriteWatch(watch,block,g,step,"cell_0_0_15",{0,0,15});
      lrWriteWatch(watch,block,g,step,"cell_0_1_15",{0,1,15});
      stepsCompleted=step;

      if(!current.finite)stopReason="nonfinite";
      else if(mach>machLimit)stopReason="Mach_over_0.05";
      else if(current.rhoMin<rhoMinLimit||current.rhoMax>rhoMaxLimit)stopReason="rho_threshold";
      else if(illegal>0)stopReason="illegal_link";
      else if(materialChanges>0)stopReason="material_change";
      else if(std::abs(relativeResidual)>lrMassResidualLimit)stopReason="mass_residual";
      else stopReason.clear();
      if(!stopReason.empty()){
        thresholdPass=false;writer.write(step);break;
      }
      if(step==lrRegressionSteps||step==totalSteps)writer.write(step);
      previous=current;
    }
    if(thresholdPass)stopReason="completed_requested_observation";
    const bool countsUnchanged=materialCounts(geometry)==initialCounts;
    const bool completed=stepsCompleted==totalSteps;
    const bool outwardPhysical=cumulativeOut>cumulativeIn&&cumulativeOut>0;
    thresholdPass=thresholdPass&&completed&&countsUnchanged&&maxInvalid==0&&maxFalse==0
      &&maxMaterialChanges==0&&maxMach<=machLimit&&globalRhoMin>=rhoMinLimit
      &&globalRhoMax<=rhoMaxLimit&&maxAbsResidual<=lrMassResidualLimit&&outwardPhysical;

    std::ofstream result(outDir/"threshold_result.txt");result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\nthreshold_checks_PASS="<<thresholdPass
      <<"\ntrend_check_pending=true\nsteps_requested="<<totalSteps
      <<"\nsteps_completed="<<stepsCompleted<<"\nmoving_steps="<<stepsCompleted
      <<"\ndeceleration_steps=0\nhold_steps=0\nfinal_h_nm="<<hAt(stepsCompleted,true)*1e9
      <<"\nfinal_displacement_nm="<<(75e-9-hAt(stepsCompleted,true))*1e9
      <<"\nconversion_threshold_margin_nm="<<(hAt(stepsCompleted,true)-72.5e-9)*1e9
      <<"\nmax_Mach="<<maxMach<<"\nmax_Mach_step="<<maxMachStep
      <<"\nmax_Mach_cell="<<maxMachIx<<','<<maxMachIy<<','<<maxMachIz
      <<"\nrho_range="<<globalRhoMin<<','<<globalRhoMax
      <<"\nmax_speed_m_s="<<converter.getPhysVelocity(globalMaxSpeed)
      <<"\nmax_speed_step="<<maxSpeedStep<<"\nmax_speed_cell="<<maxSpeedIx<<','<<maxSpeedIy<<','<<maxSpeedIz
      <<"\nmax_abs_relative_mass_balance_residual="<<maxAbsResidual
      <<"\nfinal_relative_mass_balance_residual="
      <<(current.mass-initial.mass+cumulativeOut-cumulativeIn)/initial.mass
      <<"\ncumulative_in_mass_kg="<<cumulativeIn<<"\ncumulative_out_mass_kg="<<cumulativeOut
      <<"\nlow_outward_flux_range_kg_s="<<minLowFlux<<','<<maxLowFlux
      <<"\nhigh_outward_flux_range_kg_s="<<minHighFlux<<','<<maxHighFlux
      <<"\nmax_invalid_links="<<maxInvalid<<"\nmax_false_periodic_solid_links="<<maxFalse
      <<"\nmaterial_conversions=0\nmax_material_changes="<<maxMaterialChanges
      <<"\nmaterial_counts_unchanged="<<countsUnchanged
      <<"\npressure_nodes="<<pressureAudit[0]<<"\npressure_nodes_correct_flat_normal="<<pressureAudit[1]
      <<"\npressure_zero_normals="<<pressureAudit[2]<<"\npressure_other_normals="<<pressureAudit[3]
      <<"\nstop_reason="<<stopReason<<"\nexit_code="<<(thresholdPass?0:3)<<'\n';
    std::ofstream record(outDir/"run_record.txt");record
      <<"run_id="<<runId<<"\ncommand=mpirun -np 1 ./explicit_piston_zouhe_preconversion_longrun "
      <<(regression?"regression":"longrun")<<"\nsteps="<<totalSteps
      <<"\nmaterial_conversion_enabled=false\nexit_code="<<(thresholdPass?0:3)<<'\n';
    log<<"completed="<<completed<<"\nthreshold_checks_PASS="<<thresholdPass
       <<"\nstop_reason="<<stopReason<<'\n';
    return thresholdPass?0:3;
  }catch(const std::exception& e){
    log<<"exception="<<e.what()<<"\nexit_code=4\n";
    std::ofstream failure(outDir/"failure.txt");failure<<e.what()<<'\n';
    std::cerr<<e.what()<<'\n';return 4;
  }
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1||argc!=2)return 2;
  const std::string mode=argv[1];
  if(mode=="regression")return lrRun(true);
  if(mode=="longrun")return lrRun(false);
  return 2;
}
