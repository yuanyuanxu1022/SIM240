#define main step55_phase2_frozen_support_main
#include "../explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include "dynamic_topology_manager.h"

using namespace olb;

namespace {

constexpr T targetDisplacement=3e-9;
constexpr T residualLimit=1e-3;

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
        q=(lo+hi)/2;
        velocityCoefficient=c[2]*uWall*dt/dx;
      }
      if(!(q>=0&&q<=1)) ++invalid;
      else {
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,velocityCoefficient);
        ++active;
      }
    }
  });
  lattice.getCommunicator(stage::Full()).communicate();
  return {active,invalid,recovered,falseSolid};
}

T surfaceHeight(T x,T h)
{
  x=std::fmod(x,Lx);if(x<0)x+=Lx;
  return (x<60e-9||x>=180e-9)?h:h+grooveDepth;
}

T alpha(const Vector<T,3>& r,T h)
{
  const T low=std::max(r[2]-dx/T(2),T(0));
  const T high=std::min(r[2]+dx/T(2),surfaceHeight(r[0],h));
  return std::clamp((high-low)/dx,T(0),T(1));
}

struct Stats {
  long long fluidCells{};
  T activeMass{},geomMass{},popMass{};
  T maxStoredRecoveryDifference{};
  T rhoMin=std::numeric_limits<T>::max();
  T rhoMax=-std::numeric_limits<T>::max();
  T maxMach{},lowOut{},highOut{};
  int maxIx{},maxIy{},maxIz{},maxMaterial{};
  bool finite=true;
};

template<class CELL>
T storedPopulationRho(CELL& cell)
{
  // OpenLB 5953d8a-dirty stores shifted populations.  This is the direct
  // implementation of src/dynamics/lbm.h:290-297: rho = 1 + sum_i f_i.
  T rho=T(1);
  for(int i=0;i<D::q;++i)rho+=cell[i];
  return rho;
}

template<class L,class G>
Stats computeStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter,T h)
{
  Stats s;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC);auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      auto cell=block.get(p);const auto r=g.getPhysR(p);
      const T rho=cell.computeRho();const T rhoPop=storedPopulationRho(cell);
      const T rhoLbm=lbm<D>::computeRho(cell);const T a=alpha(r,h);
      if(a>0) {
        s.geomMass+=a*rho*rhoPhys*dx*dx*dx;
        s.popMass+=a*rhoPop*rhoPhys*dx*dx*dx;
        s.maxStoredRecoveryDifference=std::max(
          s.maxStoredRecoveryDifference,std::abs(rhoPop-rhoLbm));
        s.finite&=std::isfinite(rho)&&std::isfinite(rhoPop)&&std::isfinite(a);
      }
      const int material=g.getMaterial(p);
      if(!isFluidMaterial(material)) return;
      T u[3]{};cell.computeU(u);
      const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      const T mach=speed/std::sqrt(T(1)/3);
      ++s.fluidCells;s.activeMass+=rho*rhoPhys*dx*dx*dx;
      s.rhoMin=std::min(s.rhoMin,rho);s.rhoMax=std::max(s.rhoMax,rho);
      if(mach>s.maxMach) {
        s.maxMach=mach;s.maxIx=p[0];s.maxIy=p[1];s.maxIz=p[2];s.maxMaterial=material;
      }
      s.finite&=std::isfinite(rho)&&std::isfinite(speed);
      for(int i=0;i<D::q;++i)s.finite&=std::isfinite(cell[i]);
      if(material==4||material==5) {
        const T signedOut=(material==4?-1:1)*rho*rhoPhys
                         *converter.getPhysVelocity(u[1])*dx*dx;
        if(material==4)s.lowOut+=signedOut;else s.highOut+=signedOut;
      }
    });
  }
  return s;
}

struct EventMassAudit {
  T sumAlpha{};
  T sumAlphaRhoMomenta{};
  T sumAlphaRhoPopulation{};
  T sumStoredRecoveredRho{};
  T maxPopulationDelta{};
  T maxStoredRecoveryDifference{};
};

template<class L>
EventMassAudit auditEventCells(L& lattice,const step55::TopologyTransaction& tx,T h)
{
  EventMassAudit audit;
  for(const auto& snapshot:tx.snapshots) {
    auto cell=lattice.getBlock(snapshot.topology.iC).get(snapshot.topology.latticeR);
    const T a=alpha(snapshot.topology.physicalR,h);
    const T rhoMomenta=cell.computeRho();
    const T rhoPopulation=storedPopulationRho(cell);
    audit.sumAlpha+=a;
    audit.sumAlphaRhoMomenta+=a*rhoMomenta;
    audit.sumAlphaRhoPopulation+=a*rhoPopulation;
    audit.sumStoredRecoveredRho+=rhoPopulation;
    audit.maxStoredRecoveryDifference=std::max(audit.maxStoredRecoveryDifference,
      std::abs(rhoPopulation-lbm<D>::computeRho(cell)));
    for(int i=0;i<D::q;++i) {
      audit.maxPopulationDelta=std::max(audit.maxPopulationDelta,
        std::abs(cell[i]-snapshot.population[i]));
    }
  }
  return audit;
}

void writeEventAudit(std::ofstream& out,int step,const char* phase,
                     const EventMassAudit& audit)
{
  const T massScale=rhoPhys*dx*dx*dx;
  out<<step<<','<<phase<<','<<audit.sumAlpha<<','
     <<audit.sumAlphaRhoMomenta<<','<<audit.sumAlphaRhoPopulation<<','
     <<audit.sumStoredRecoveredRho<<','
     <<audit.sumAlphaRhoMomenta*massScale<<','
     <<audit.sumAlphaRhoPopulation*massScale<<','
     <<audit.sumStoredRecoveredRho*massScale<<','
     <<audit.maxPopulationDelta<<','<<audit.maxStoredRecoveryDifference<<'\n';
}

enum class PopulationStrategy { A, B, C };

PopulationStrategy parseStrategy(const std::string& name)
{
  if(name=="A")return PopulationStrategy::A;
  if(name=="B")return PopulationStrategy::B;
  if(name=="C")return PopulationStrategy::C;
  throw std::runtime_error("strategy must be A, B, or C");
}

const char* strategyDescription(PopulationStrategy strategy)
{
  switch(strategy) {
    case PopulationStrategy::A:return "rho_1_u_0_equilibrium";
    case PopulationStrategy::B:return "source_rho_pop_u_0_equilibrium";
    case PopulationStrategy::C:return "persistent_fluid_neighbor_mean_rho_pop_u_0_equilibrium";
  }
  return "invalid";
}

struct StrategyAudit {
  T sumAlphaRhoBefore{};
  T sumAlphaRhoAfter{};
  T sumRhoBefore{};
  T sumRhoAfter{};
  T targetRhoMin=std::numeric_limits<T>::max();
  T targetRhoMax=-std::numeric_limits<T>::max();
  int minNeighborCount=std::numeric_limits<int>::max();
  int maxNeighborCount{};
  T maxRhoRecoveryError{};
  T maxMomentumAfter{};
};

template<class L,class G>
StrategyAudit initializeConvertedEquilibrium(
  L& lattice,G& geometry,const step55::TopologyTransaction& tx,
  PopulationStrategy strategy,T h,std::ofstream& phaseLog)
{
  StrategyAudit audit;
  auto& g=geometry.getBlockGeometry(0);
  for(const auto& snapshot:tx.snapshots) {
    auto& block=lattice.getBlock(snapshot.topology.iC);
    auto cell=block.get(snapshot.topology.latticeR);
    T sourceRho=T(1);
    for(T f:snapshot.population)sourceRho+=f;
    T targetRho=T(1);
    int neighbors=0;
    if(strategy==PopulationStrategy::B) {
      targetRho=sourceRho;
    } else if(strategy==PopulationStrategy::C) {
      targetRho=0;
      for(int i=1;i<D::q;++i) {
        auto q=snapshot.topology.latticeR+descriptors::c<D>(i);
        if(q[0]<0||q[0]>=48)q[0]=wrapX(q[0]);
        const int material=g.getMaterial(q);
        if(!isFluidMaterial(material))continue;
        auto neighbor=block.get(q);
        targetRho+=storedPopulationRho(neighbor);
        ++neighbors;
      }
      if(neighbors==0)throw std::runtime_error("strategy C conversion cell has no persistent fluid neighbor");
      targetRho/=neighbors;
    }
    const T a=alpha(snapshot.topology.physicalR,h);
    audit.sumAlphaRhoBefore+=a*sourceRho;
    audit.sumRhoBefore+=sourceRho;
    audit.targetRhoMin=std::min(audit.targetRhoMin,targetRho);
    audit.targetRhoMax=std::max(audit.targetRhoMax,targetRho);
    if(strategy==PopulationStrategy::C) {
      audit.minNeighborCount=std::min(audit.minNeighborCount,neighbors);
      audit.maxNeighborCount=std::max(audit.maxNeighborCount,neighbors);
    }
    const T zero[3]{0,0,0};
    for(int i=0;i<D::q;++i) {
      cell[i]=equilibrium<D>::secondOrder(i,targetRho,zero,T(0));
    }
    const T rhoAfter=storedPopulationRho(cell);
    audit.sumAlphaRhoAfter+=a*rhoAfter;
    audit.sumRhoAfter+=rhoAfter;
    audit.maxRhoRecoveryError=std::max(audit.maxRhoRecoveryError,
                                       std::abs(rhoAfter-targetRho));
    T momentum[3]{};
    lbm<D>::computeJ(cell,momentum);
    audit.maxMomentumAfter=std::max(audit.maxMomentumAfter,
      std::sqrt(momentum[0]*momentum[0]+momentum[1]*momentum[1]+momentum[2]*momentum[2]));
  }
  phaseLog<<tx.step<<",5,population_policy,"<<tx.fluidToSolid.size()<<','
          <<tx.solidToFluid.size()<<','<<tx.snapshots.size()<<','
          <<strategyDescription(strategy)<<"\n";
  return audit;
}

T eventWallMass(const step55::TopologyTransaction& tx)
{
  T value=0;
  for(const auto& snapshot:tx.snapshots) {
    T rho=T(1);for(T f:snapshot.population)rho+=f;
    value+=rho*(alpha(snapshot.topology.physicalR,tx.hNew)
               -alpha(snapshot.topology.physicalR,tx.hOld))*rhoPhys*dx*dx*dx;
  }
  return value;
}

int targetStep()
{
  for(int step=1;step<=trajectorySteps;++step) {
    if(75e-9-hAt(step,true)>targetDisplacement) return step-1;
  }
  throw std::runtime_error("3 nm target not reached by frozen trajectory");
}

template<class L,class G>
long long writeBeforeAfter(std::ofstream& out,L& lattice,G& geometry,
                           const step55::TopologyTransaction& tx,const char* phase,
                           const std::string& expectedSolidDynamics)
{
  long long dynamicsErrors=0;
  for(const auto& snapshot:tx.snapshots) {
    const auto& c=snapshot.topology;auto& block=lattice.getBlock(c.iC);
    auto cell=block.get(c.latticeR);T u[3]{};cell.computeU(u);
    const T rho=cell.computeRho();
    const std::string dynamics=typeid(*block.getDynamics(c.nodeId)).name();
    if(std::string(phase)=="after" && dynamics!=expectedSolidDynamics)++dynamicsErrors;
    out<<tx.step<<','<<phase<<','<<c.iC<<','<<c.nodeId<<','<<c.latticeR[0]<<','
       <<c.latticeR[1]<<','<<c.latticeR[2]<<','<<c.physicalR[0]*1e9<<','
       <<c.physicalR[1]*1e9<<','<<c.physicalR[2]*1e9<<','
       <<geometry.getBlockGeometry(c.iC).getMaterial(c.latticeR)<<','<<rho<<','
       <<u[0]<<','<<u[1]<<','<<u[2]<<','<<dynamics;
    for(int i=0;i<D::q;++i)out<<','<<cell[i];
    out<<'\n';
  }
  return dynamicsErrors;
}

} // namespace

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1)return 2;
  if(argc!=2) {
    std::cerr<<"usage: "<<argv[0]<<" A|B|C\n";return 2;
  }
  const std::string strategyName=argv[1];
  const auto strategy=parseStrategy(strategyName);
  const std::string runId="step5D_strategy_"+strategyName+"_0to3nm_v1_20260909";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){
    std::cerr<<"Refusing to overwrite "<<outDir<<'\n';return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream runLog(outDir/"run.log");runLog<<std::setprecision(17)<<std::boolalpha;
  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});
    geometry.communicate();const auto initialMaterials=materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for(int material:{1,4,5})lattice.iniEquilibrium(geometry,material,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();lattice.defineRho(geometry,4,one);lattice.defineRho(geometry,5,one);
    lattice.communicate();
    std::string expectedSolidDynamics;
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      if(expectedSolidDynamics.empty()&&g.getMaterial(p)==3) {
        expectedSolidDynamics=typeid(*lattice.getBlock(0).getDynamics(g.getCellId(p))).name();
      }
    });
    if(expectedSolidDynamics.empty())throw std::runtime_error("NoDynamics reference not found");

    std::ofstream prediction(outDir/"topology_prediction.csv");
    prediction<<"step,displacement_nm,fluid_to_solid_count,solid_to_fluid_count\n";
    std::ofstream phases(outDir/"transaction_phase_log.csv");
    phases<<"step,phase,operation,fluid_to_solid_count,solid_to_fluid_count,affected_count,status\n";
    std::ofstream events(outDir/"topology_events.csv");
    events<<std::setprecision(17);
    events<<"step,block,node_id,ix,iy,iz,x_nm,y_nm,z_nm,old_material,new_material,rho,"
             "ux,uy,uz,momentum_x,momentum_y,momentum_z,dynamics_type";
    for(int i=0;i<D::q;++i) {
      events<<",f"<<i;
    }
    events<<'\n';
    std::ofstream beforeAfter(outDir/"conversion_before_after.csv");
    beforeAfter<<std::setprecision(17);
    beforeAfter<<"step,phase,block,node_id,ix,iy,iz,x_nm,y_nm,z_nm,material,rho,ux,uy,uz,dynamics_type";
    for(int i=0;i<D::q;++i) {
      beforeAfter<<",f"<<i;
    }
    beforeAfter<<'\n';
    std::ofstream history(outDir/"first_conversion_history.csv");
    history<<std::setprecision(17)<<std::boolalpha
      <<"step,time_s,h_nm,displacement_nm,event_f2s,event_s2f,cumulative_f2s,"
        "material1,material2,material3,material4,material5,active_links,invalid_links,"
        "periodic_mapping_mismatches,dynamics_errors,active_fluid_mass_kg,M_geom_old_kg,"
        "M_pop_kg,M_geom_old_minus_M_pop_kg,cumulative_outward_mass_kg,"
        "R_geom_old_relative,R_pop_relative,cumulative_delta_M_wall_signed_kg,"
        "R_corrected_relative,rho_min,rho_max,max_Mach,max_ix,"
        "max_iy,max_iz,max_material,finite\n";
    std::ofstream eventAudit(outDir/"conversion_event_mass_audit.csv");
    eventAudit<<std::setprecision(17)
      <<"step,phase,sum_alpha,sum_alpha_rho_momenta,sum_alpha_rho_population,"
        "sum_stored_recovered_rho,alpha_momenta_mass_kg,alpha_population_mass_kg,"
        "stored_recovered_mass_kg,max_population_delta,max_stored_recovery_difference\n";
    std::ofstream strategyAuditFile(outDir/"population_strategy_event_audit.csv");
    strategyAuditFile<<std::setprecision(17)
      <<"step,strategy,sum_alpha_rho_before,sum_alpha_rho_after,"
        "alpha_population_delta_mass_kg,sum_rho_before,sum_rho_after,"
        "full_population_delta_mass_kg,target_rho_min,target_rho_max,"
        "min_neighbor_count,max_neighbor_count,max_rho_recovery_error,"
        "max_momentum_after,delta_M_wall_signed_kg\n";

    const int lastStep=targetStep();
    auto initial=computeStats(lattice,geometry,converter,75e-9),previous=initial,current=initial;
    T cumulativeOut=0,cumulativeWallMass=0,maxAbsResidual=0,maxAbsPopResidual=0;
    T maxAbsCorrectedResidual=0,globalMinRho=initial.rhoMin;
    T globalMaxRho=initial.rhoMax,globalMaxMach=initial.maxMach;
    long long cumulativeF2S=0,maxMappingMismatch=0,totalDynamicsErrors=0;
    int firstConversionStep=-1,firstConversionCount=0,completed=0,maxInvalid=0;
    T firstConversionDisplacement=0,residualBeforeEvent=0,residualAfterEvent=0;
    T popResidualBeforeEvent=0,popResidualAfterEvent=0;
    T correctedResidualBeforeEvent=0,correctedResidualAfterEvent=0;
    T strategyPopulationMassDelta=0;
    bool finite=true,failed=false;
    for(int step=1;step<=lastStep;++step) {
      const T hOld=hAt(step-1,true),hNew=hAt(step,true);
      auto tx=step55::beginTopologyTransaction(lattice,geometry,step,hOld,hNew,phases);
      prediction<<step<<','<<(75e-9-hNew)*1e9<<','<<tx.fluidToSolid.size()<<','
                <<tx.solidToFluid.size()<<'\n';
      for(const auto& snapshot:tx.snapshots) {
        const auto& c=snapshot.topology;
        events<<step<<','<<c.iC<<','<<c.nodeId<<','<<c.latticeR[0]<<','<<c.latticeR[1]<<','
          <<c.latticeR[2]<<','<<c.physicalR[0]*1e9<<','<<c.physicalR[1]*1e9<<','
          <<c.physicalR[2]*1e9<<','<<c.oldMaterial<<','<<c.newMaterial<<','<<snapshot.rho
          <<','<<snapshot.velocity[0]<<','<<snapshot.velocity[1]<<','<<snapshot.velocity[2]
          <<','<<snapshot.momentum[0]<<','<<snapshot.momentum[1]<<','<<snapshot.momentum[2]
          <<','<<snapshot.dynamicsType;
        for(T f:snapshot.population) {
          events<<','<<f;
        }
        events<<'\n';
      }
      if(!tx.fluidToSolid.empty()) {
        writeBeforeAfter(beforeAfter,lattice,geometry,tx,"before",expectedSolidDynamics);
        writeEventAudit(eventAudit,step,"before_material_commit",auditEventCells(lattice,tx,hNew));
        if(firstConversionStep<0) {
          firstConversionStep=step;firstConversionCount=tx.fluidToSolid.size();
          firstConversionDisplacement=(75e-9-hNew)*1e9;
          residualBeforeEvent=(previous.geomMass-initial.geomMass+cumulativeOut)/initial.geomMass;
          popResidualBeforeEvent=(previous.popMass-initial.popMass+cumulativeOut)/initial.popMass;
          correctedResidualBeforeEvent=(previous.popMass-initial.popMass+cumulativeOut
                                        -cumulativeWallMass)/initial.popMass;
        }
      }
      step55::commitMaterialTopology(geometry,tx,phases);
      step55::assignConvertedDynamics(lattice,tx,phases);
      StrategyAudit strategyAudit;
      if(!tx.fluidToSolid.empty()) {
        const T wallMass=eventWallMass(tx);
        cumulativeWallMass+=wallMass;
        strategyAudit=initializeConvertedEquilibrium(
          lattice,geometry,tx,strategy,hNew,phases);
        const T massScale=rhoPhys*dx*dx*dx;
        strategyPopulationMassDelta=(strategyAudit.sumAlphaRhoAfter
                                    -strategyAudit.sumAlphaRhoBefore)*massScale;
        strategyAuditFile<<step<<','<<strategyName<<','
          <<strategyAudit.sumAlphaRhoBefore<<','<<strategyAudit.sumAlphaRhoAfter<<','
          <<strategyPopulationMassDelta<<','<<strategyAudit.sumRhoBefore<<','
          <<strategyAudit.sumRhoAfter<<','
          <<(strategyAudit.sumRhoAfter-strategyAudit.sumRhoBefore)*massScale<<','
          <<strategyAudit.targetRhoMin<<','<<strategyAudit.targetRhoMax<<','
          <<(strategy==PopulationStrategy::C?strategyAudit.minNeighborCount:0)<<','
          <<strategyAudit.maxNeighborCount<<','<<strategyAudit.maxRhoRecoveryError<<','
          <<strategyAudit.maxMomentumAfter<<','<<wallMass<<'\n';
      } else {
        phases<<step<<",5,population_policy,0,0,0,no_op\n";
      }
      tx.overlapMismatches=step55::auditPeriodicMaterialMapping(geometry,hNew);
      const long long dynamicsErrors=writeBeforeAfter(
        beforeAfter,lattice,geometry,tx,"after",expectedSolidDynamics);
      if(!tx.fluidToSolid.empty()) {
        writeEventAudit(eventAudit,step,"after_dynamics_before_stream",
                        auditEventCells(lattice,tx,hNew));
      }
      const auto links=updatePeriodicLinks(lattice,geometry,hNew,wallSpeed(step,true));
      lattice.collide();lattice.AndStream();
      current=computeStats(lattice,geometry,converter,hNew);
      const T previousOut=previous.lowOut+previous.highOut;
      const T currentOut=current.lowOut+current.highOut;
      cumulativeOut+=T(.5)*(previousOut+currentOut)*dt;
      const T residual=(current.geomMass-initial.geomMass+cumulativeOut)/initial.geomMass;
      const T popResidual=(current.popMass-initial.popMass+cumulativeOut)/initial.popMass;
      const T correctedResidual=(current.popMass-initial.popMass+cumulativeOut
                                 -cumulativeWallMass)/initial.popMass;
      if(!tx.fluidToSolid.empty()) {
        residualAfterEvent=residual;popResidualAfterEvent=popResidual;
        correctedResidualAfterEvent=correctedResidual;
      }
      const auto counts=materialCounts(geometry);
      cumulativeF2S+=tx.fluidToSolid.size();
      history<<step<<','<<step*dt<<','<<hNew*1e9<<','<<(75e-9-hNew)*1e9<<','
        <<tx.fluidToSolid.size()<<','<<tx.solidToFluid.size()<<','<<cumulativeF2S<<','
        <<counts[1]<<','<<counts[2]<<','<<counts[3]<<','<<counts[4]<<','<<counts[5]<<','
        <<links[0]<<','<<links[1]+links[3]<<','<<tx.overlapMismatches<<','<<dynamicsErrors
        <<','<<current.activeMass<<','<<current.geomMass<<','<<current.popMass<<','
        <<current.geomMass-current.popMass<<','<<cumulativeOut<<','<<residual<<','<<popResidual
        <<','<<cumulativeWallMass<<','<<correctedResidual
        <<','<<current.rhoMin<<','<<current.rhoMax<<','<<current.maxMach<<','<<current.maxIx
        <<','<<current.maxIy<<','<<current.maxIz<<','<<current.maxMaterial<<','<<current.finite<<'\n';
      completed=step;maxInvalid=std::max(maxInvalid,links[1]+links[3]);
      maxMappingMismatch=std::max(maxMappingMismatch,tx.overlapMismatches);
      totalDynamicsErrors+=dynamicsErrors;maxAbsResidual=std::max(maxAbsResidual,std::abs(residual));
      maxAbsPopResidual=std::max(maxAbsPopResidual,std::abs(popResidual));
      maxAbsCorrectedResidual=std::max(maxAbsCorrectedResidual,std::abs(correctedResidual));
      globalMinRho=std::min(globalMinRho,current.rhoMin);
      globalMaxRho=std::max(globalMaxRho,current.rhoMax);
      globalMaxMach=std::max(globalMaxMach,current.maxMach);finite&=current.finite;
      previous=current;
      failed=!finite||globalMinRho<rhoMinLimit||globalMaxRho>rhoMaxLimit
        ||globalMaxMach>machLimit||maxInvalid||maxMappingMismatch||totalDynamicsErrors;
      if(failed)break;
    }
    const auto finalMaterials=materialCounts(geometry);
    const bool reached=completed==lastStep;
    const bool conversionOccurred=firstConversionStep>=0;
    const bool materialDeltaCorrect=conversionOccurred
      &&finalMaterials[3]-initialMaterials[3]==cumulativeF2S;
    const bool pass=reached&&conversionOccurred&&materialDeltaCorrect&&!failed
      &&maxAbsCorrectedResidual<residualLimit;
    std::ofstream result(outDir/"result.txt");
    result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\nPASS="<<pass<<"\nsteps_completed="<<completed
      <<"\nfinal_displacement_nm="<<(75e-9-hAt(completed,true))*1e9
      <<"\nfirst_conversion_step="<<firstConversionStep
      <<"\nfirst_conversion_displacement_nm="<<firstConversionDisplacement
      <<"\nfirst_conversion_count="<<firstConversionCount
      <<"\ncumulative_fluid_to_solid="<<cumulativeF2S
      <<"\nmaterial3_delta="<<finalMaterials[3]-initialMaterials[3]
      <<"\nmaterial_delta_correct="<<materialDeltaCorrect
      <<"\ndynamics_errors="<<totalDynamicsErrors
      <<"\nmax_periodic_mapping_mismatches="<<maxMappingMismatch
      <<"\nmax_illegal_links="<<maxInvalid
      <<"\nrho_range="<<globalMinRho<<','<<globalMaxRho
      <<"\nmax_Mach="<<globalMaxMach
      <<"\nmax_abs_R_geom_relative="<<maxAbsResidual
      <<"\nmax_abs_R_pop_relative="<<maxAbsPopResidual
      <<"\nmax_abs_R_corrected_relative="<<maxAbsCorrectedResidual
      <<"\nR_geom_before_first_event="<<residualBeforeEvent
      <<"\nR_geom_after_first_event="<<residualAfterEvent
      <<"\nR_pop_before_first_event="<<popResidualBeforeEvent
      <<"\nR_pop_after_first_event="<<popResidualAfterEvent
      <<"\nR_corrected_before_first_event="<<correctedResidualBeforeEvent
      <<"\nR_corrected_after_first_event="<<correctedResidualAfterEvent
      <<"\nstrategy_alpha_population_delta_mass_kg="<<strategyPopulationMassDelta
      <<"\ncumulative_delta_M_wall_signed_kg="<<cumulativeWallMass
      <<"\nmax_stored_recovery_difference="<<current.maxStoredRecoveryDifference
      <<"\nnonfinite="<<(!finite)<<"\nexit_code="<<(pass?0:3)<<'\n';
    std::ofstream manifest(outDir/"run_manifest.txt");
    manifest<<"model=SIM-EC1XT240\nrun_id="<<runId
      <<"\ncommand=mpirun -np 1 ./step5D_population_strategy_test "<<strategyName<<"\n"
      <<"frozen_step4_sha256=9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2\n"
      <<"target_displacement_nm=3\npressure_boundary=ZouHe_unchanged\n"
      <<"population_policy="<<strategyDescription(strategy)<<"\n"
      <<"only_physical_change=converted_cell_population_initialization\n"
      <<"exit_code="<<(pass?0:3)<<'\n';
    runLog<<"completed_steps="<<completed<<"\nPASS="<<pass
      <<"\nfirst_conversion_step="<<firstConversionStep
      <<"\nexit_code="<<(pass?0:3)<<'\n';
    return pass?0:3;
  }catch(const std::exception& e){
    runLog<<"exception="<<e.what()<<"\nexit_code=4\n";
    std::ofstream(outDir/"failure.txt")<<e.what()<<'\n';
    std::cerr<<e.what()<<'\n';return 4;
  }
}
