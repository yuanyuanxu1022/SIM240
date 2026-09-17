#define main root_cause_boundary_base_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <map>
#include <set>
#include <sstream>
#include <tuple>
#include <vector>

constexpr int rcConversionStep=3595;

int rcWrapX(int i){int q=i%48;return q<0?q+48:q;}

int rcMaterialAt(const Vector<T,3>& r,T h)
{
  if(r[2]<0)return 2;
  if(punch(r[0],r[2],h))return 3;
  if(r[1]<dx)return 4;
  if(r[1]>Ly-dx)return 5;
  return 1;
}

T rcAlpha(const Vector<T,3>& r,T h)
{
  T x=std::fmod(r[0],Lx);if(x<0)x+=Lx;
  const T surface=(x<60e-9||x>=180e-9)?h:h+grooveDepth;
  return std::clamp((std::min(r[2]+dx/2,surface)-std::max(r[2]-dx/2,T(0)))/dx,T(0),T(1));
}

template<class CELL>
T rcDirectRho(CELL cell){T rho=1;for(int i=0;i<D::q;++i)rho+=cell[i];return rho;}

struct RCCell {
  LatticeR<3> p{};Vector<T,3> r{};int material=0;T rhoBoundary=0,rhoDirect=0;
  std::array<T,3> u{},j{};std::array<T,D::q> f{},q{},vc{};
};

template<class CELL>
RCCell rcSnapshot(CELL cell,int material,LatticeR<3> p,const Vector<T,3>& r)
{
  RCCell s;s.p=p;s.r=r;s.material=material;s.rhoBoundary=cell.computeRho();s.rhoDirect=rcDirectRho(cell);
  cell.computeU(s.u.data());
  for(int i=0;i<D::q;++i){
    s.f[i]=cell[i];s.q[i]=cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
    s.vc[i]=cell.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(i);
    for(int d=0;d<3;++d)s.j[d]+=s.f[i]*descriptors::c<D>(i,d);
  }
  return s;
}

template<class L,class G>
std::array<int,4> rcUpdateLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,recovered=0,falseSolid=0;
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p){
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i){cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);}
    if(!isFluidMaterial(g.getMaterial(p)))return;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i){
      const auto c=descriptors::c<D>(i);auto raw=p+c,mapped=raw;const bool crosses=raw[0]<0||raw[0]>=48;
      if(crosses)mapped[0]=rcWrapX(raw[0]);
      const int rawM=g.getMaterial(raw),solidM=crosses?g.getMaterial(mapped):rawM;
      if(crosses&&(solidM==2||solidM==3)&&rawM!=2&&rawM!=3)++recovered;
      if(crosses&&(rawM==2||rawM==3)&&solidM!=2&&solidM!=3)++falseSolid;
      if(solidM!=2&&solidM!=3)continue;
      T q=.5,vc=0;
      if(solidM==3){
        T lo=0,hi=1;
        for(int k=0;k<50;++k){const T a=(lo+hi)/2;T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;if(punch(x,r[2]+a*dx*c[2],h))hi=a;else lo=a;}
        q=(lo+hi)/2;vc=c[2]*uWall*dt/dx;
      }
      if(!(q>=0&&q<=1))++invalid;
      else{cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,vc);++active;}
    }
  });
  lattice.communicate();return{active,invalid,recovered,falseSolid};
}

struct RCBudget {
  long long fluidCells=0;T massBoundary=0,massDirect=0,geomBoundary=0,geomDirect=0;
  std::array<T,3> momentum{},geomMomentum{};std::array<T,D::q> shifted{},full{};
};

template<class L,class G>
RCBudget rcBudget(L& lattice,G& geometry,T h)
{
  RCBudget b;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    if(!isFluidMaterial(g.getMaterial(p)))return;
    auto s=rcSnapshot(block.get(p),g.getMaterial(p),p,g.getPhysR(p));const T alpha=rcAlpha(s.r,h);
    ++b.fluidCells;b.massBoundary+=s.rhoBoundary;b.massDirect+=s.rhoDirect;
    b.geomBoundary+=alpha*s.rhoBoundary;b.geomDirect+=alpha*s.rhoDirect;
    for(int d=0;d<3;++d){b.momentum[d]+=s.j[d];b.geomMomentum[d]+=alpha*s.j[d];}
    for(int i=0;i<D::q;++i){b.shifted[i]+=s.f[i];b.full[i]+=s.f[i]+descriptors::t<T,D>(i);}
  });return b;
}

struct RCExtrema {
  RCCell machCell,rhoMinCell,rhoMaxCell,popCell;T maxMach=-1,minRho=1e300,maxRho=-1e300,maxAbsPop=-1;int pop=-1;
};

template<class L,class G>
RCExtrema rcExtrema(L& lattice,G& geometry)
{
  RCExtrema e;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    if(!isFluidMaterial(g.getMaterial(p)))return;
    auto s=rcSnapshot(block.get(p),g.getMaterial(p),p,g.getPhysR(p));
    const T mach=std::sqrt(s.u[0]*s.u[0]+s.u[1]*s.u[1]+s.u[2]*s.u[2])/std::sqrt(T(1)/3);
    if(mach>e.maxMach){e.maxMach=mach;e.machCell=s;}if(s.rhoBoundary<e.minRho){e.minRho=s.rhoBoundary;e.rhoMinCell=s;}
    if(s.rhoBoundary>e.maxRho){e.maxRho=s.rhoBoundary;e.rhoMaxCell=s;}
    for(int i=0;i<D::q;++i)if(std::abs(s.f[i])>e.maxAbsPop){e.maxAbsPop=std::abs(s.f[i]);e.pop=i;e.popCell=s;}
  });return e;
}

using RCKey=std::tuple<int,int,int>;
struct RCReceiver {RCCell before,afterTransfer,afterStep;int sourceCount=0;std::array<T,D::q> received{};};

std::vector<LatticeR<3>> rcReceivers(const RCCell& source,auto& geometry,T h)
{
  auto& g=geometry.getBlockGeometry(0);std::vector<LatticeR<3>> out;
  const std::array<Vector<int,3>,5> offsets{Vector<int,3>{0,0,-1},Vector<int,3>{1,0,-1},Vector<int,3>{-1,0,-1},Vector<int,3>{0,1,-1},Vector<int,3>{0,-1,-1}};
  for(const auto& d:offsets){LatticeR<3> q=source.p+d;q[0]=rcWrapX(q[0]);if(q[1]<0||q[1]>=48)continue;
    if(isFluidMaterial(g.getMaterial(q))&&rcMaterialAt(g.getPhysR(q),h)!=3)out.push_back(q);}
  return out;
}

void rcWriteBudget(std::ofstream& out,const std::string& phase,const RCBudget& b,const RCBudget& ref)
{
  const T cellMass=rhoPhys*dx*dx*dx,velocityScale=dx/dt;
  out<<phase<<','<<b.fluidCells<<','<<b.massBoundary*cellMass<<','<<b.massDirect*cellMass<<','
     <<b.geomBoundary*cellMass<<','<<b.geomDirect*cellMass<<','<<(b.geomBoundary-ref.geomBoundary)*cellMass<<','
     <<(b.geomDirect-ref.geomDirect)*cellMass;
  for(int d=0;d<3;++d)out<<','<<b.momentum[d]*cellMass*velocityScale;
  for(int d=0;d<3;++d)out<<','<<b.geomMomentum[d]*cellMass*velocityScale;
  for(int i=0;i<D::q;++i){out<<','<<b.shifted[i];}
  for(int i=0;i<D::q;++i){out<<','<<b.full[i];}
  out<<'\n';
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)return 2;
  const std::string runId="conversion_root_cause_diag_v1_20260908";const auto out=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(out)){std::cerr<<"Refusing to overwrite "<<out<<'\n';return 2;}std::filesystem::create_directories(out);singleton::directories().setOutputDir((out.string()+"/").c_str());
  try{
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> load(cuboids);SuperGeometry<T,3> geometry(cuboids,load,overlap);auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});geometry.communicate();
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);SuperLattice<T,D> lattice(converter,cuboids,load);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);for(int m:{1,4,5})lattice.iniEquilibrium(geometry,m,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});lattice.initialize();lattice.defineRho(geometry,4,one);lattice.defineRho(geometry,5,one);lattice.communicate();
    std::array<int,4> links{};for(int step=1;step<rcConversionStep;++step){links=rcUpdateLinks(lattice,geometry,hAt(step,true),wallSpeed(step,true));lattice.collideAndStream();}
    const T hPrev=hAt(rcConversionStep-1,true),hNow=hAt(rcConversionStep,true);
    const RCBudget budgetBeforePrev=rcBudget(lattice,geometry,hPrev),budgetBefore=rcBudget(lattice,geometry,hNow);
    auto& block=lattice.getBlock(0);std::vector<RCCell> sources;
    g.forCoreSpatialLocations([&](LatticeR<3> p){if(isFluidMaterial(g.getMaterial(p))&&rcMaterialAt(g.getPhysR(p),hNow)==3)sources.push_back(rcSnapshot(block.get(p),g.getMaterial(p),p,g.getPhysR(p)));});
    std::map<RCKey,RCReceiver> receivers;
    for(const auto& source:sources)for(const auto& q:rcReceivers(source,geometry,hNow))receivers[{q[0],q[1],q[2]}];
    for(auto& [key,r]:receivers){LatticeR<3> p{std::get<0>(key),std::get<1>(key),std::get<2>(key)};r.before=rcSnapshot(block.get(p),g.getMaterial(p),p,g.getPhysR(p));}

    std::ofstream linkCsv(out/"conversion_link_change.csv");linkCsv<<std::setprecision(17)<<"phase,converted_ix,converted_iy,converted_iz,owner_ix,owner_iy,owner_iz,direction,opposite,q,wall_velocity_coefficient\n";
    long long oldLinks=0;
    for(const auto& source:sources)for(int i=1;i<D::q;++i)if(source.q[i]>=0){linkCsv<<"before,"<<source.p[0]<<','<<source.p[1]<<','<<source.p[2]<<','<<source.p[0]<<','<<source.p[1]<<','<<source.p[2]<<','<<i<<','<<descriptors::opposite<D>(i)<<','<<source.q[i]<<','<<source.vc[i]<<'\n';++oldLinks;}

    for(const auto& source:sources){const auto rr=rcReceivers(source,geometry,hNow);const T alpha=rcAlpha(source.r,hNow);
      for(const auto& q:rr){auto& info=receivers[{q[0],q[1],q[2]}];++info.sourceCount;auto dst=block.get(q);
        for(int i=0;i<D::q;++i){const T add=alpha*(source.f[i]+descriptors::t<T,D>(i))/rr.size();dst[i]+=add;info.received[i]+=add;}}
    }
    for(auto& [key,r]:receivers){LatticeR<3> p{std::get<0>(key),std::get<1>(key),std::get<2>(key)};r.afterTransfer=rcSnapshot(block.get(p),g.getMaterial(p),p,g.getPhysR(p));}
    for(const auto& source:sources){g.set(source.p,3);block.template defineDynamics<NoDynamics>(source.p);}geometry.communicate();lattice.communicate();
    links=rcUpdateLinks(lattice,geometry,hNow,wallSpeed(rcConversionStep,true));long long newLinks=0;
    for(const auto& source:sources)for(int i=1;i<D::q;++i){const auto c=descriptors::c<D>(i);LatticeR<3> owner=source.p-c;owner[0]=rcWrapX(owner[0]);
      if(owner[1]<0||owner[1]>=48||owner[2]<0||!isFluidMaterial(g.getMaterial(owner)))continue;
      auto cell=block.get(owner);const T q=cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
      if(q>=0){linkCsv<<"after,"<<source.p[0]<<','<<source.p[1]<<','<<source.p[2]<<','<<owner[0]<<','<<owner[1]<<','<<owner[2]<<','<<i<<','<<descriptors::opposite<D>(i)<<','<<q<<','<<cell.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(i)<<'\n';++newLinks;}}
    const RCBudget budgetAfterConversion=rcBudget(lattice,geometry,hNow);const auto extremaAfterTransfer=rcExtrema(lattice,geometry);
    lattice.collideAndStream();const RCBudget budgetAfterStep=rcBudget(lattice,geometry,hNow);const auto extremaAfterStep=rcExtrema(lattice,geometry);
    for(auto& [key,r]:receivers){LatticeR<3> p{std::get<0>(key),std::get<1>(key),std::get<2>(key)};r.afterStep=rcSnapshot(block.get(p),g.getMaterial(p),p,g.getPhysR(p));}

    std::ofstream budgetCsv(out/"conversion_mass_momentum_budget.csv");budgetCsv<<std::setprecision(17)
      <<"phase,fluid_cells,M_full_boundary_kg,M_full_direct_kg,M_geom_boundary_kg,M_geom_direct_kg,delta_M_geom_boundary_kg,delta_M_geom_direct_kg,"
        "momentum_x_kg_m_s,momentum_y_kg_m_s,momentum_z_kg_m_s,geom_momentum_x_kg_m_s,geom_momentum_y_kg_m_s,geom_momentum_z_kg_m_s";
    for(int i=0;i<D::q;++i){budgetCsv<<",sum_shifted_f"<<i;}
    for(int i=0;i<D::q;++i){budgetCsv<<",sum_full_F"<<i;}
    budgetCsv<<'\n';
    rcWriteBudget(budgetCsv,"before_at_h_previous",budgetBeforePrev,budgetBefore);
    rcWriteBudget(budgetCsv,"before_at_conversion_h",budgetBefore,budgetBefore);
    rcWriteBudget(budgetCsv,"after_conversion_before_collision",budgetAfterConversion,budgetBefore);
    rcWriteBudget(budgetCsv,"after_first_collide_stream",budgetAfterStep,budgetBefore);

    std::ofstream popCsv(out/"conversion_population_trace.csv");popCsv<<std::setprecision(17)
      <<"direction,cx,cy,cz,opposite,sum_shifted_before,sum_shifted_after_conversion,delta_shifted_active_fluid,sum_full_before,sum_full_after_conversion,delta_full_active_fluid,max_abs_cell_delta,max_delta_ix,max_delta_iy,max_delta_iz,max_delta_material,after_first_step_sum_shifted\n";
    for(int i=0;i<D::q;++i){T maxDelta=0;RCCell maxCell;
      for(const auto& source:sources)if(std::abs(source.f[i])>maxDelta){maxDelta=std::abs(source.f[i]);maxCell=source;}
      for(const auto& [key,r]:receivers){const T d=r.afterTransfer.f[i]-r.before.f[i];if(std::abs(d)>maxDelta){maxDelta=std::abs(d);maxCell=r.afterTransfer;}}
      popCsv<<i<<','<<descriptors::c<D>(i,0)<<','<<descriptors::c<D>(i,1)<<','<<descriptors::c<D>(i,2)<<','<<descriptors::opposite<D>(i)<<','
        <<budgetBefore.shifted[i]<<','<<budgetAfterConversion.shifted[i]<<','<<budgetAfterConversion.shifted[i]-budgetBefore.shifted[i]<<','
        <<budgetBefore.full[i]<<','<<budgetAfterConversion.full[i]<<','<<budgetAfterConversion.full[i]-budgetBefore.full[i]<<','<<maxDelta<<','
        <<maxCell.p[0]<<','<<maxCell.p[1]<<','<<maxCell.p[2]<<','<<maxCell.material<<','<<budgetAfterStep.shifted[i]<<'\n';}

    std::ofstream receiverCsv(out/"receiver_mass_distribution.csv");receiverCsv<<std::setprecision(17)
      <<"ix,iy,iz,x_nm,y_nm,z_nm,material,source_count,received_mass_lattice,received_mass_kg,received_jx,received_jy,received_jz,"
        "rho_boundary_before,rho_direct_before,rho_boundary_after_transfer,rho_direct_after_transfer,Mach_after_transfer,rho_boundary_after_step,rho_direct_after_step,Mach_after_step";
    for(int i=0;i<D::q;++i){receiverCsv<<",received_F"<<i;}
    receiverCsv<<'\n';
    for(const auto& [key,r]:receivers){T mass=0;std::array<T,3> j{};for(int i=0;i<D::q;++i){mass+=r.received[i];for(int d=0;d<3;++d)j[d]+=r.received[i]*descriptors::c<D>(i,d);}
      auto mach=[](const RCCell& s){return std::sqrt(s.u[0]*s.u[0]+s.u[1]*s.u[1]+s.u[2]*s.u[2])/std::sqrt(T(1)/3);};
      receiverCsv<<r.before.p[0]<<','<<r.before.p[1]<<','<<r.before.p[2]<<','<<r.before.r[0]*1e9<<','<<r.before.r[1]*1e9<<','<<r.before.r[2]*1e9<<','<<r.before.material<<','<<r.sourceCount<<','<<mass<<','<<mass*rhoPhys*dx*dx*dx<<','<<j[0]<<','<<j[1]<<','<<j[2]<<','
        <<r.before.rhoBoundary<<','<<r.before.rhoDirect<<','<<r.afterTransfer.rhoBoundary<<','<<r.afterTransfer.rhoDirect<<','<<mach(r.afterTransfer)<<','<<r.afterStep.rhoBoundary<<','<<r.afterStep.rhoDirect<<','<<mach(r.afterStep);
      for(T f:r.received){receiverCsv<<','<<f;}
      receiverCsv<<'\n';}

    auto writeExtreme=[](std::ofstream& f,const std::string& phase,const std::string& kind,const RCCell& c,T value,int pop){
      f<<phase<<','<<kind<<','<<value<<','<<c.p[0]<<','<<c.p[1]<<','<<c.p[2]<<','<<c.r[0]*1e9<<','<<c.r[1]*1e9<<','<<c.r[2]*1e9<<','<<c.material<<','<<c.rhoBoundary<<','<<c.rhoDirect<<','<<c.u[0]<<','<<c.u[1]<<','<<c.u[2]<<','<<pop;
      for(T x:c.f){f<<','<<x;}
      f<<'\n';};
    std::ofstream anomaly(out/"first_anomaly_cells.csv");anomaly<<std::setprecision(17)<<"phase,kind,value,ix,iy,iz,x_nm,y_nm,z_nm,material,rho_boundary,rho_direct,ux,uy,uz,population_index";
    for(int i=0;i<D::q;++i){anomaly<<",f"<<i;}
    anomaly<<'\n';
    writeExtreme(anomaly,"after_conversion_before_collision","max_Mach",extremaAfterTransfer.machCell,extremaAfterTransfer.maxMach,-1);
    writeExtreme(anomaly,"after_conversion_before_collision","rho_min",extremaAfterTransfer.rhoMinCell,extremaAfterTransfer.minRho,-1);
    writeExtreme(anomaly,"after_conversion_before_collision","rho_max",extremaAfterTransfer.rhoMaxCell,extremaAfterTransfer.maxRho,-1);
    writeExtreme(anomaly,"after_conversion_before_collision","max_abs_population",extremaAfterTransfer.popCell,extremaAfterTransfer.maxAbsPop,extremaAfterTransfer.pop);
    writeExtreme(anomaly,"after_first_collide_stream","max_Mach",extremaAfterStep.machCell,extremaAfterStep.maxMach,-1);
    writeExtreme(anomaly,"after_first_collide_stream","rho_min",extremaAfterStep.rhoMinCell,extremaAfterStep.minRho,-1);
    writeExtreme(anomaly,"after_first_collide_stream","rho_max",extremaAfterStep.rhoMaxCell,extremaAfterStep.maxRho,-1);
    writeExtreme(anomaly,"after_first_collide_stream","max_abs_population",extremaAfterStep.popCell,extremaAfterStep.maxAbsPop,extremaAfterStep.pop);

    std::ofstream manifest(out/"run_manifest.txt");manifest<<std::setprecision(17)<<std::boolalpha
      <<"model_name=SIM-EC1XT240\nrun_id="<<runId<<"\ncommand=mpirun -np 1 ./explicit_piston_conversion_root_cause_diag\n"
      <<"openlb_version="<<OLB_VERSION<<"\nconversion_step="<<rcConversionStep<<"\nconverted_nodes="<<sources.size()<<"\nold_bouzidi_links="<<oldLinks
      <<"\nnew_bouzidi_links="<<newLinks<<"\nactive_links_after="<<links[0]<<"\ninvalid_links="<<links[1]<<"\nrecovered_periodic_links="<<links[2]
      <<"\nfalse_solid_links="<<links[3]<<"\nmax_Mach_before_collision="<<extremaAfterTransfer.maxMach<<"\nmax_Mach_after_step="<<extremaAfterStep.maxMach
      <<"\nrho_range_after_step="<<extremaAfterStep.minRho<<','<<extremaAfterStep.maxRho<<"\nstep5_algorithm_modified=false\nstep6_executed=false\nexit_code=0\n";
    return sources.size()==2304&&links[1]==0&&links[3]==0?0:3;
  }catch(const std::exception& e){std::ofstream(out/"failure.txt")<<e.what()<<'\n';std::cerr<<e.what()<<'\n';return 4;}
}
