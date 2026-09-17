#define main step5f_frozen_support_main
#include "../explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include "dynamic_topology_manager.h"

#include <map>
#include <set>

using namespace olb;

namespace {

constexpr T correctedResidualLimit=1e-3;
constexpr T populationResidualLimit=1e-3;

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
  T popMass{};
  T rhoMin=std::numeric_limits<T>::max();
  T rhoMax=-std::numeric_limits<T>::max();
  T maxMach{},lowOut{},highOut{};
  int maxIx{},maxIy{},maxIz{},maxMaterial{};
  bool finite=true;
};

template<class CELL>
T storedPopulationRho(CELL& cell)
{
  T rho=1;
  for(int i=0;i<D::q;++i) rho+=cell[i];
  return rho;
}

template<class L,class G>
Stats computeStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter,T h)
{
  Stats s;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC);auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      auto cell=block.get(p);const T rhoPop=storedPopulationRho(cell);
      const T a=alpha(g.getPhysR(p),h);
      if(a>0) {
        s.popMass+=a*rhoPop*rhoPhys*dx*dx*dx;
        s.finite&=std::isfinite(rhoPop)&&std::isfinite(a);
      }
      const int material=g.getMaterial(p);
      if(!isFluidMaterial(material)) return;
      const T rho=cell.computeRho();T u[3]{};cell.computeU(u);
      const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      const T mach=speed/std::sqrt(T(1)/3);
      ++s.fluidCells;s.rhoMin=std::min(s.rhoMin,rho);s.rhoMax=std::max(s.rhoMax,rho);
      if(mach>s.maxMach) {
        s.maxMach=mach;s.maxIx=p[0];s.maxIy=p[1];s.maxIz=p[2];s.maxMaterial=material;
      }
      s.finite&=std::isfinite(rho)&&std::isfinite(speed);
      for(int i=0;i<D::q;++i) s.finite&=std::isfinite(cell[i]);
      if(material==4||material==5) {
        const T signedOut=(material==4?-1:1)*rho*rhoPhys
                         *converter.getPhysVelocity(u[1])*dx*dx;
        if(material==4) s.lowOut+=signedOut; else s.highOut+=signedOut;
      }
    });
  }
  return s;
}

struct OldLinkState {
  int iC{};
  LatticeR<3> owner{};
  int direction{};
  int opposite{};
  T qOld{};
  T velocityOld{};
  LatticeR<3> expectedNewOwner{};
  LatticeR<3> transferOwner{};
  T qNew{-1};
  T velocityNew{};
  bool exactNewLink{};
  int newOwnerMaterial{};
  bool transferToBulk{};
};

struct TransitionAudit {
  std::vector<OldLinkState> links;
  long long exactPairs{};
  long long cornerOrPressureTerminations{};
  long long transferredLinks{};
  long long duplicateOldTargets{};
  long long oldNewWriterConflicts{};
};

template<class L>
TransitionAudit captureOldLinkState(L& lattice,const step55::TopologyTransaction& tx)
{
  TransitionAudit audit;
  std::set<std::tuple<int,int,int,int,int>> targets;
  for(const auto& change:tx.fluidToSolid) {
    auto cell=lattice.getBlock(change.iC).get(change.latticeR);
    for(int i=1;i<D::q;++i) {
      const T q=cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
      if(q<0) continue;
      OldLinkState state;
      state.iC=change.iC;
      state.owner=change.latticeR;
      state.direction=i;
      state.opposite=descriptors::opposite<D>(i);
      state.qOld=q;
      state.velocityOld=cell.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(i);
      state.expectedNewOwner=state.owner-descriptors::c<D>(i);
      state.expectedNewOwner[0]=wrapX(state.expectedNewOwner[0]);
      if(!targets.insert({state.iC,state.owner[0],state.owner[1],state.owner[2],state.opposite}).second) {
        ++audit.duplicateOldTargets;
      }
      audit.links.push_back(state);
    }
  }
  return audit;
}

template<class L,class G>
void buildTransitionMap(L& lattice,G& geometry,TransitionAudit& audit,
                        std::ofstream& transitionLog,int step)
{
  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  for(auto& state:audit.links) {
    const auto p=state.expectedNewOwner;
    if(p[1]>=0&&p[1]<48&&p[2]>=0&&p[2]<40
       &&isFluidMaterial(g.getMaterial(p))) {
      auto newOwner=block.get(p);
      state.newOwnerMaterial=g.getMaterial(p);
      state.qNew=newOwner.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(state.direction);
      state.velocityNew=newOwner.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(state.direction);
      state.exactNewLink=state.qNew>=0;
    }
    if(state.exactNewLink) ++audit.exactPairs;
    state.transferToBulk=state.exactNewLink&&state.newOwnerMaterial==1;
    state.transferOwner=state.expectedNewOwner;
    if(state.exactNewLink&&(state.newOwnerMaterial==4||state.newOwnerMaterial==5)) {
      state.transferOwner[1]+=state.newOwnerMaterial==4?1:-1;
      state.transferToBulk=g.getMaterial(state.transferOwner)==1;
    }
    if(state.transferToBulk) ++audit.transferredLinks;
    else ++audit.cornerOrPressureTerminations;

    auto oldOwner=block.get(state.owner);
    if(oldOwner.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(state.direction)>=0) {
      ++audit.oldNewWriterConflicts;
    }
    transitionLog<<step<<','<<state.iC<<','<<state.owner[0]<<','<<state.owner[1]<<','
      <<state.owner[2]<<','<<state.direction<<','<<state.opposite<<','<<state.qOld<<','
      <<state.velocityOld<<','<<state.expectedNewOwner[0]<<','<<state.expectedNewOwner[1]
      <<','<<state.expectedNewOwner[2]<<','<<state.qNew<<','<<state.velocityNew<<','
      <<state.exactNewLink<<','<<state.newOwnerMaterial<<','<<state.transferOwner[0]<<','
      <<state.transferOwner[1]<<','<<state.transferOwner[2]<<','<<state.transferToBulk<<','
      <<(state.transferToBulk?"bulk_zeroth_moment_transfer":"corner_or_pressure_termination")<<'\n';
  }
}

template<class CELL>
T bouzidiValue(CELL& owner,int direction,T q,T velocityCoefficient)
{
  const int opposite=descriptors::opposite<D>(direction);
  const auto c=descriptors::c<D>(direction);
  auto solidSide=owner.neighbor(c);
  auto fluidSide=owner.neighbor(descriptors::c<D>(opposite));
  const T velocityTerm=velocityCoefficient*descriptors::t<T,D>(direction)
                      *descriptors::invCs2<T,D>();
  if(q==0) return owner[direction]-T(2)*velocityTerm;
  if(q<=T(.5)) {
    return T(2)*q*solidSide[direction]+(T(1)-T(2)*q)*owner[direction]
           -T(2)*velocityTerm;
  }
  return T(.5)/q*solidSide[direction]
       + T(.5)*(T(2)*q-T(1))/q*fluidSide[opposite]-velocityTerm/q;
}

template<class L,class G>
void collideAndStreamWithTransition(L& lattice,G& geometry,TransitionAudit& transition,
                                    T h,std::ofstream& transferLog,int step)
{
  lattice.collide();
  auto& block=lattice.getBlock(0);
  block.stream();
  lattice.getCommunicator(stage::PostStream()).communicate();

  std::map<std::tuple<int,int,int>,T> densityTransfer;
  for(const auto& state:transition.links) if(state.transferToBulk) {
    auto oldOwner=block.get(state.owner);
    const T oldPre=oldOwner[state.opposite];
    const T oldClosed=bouzidiValue(oldOwner,state.direction,state.qOld,state.velocityOld);
    const T alphaOld=alpha(geometry.getBlockGeometry(state.iC).getPhysR(state.owner),h);
    const T alphaNew=alpha(geometry.getBlockGeometry(state.iC).getPhysR(state.transferOwner),h);
    if(!(alphaNew>0)) throw std::runtime_error("transition new owner has zero alpha");
    const T transferredDensity=(alphaOld/alphaNew)*(oldClosed-oldPre);
    densityTransfer[{state.transferOwner[0],state.transferOwner[1],
                     state.transferOwner[2]}]+=transferredDensity;
    transferLog<<step<<','<<state.owner[0]<<','<<state.owner[1]<<','<<state.owner[2]<<','
      <<state.transferOwner[0]<<','<<state.transferOwner[1]<<','
      <<state.transferOwner[2]<<','<<state.direction<<','<<state.opposite<<','
      <<alphaOld<<','<<alphaNew<<','<<oldPre<<','<<oldClosed<<','
      <<transferredDensity<<'\n';
  }

  struct ReceiverBoundaryState {
    std::array<T,D::q> q{};
    std::array<T,D::q> velocity{};
  };
  std::map<std::tuple<int,int,int>,ReceiverBoundaryState> receiverBoundary;
  for(const auto& [key,deltaRho]:densityTransfer) {
    (void)deltaRho;
    const auto [ix,iy,iz]=key;auto owner=block.get({ix,iy,iz});
    auto& saved=receiverBoundary[key];
    for(int i=0;i<D::q;++i) {
      saved.q[i]=owner.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
      saved.velocity[i]=owner.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(i);
      owner.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
    }
  }
  block.template postProcess<stage::PostStream>();

  // One custom writer performs both the original Bouzidi closure and the
  // scalar ownership handoff for each receiver cell.  No standard Bouzidi
  // postprocessor writes these receiver populations in this event step.
  for(const auto& [key,deltaRho]:densityTransfer) {
    const auto [ix,iy,iz]=key;auto owner=block.get({ix,iy,iz});
    const auto& saved=receiverBoundary.at(key);
    for(int i=1;i<D::q;++i) if(saved.q[i]>=0) {
      owner[descriptors::opposite<D>(i)]=bouzidiValue(owner,i,saved.q[i],saved.velocity[i]);
    }
    for(int i=0;i<D::q;++i) owner[i]+=descriptors::t<T,D>(i)*deltaRho;
    for(int i=0;i<D::q;++i) {
      owner.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,saved.q[i]);
      owner.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,saved.velocity[i]);
    }
  }
  lattice.getCommunicator(stage::PostPostProcess()).communicate();
}

T eventWallMass(const step55::TopologyTransaction& tx,T hOld,T hNew)
{
  T result=0;
  for(const auto& snapshot:tx.snapshots) {
    T rhoPop=1;
    for(T f:snapshot.population) rhoPop+=f;
    const T deltaAlpha=alpha(snapshot.topology.physicalR,hNew)
                      -alpha(snapshot.topology.physicalR,hOld);
    result+=deltaAlpha*rhoPop*rhoPhys*dx*dx*dx;
  }
  return result;
}

int targetStepFor(T targetDisplacement)
{
  if(targetDisplacement==10e-9) return trajectorySteps;
  for(int step=1;step<=trajectorySteps;++step) {
    if(75e-9-hAt(step,true)>targetDisplacement) return step-1;
  }
  throw std::runtime_error("requested target not reached by frozen trajectory");
}

} // namespace

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1) return 2;
  T targetNm=3;
  for(int i=1;i<argc;++i) {
    const std::string arg=argv[i];
    if(arg=="--target-nm=3") targetNm=3;
    else if(arg=="--target-nm=10") targetNm=10;
    else { std::cerr<<"Unsupported argument "<<arg<<'\n'; return 2; }
  }
  const std::string suffix=targetNm==3?"0to3nm_v5_20260909":"0to10nm_v5_20260909";
  const std::string runId="step5F_link_transition_"+suffix;
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)) {
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
    for(int material:{1,4,5}) lattice.iniEquilibrium(geometry,material,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();lattice.defineRho(geometry,4,one);lattice.defineRho(geometry,5,one);
    lattice.communicate();

    std::string expectedSolidDynamics;
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      if(expectedSolidDynamics.empty()&&g.getMaterial(p)==3) {
        expectedSolidDynamics=typeid(*lattice.getBlock(0).getDynamics(g.getCellId(p))).name();
      }
    });
    if(expectedSolidDynamics.empty()) throw std::runtime_error("NoDynamics reference not found");

    std::ofstream phases(outDir/"transaction_phase_log.csv");
    phases<<"step,phase,operation,fluid_to_solid_count,solid_to_fluid_count,affected_count,status\n";
    std::ofstream prediction(outDir/"topology_prediction.csv");
    prediction<<"step,displacement_nm,fluid_to_solid_count,solid_to_fluid_count\n";
    std::ofstream events(outDir/"conversion_events.csv");
    events<<"step,ix,iy,iz,x_nm,y_nm,z_nm,old_material,new_material\n";
    std::ofstream transitionLog(outDir/"link_transition_map.csv");
    transitionLog<<std::setprecision(17)<<std::boolalpha
      <<"step,block,old_owner_ix,old_owner_iy,old_owner_iz,direction,opposite,q_old,"
        "wall_velocity_old,new_owner_ix,new_owner_iy,new_owner_iz,q_new,wall_velocity_new,"
        "exact_new_link,new_owner_material,transfer_owner_ix,transfer_owner_iy,transfer_owner_iz,"
        "transfer_to_bulk,transition_action\n";
    std::ofstream transferLog(outDir/"link_transition_population_ledger.csv");
    transferLog<<std::setprecision(17)
      <<"step,old_owner_ix,old_owner_iy,old_owner_iz,new_owner_ix,new_owner_iy,new_owner_iz,"
        "direction,opposite,alpha_old,alpha_new,old_target_before_closure,old_closed_value,"
        "transferred_density_to_bulk_owner\n";
    std::ofstream history(outDir/"step5F_history.csv");
    history<<std::setprecision(17)<<std::boolalpha
      <<"step,time_s,h_nm,displacement_nm,event_f2s,cumulative_f2s,material1,material2,"
        "material3,material4,material5,standard_active_links,transition_old_links,"
        "exact_transition_pairs,transferred_bulk_links,transition_terminations,duplicate_old_targets,writer_conflicts,"
        "illegal_links,periodic_mapping_mismatches,dynamics_errors,M_pop_kg,"
        "cumulative_outward_mass_kg,cumulative_wall_mass_signed_kg,R_pop_relative,"
        "R_corrected_relative,rho_min,rho_max,max_Mach,max_ix,max_iy,max_iz,max_material,finite\n";

    const int lastStep=targetStepFor(targetNm*1e-9);
    auto initial=computeStats(lattice,geometry,converter,75e-9),previous=initial,current=initial;
    T cumulativeOut=0,cumulativeWallMass=0,maxAbsRPop=0,maxAbsRCorrected=0;
    T globalMinRho=initial.rhoMin,globalMaxRho=initial.rhoMax,globalMaxMach=initial.maxMach;
    T rPopBeforeFirst=0,rPopAfterFirst=0,rCorrectedBeforeFirst=0,rCorrectedAfterFirst=0;
    long long cumulativeF2S=0,totalTransitionLinks=0,totalExactPairs=0,totalTransferredLinks=0,totalTerminations=0;
    long long maxMappingMismatch=0,totalDynamicsErrors=0,totalDuplicateTargets=0,totalWriterConflicts=0;
    int completed=0,maxInvalid=0,firstConversionStep=-1,firstConversionCount=0;
    bool finite=true,failed=false;
    for(int step=1;step<=lastStep;++step) {
      const T hOld=hAt(step-1,true),hNew=hAt(step,true);
      auto tx=step55::beginTopologyTransaction(lattice,geometry,step,hOld,hNew,phases);
      prediction<<step<<','<<(75e-9-hNew)*1e9<<','<<tx.fluidToSolid.size()<<','
                <<tx.solidToFluid.size()<<'\n';
      for(const auto& c:tx.fluidToSolid) {
        events<<step<<','<<c.latticeR[0]<<','<<c.latticeR[1]<<','<<c.latticeR[2]<<','
          <<c.physicalR[0]*1e9<<','<<c.physicalR[1]*1e9<<','<<c.physicalR[2]*1e9
          <<','<<c.oldMaterial<<','<<c.newMaterial<<'\n';
      }
      TransitionAudit transition=captureOldLinkState(lattice,tx);
      const T rPopBefore=(previous.popMass-initial.popMass+cumulativeOut)/initial.popMass;
      const T rCorrectedBefore=(previous.popMass-initial.popMass+cumulativeOut-cumulativeWallMass)
                              /initial.popMass;
      if(!tx.fluidToSolid.empty()&&firstConversionStep<0) {
        firstConversionStep=step;firstConversionCount=tx.fluidToSolid.size();
        rPopBeforeFirst=rPopBefore;rCorrectedBeforeFirst=rCorrectedBefore;
      }
      const T wallMassThisEvent=eventWallMass(tx,hOld,hNew);
      step55::commitMaterialTopology(geometry,tx,phases);
      step55::assignConvertedDynamics(lattice,tx,phases);
      step55::initializeConvertedPopulations(lattice,tx,phases);
      tx.overlapMismatches=step55::auditPeriodicMaterialMapping(geometry,hNew);
      long long dynamicsErrors=0;
      for(const auto& c:tx.fluidToSolid) {
        const auto type=typeid(*lattice.getBlock(c.iC).getDynamics(c.nodeId)).name();
        if(type!=expectedSolidDynamics) ++dynamicsErrors;
      }
      const auto links=updatePeriodicLinks(lattice,geometry,hNew,wallSpeed(step,true));
      buildTransitionMap(lattice,geometry,transition,transitionLog,step);

      if(transition.links.empty()) lattice.collide(),lattice.AndStream();
      else collideAndStreamWithTransition(lattice,geometry,transition,hNew,transferLog,step);
      current=computeStats(lattice,geometry,converter,hNew);
      cumulativeOut+=T(.5)*(previous.lowOut+previous.highOut+current.lowOut+current.highOut)*dt;
      cumulativeWallMass+=wallMassThisEvent;
      const T rPop=(current.popMass-initial.popMass+cumulativeOut)/initial.popMass;
      const T rCorrected=(current.popMass-initial.popMass+cumulativeOut-cumulativeWallMass)
                         /initial.popMass;
      if(!tx.fluidToSolid.empty()&&step==firstConversionStep) {
        rPopAfterFirst=rPop;rCorrectedAfterFirst=rCorrected;
      }
      const auto counts=materialCounts(geometry);
      cumulativeF2S+=tx.fluidToSolid.size();totalTransitionLinks+=transition.links.size();
      totalExactPairs+=transition.exactPairs;totalTerminations+=transition.cornerOrPressureTerminations;
      totalTransferredLinks+=transition.transferredLinks;
      totalDuplicateTargets+=transition.duplicateOldTargets;
      totalWriterConflicts+=transition.oldNewWriterConflicts;
      totalDynamicsErrors+=dynamicsErrors;maxMappingMismatch=std::max(maxMappingMismatch,tx.overlapMismatches);
      maxInvalid=std::max(maxInvalid,links[1]+links[3]);
      maxAbsRPop=std::max(maxAbsRPop,std::abs(rPop));
      maxAbsRCorrected=std::max(maxAbsRCorrected,std::abs(rCorrected));
      globalMinRho=std::min(globalMinRho,current.rhoMin);globalMaxRho=std::max(globalMaxRho,current.rhoMax);
      globalMaxMach=std::max(globalMaxMach,current.maxMach);finite&=current.finite;
      history<<step<<','<<step*dt<<','<<hNew*1e9<<','<<(75e-9-hNew)*1e9<<','
        <<tx.fluidToSolid.size()<<','<<cumulativeF2S<<','<<counts[1]<<','<<counts[2]<<','
        <<counts[3]<<','<<counts[4]<<','<<counts[5]<<','<<links[0]<<','<<transition.links.size()
        <<','<<transition.exactPairs<<','<<transition.transferredLinks<<','<<transition.cornerOrPressureTerminations<<','
        <<transition.duplicateOldTargets<<','<<transition.oldNewWriterConflicts<<','
        <<links[1]+links[3]<<','<<tx.overlapMismatches<<','<<dynamicsErrors<<','<<current.popMass
        <<','<<cumulativeOut<<','<<cumulativeWallMass<<','<<rPop<<','<<rCorrected<<','
        <<current.rhoMin<<','<<current.rhoMax<<','<<current.maxMach<<','<<current.maxIx<<','
        <<current.maxIy<<','<<current.maxIz<<','<<current.maxMaterial<<','<<current.finite<<'\n';
      completed=step;previous=current;
      failed=!finite||globalMinRho<rhoMinLimit||globalMaxRho>rhoMaxLimit
        ||globalMaxMach>machLimit||maxInvalid||maxMappingMismatch||totalDynamicsErrors
        ||totalDuplicateTargets||totalWriterConflicts;
      if(failed) break;
    }

    const auto finalMaterials=materialCounts(geometry);
    const bool reached=completed==lastStep;
    const bool conversionOccurred=firstConversionStep>=0;
    const bool materialDeltaCorrect=conversionOccurred
      &&finalMaterials[3]-initialMaterials[3]==cumulativeF2S;
    const bool pass=reached&&conversionOccurred&&materialDeltaCorrect&&!failed
      &&maxAbsRPop<populationResidualLimit&&maxAbsRCorrected<correctedResidualLimit;
    std::ofstream result(outDir/"result.txt");result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\nPASS="<<pass<<"\ntarget_displacement_nm="<<targetNm
      <<"\nsteps_completed="<<completed<<"\nfinal_displacement_nm="<<(75e-9-hAt(completed,true))*1e9
      <<"\nfirst_conversion_step="<<firstConversionStep<<"\nfirst_conversion_count="<<firstConversionCount
      <<"\ncumulative_fluid_to_solid="<<cumulativeF2S
      <<"\nmaterial3_delta="<<finalMaterials[3]-initialMaterials[3]
      <<"\nmaterial_delta_correct="<<materialDeltaCorrect
      <<"\ntotal_transition_old_links="<<totalTransitionLinks
      <<"\ntotal_exact_transition_pairs="<<totalExactPairs
      <<"\ntotal_transferred_bulk_links="<<totalTransferredLinks
      <<"\ntotal_transition_terminations="<<totalTerminations
      <<"\nduplicate_old_targets="<<totalDuplicateTargets
      <<"\nwriter_conflicts="<<totalWriterConflicts
      <<"\ndynamics_errors="<<totalDynamicsErrors
      <<"\nmax_periodic_mapping_mismatches="<<maxMappingMismatch
      <<"\nmax_illegal_links="<<maxInvalid
      <<"\nrho_range="<<globalMinRho<<','<<globalMaxRho<<"\nmax_Mach="<<globalMaxMach
      <<"\nmax_abs_R_pop_relative="<<maxAbsRPop
      <<"\nmax_abs_R_corrected_relative="<<maxAbsRCorrected
      <<"\nR_pop_before_first_event="<<rPopBeforeFirst
      <<"\nR_pop_after_first_event="<<rPopAfterFirst
      <<"\nR_corrected_before_first_event="<<rCorrectedBeforeFirst
      <<"\nR_corrected_after_first_event="<<rCorrectedAfterFirst
      <<"\nnonfinite="<<(!finite)<<"\nexit_code="<<(pass?0:3)<<'\n';
    std::ofstream manifest(outDir/"run_manifest.txt");manifest
      <<"model=SIM-EC1XT240\nrun_id="<<runId
      <<"\ncommand=mpirun -np 1 ./step5F_link_transition_fix --target-nm="<<targetNm
      <<"\nfrozen_step4_sha256=9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2\n"
        "transition=single_writer_bouzidi_plus_alpha_weighted_zeroth_moment_bulk_handoff\n"
        "population_initialization=preserve_unchanged\npressure_boundary=ZouHe_unchanged\n"
      <<"exit_code="<<(pass?0:3)<<'\n';
    runLog<<"completed_steps="<<completed<<"\nPASS="<<pass<<"\nexit_code="<<(pass?0:3)<<'\n';
    return pass?0:3;
  } catch(const std::exception& e) {
    runLog<<"exception="<<e.what()<<"\nexit_code=4\n";
    std::ofstream(outDir/"failure.txt")<<e.what()<<'\n';
    std::cerr<<e.what()<<'\n';return 4;
  }
}
