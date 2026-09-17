#define main embedded_boundary_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

// Last step before the fixed material topology ceases to represent the moving
// punch. Step 3595 would place 2304 still-fluid cell centres inside the solid.
constexpr int cvSteps=3594;
constexpr T cvResidualLimit=1e-3;

int cvWrapX(int ix)
{
  const int wrapped=ix%48;
  return wrapped<0?wrapped+48:wrapped;
}

template<class L,class G>
std::array<int,4> cvUpdatePeriodicLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,recovered=0,falseSolid=0;
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p) {
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i) {
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
    }
    if(!isFluidMaterial(g.getMaterial(p))) return;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i) {
      const auto c=descriptors::c<D>(i);auto raw=p+c,mapped=raw;
      const bool crosses=raw[0]<0||raw[0]>=48;
      if(crosses) mapped[0]=cvWrapX(raw[0]);
      const int rawMaterial=g.getMaterial(raw);
      const int solidMaterial=crosses?g.getMaterial(mapped):rawMaterial;
      if(crosses&&(solidMaterial==2||solidMaterial==3)
         &&rawMaterial!=2&&rawMaterial!=3) ++recovered;
      if(crosses&&(rawMaterial==2||rawMaterial==3)
         &&solidMaterial!=2&&solidMaterial!=3) ++falseSolid;
      if(solidMaterial!=2&&solidMaterial!=3) continue;
      T q=.5,velocityCoefficient=0;
      if(solidMaterial==3) {
        T lo=0,hi=1;
        for(int k=0;k<50;++k) {
          const T a=(lo+hi)/2;
          T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;
          if(punch(x,r[2]+a*dx*c[2],h)) hi=a;else lo=a;
        }
        q=(lo+hi)/2;velocityCoefficient=c[2]*uWall*dt/dx;
      }
      if(!(q>=0&&q<=1)) ++invalid;
      else {
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(
          i,velocityCoefficient);
        ++active;
      }
    }
  });
  lattice.communicate();return {active,invalid,recovered,falseSolid};
}

template<class L,class G>
void cvSetAllZouHePressure(L& lattice,G& geometry,
                           SuperIndicatorFfromIndicatorF3D<T>& outside)
{
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
}

T cvSurfaceHeight(T x,T h)
{
  x=std::fmod(x,Lx);
  if(x<0) x+=Lx;
  return (x<60e-9||x>=180e-9) ? h : h+grooveDepth;
}

T cvAlpha(const Vector<T,3>& r,T h)
{
  const T zLow=r[2]-dx/T(2);
  const T zHigh=r[2]+dx/T(2);
  const T fluidLow=std::max(zLow,T(0));
  const T fluidHigh=std::min(zHigh,cvSurfaceHeight(r[0],h));
  return std::clamp((fluidHigh-fluidLow)/dx,T(0),T(1));
}

T cvAnalyticalVolume(T h)
{
  return Lx*Ly*h+120e-9*Ly*grooveDepth;
}

template<class G>
T cvAlphaVolume(G& geometry,T h)
{
  T volume=0;
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    volume+=cvAlpha(g.getPhysR(p),h)*dx*dx*dx;
  });
  return volume;
}

template<class G>
long long cvMaterialChangeCount(G& geometry)
{
  long long changed=0;
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    if(g.getMaterial(p)!=materialAt(g.getPhysR(p))) ++changed;
  });
  return changed;
}

template<class G>
long long cvPendingFluidInsidePunch(G& geometry,T h)
{
  long long count=0;
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material=g.getMaterial(p);
    const auto r=g.getPhysR(p);
    if(isFluidMaterial(material)&&punch(r[0],r[2],h))++count;
  });
  return count;
}

template<class L,class G>
void cvWritePressureDistribution(const std::filesystem::path& path,L& lattice,
                                 G& geometry,const UnitConverter<T,D>& converter)
{
  std::ofstream out(path);
  out<<std::setprecision(17)
     <<"ix,iy,iz,x_nm,y_nm,z_nm,material,rho,lattice_pressure,physical_pressure_Pa\n";
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material=g.getMaterial(p);if(!isFluidMaterial(material))return;
    const T rho=block.get(p).computeRho();
    const T latticePressure=(rho-1)/descriptors::invCs2<T,D>();
    const T physicalPressure=converter.getPhysPressure(latticePressure);
    const auto r=g.getPhysR(p);
    out<<p[0]<<','<<p[1]<<','<<p[2]<<','<<r[0]*1e9<<','<<r[1]*1e9<<','
       <<r[2]*1e9<<','<<material<<','<<rho<<','<<latticePressure<<','
       <<physicalPressure<<'\n';
  });
}

struct CVStats {
  long long fluidCells=0;
  T fullMass=0,geomMass=0,rhoSum=0;
  T rhoMin=std::numeric_limits<T>::max();
  T rhoMax=-std::numeric_limits<T>::max();
  T maxU=0,maxAbsF3=0,maxAbsF8=0,maxAbsF17=0;
  T macroInRate=0,macroOutRate=0;
  T watchF3=0,watchF8=0,watchF17=0;
  bool finite=true;
};

template<class L,class G>
CVStats cvStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter,T h)
{
  CVStats s;
  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material=g.getMaterial(p);
    if(!isFluidMaterial(material)) return;
    auto cell=block.get(p);
    T u[3]{};
    cell.computeU(u);
    const T rho=cell.computeRho();
    const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
    const T alpha=cvAlpha(g.getPhysR(p),h);
    ++s.fluidCells;
    s.rhoSum+=rho;
    s.fullMass+=rho*rhoPhys*dx*dx*dx;
    s.geomMass+=alpha*rho*rhoPhys*dx*dx*dx;
    s.rhoMin=std::min(s.rhoMin,rho);
    s.rhoMax=std::max(s.rhoMax,rho);
    s.maxU=std::max(s.maxU,speed);
    s.maxAbsF3=std::max(s.maxAbsF3,std::abs(cell[3]));
    s.maxAbsF8=std::max(s.maxAbsF8,std::abs(cell[8]));
    s.maxAbsF17=std::max(s.maxAbsF17,std::abs(cell[17]));
    s.finite&=std::isfinite(rho)&&std::isfinite(speed)&&std::isfinite(alpha);
    for(int i=0;i<D::q;++i) s.finite&=std::isfinite(cell[i]);
    if(material==4||material==5) {
      const T uy=converter.getPhysVelocity(u[1]);
      const T signedOut=(material==4?-1:1)*rho*rhoPhys*uy*dx*dx;
      if(signedOut>=0) s.macroOutRate+=signedOut;
      else s.macroInRate-=signedOut;
    }
  });
  auto watch=block.get({0,0,14});
  s.watchF3=watch[3];s.watchF8=watch[8];s.watchF17=watch[17];
  return s;
}

struct CVPopulationFlux { T inMass=0,outMass=0; };

template<class L,class G>
CVPopulationFlux cvPopulationFlux(L& lattice,G& geometry)
{
  CVPopulationFlux flux;
  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material=g.getMaterial(p);
    if(material!=4&&material!=5) return;
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i) {
      const int cy=descriptors::c<D>(i,1);
      if(cy==0) continue;
      const T mass=(cell[i]+descriptors::t<T,D>(i))*rhoPhys*dx*dx*dx;
      const bool outgoing=material==4 ? cy<0 : cy>0;
      if(outgoing) flux.outMass+=mass; else flux.inMass+=mass;
    }
  });
  return flux;
}

void cvHeader(std::ofstream& out)
{
  out<<"step,physical_time_s,piston_position_nm,displacement_nm,wall_velocity_m_s,"
       "M_full_kg,M_geom_kg,average_rho,min_rho,max_rho,analytical_fluid_volume_m3,"
       "alpha_integrated_fluid_volume_m3,swept_volume_m3,full_fluid_cell_volume_m3,"
       "cumulative_macro_in_mass_kg,cumulative_macro_out_mass_kg,"
       "cumulative_population_in_mass_kg,cumulative_population_out_mass_kg,"
       "R_full_macro_kg,R_full_macro_relative,R_full_population_kg,"
       "R_full_population_relative,R_geom_macro_kg,R_geom_macro_relative,"
       "R_geom_population_kg,R_geom_population_relative,max_Mach,max_velocity_m_s,"
       "illegal_links,material_conversion_count,material_change_count,"
       "watch_0_0_14_f3,watch_0_0_14_f8,watch_0_0_14_f17,"
       "max_abs_f3,max_abs_f8,max_abs_f17,finite\n";
}

void cvWrite(std::ofstream& out,int step,T h,T wallVelocity,const CVStats& s,
             T alphaVolume,T macroIn,T macroOut,T popIn,T popOut,
             const CVStats& initial,int illegal,long long materialChanges,
             const UnitConverter<T,D>& converter)
{
  const T rFullMacro=s.fullMass-initial.fullMass-macroIn+macroOut;
  const T rFullPop=s.fullMass-initial.fullMass-popIn+popOut;
  const T rGeomMacro=s.geomMass-initial.geomMass-macroIn+macroOut;
  const T rGeomPop=s.geomMass-initial.geomMass-popIn+popOut;
  out<<step<<','<<step*dt<<','<<h*1e9<<','<<(75e-9-h)*1e9<<','<<wallVelocity
     <<','<<s.fullMass<<','<<s.geomMass<<','<<s.rhoSum/s.fluidCells<<','<<s.rhoMin
     <<','<<s.rhoMax<<','<<cvAnalyticalVolume(h)<<','<<alphaVolume<<','
     <<cvAnalyticalVolume(75e-9)-cvAnalyticalVolume(h)<<','
     <<s.fluidCells*dx*dx*dx<<','<<macroIn<<','<<macroOut<<','<<popIn<<','<<popOut
     <<','<<rFullMacro<<','<<rFullMacro/initial.fullMass<<','<<rFullPop<<','
     <<rFullPop/initial.fullMass<<','<<rGeomMacro<<','<<rGeomMacro/initial.geomMass
     <<','<<rGeomPop<<','<<rGeomPop/initial.geomMass<<','
     <<s.maxU/std::sqrt(T(1)/3)<<','<<converter.getPhysVelocity(s.maxU)<<','
     <<illegal<<",0,"<<materialChanges<<','<<s.watchF3<<','<<s.watchF8<<','
     <<s.watchF17<<','<<s.maxAbsF3<<','<<s.maxAbsF8<<','<<s.maxAbsF17<<','
     <<s.finite<<'\n';
}

int cvValidateVolume()
{
  const std::filesystem::path path="geometry_volume_fraction_validation.csv";
  if(std::filesystem::exists(path)) {
    std::cerr<<"Refusing to overwrite "<<path<<'\n';return 2;
  }
  IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);
  cuboids.setPeriodicity({true,false,false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    g.set(p,materialAt(g.getPhysR(p)));
  });
  geometry.communicate();
  std::ofstream out(path);
  out<<std::setprecision(17)
     <<"step,piston_position_nm,analytical_fluid_volume_m3,"
       "alpha_integrated_fluid_volume_m3,absolute_difference_m3,"
       "relative_difference,full_fluid_cell_volume_m3,swept_volume_m3\n";
  bool pass=true;
  for(int step:{0,100,500,650,1000,1156,1500,2000}) {
    const T h=hAt(step,true);
    const T analytical=cvAnalyticalVolume(h);
    const T integrated=cvAlphaVolume(geometry,h);
    const T difference=integrated-analytical;
    pass&=std::abs(difference)/analytical<1e-12;
    out<<step<<','<<h*1e9<<','<<analytical<<','<<integrated<<','<<difference
       <<','<<difference/analytical<<','<<57600*dx*dx*dx<<','
       <<cvAnalyticalVolume(75e-9)-analytical<<'\n';
  }
  return pass?0:3;
}

int cvRun(bool closed)
{
  const std::string runId=closed
    ? "step5_3_closed_not_authorized"
    : "step5_3_no_conversion_prethreshold_3594_v1_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)) {
    std::cerr<<"Refusing to overwrite "<<outDir<<'\n';return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log");
  log<<std::setprecision(17)<<std::boolalpha;
  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);
    cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      g.set(p,materialAt(g.getPhysR(p)));
    });
    geometry.communicate();
    const auto initialCounts=materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    if(closed) {
      boundary::set<boundary::BounceBack>(lattice,geometry,4);
      boundary::set<boundary::BounceBack>(lattice,geometry,5);
    } else {
      cvSetAllZouHePressure(lattice,geometry,outside);
    }
    dynamics::set<NoDynamics>(lattice,geometry,2);
    dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for(int material:{1,4,5}) lattice.iniEquilibrium(geometry,material,one,zero);
    lattice.addPostProcessor<stage::PostStream>(
      meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();
    if(!closed) {
      lattice.defineRho(geometry,4,one);
      lattice.defineRho(geometry,5,one);
    }
    lattice.communicate();

    cvWritePressureDistribution(outDir/"pressure_distribution_initial.csv",
                                lattice,geometry,converter);

    std::ofstream history(outDir/"moving_control_volume_longrun_history.csv");
    history<<std::setprecision(17)<<std::boolalpha;
    cvHeader(history);
    auto initial=cvStats(lattice,geometry,converter,75e-9);
    auto previous=initial,current=initial;
    T macroIn=0,macroOut=0,popIn=0,popOut=0;
    T maxMach=0,minRho=std::numeric_limits<T>::max();
    T maxRho=-std::numeric_limits<T>::max(),maxAbsRGeom=0;
    T globalMaxF3=initial.maxAbsF3,globalMaxF8=initial.maxAbsF8;
    T globalMaxF17=initial.maxAbsF17;
    int completed=0,maxIllegal=0;
    long long maxMaterialChanges=0;
    bool finite=true;
    cvWrite(history,0,75e-9,0,initial,cvAlphaVolume(geometry,75e-9),
            0,0,0,0,initial,0,0,converter);
    std::ofstream topology(outDir/"topology_audit.csv");
    topology<<"step,h_nm,fluid_centres_inside_continuous_punch\n";
    topology<<"0,75,0\n";
    for(int step=1;step<=cvSteps;++step) {
      const T h=hAt(step,true),wallVelocity=wallSpeed(step,true);
      const auto pending=cvPendingFluidInsidePunch(geometry,h);
      topology<<step<<','<<std::setprecision(17)<<h*1e9<<','<<pending<<'\n';
      if(pending)throw std::runtime_error("fixed fluid topology entered moving solid before configured stop");
      const auto links=cvUpdatePeriodicLinks(lattice,geometry,h,wallVelocity);
      const int illegal=links[1]+links[3];
      lattice.collide();
      const auto popStep=closed?CVPopulationFlux{}:cvPopulationFlux(lattice,geometry);
      lattice.AndStream();
      current=cvStats(lattice,geometry,converter,h);
      macroIn+=T(.5)*(previous.macroInRate+current.macroInRate)*dt;
      macroOut+=T(.5)*(previous.macroOutRate+current.macroOutRate)*dt;
      popIn+=popStep.inMass;popOut+=popStep.outMass;
      const auto changes=cvMaterialChangeCount(geometry);
      const T alphaVolume=cvAlphaVolume(geometry,h);
      cvWrite(history,step,h,wallVelocity,current,alphaVolume,macroIn,macroOut,
              popIn,popOut,initial,illegal,changes,converter);
      const T rGeomMacro=current.geomMass-initial.geomMass-macroIn+macroOut;
      maxAbsRGeom=std::max(maxAbsRGeom,std::abs(rGeomMacro/initial.geomMass));
      maxMach=std::max(maxMach,current.maxU/std::sqrt(T(1)/3));
      globalMaxF3=std::max(globalMaxF3,current.maxAbsF3);
      globalMaxF8=std::max(globalMaxF8,current.maxAbsF8);
      globalMaxF17=std::max(globalMaxF17,current.maxAbsF17);
      minRho=std::min(minRho,current.rhoMin);maxRho=std::max(maxRho,current.rhoMax);
      maxIllegal=std::max(maxIllegal,illegal);
      maxMaterialChanges=std::max(maxMaterialChanges,changes);
      previous=current;completed=step;finite=current.finite;
      if(!finite||maxMach>machLimit||minRho<rhoMinLimit||maxRho>rhoMaxLimit
         ||illegal||changes) break;
    }
    const T finalFullMacro=current.fullMass-initial.fullMass-macroIn+macroOut;
    const T finalFullPop=current.fullMass-initial.fullMass-popIn+popOut;
    const T finalGeomMacro=current.geomMass-initial.geomMass-macroIn+macroOut;
    const T finalGeomPop=current.geomMass-initial.geomMass-popIn+popOut;
    const bool unchanged=materialCounts(geometry)==initialCounts;
    const bool preconversionPass=completed==cvSteps&&finite&&maxMach<=machLimit
      &&minRho>=rhoMinLimit&&maxRho<=rhoMaxLimit&&maxIllegal==0
      &&maxMaterialChanges==0&&unchanged&&maxAbsRGeom<=cvResidualLimit;
    const long long nextStepPending=cvPendingFluidInsidePunch(
      geometry,hAt(cvSteps+1,true));
    const bool fullTenNmPass=false;
    const bool pass=preconversionPass&&fullTenNmPass;
    cvWritePressureDistribution(outDir/"pressure_distribution_final.csv",
                                lattice,geometry,converter);
    const T minPressure=converter.getPhysPressure(
      (minRho-1)/descriptors::invCs2<T,D>());
    const T maxPressure=converter.getPhysPressure(
      (maxRho-1)/descriptors::invCs2<T,D>());
    std::ofstream result(outDir/"result.txt");
    result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\ncase="<<(closed?"M2_closed":"C_open")
      <<"\nPASS="<<pass<<"\npreconversion_PASS="<<preconversionPass
      <<"\nfull_10nm_PASS="<<fullTenNmPass
      <<"\nfull_10nm_reachable_without_material_conversion=false"
      <<"\nstop_reason=last_valid_step_before_material_topology_change"
      <<"\nsteps_completed="<<completed
      <<"\nmax_Mach="<<maxMach<<"\nrho_range="<<minRho<<','<<maxRho
      <<"\nfinal_displacement_nm="<<(75e-9-hAt(completed,true))*1e9
      <<"\nrequested_displacement_nm=10"
      <<"\nnext_step="<<cvSteps+1
      <<"\nnext_step_pending_fluid_inside_punch="<<nextStepPending
      <<"\nphysical_pressure_range_Pa="<<minPressure<<','<<maxPressure
      <<"\nfinal_M_full_kg="<<current.fullMass<<"\nfinal_M_geom_kg="<<current.geomMass
      <<"\nfinal_R_full_macro_relative="<<finalFullMacro/initial.fullMass
      <<"\nfinal_R_full_population_relative="<<finalFullPop/initial.fullMass
      <<"\nfinal_R_geom_macro_relative="<<finalGeomMacro/initial.geomMass
      <<"\nfinal_R_geom_population_relative="<<finalGeomPop/initial.geomMass
      <<"\nmax_abs_R_geom_macro_relative="<<maxAbsRGeom
      <<"\ncumulative_macro_in_mass_kg="<<macroIn
      <<"\ncumulative_macro_out_mass_kg="<<macroOut
      <<"\ncumulative_population_in_mass_kg="<<popIn
      <<"\ncumulative_population_out_mass_kg="<<popOut
      <<"\nmax_illegal_links="<<maxIllegal
      <<"\nmaterial_conversions=0\nmax_material_changes="<<maxMaterialChanges
      <<"\nmaterial_field_unchanged="<<unchanged
      <<"\nmax_abs_f3="<<globalMaxF3<<"\nmax_abs_f8="<<globalMaxF8
      <<"\nmax_abs_f17="<<globalMaxF17
      <<"\nexit_code="<<(pass?0:3)<<'\n';
    std::ofstream record(outDir/"run_record.txt");
    record<<"run_id="<<runId<<"\ncommand=mpirun -np 1 "
      <<"./explicit_piston_moving_boundary_compression "
      <<(closed?"M2":"C")<<"\nsteps=3594\nmaterial_conversion_enabled=false\n"
      <<"requested_displacement_nm=10\nactual_stop_step=3594\n"
      <<"stop_before_fixed_topology_invalid=true\n"
      <<"exit_code="<<(pass?0:3)<<'\n';
    log<<"completed_steps="<<completed<<"\nPASS="<<pass
       <<"\nexit_code="<<(pass?0:3)<<'\n';
    return pass?0:3;
  } catch(const std::exception& e) {
    log<<"exception="<<e.what()<<"\nexit_code=4\n";
    std::ofstream(outDir/"failure.txt")<<e.what()<<'\n';
    return 4;
  }
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1||argc!=2) return 2;
  const std::string mode=argv[1];
  if(mode=="volume") return cvValidateVolume();
  if(mode=="M2") return cvRun(true);
  if(mode=="C") return cvRun(false);
  return 2;
}
