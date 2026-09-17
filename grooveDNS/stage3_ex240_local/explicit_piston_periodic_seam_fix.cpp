#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

int periodicX(int ix)
{
  int wrapped=ix%48;
  return wrapped<0?wrapped+48:wrapped;
}

template<class G>
std::array<int,2> markPeriodicAwarePressureIntersections(G& geometry)
{
  std::array<int,2> marked{};
  for(int iC=0;iC<geometry.getLoadBalancer().size();++iC){
    auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p){
      const int material=g.getMaterial(p);
      if(material!=4&&material!=5)return;
      bool touchesSolid=false;
      for(int i=1;i<D::q;++i){
        const auto c=descriptors::c<D>(i);
        LatticeR<3> neighbor=p+c;
        if(neighbor[0]<0||neighbor[0]>=48)neighbor[0]=periodicX(neighbor[0]);
        const int neighborMaterial=g.getMaterial(neighbor);
        touchesSolid|=neighborMaterial==2||neighborMaterial==3;
      }
      if(touchesSolid){
        g.set(p,material==4?6:7);++marked[material==4?0:1];
      }
    });
  }
  geometry.communicate();return marked;
}

template<class L,class G>
std::array<int,4> updatePeriodicAwareLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,missingPeriodicSolid=0,extraPeriodicSolid=0;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC){
    auto& block=lattice.getBlock(iC);auto& g=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p){
      auto cell=block.get(p);
      for(int i=0;i<D::q;++i){
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
      }
      if(!isFluidMaterial(g.getMaterial(p)))return;
      const auto r=g.getPhysR(p);
      for(int i=1;i<D::q;++i){
        const auto c=descriptors::c<D>(i);
        LatticeR<3> raw=p+c,mapped=raw;
        const bool crosses=raw[0]<0||raw[0]>=48;
        if(crosses)mapped[0]=periodicX(raw[0]);
        const int rawMaterial=g.getMaterial(raw);
        const int material=crosses?g.getMaterial(mapped):rawMaterial;
        if(crosses&&(material==2||material==3)
           &&rawMaterial!=2&&rawMaterial!=3)++missingPeriodicSolid;
        if(crosses&&(rawMaterial==2||rawMaterial==3)
           &&material!=2&&material!=3)++extraPeriodicSolid;
        if(material!=2&&material!=3)continue;
        T q=.5,velocityCoefficient=0;
        if(material==3){
          T lo=0,hi=1;
          for(int k=0;k<50;++k){
            const T a=(lo+hi)/2;
            T x=r[0]+a*dx*c[0];
            x=std::fmod(x,Lx);if(x<0)x+=Lx;
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
  }
  lattice.communicate();return{active,invalid,missingPeriodicSolid,extraPeriodicSolid};
}

int runPeriodicFix(bool fixedB)
{
  const bool moving=!fixedB;
  const std::string runId=fixedB
    ?"boundary_intersection_periodic_link_fix_B650_20260907"
    :"boundary_intersection_periodic_link_fix_C650_20260907";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"exists\n";return 2;}
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log");log<<std::setprecision(17)<<std::boolalpha;
  try{
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    for(int iC=0;iC<loadBalancer.size();++iC){
      auto& g=geometry.getBlockGeometry(iC);
      g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});
    }
    geometry.communicate();
    std::array<int,2> marked{};
    if(!fixedB)marked=markPeriodicAwarePressureIntersections(geometry);
    const auto initialCounts=materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    if(!fixedB){
      boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
        lattice,geometry.getMaterialIndicator(6),geometry.getMaterialIndicator(1),outside);
      boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
        lattice,geometry.getMaterialIndicator(7),geometry.getMaterialIndicator(1),outside);
    }
    dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
    for(int m:{1,4,5,6,7})lattice.iniEquilibrium(geometry,m,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();

    std::ofstream csv(outDir/"diagnostics.csv");
    csv<<std::setprecision(17)
      <<"step,time_s,h_nm,wall_speed_m_s,active_links,invalid_links,"
      <<"periodic_solid_links_recovered,periodic_false_solid_links,fluid_nodes,"
      <<"raw_fluid_mass_kg,mass_relative_change,low_outward_flux_kg_s,"
      <<"high_outward_flux_kg_s,net_outward_flux_kg_s,cumulative_outward_mass_kg,"
      <<"mass_balance_residual_kg,relative_mass_balance_residual,rho_min,rho_max,"
      <<"max_speed_m_s,max_Mach,max_ix,max_iy,max_iz,max_material,finite,"
      <<"material_conversions\n";
    std::array<LatticeR<3>,4> points{{{0,0,13},{47,0,13},{0,0,14},{0,0,15}}};
    std::array<const char*,4> names{{"cell_0_0_13","cell_47_0_13",
                                    "cell_0_0_14","cell_0_0_15"}};
    std::array<std::ofstream,4> history{
      std::ofstream(outDir/"cell_0_0_13_history.csv"),
      std::ofstream(outDir/"cell_47_0_13_history.csv"),
      std::ofstream(outDir/"cell_0_0_14_history.csv"),
      std::ofstream(outDir/"cell_0_0_15_history.csv")};
    for(auto& stream:history){stream<<std::setprecision(17);writeCellHeader(stream);}
    auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
    Stats initial=computeStats(lattice,geometry,converter),previous=initial,current=initial;
    T cumulativeOut=0,maxResidual=0,maxMach=0,minRho=1e300,maxRho=-1e300;
    T globalMaxSpeed=0;int globalIx=0,globalIy=0,globalIz=0,globalMaterial=0;
    int firstMach=-1,firstRho=-1,firstNonfinite=-1,firstMachIx=-1,firstMachIy=-1,
        firstMachIz=-1,firstMachMaterial=-1,maxInvalid=0,maxFalse=0;
    for(int step=0;step<=650;++step){
      const auto links=updatePeriodicAwareLinks(lattice,geometry,hAt(step,moving),
                                                wallSpeed(step,moving));
      maxInvalid=std::max(maxInvalid,links[1]);maxFalse=std::max(maxFalse,links[3]);
      if(step)lattice.collideAndStream();
      current=computeStats(lattice,geometry,converter);
      if(step)cumulativeOut+=T(.5)*((previous.lowOut+previous.highOut)
                                   +(current.lowOut+current.highOut))*dt;
      const T residual=current.mass-initial.mass+cumulativeOut;
      const T mach=current.maxU/std::sqrt(T(1)/3);
      maxResidual=std::max(maxResidual,std::abs(residual/initial.mass));
      maxMach=std::max(maxMach,mach);minRho=std::min(minRho,current.rhoMin);
      maxRho=std::max(maxRho,current.rhoMax);
      if(current.maxU>globalMaxSpeed){globalMaxSpeed=current.maxU;globalIx=current.maxIx;
        globalIy=current.maxIy;globalIz=current.maxIz;globalMaterial=current.maxMaterial;}
      if(firstMach<0&&mach>machLimit){firstMach=step;firstMachIx=current.maxIx;
        firstMachIy=current.maxIy;firstMachIz=current.maxIz;
        firstMachMaterial=current.maxMaterial;}
      if(firstRho<0&&(current.rhoMin<rhoMinLimit||current.rhoMax>rhoMaxLimit))firstRho=step;
      if(firstNonfinite<0&&!current.finite)firstNonfinite=step;
      csv<<step<<','<<step*dt<<','<<hAt(step,moving)*1e9<<','<<wallSpeed(step,moving)
        <<','<<links[0]<<','<<links[1]<<','<<links[2]<<','<<links[3]<<','
        <<current.fluidNodes<<','<<current.mass<<','
        <<(current.mass-initial.mass)/initial.mass<<','<<current.lowOut<<','
        <<current.highOut<<','<<(current.lowOut+current.highOut)<<','<<cumulativeOut
        <<','<<residual<<','<<residual/initial.mass<<','<<current.rhoMin<<','
        <<current.rhoMax<<','<<converter.getPhysVelocity(current.maxU)<<','<<mach
        <<','<<current.maxIx<<','<<current.maxIy<<','<<current.maxIz<<','
        <<current.maxMaterial<<','<<current.finite<<",0\n";
      for(int i=0;i<4;++i)writeCell(history[i],block,g,points[i],step);
      previous=current;if(!current.finite)break;
    }
    const T finalResidual=current.mass-initial.mass+cumulativeOut;
    const bool materialUnchanged=materialCounts(geometry)==initialCounts;
    const bool pass=current.finite&&firstMach<0&&firstRho<0&&maxInvalid==0
                   &&maxFalse==0&&materialUnchanged;
    std::ofstream result(outDir/"result.txt");
    result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\ncase="<<(fixedB?"B":"C_periodic_aware_links")
      <<"\nPASS="<<pass<<"\nsteps_requested=650\nsteps_completed="
      <<(firstNonfinite<0?650:firstNonfinite)<<"\nintersection_low_cells="<<marked[0]
      <<"\nintersection_high_cells="<<marked[1]<<"\nmax_Mach="<<maxMach
      <<"\nfirst_Mach_over_0.05_step="<<firstMach<<"\nfirst_Mach_location="
      <<firstMachIx<<','<<firstMachIy<<','<<firstMachIz
      <<"\nfirst_Mach_material="<<firstMachMaterial<<"\nrho_range="<<minRho<<','<<maxRho
      <<"\nfirst_rho_outside_0.8_1.2_step="<<firstRho
      <<"\nfirst_nonfinite_step="<<firstNonfinite<<"\nmax_speed_m_s="
      <<converter.getPhysVelocity(globalMaxSpeed)<<"\nmax_speed_location="<<globalIx<<','
      <<globalIy<<','<<globalIz<<"\nmax_speed_material="<<globalMaterial
      <<"\ninitial_raw_fluid_mass_kg="<<initial.mass<<"\nfinal_raw_fluid_mass_kg="
      <<current.mass<<"\ncumulative_outward_mass_kg="<<cumulativeOut
      <<"\nfinal_relative_mass_balance_residual="<<finalResidual/initial.mass
      <<"\nmax_abs_relative_mass_balance_residual="<<maxResidual
      <<"\nmax_invalid_links="<<maxInvalid<<"\nmax_false_periodic_solid_links="<<maxFalse
      <<"\nmaterial_conversions=0\nmaterial_field_unchanged="<<materialUnchanged
      <<"\nexit_code="<<(pass?0:3)<<"\nexit_reason="
      <<(pass?"all_frozen_650_step_checks_passed":
                "one_or_more_frozen_650_step_checks_failed")<<'\n';
    std::ofstream record(outDir/"run_record.txt");
    record<<"run_id="<<runId<<"\ncommand=./explicit_piston_periodic_seam_fix "
          <<(fixedB?"B":"Cfix")<<"\nexit_code="<<(pass?0:3)<<"\nexit_reason="
          <<(pass?"all_frozen_650_step_checks_passed":
                    "one_or_more_frozen_650_step_checks_failed")<<'\n';
    log<<"completed=true\nPASS="<<pass<<"\nexit_code="<<(pass?0:3)<<'\n';
    return pass?0:3;
  }catch(const std::exception& e){
    log<<"completed=false\nexception="<<e.what()<<"\nexit_code=4\n";
    std::cerr<<e.what()<<'\n';return 4;
  }
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1||argc!=2)return 2;
  const std::string mode=argv[1];
  if(mode=="B")return runPeriodicFix(true);
  if(mode=="Cfix")return runPeriodicFix(false);
  return 2;
}
