#ifndef SIM_EC1XT240_DYNAMIC_TOPOLOGY_MANAGER_H
#define SIM_EC1XT240_DYNAMIC_TOPOLOGY_MANAGER_H

#include <array>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <typeinfo>
#include <vector>

namespace step55 {

constexpr int temporarySolidMaterial = 30;

struct TopologyCell {
  int iC{};
  std::size_t nodeId{};
  olb::LatticeR<3> latticeR{};
  olb::Vector<T,3> physicalR{};
  int oldMaterial{};
  int newMaterial{};
};

struct CellStateSnapshot {
  TopologyCell topology;
  std::array<T,D::q> population{};
  T rho{};
  olb::Vector<T,3> velocity{};
  olb::Vector<T,3> momentum{};
  std::string dynamicsType;
};

struct TopologyTransaction {
  int step{};
  T hOld{};
  T hNew{};
  std::vector<TopologyCell> fluidToSolid;
  std::vector<TopologyCell> solidToFluid;
  std::vector<CellStateSnapshot> snapshots;
  long long committed{};
  long long dynamicsSwitched{};
  long long populationInitialized{};
  long long overlapMismatches{};
};

inline int desiredMaterial(const olb::Vector<T,3>& r, T h)
{
  if (r[2] < 0) return 2;
  if (punch(r[0],r[2],h)) return 3;
  if (r[1] < dx) return 4;
  if (r[1] > Ly-dx) return 5;
  return 1;
}

template<class G>
std::pair<std::vector<TopologyCell>,std::vector<TopologyCell>>
predictTopologyDelta(G& geometry, T hOld, T hNew)
{
  (void)hOld;
  std::vector<TopologyCell> fluidToSolid;
  std::vector<TopologyCell> solidToFluid;
  for (int iC=0; iC<geometry.getLoadBalancer().size(); ++iC) {
    auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](olb::LatticeR<3> p) {
      const int oldMaterial=g.getMaterial(p);
      const int newMaterial=desiredMaterial(g.getPhysR(p),hNew);
      if (oldMaterial==newMaterial) return;
      TopologyCell change{iC,g.getCellId(p),p,g.getPhysR(p),oldMaterial,newMaterial};
      if (isFluidMaterial(oldMaterial) && newMaterial==3) {
        fluidToSolid.push_back(change);
      } else if (oldMaterial==3 && isFluidMaterial(newMaterial)) {
        solidToFluid.push_back(change);
      } else {
        throw std::runtime_error("unsupported topology transition "
          +std::to_string(oldMaterial)+"->"+std::to_string(newMaterial));
      }
    });
  }
  return {std::move(fluidToSolid),std::move(solidToFluid)};
}

template<class L,class G>
TopologyTransaction beginTopologyTransaction(
  L& lattice,G& geometry,int step,T hOld,T hNew,std::ofstream& phaseLog)
{
  TopologyTransaction tx;
  tx.step=step;tx.hOld=hOld;tx.hNew=hNew;
  auto delta=predictTopologyDelta(geometry,hOld,hNew);
  tx.fluidToSolid=std::move(delta.first);
  tx.solidToFluid=std::move(delta.second);
  phaseLog<<step<<",1,predict,"<<tx.fluidToSolid.size()<<','
          <<tx.solidToFluid.size()<<",0,ok\n";

  for (const auto& change:tx.fluidToSolid) {
    auto& block=lattice.getBlock(change.iC);
    auto cell=block.get(change.latticeR);
    CellStateSnapshot snapshot;
    snapshot.topology=change;
    snapshot.rho=cell.computeRho();
    T u[3]{};cell.computeU(u);
    snapshot.velocity={u[0],u[1],u[2]};
    snapshot.momentum={snapshot.rho*u[0],snapshot.rho*u[1],snapshot.rho*u[2]};
    for (int iPop=0;iPop<D::q;++iPop) snapshot.population[iPop]=cell[iPop];
    snapshot.dynamicsType=typeid(*block.getDynamics(change.nodeId)).name();
    tx.snapshots.push_back(std::move(snapshot));
  }
  phaseLog<<step<<",2,snapshot,"<<tx.fluidToSolid.size()<<','
          <<tx.solidToFluid.size()<<','<<tx.snapshots.size()<<",ok\n";
  return tx;
}

template<class G>
void commitMaterialTopology(G& geometry,TopologyTransaction& tx,
                            std::ofstream& phaseLog)
{
  if (!tx.solidToFluid.empty()) {
    throw std::runtime_error("solid-to-fluid is outside STEP 5.5 phase-one scope");
  }
  for (const auto& change:tx.fluidToSolid) {
    geometry.getBlockGeometry(change.iC).set(change.latticeR,temporarySolidMaterial);
  }
  if (!tx.fluidToSolid.empty()) {
    // The unconditional super-level rename marks SuperGeometry communication
    // dirty.  Direct BlockGeometry::set followed by communicate is insufficient
    // in this OpenLB version because communicate() is guarded by a dirty flag.
    geometry.rename(temporarySolidMaterial,3);
    geometry.communicate();
  }
  tx.committed=tx.fluidToSolid.size();
  phaseLog<<tx.step<<",3,material_commit,"<<tx.fluidToSolid.size()<<','
          <<tx.solidToFluid.size()<<','<<tx.committed
          <<','<<(tx.committed?"committed":"no_op")<<"\n";
}

template<class L>
void assignConvertedDynamics(L& lattice,TopologyTransaction& tx,
                             std::ofstream& phaseLog)
{
  for (const auto& change:tx.fluidToSolid) {
    lattice.getBlock(change.iC).template defineDynamics<olb::NoDynamics>(change.latticeR);
    ++tx.dynamicsSwitched;
  }
  phaseLog<<tx.step<<",4,dynamics_switch,"<<tx.fluidToSolid.size()<<','
          <<tx.solidToFluid.size()<<','<<tx.dynamicsSwitched
          <<','<<(tx.dynamicsSwitched?"NoDynamics":"no_op")<<"\n";
}

template<class L>
void initializeConvertedPopulations(L& lattice,TopologyTransaction& tx,
                                    std::ofstream& phaseLog)
{
  // Phase one deliberately preserves the stored populations of newly covered
  // cells.  It does not redistribute, normalize, clear, or equilibrate mass.
  // The policy is auditable and safe for a no-event 0->1 nm test; its physical
  // mass closure must be validated separately when a real event is authorized.
  for (const auto& snapshot:tx.snapshots) {
    auto cell=lattice.getBlock(snapshot.topology.iC).get(snapshot.topology.latticeR);
    for (int iPop=0;iPop<D::q;++iPop) {
      if (cell[iPop]!=snapshot.population[iPop]) {
        throw std::runtime_error("population changed before initialization phase");
      }
    }
    ++tx.populationInitialized;
  }
  phaseLog<<tx.step<<",5,population_policy,"<<tx.fluidToSolid.size()<<','
          <<tx.solidToFluid.size()<<','<<tx.populationInitialized
          <<','<<(tx.populationInitialized?"preserved":"no_op")<<"\n";
}

template<class G>
long long auditPeriodicMaterialMapping(G& geometry,T h)
{
  long long mismatches=0;
  auto& g=geometry.getBlockGeometry(0);
  for (int iy=0;iy<48;++iy) for (int iz=0;iz<40;++iz) {
    // BlockGeometry::getMaterial returns material 0 for coordinates outside
    // the core. STEP 4 therefore maps x-periodic neighbors explicitly. Audit
    // those mapped core sources instead of treating negative indices as halo.
    for (int ix:{0,47}) {
      const olb::LatticeR<3> mapped{ix,iy,iz};
      if (g.getMaterial(mapped)!=desiredMaterial(g.getPhysR(mapped),h)) ++mismatches;
    }
  }
  return mismatches;
}

template<class L,class G>
TopologyTransaction updatePistonTopology(
  L& lattice,G& geometry,int step,T hOld,T hNew,
  std::ofstream& predictionLog,std::ofstream& phaseLog,
  std::ofstream& eventLog)
{
  auto tx=beginTopologyTransaction(lattice,geometry,step,hOld,hNew,phaseLog);
  predictionLog<<step<<','<<(75e-9-hNew)*1e9<<','
               <<tx.fluidToSolid.size()<<','<<tx.solidToFluid.size()<<"\n";
  for (const auto& snapshot:tx.snapshots) {
    const auto& c=snapshot.topology;
    eventLog<<step<<','<<c.iC<<','<<c.nodeId<<','<<c.latticeR[0]<<','
      <<c.latticeR[1]<<','<<c.latticeR[2]<<','<<c.physicalR[0]*1e9<<','
      <<c.physicalR[1]*1e9<<','<<c.physicalR[2]*1e9<<','<<c.oldMaterial<<','
      <<c.newMaterial<<','<<snapshot.rho<<','<<snapshot.velocity[0]<<','
      <<snapshot.velocity[1]<<','<<snapshot.velocity[2]<<','
      <<snapshot.momentum[0]<<','<<snapshot.momentum[1]<<','
      <<snapshot.momentum[2]<<','<<snapshot.dynamicsType;
    for (T f:snapshot.population) eventLog<<','<<f;
    eventLog<<'\n';
  }
  commitMaterialTopology(geometry,tx,phaseLog);
  assignConvertedDynamics(lattice,tx,phaseLog);
  initializeConvertedPopulations(lattice,tx,phaseLog);
  tx.overlapMismatches=auditPeriodicMaterialMapping(geometry,hNew);
  return tx;
}

} // namespace step55

#endif
