#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <sstream>

int tracePeriodicX(int ix)
{
  int wrapped=ix%48;
  return wrapped<0?wrapped+48:wrapped;
}

template<class G>
std::array<int,2> traceMarkPeriodicAwarePressureIntersections(G& geometry)
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
        if(neighbor[0]<0||neighbor[0]>=48)neighbor[0]=tracePeriodicX(neighbor[0]);
        const int neighborMaterial=g.getMaterial(neighbor);
        touchesSolid|=neighborMaterial==2||neighborMaterial==3;
      }
      if(touchesSolid){g.set(p,material==4?6:7);++marked[material==4?0:1];}
    });
  }
  geometry.communicate();return marked;
}

template<class L,class G>
std::array<int,4> traceUpdatePeriodicAwareLinks(L& lattice,G& geometry,T h,T uWall)
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
        if(crosses)mapped[0]=tracePeriodicX(raw[0]);
        const int rawMaterial=g.getMaterial(raw);
        const int material=crosses?g.getMaterial(mapped):rawMaterial;
        if(crosses&&(material==2||material==3)&&rawMaterial!=2&&rawMaterial!=3)
          ++missingPeriodicSolid;
        if(crosses&&(rawMaterial==2||rawMaterial==3)&&material!=2&&material!=3)
          ++extraPeriodicSolid;
        if(material!=2&&material!=3)continue;
        T q=.5,velocityCoefficient=0;
        if(material==3){
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
  }
  lattice.communicate();return{active,invalid,missingPeriodicSolid,extraPeriodicSolid};
}

struct F3Point {
  const char* name;
  LatticeR<3> p;
};

constexpr std::array<F3Point,11> f3Points {{
  {"target",                 {0,0,13}},
  {"donor",                  {0,0,14}},
  {"donor_z_plus",           {0,0,15}},
  {"donor_z_minus",          {0,0,13}},
  {"donor_y_interior",       {0,1,14}},
  {"donor_x_periodic",       {47,0,14}},
  {"donor_x_plus",           {1,0,14}},
  {"donor_y_high_counterpart",{0,47,14}},
  {"f8_stream_source",        {0,1,15}},
  {"f8_source_z_solid",       {0,1,16}},
  {"f8_source_y_plus",        {0,2,15}}
}};

template<class B,class G>
void writeF3Snapshot(std::ofstream& out,B& block,G& geometry,int step,
                     const char* stage,const F3Point& point)
{
  auto cell=block.get(point.p);
  const int material=geometry.getMaterial(point.p);
  T rhoBoundary=cell.computeRho(),uBoundary[3]{};
  cell.computeU(uBoundary);
  T rhoDirect=1,j[3]{},normalDriver=0;
  std::array<T,D::q> f{},rhoContribution{},jxContribution{},
                     jyContribution{},jzContribution{},normalContribution{};
  for(int i=0;i<D::q;++i){
    const auto c=descriptors::c<D>(i);
    f[i]=cell[i];
    rhoDirect+=f[i];
    for(int d=0;d<3;++d)j[d]+=f[i]*c[d];
    // OpenLB stores shifted populations: the physical population is f_i+w_i.
    rhoContribution[i]=f[i]+descriptors::t<T,D>(i);
    jxContribution[i]=f[i]*c[0];
    jyContribution[i]=f[i]*c[1];
    jzContribution[i]=f[i]*c[2];
    // Low-y LocalPressure (direction=1, orientation=-1) computes
    // u_y=-(2*rhoNormal+rhoOnWall+1-rho)/rho.  rho is fixed to one,
    // hence each shifted f with cy=-1 contributes -2*f and each cy=0
    // contributes -f to the reconstructed normal velocity numerator.
    if(c[1]==-1)normalContribution[i]=-2*f[i];
    else if(c[1]==0)normalContribution[i]=-f[i];
    normalDriver+=normalContribution[i];
  }
  const T directSpeed=std::sqrt(j[0]*j[0]+j[1]*j[1]+j[2]*j[2])/rhoDirect;
  const T boundarySpeed=std::sqrt(uBoundary[0]*uBoundary[0]
                                +uBoundary[1]*uBoundary[1]
                                +uBoundary[2]*uBoundary[2]);
  out<<step<<','<<stage<<','<<point.name<<','<<point.p[0]<<','<<point.p[1]
     <<','<<point.p[2]<<','<<material<<','<<rhoBoundary<<','<<uBoundary[0]
     <<','<<uBoundary[1]<<','<<uBoundary[2]<<','
     <<boundarySpeed/std::sqrt(T(1)/3)<<','<<rhoDirect<<','<<j[0]/rhoDirect
     <<','<<j[1]/rhoDirect<<','<<j[2]/rhoDirect<<','
     <<directSpeed/std::sqrt(T(1)/3)<<','<<normalDriver;
  for(T v:f)out<<','<<v;
  for(T v:rhoContribution)out<<','<<v;
  for(T v:jxContribution)out<<','<<v;
  for(T v:jyContribution)out<<','<<v;
  for(T v:jzContribution)out<<','<<v;
  for(T v:normalContribution)out<<','<<v;
  out<<'\n';
}

void writeF3Header(std::ofstream& out)
{
  out<<"step,stage,cell_name,ix,iy,iz,material,rho_boundary,ux_boundary,"
        "uy_boundary,uz_boundary,Mach_boundary,rho_direct_shifted,"
        "ux_direct_shifted,uy_direct_shifted,uz_direct_shifted,"
        "Mach_direct_shifted,localpressure_low_y_normal_driver";
  for(int i=0;i<D::q;++i)out<<",f"<<i;
  for(int i=0;i<D::q;++i)out<<",rho_contrib_f"<<i;
  for(int i=0;i<D::q;++i)out<<",jx_contrib_f"<<i;
  for(int i=0;i<D::q;++i)out<<",jy_contrib_f"<<i;
  for(int i=0;i<D::q;++i)out<<",jz_contrib_f"<<i;
  for(int i=0;i<D::q;++i)out<<",lp_normal_contrib_f"<<i;
  out<<'\n';
}

int runF3ReverseTrace(bool closedReference)
{
  const std::string runId=closedReference
    ?"f3_moving_closed_A_population_reference_20260908"
    :"f3_reverse_causal_trace_C_v3_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){
    std::cerr<<"Refusing to overwrite "<<outDir<<'\n';return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());

  IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);
  cuboids.setPeriodicity({true,false,false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  for(int iC=0;iC<loadBalancer.size();++iC){
    auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});
  }
  geometry.communicate();
  std::array<int,2> marked{};
  if(!closedReference)marked=traceMarkPeriodicAwarePressureIntersections(geometry);
  SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
  UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
  SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
  dynamics::set<BGKdynamics>(lattice,geometry,1);
  if(closedReference){
    boundary::set<boundary::BounceBack>(lattice,geometry,4);
    boundary::set<boundary::BounceBack>(lattice,geometry,5);
  }else{
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(6),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(7),geometry.getMaterialIndicator(1),outside);
  }
  dynamics::set<NoDynamics>(lattice,geometry,2);
  dynamics::set<NoDynamics>(lattice,geometry,3);
  AnalyticalConst3D<T,T> one(1),zero(0,0,0);
  lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
  for(int m:{1,4,5,6,7})lattice.iniEquilibrium(geometry,m,one,zero);
  lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
  lattice.initialize();

  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  std::ofstream trace(outDir/"f3_reverse_operator_trace.csv");
  trace<<std::setprecision(17);writeF3Header(trace);
  std::ofstream source(outDir/"f3_stream_source_check.csv");
  source<<std::setprecision(17)
        <<"step,donor_f3_post_collision_pre_comm,donor_f3_post_collision_post_comm,"
          "target_f3_pre_stream,target_f3_post_stream,exact_stream_copy_error\n";

  constexpr int last=220;
  for(int step=1;step<=last;++step){
    const auto links=traceUpdatePeriodicAwareLinks(lattice,geometry,hAt(step,true),wallSpeed(step,true));
    if(links[1]||links[3]){
      std::cerr<<"link audit failed at step "<<step<<'\n';return 3;
    }
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"pre_collision_after_full_communicate",point);
    lattice.executePostProcessors(stage::PreCollide{});
    lattice.executeCustomTasks(stage::PreCollide{});
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"post_PreCollide_pre_collision",point);
    for(int iC=0;iC<loadBalancer.size();++iC)lattice.getBlock(iC).collide();
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"post_LP_reconstruction_and_collision_pre_comm",point);
    const T donorBeforeComm=block.get({0,0,14})[3];
    lattice.getCommunicator(stage::PostCollide{}).communicate();
    const T donorAfterComm=block.get({0,0,14})[3];
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"post_PostCollide_comm",point);
    for(int iC=0;iC<loadBalancer.size();++iC)
      lattice.getBlock(iC).template postProcess<stage::PostCollide>();
    const T targetBeforeStream=block.get({0,0,13})[3];
    for(int iC=0;iC<loadBalancer.size();++iC)lattice.getBlock(iC).stream();
    const T targetAfterStream=block.get({0,0,13})[3];
    source<<step<<','<<donorBeforeComm<<','<<donorAfterComm<<','<<targetBeforeStream
          <<','<<targetAfterStream<<','<<(targetAfterStream-donorAfterComm)<<'\n';
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"post_stream_pre_PostStream_comm",point);
    lattice.getCommunicator(stage::PostStream{}).communicate();
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"post_PostStream_comm_pre_Bouzidi",point);
    for(int iC=0;iC<loadBalancer.size();++iC)
      lattice.getBlock(iC).template postProcess<stage::PostStream>();
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"post_moving_Bouzidi_PostStream",point);
    lattice.executeCustomTasks(stage::PostStream{});
    lattice.getCommunicator(stage::PostPostProcess{}).communicate();
    for(const auto& point:f3Points)
      writeF3Snapshot(trace,block,g,step,"post_PostPostProcess_comm",point);
  }
  std::ofstream record(outDir/"run_record.txt");
  record<<"run_id="<<runId<<"\ncommand=./explicit_piston_f3_reverse_trace\n"
        <<"case="<<(closedReference?"A_moving_Bouzidi_closed_sides_population_reference":
                                      "C_moving_Bouzidi_LocalPressure")
        <<"\nsteps=220\ntrace_window=1..220\nmaterial_conversion_enabled=false\n"
        <<"periodic_aware_solid_links=true\nintersection_low_cells="<<marked[0]
        <<"\nintersection_high_cells="<<marked[1]
        <<"\nexit_code=0\nexit_reason=targeted_f3_reverse_trace_completed\n";
  return 0;
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1)return 2;
  if(argc!=2)return 2;
  const std::string mode=argv[1];
  if(mode=="A")return runF3ReverseTrace(true);
  if(mode=="C")return runF3ReverseTrace(false);
  return 2;
}
