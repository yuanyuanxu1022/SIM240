#define main step55_frozen_support_main
#include "../explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include "dynamic_topology_manager.h"

using namespace olb;

namespace {

constexpr T targetDisplacement=1e-9;

int wrapX(int ix)
{
  const int wrapped=ix%48;
  return wrapped<0?wrapped+48:wrapped;
}

template<class L,class G>
std::array<int,4> updatePeriodicLinks(L& lattice,G& geometry,T h,T uWall)
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
      if(crosses) mapped[0]=wrapX(raw[0]);
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
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,velocityCoefficient);
        ++active;
      }
    }
  });
  // Force the full-field communicator. Direct block field writes do not set
  // SuperLattice::_communicationNeeded in this OpenLB version.
  lattice.getCommunicator(stage::Full()).communicate();
  return {active,invalid,recovered,falseSolid};
}

struct TestStats {
  long long fluidCells{};
  T rhoMin=std::numeric_limits<T>::max();
  T rhoMax=-std::numeric_limits<T>::max();
  T maxMach{};
  bool finite=true;
};

template<class L,class G>
TestStats computeTestStats(L& lattice,G& geometry)
{
  TestStats s;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC);auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      if(!isFluidMaterial(g.getMaterial(p))) return;
      auto cell=block.get(p);T u[3]{};cell.computeU(u);const T rho=cell.computeRho();
      const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      ++s.fluidCells;s.rhoMin=std::min(s.rhoMin,rho);s.rhoMax=std::max(s.rhoMax,rho);
      s.maxMach=std::max(s.maxMach,speed/std::sqrt(T(1)/3));
      s.finite&=std::isfinite(rho)&&std::isfinite(speed);
      for(int i=0;i<D::q;++i)s.finite&=std::isfinite(cell[i]);
    });
  }
  return s;
}

int targetStep()
{
  for(int step=1;step<=trajectorySteps;++step) {
    if(75e-9-hAt(step,true)>=targetDisplacement) return step;
  }
  throw std::runtime_error("target displacement not reached by frozen trajectory");
}

} // namespace

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1) return 2;
  const std::string runId="topology_transaction_0to1nm_v2_20260909";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)) {
    std::cerr<<"Refusing to overwrite "<<outDir<<'\n';return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream runLog(outDir/"run.log");
  runLog<<std::setprecision(17)<<std::boolalpha;
  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);
    cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});
    geometry.communicate();
    const auto initialMaterials=materialCounts(geometry);

    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    dynamics::set<NoDynamics>(lattice,geometry,2);
    dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for(int material:{1,4,5})lattice.iniEquilibrium(geometry,material,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();
    lattice.defineRho(geometry,4,one);lattice.defineRho(geometry,5,one);
    lattice.communicate();

    std::ofstream prediction(outDir/"topology_prediction.csv");
    prediction<<"step,displacement_nm,fluid_to_solid_count,solid_to_fluid_count\n";
    std::ofstream phases(outDir/"transaction_phase_log.csv");
    phases<<"step,phase,operation,fluid_to_solid_count,solid_to_fluid_count,affected_count,status\n";
    std::ofstream events(outDir/"topology_events.csv");
    events<<"step,block,node_id,ix,iy,iz,x_nm,y_nm,z_nm,old_material,new_material,rho,"
             "ux,uy,uz,momentum_x,momentum_y,momentum_z,dynamics_type";
    for(int i=0;i<D::q;++i) {
      events<<",f"<<i;
    }
    events<<'\n';
    std::ofstream history(outDir/"short_run_history.csv");
    history<<"step,time_s,h_nm,displacement_nm,fluid_to_solid_count,solid_to_fluid_count,"
             "committed,dynamics_switched,population_initialized,periodic_mapping_mismatches,"
             "active_links,invalid_links,false_periodic_solid_links,fluid_cells,rho_min,rho_max,"
             "max_Mach,finite\n"<<std::setprecision(17)<<std::boolalpha;

    const int lastStep=targetStep();
    TestStats stats=computeTestStats(lattice,geometry);
    T globalRhoMin=stats.rhoMin,globalRhoMax=stats.rhoMax,globalMaxMach=stats.maxMach;
    long long totalF2S=0,totalS2F=0,totalCommitted=0,totalDynamics=0,totalPopulation=0;
    long long maxOverlapMismatch=0;int maxInvalid=0,completed=0;bool finite=stats.finite;
    for(int step=1;step<=lastStep;++step) {
      const T hOld=hAt(step-1,true),hNew=hAt(step,true);
      auto tx=step55::updatePistonTopology(lattice,geometry,step,hOld,hNew,
                                           prediction,phases,events);
      const auto links=updatePeriodicLinks(lattice,geometry,hNew,wallSpeed(step,true));
      lattice.collide();lattice.AndStream();
      stats=computeTestStats(lattice,geometry);
      history<<step<<','<<step*dt<<','<<hNew*1e9<<','<<(75e-9-hNew)*1e9<<','
        <<tx.fluidToSolid.size()<<','<<tx.solidToFluid.size()<<','<<tx.committed<<','
        <<tx.dynamicsSwitched<<','<<tx.populationInitialized<<','<<tx.overlapMismatches<<','
        <<links[0]<<','<<links[1]<<','<<links[3]<<','<<stats.fluidCells<<','<<stats.rhoMin<<','
        <<stats.rhoMax<<','<<stats.maxMach<<','<<stats.finite<<'\n';
      totalF2S+=tx.fluidToSolid.size();totalS2F+=tx.solidToFluid.size();
      totalCommitted+=tx.committed;totalDynamics+=tx.dynamicsSwitched;
      totalPopulation+=tx.populationInitialized;
      maxOverlapMismatch=std::max(maxOverlapMismatch,tx.overlapMismatches);
      maxInvalid=std::max(maxInvalid,links[1]+links[3]);
      globalRhoMin=std::min(globalRhoMin,stats.rhoMin);
      globalRhoMax=std::max(globalRhoMax,stats.rhoMax);
      globalMaxMach=std::max(globalMaxMach,stats.maxMach);
      finite&=stats.finite;completed=step;
      if(!finite||globalMaxMach>machLimit||globalRhoMin<rhoMinLimit
         ||globalRhoMax>rhoMaxLimit||maxInvalid||maxOverlapMismatch)break;
    }
    const auto finalMaterials=materialCounts(geometry);
    const bool materialChanged=finalMaterials!=initialMaterials;
    const bool reached=(75e-9-hAt(completed,true))>=targetDisplacement;
    const bool stable=reached&&finite&&globalMaxMach<=machLimit
      &&globalRhoMin>=rhoMinLimit&&globalRhoMax<=rhoMaxLimit
      &&maxInvalid==0&&maxOverlapMismatch==0;
    const bool eventExercised=totalF2S>0||totalS2F>0;

    std::ofstream result(outDir/"result.txt");
    result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\nPASS_zero_event_framework="<<stable
      <<"\nreal_topology_event_exercised="<<eventExercised
      <<"\nmaterial_commit_validated="<<(eventExercised&&totalCommitted==totalF2S)
      <<"\ndynamics_switch_validated="<<(eventExercised&&totalDynamics==totalF2S)
      <<"\nsteps_completed="<<completed
      <<"\nfinal_displacement_nm="<<(75e-9-hAt(completed,true))*1e9
      <<"\nfluid_to_solid_count="<<totalF2S
      <<"\nsolid_to_fluid_count="<<totalS2F
      <<"\ncommitted_count="<<totalCommitted
      <<"\ndynamics_switched_count="<<totalDynamics
      <<"\npopulation_policy_count="<<totalPopulation
      <<"\nmaterial_field_changed="<<materialChanged
      <<"\nmax_periodic_overlap_mismatches="<<maxOverlapMismatch
      <<"\nmax_illegal_links="<<maxInvalid
      <<"\nrho_range="<<globalRhoMin<<','<<globalRhoMax
      <<"\nmax_Mach="<<globalMaxMach
      <<"\nnonfinite="<<(!finite)
      <<"\nexit_code="<<(stable?0:3)<<'\n';
    std::ofstream manifest(outDir/"run_manifest.txt");
    manifest<<"model=SIM-EC1XT240\nrun_id="<<runId
      <<"\ncommand=mpirun -np 1 ./topology_transaction_test\n"
      <<"frozen_step4_sha256=9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2\n"
      <<"trajectory=frozen_step4_smooth5\ntarget_displacement_nm=1\n"
      <<"two_phase=false\nboundary_reinitialized_each_step=false\n"
      <<"full_lattice_copy=false\nexit_code="<<(stable?0:3)<<'\n';
    runLog<<"completed=true\nzero_event_framework_pass="<<stable
          <<"\nreal_topology_event_exercised="<<eventExercised
          <<"\nexit_code="<<(stable?0:3)<<'\n';
    return stable?0:3;
  } catch(const std::exception& e) {
    runLog<<"completed=false\nexception="<<e.what()<<"\nexit_code=4\n";
    std::ofstream(outDir/"failure.txt")<<e.what()<<'\n';
    std::cerr<<e.what()<<'\n';return 4;
  }
}
