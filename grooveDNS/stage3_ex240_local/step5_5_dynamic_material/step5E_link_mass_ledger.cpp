#define main step5e_frozen_support_main
#include "../explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include "dynamic_topology_manager.h"

#include <set>
#include <tuple>
#include <vector>

using namespace olb;

namespace {

constexpr int NX=48,NY=48,NZ=40,eventStep=3595;
constexpr T massScale=rhoPhys*dx*dx*dx;

int wrapX5E(int ix) { int v=ix%NX;return v<0?v+NX:v; }
std::size_t cellIndex(LatticeR<3> p) { return (p[2]*NY+p[1])*NX+p[0]; }
std::size_t popIndex(LatticeR<3> p,int i) { return cellIndex(p)*D::q+i; }
bool inCore(LatticeR<3> p) {
  return p[0]>=0&&p[0]<NX&&p[1]>=0&&p[1]<NY&&p[2]>=0&&p[2]<NZ;
}

T surface5E(T x,T h) {
  x=std::fmod(x,Lx);if(x<0)x+=Lx;
  return (x<60e-9||x>=180e-9)?h:h+grooveDepth;
}
T alpha5E(const Vector<T,3>& r,T h) {
  return std::clamp((std::min(r[2]+dx/T(2),surface5E(r[0],h))
                    -std::max(r[2]-dx/T(2),T(0)))/dx,T(0),T(1));
}

template<class L>
std::vector<T> capturePopulations(L& lattice) {
  std::vector<T> values(std::size_t(NX)*NY*NZ*D::q);
  auto& block=lattice.getBlock(0);
  for(int iz=0;iz<NZ;++iz)for(int iy=0;iy<NY;++iy)for(int ix=0;ix<NX;++ix) {
    LatticeR<3> p{ix,iy,iz};auto cell=block.get(p);
    for(int i=0;i<D::q;++i)values[popIndex(p,i)]=cell[i];
  }
  return values;
}

template<class G>
std::vector<int> captureMaterials(G& geometry) {
  std::vector<int> values(std::size_t(NX)*NY*NZ);
  auto& g=geometry.getBlockGeometry(0);
  for(int iz=0;iz<NZ;++iz)for(int iy=0;iy<NY;++iy)for(int ix=0;ix<NX;++ix) {
    LatticeR<3> p{ix,iy,iz};values[cellIndex(p)]=g.getMaterial(p);
  }
  return values;
}

template<class L>
std::pair<std::vector<T>,std::vector<T>> captureLinkFields(L& lattice) {
  std::vector<T> q(std::size_t(NX)*NY*NZ*D::q),v(q.size());auto& block=lattice.getBlock(0);
  for(int iz=0;iz<NZ;++iz)for(int iy=0;iy<NY;++iy)for(int ix=0;ix<NX;++ix) {
    LatticeR<3> p{ix,iy,iz};auto cell=block.get(p);
    for(int i=0;i<D::q;++i) {
      q[popIndex(p,i)]=cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
      v[popIndex(p,i)]=cell.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(i);
    }
  }
  return {std::move(q),std::move(v)};
}

template<class L,class G>
std::array<int,4> refreshLinks5E(L& lattice,G& geometry,T h,T uWall) {
  int active=0,invalid=0,recovered=0,falseSolid=0;auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i) {
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
    }
    if(!isFluidMaterial(g.getMaterial(p)))return;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i) {
      const auto c=descriptors::c<D>(i);auto raw=p+c,mapped=raw;
      const bool crosses=raw[0]<0||raw[0]>=NX;if(crosses)mapped[0]=wrapX5E(raw[0]);
      const int rawMat=g.getMaterial(raw),solidMat=crosses?g.getMaterial(mapped):rawMat;
      if(crosses&&(solidMat==2||solidMat==3)&&rawMat!=2&&rawMat!=3)++recovered;
      if(crosses&&(rawMat==2||rawMat==3)&&solidMat!=2&&solidMat!=3)++falseSolid;
      if(solidMat!=2&&solidMat!=3)continue;
      T q=.5,vc=0;
      if(solidMat==3) {
        T lo=0,hi=1;
        for(int k=0;k<50;++k) {
          const T a=(lo+hi)/2;T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;
          if(punch(x,r[2]+a*dx*c[2],h))hi=a;else lo=a;
        }
        q=(lo+hi)/2;vc=c[2]*uWall*dt/dx;
      }
      if(q<0||q>1)++invalid;
      else {
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,vc);++active;
      }
    }
  });
  lattice.getCommunicator(stage::Full()).communicate();
  return {active,invalid,recovered,falseSolid};
}

T massFromSnapshot(const std::vector<T>& f,auto& geometry,T h,
                   const std::set<std::size_t>* subset=nullptr) {
  T mass=0;auto& g=geometry.getBlockGeometry(0);
  for(int iz=0;iz<NZ;++iz)for(int iy=0;iy<NY;++iy)for(int ix=0;ix<NX;++ix) {
    LatticeR<3> p{ix,iy,iz};const auto id=cellIndex(p);
    if(subset&&!subset->contains(id))continue;
    T rho=1;for(int i=0;i<D::q;++i)rho+=f[popIndex(p,i)];
    mass+=alpha5E(g.getPhysR(p),h)*rho*massScale;
  }
  return mass;
}

struct LinkRecord {
  LatticeR<3> owner{},neighbor{};int i{},opp{},oldOwnerMat{},newOwnerMat{};
  int oldNeighborMat{},newNeighborMat{};T qOld{},qNew{},vOld{},vNew{};
  T preStream{},postStream{},postComm{},postBouzidi{};
  T xbI{},xsI{},xfOpp{},expected{},oldExpected{},deltaStreamMass{},deltaCommMass{},deltaBouzidiMass{};
  T counterfactualOldBouzidiMass{};
  bool crossesX{},newActive{},oldActive{};
};

void writeLinks(const std::filesystem::path& outDir,std::vector<LinkRecord>& links) {
  auto header=[](std::ofstream& out) {
    out<<"owner_ix,owner_iy,owner_iz,direction,opposite,neighbor_ix,neighbor_iy,neighbor_iz,"
         "crosses_x,old_owner_material,new_owner_material,old_neighbor_material,new_neighbor_material,"
         "old_active,new_active,q_old,q_new,wall_velocity_coefficient_old,wall_velocity_coefficient_new,"
         "population_before_stream,population_after_stream,population_after_poststream_communication,"
         "population_after_bouzidi,xb_i_after_comm,xs_i_after_comm,xf_opp_after_comm,"
         "bouzidi_expected,counterfactual_old_bouzidi_expected,delta_mass_stream_kg,"
         "delta_mass_communication_kg,delta_mass_bouzidi_kg,counterfactual_old_bouzidi_delta_mass_kg,"
         "delta_mass_link_total_kg\n";
  };
  auto row=[](std::ofstream& out,const LinkRecord& a) {
    out<<a.owner[0]<<','<<a.owner[1]<<','<<a.owner[2]<<','<<a.i<<','<<a.opp<<','
       <<a.neighbor[0]<<','<<a.neighbor[1]<<','<<a.neighbor[2]<<','<<a.crossesX<<','
       <<a.oldOwnerMat<<','<<a.newOwnerMat<<','<<a.oldNeighborMat<<','<<a.newNeighborMat<<','
       <<a.oldActive<<','<<a.newActive<<','<<a.qOld<<','<<a.qNew<<','<<a.vOld<<','<<a.vNew<<','
       <<a.preStream<<','<<a.postStream<<','<<a.postComm<<','<<a.postBouzidi<<','
       <<a.xbI<<','<<a.xsI<<','<<a.xfOpp<<','<<a.expected<<','<<a.oldExpected<<','<<a.deltaStreamMass<<','
       <<a.deltaCommMass<<','<<a.deltaBouzidiMass<<','<<a.counterfactualOldBouzidiMass<<','
       <<a.deltaStreamMass+a.deltaCommMass+a.deltaBouzidiMass<<'\n';
  };
  std::ofstream all(outDir/"affected_link_mass_ledger.csv");all<<std::setprecision(17)<<std::boolalpha;header(all);
  for(const auto& a:links)row(all,a);
  std::sort(links.begin(),links.end(),[](const auto& a,const auto& b) {
    return std::abs(a.deltaStreamMass+a.deltaCommMass+a.deltaBouzidiMass)
         > std::abs(b.deltaStreamMass+b.deltaCommMass+b.deltaBouzidiMass);
  });
  std::ofstream top(outDir/"top100_link_mass_contributions.csv");top<<std::setprecision(17)<<std::boolalpha;header(top);
  for(std::size_t i=0;i<std::min<std::size_t>(100,links.size());++i)row(top,links[i]);
}

} // namespace

int main(int argc,char** argv) {
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)return 2;
  const std::string runId="step5E_link_mass_ledger_3594_3595_v3_20260909";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"Refusing overwrite\n";return 2;}
  std::filesystem::create_directories(outDir);singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});
    geometry.communicate();SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for(int m:{1,4,5})lattice.iniEquilibrium(geometry,m,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();lattice.defineRho(geometry,4,one);lattice.defineRho(geometry,5,one);lattice.communicate();
    std::ofstream phases(outDir/"transaction_phase_log.csv");
    phases<<"step,phase,operation,fluid_to_solid_count,solid_to_fluid_count,affected_count,status\n";
    for(int step=1;step<eventStep;++step) {
      const T h=hAt(step,true);refreshLinks5E(lattice,geometry,h,wallSpeed(step,true));
      lattice.collide();lattice.AndStream();
    }
    const T hOld=hAt(eventStep-1,true),hNew=hAt(eventStep,true);
    const auto oldMat=captureMaterials(geometry);const auto oldFields=captureLinkFields(lattice);
    const auto beforeTx=capturePopulations(lattice);
    auto tx=step55::beginTopologyTransaction(lattice,geometry,eventStep,hOld,hNew,phases);
    std::set<std::size_t> converted;
    for(const auto& c:tx.fluidToSolid)converted.insert(cellIndex(c.latticeR));
    step55::commitMaterialTopology(geometry,tx,phases);step55::assignConvertedDynamics(lattice,tx,phases);
    step55::initializeConvertedPopulations(lattice,tx,phases);
    const auto linkCounts=refreshLinks5E(lattice,geometry,hNew,wallSpeed(eventStep,true));
    const auto newMat=captureMaterials(geometry);const auto newFields=captureLinkFields(lattice);
    const auto afterTx=capturePopulations(lattice);
    lattice.collide();const auto afterCollision=capturePopulations(lattice);
    lattice.getBlock(0).stream();const auto afterStream=capturePopulations(lattice);
    lattice.getCommunicator(stage::PostStream()).communicate();const auto afterComm=capturePopulations(lattice);

    std::vector<LinkRecord> links;std::set<std::size_t> affectedCells;auto& block=lattice.getBlock(0);
    for(int iz=0;iz<NZ;++iz)for(int iy=0;iy<NY;++iy)for(int ix=0;ix<NX;++ix)for(int i=1;i<D::q;++i) {
      LatticeR<3> p{ix,iy,iz};auto raw=p+descriptors::c<D>(i),mapped=raw;
      const bool cross=raw[0]<0||raw[0]>=NX;if(cross)mapped[0]=wrapX5E(raw[0]);
      const bool neighborCore=inCore(mapped);const bool touches=converted.contains(cellIndex(p))
        ||(neighborCore&&converted.contains(cellIndex(mapped)));
      if(!touches)continue;
      const T qo=oldFields.first[popIndex(p,i)],qn=newFields.first[popIndex(p,i)];
      if(qo<0&&qn<0)continue;
      LinkRecord a;a.owner=p;a.neighbor=mapped;a.i=i;a.opp=descriptors::opposite<D>(i);a.crossesX=cross;
      a.oldOwnerMat=oldMat[cellIndex(p)];a.newOwnerMat=newMat[cellIndex(p)];
      a.oldNeighborMat=neighborCore?oldMat[cellIndex(mapped)]:0;a.newNeighborMat=neighborCore?newMat[cellIndex(mapped)]:0;
      a.qOld=qo;a.qNew=qn;a.vOld=oldFields.second[popIndex(p,i)];a.vNew=newFields.second[popIndex(p,i)];
      a.oldActive=qo>=0;a.newActive=qn>=0;a.preStream=afterCollision[popIndex(p,a.opp)];
      a.postStream=afterStream[popIndex(p,a.opp)];a.postComm=afterComm[popIndex(p,a.opp)];
      auto owner=block.get(p);const auto c=descriptors::c<D>(i);auto xs=owner.neighbor(c);auto xf=owner.neighbor(descriptors::c<D>(a.opp));
      a.xbI=owner[i];a.xsI=xs[i];a.xfOpp=xf[a.opp];a.expected=a.postComm;
      if(qn>0) {
        const T velo=a.vNew*descriptors::t<T,D>(i)*descriptors::invCs2<T,D>();
        a.expected=qn<=T(.5)?T(2)*qn*a.xsI+(T(1)-T(2)*qn)*a.xbI-T(2)*velo
          :T(.5)/qn*a.xsI+T(.5)*(T(2)*qn-T(1))/qn*a.xfOpp-T(1)/qn*velo;
      } else if(qn==0) {
        const T velo=a.vNew*descriptors::t<T,D>(i)*descriptors::invCs2<T,D>();a.expected=a.xbI-T(2)*velo;
      }
      const T aw=alpha5E(g.getPhysR(p),hNew);
      a.oldExpected=a.postComm;
      if(qo>0) {
        const T velo=a.vOld*descriptors::t<T,D>(i)*descriptors::invCs2<T,D>();
        a.oldExpected=qo<=T(.5)?T(2)*qo*a.xsI+(T(1)-T(2)*qo)*a.xbI-T(2)*velo
          :T(.5)/qo*a.xsI+T(.5)*(T(2)*qo-T(1))/qo*a.xfOpp-T(1)/qo*velo;
        a.counterfactualOldBouzidiMass=aw*(a.oldExpected-a.postComm)*massScale;
      } else if(qo==0) {
        const T velo=a.vOld*descriptors::t<T,D>(i)*descriptors::invCs2<T,D>();
        a.oldExpected=a.xbI-T(2)*velo;
        a.counterfactualOldBouzidiMass=aw*(a.oldExpected-a.postComm)*massScale;
      }
      a.deltaStreamMass=aw*(a.postStream-a.preStream)*massScale;
      a.deltaCommMass=aw*(a.postComm-a.postStream)*massScale;
      affectedCells.insert(cellIndex(p));if(neighborCore)affectedCells.insert(cellIndex(mapped));links.push_back(a);
    }
    block.template postProcess<stage::PostStream>();const auto afterBouzidi=capturePopulations(lattice);
    lattice.getCommunicator(stage::PostPostProcess()).communicate();
    T sumLink=0,sumOldClosure=0,sumTotalLink=0,maxPos=-std::numeric_limits<T>::max(),maxNeg=std::numeric_limits<T>::max(),maxFormulaError=0;
    int posIndex=-1,negIndex=-1;std::set<std::pair<std::size_t,int>> targets;long long duplicateTargets=0;
    for(std::size_t k=0;k<links.size();++k) {
      auto& a=links[k];a.postBouzidi=afterBouzidi[popIndex(a.owner,a.opp)];
      const T aw=alpha5E(g.getPhysR(a.owner),hNew);
      a.deltaBouzidiMass=aw*(a.postBouzidi-a.postComm)*massScale;sumLink+=a.deltaBouzidiMass;
      sumOldClosure+=a.counterfactualOldBouzidiMass;
      const T total=a.deltaStreamMass+a.deltaCommMass+a.deltaBouzidiMass;sumTotalLink+=total;
      if(total>maxPos){maxPos=total;posIndex=k;}
      if(total<maxNeg){maxNeg=total;negIndex=k;}
      if(a.newActive) {
        if(!targets.insert({cellIndex(a.owner),a.opp}).second)++duplicateTargets;
        maxFormulaError=std::max(maxFormulaError,std::abs(a.postBouzidi-a.expected));
      }
    }
    writeLinks(outDir,links);
    std::ofstream stages(outDir/"stage_mass_ledger.csv");stages<<std::setprecision(17);
    stages<<"stage,h_nm,global_M_pop_kg,affected_region_M_pop_kg,delta_global_from_previous_kg\n";
    T previous=massFromSnapshot(beforeTx,geometry,hOld);
    auto stage=[&](const char* name,const std::vector<T>& f,T h) {const T m=massFromSnapshot(f,geometry,h);
      stages<<name<<','<<h*1e9<<','<<m<<','<<massFromSnapshot(f,geometry,h,&affectedCells)<<','<<m-previous<<'\n';previous=m;};
    stage("before_transaction_hOld",beforeTx,hOld);stage("before_transaction_reweighted_hNew",beforeTx,hNew);
    stage("after_transaction_before_collision",afterTx,hNew);stage("after_collision",afterCollision,hNew);
    stage("after_stream_before_communication",afterStream,hNew);stage("after_poststream_communication",afterComm,hNew);
    stage("after_bouzidi",afterBouzidi,hNew);
    std::ofstream result(outDir/"result.txt");result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<"\nstep="<<eventStep<<"\nconverted_nodes="<<tx.fluidToSolid.size()
      <<"\naffected_links="<<links.size()<<"\nactive_links_after_refresh="<<linkCounts[0]
      <<"\nillegal_links="<<linkCounts[1]+linkCounts[3]<<"\nduplicate_bouzidi_targets="<<duplicateTargets
      <<"\nmax_bouzidi_formula_error="<<maxFormulaError<<"\nsum_affected_bouzidi_delta_mass_kg="<<sumLink
      <<"\nsum_counterfactual_deactivated_old_bouzidi_delta_mass_kg="<<sumOldClosure
      <<"\nsum_affected_link_total_mass_kg="<<sumTotalLink
      <<"\nmax_positive_link_index="<<posIndex<<"\nmax_positive_link_mass_kg="<<maxPos
      <<"\nmax_negative_link_index="<<negIndex<<"\nmax_negative_link_mass_kg="<<maxNeg<<"\nexit_code=0\n";
    std::ofstream manifest(outDir/"run_manifest.txt");manifest
      <<"model=SIM-EC1XT240\ncommand=mpirun -np 1 ./step5E_link_mass_ledger\n"
      <<"scope=step3594_to_3595_diagnostic_only\npopulation_policy=preserve\nexit_code=0\n";
    return 0;
  } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 4;}
}
