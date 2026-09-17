#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <map>

struct SeamPoint {
  const char* name;
  LatticeR<3> p;
  bool core;
};

constexpr std::array<SeamPoint,16> seamPoints {{
  {"new_alarm",             {0,0,13}, true},
  {"periodic_counterpart",  {47,0,13}, true},
  {"left_x_halo",           {-1,0,13}, false},
  {"right_x_halo",          {48,0,13}, false},
  {"y_interior",            {0,1,13}, true},
  {"z_minus",               {0,0,12}, true},
  {"z_plus",                {0,0,14}, true},
  {"old_alarm",             {0,0,14}, true},
  {"old_dual",              {0,0,15}, true},
  {"old_dual_periodic",     {47,0,15}, true},
  {"mapped_missing_solid",  {47,0,16}, true},
  {"high_y_seam",           {0,47,13}, true}
  ,{"x1_same_layer",         {1,0,13}, true}
  ,{"x6_same_layer",         {6,0,13}, true}
  ,{"x12_same_layer",        {12,0,13}, true}
  ,{"x24_same_layer",        {24,0,13}, true}
}};

int wrapX(int ix)
{
  int wrapped=ix%48;
  return wrapped<0?wrapped+48:wrapped;
}

template<class B,class G>
void writeSeamSnapshot(std::ofstream& out,B& block,G& geometry,
                       int step,const char* stage,const SeamPoint& point)
{
  auto cell=block.get(point.p);
  T rhoDirect=1,j[3]{};
  std::array<T,D::q> f{},q{};
  for(int i=0;i<D::q;++i){
    f[i]=cell[i];rhoDirect+=f[i];
    const auto c=descriptors::c<D>(i);
    for(int d=0;d<3;++d)j[d]+=f[i]*c[d];
    q[i]=cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
  }
  T rhoBoundary=std::numeric_limits<T>::quiet_NaN();
  T uBoundary[3]{std::numeric_limits<T>::quiet_NaN(),
                 std::numeric_limits<T>::quiet_NaN(),
                 std::numeric_limits<T>::quiet_NaN()};
  int material=geometry.getMaterial(point.p);
  std::string dynamics="halo/no-core-dynamics";
  if(point.core){
    rhoBoundary=cell.computeRho();cell.computeU(uBoundary);
    dynamics=typeid(*block.getDynamics(point.p[0],point.p[1],point.p[2])).name();
  }
  const T directSpeed=std::sqrt(j[0]*j[0]+j[1]*j[1]+j[2]*j[2])/rhoDirect;
  const T boundarySpeed=std::sqrt(uBoundary[0]*uBoundary[0]
                                +uBoundary[1]*uBoundary[1]
                                +uBoundary[2]*uBoundary[2]);
  out<<step<<','<<stage<<','<<point.name<<','<<point.p[0]<<','<<point.p[1]<<','
     <<point.p[2]<<','<<material<<','<<point.core<<','<<std::quoted(dynamics)<<','
     <<rhoBoundary<<','<<uBoundary[0]<<','<<uBoundary[1]<<','<<uBoundary[2]<<','
     <<boundarySpeed/std::sqrt(T(1)/3)<<','<<rhoDirect<<','<<j[0]/rhoDirect<<','
     <<j[1]/rhoDirect<<','<<j[2]/rhoDirect<<','<<directSpeed/std::sqrt(T(1)/3);
  for(T v:f)out<<','<<v;
  for(T v:q)out<<','<<v;
  out<<'\n';
}

void writeSeamHeader(std::ofstream& out)
{
  out<<"step,stage,cell_name,ix,iy,iz,material,is_core,dynamics_rtti,"
     <<"rho_boundary,ux_boundary,uy_boundary,uz_boundary,Mach_boundary,"
     <<"rho_direct_shifted,ux_direct_shifted,uy_direct_shifted,"
     <<"uz_direct_shifted,Mach_direct_shifted";
  for(int i=0;i<D::q;++i)out<<",f"<<i;
  for(int i=0;i<D::q;++i)out<<",q"<<i;
  out<<'\n';
}

struct DirectionValues {
  T rawBefore=0,mappedBefore=0,rawAfter=0,mappedAfter=0;
  T targetAfterStream=0,targetAfterPostStreamComm=0,targetAfterBouzidi=0;
};

int runSeamDiagnostic()
{
  const std::string runId="periodic_seam_operator_diag_v3baseline_v2_20260907";
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
  const auto marked=markIntersectionPressureCells(geometry);
  SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
  UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
  SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
  dynamics::set<BGKdynamics>(lattice,geometry,1);
  boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(6),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(7),geometry.getMaterialIndicator(1),outside);
  dynamics::set<NoDynamics>(lattice,geometry,2);
  dynamics::set<NoDynamics>(lattice,geometry,3);
  AnalyticalConst3D<T,T> one(1),zero(0,0,0);
  lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
  for(int m:{1,4,5,6,7})lattice.iniEquilibrium(geometry,m,one,zero);
  lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
  lattice.initialize();

  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  std::ofstream trace(outDir/"periodic_seam_operator_trace.csv");
  trace<<std::setprecision(17);writeSeamHeader(trace);
  std::array<DirectionValues,D::q> tableValues{};
  constexpr int tableStep=200;

  for(int step=1;step<=220;++step){
    const auto links=updateLinks(lattice,geometry,hAt(step,true),wallSpeed(step,true));
    if(links[1]||links[4]){
      std::cerr<<"link audit failed at "<<step<<'\n';return 3;
    }
    if(step>=180){
      for(const auto& point:seamPoints)
        writeSeamSnapshot(trace,block,g,step,"pre_collision_after_full_communicate",point);
    }
    lattice.executePostProcessors(stage::PreCollide{});
    lattice.executeCustomTasks(stage::PreCollide{});
    for(int iC=0;iC<loadBalancer.size();++iC)lattice.getBlock(iC).collide();
    if(step>=180){
      for(const auto& point:seamPoints)
        writeSeamSnapshot(trace,block,g,step,"post_collision_pre_PostCollide_comm",point);
    }
    if(step==tableStep){
      const LatticeR<3> target{0,0,13};
      for(int i=0;i<D::q;++i){
        const auto c=descriptors::c<D>(i);
        LatticeR<3> raw{target[0]-c[0],target[1]-c[1],target[2]-c[2]};
        LatticeR<3> mapped{wrapX(raw[0]),raw[1],raw[2]};
        tableValues[i].rawBefore=block.get(raw)[i];
        tableValues[i].mappedBefore=block.get(mapped)[i];
      }
    }
    lattice.getCommunicator(stage::PostCollide{}).communicate();
    if(step>=180){
      for(const auto& point:seamPoints)
        writeSeamSnapshot(trace,block,g,step,"post_PostCollide_comm_pre_processor",point);
    }
    if(step==tableStep){
      const LatticeR<3> target{0,0,13};
      for(int i=0;i<D::q;++i){
        const auto c=descriptors::c<D>(i);
        LatticeR<3> raw{target[0]-c[0],target[1]-c[1],target[2]-c[2]};
        LatticeR<3> mapped{wrapX(raw[0]),raw[1],raw[2]};
        tableValues[i].rawAfter=block.get(raw)[i];
        tableValues[i].mappedAfter=block.get(mapped)[i];
      }
    }
    for(int iC=0;iC<loadBalancer.size();++iC)
      lattice.getBlock(iC).template postProcess<stage::PostCollide>();
    for(int iC=0;iC<loadBalancer.size();++iC)lattice.getBlock(iC).stream();
    if(step>=180){
      for(const auto& point:seamPoints)
        writeSeamSnapshot(trace,block,g,step,"post_stream_pre_PostStream_comm",point);
    }
    if(step==tableStep){
      auto target=block.get({0,0,13});
      for(int i=0;i<D::q;++i)tableValues[i].targetAfterStream=target[i];
    }
    lattice.getCommunicator(stage::PostStream{}).communicate();
    if(step>=180){
      for(const auto& point:seamPoints)
        writeSeamSnapshot(trace,block,g,step,"post_PostStream_comm_pre_Bouzidi",point);
    }
    if(step==tableStep){
      auto target=block.get({0,0,13});
      for(int i=0;i<D::q;++i)tableValues[i].targetAfterPostStreamComm=target[i];
    }
    for(int iC=0;iC<loadBalancer.size();++iC)
      lattice.getBlock(iC).template postProcess<stage::PostStream>();
    if(step>=180){
      for(const auto& point:seamPoints)
        writeSeamSnapshot(trace,block,g,step,"post_Bouzidi_PostStream",point);
    }
    if(step==tableStep){
      auto target=block.get({0,0,13});
      for(int i=0;i<D::q;++i)tableValues[i].targetAfterBouzidi=target[i];
    }
    lattice.executeCustomTasks(stage::PostStream{});
    lattice.getCommunicator(stage::PostPostProcess{}).communicate();
    if(step>=180){
      for(const auto& point:seamPoints)
        writeSeamSnapshot(trace,block,g,step,"post_PostPostProcess_comm",point);
    }
  }

  std::ofstream topology(outDir/"periodic_mapped_population_sources_step200.csv");
  topology<<std::setprecision(17)
    <<"direction,cx,cy,cz,opposite,raw_stream_source_ix,raw_stream_source_iy,"
    <<"raw_stream_source_iz,crosses_x_periodic,mapped_source_ix,mapped_source_iy,"
    <<"mapped_source_iz,raw_source_material,mapped_source_material,"
    <<"mapped_source_LocalPressure,mapped_source_ZouHePressure,"
    <<"mapped_source_has_Bouzidi_link,target_q,raw_f_before_PostCollide_comm,"
    <<"mapped_f_before_PostCollide_comm,raw_f_after_PostCollide_comm,"
    <<"mapped_f_after_PostCollide_comm,target_f_after_stream,"
    <<"target_f_after_PostStream_comm,target_f_after_Bouzidi\n";
  const LatticeR<3> target{0,0,13};
  for(int i=0;i<D::q;++i){
    const auto c=descriptors::c<D>(i);
    LatticeR<3> raw{target[0]-c[0],target[1]-c[1],target[2]-c[2]};
    const bool crosses=raw[0]<0||raw[0]>=48;
    LatticeR<3> mapped{wrapX(raw[0]),raw[1],raw[2]};
    const int rawMaterial=g.getMaterial(raw),mappedMaterial=g.getMaterial(mapped);
    bool mappedBouzidi=false;
    auto mappedCell=block.get(mapped);
    for(int q=1;q<D::q;++q)
      mappedBouzidi|=mappedCell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(q)>=0;
    topology<<i<<','<<c[0]<<','<<c[1]<<','<<c[2]<<','<<descriptors::opposite<D>(i)
      <<','<<raw[0]<<','<<raw[1]<<','<<raw[2]<<','<<crosses<<','<<mapped[0]<<','
      <<mapped[1]<<','<<mapped[2]<<','<<rawMaterial<<','<<mappedMaterial<<','
      <<(mappedMaterial==4||mappedMaterial==5)<<','<<(mappedMaterial==6||mappedMaterial==7)
      <<','<<mappedBouzidi<<','
      <<block.get(target).template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i)
      <<','<<tableValues[i].rawBefore<<','<<tableValues[i].mappedBefore<<','
      <<tableValues[i].rawAfter<<','<<tableValues[i].mappedAfter<<','
      <<tableValues[i].targetAfterStream<<','<<tableValues[i].targetAfterPostStreamComm
      <<','<<tableValues[i].targetAfterBouzidi<<'\n';
  }
  std::ofstream linkMap(outDir/"periodic_mapped_link_neighbors_step200.csv");
  linkMap<<std::setprecision(17)
    <<"cell_name,ix,iy,iz,direction,cx,cy,cz,opposite,raw_neighbor_ix,"
    <<"raw_neighbor_iy,raw_neighbor_iz,crosses_x_periodic,mapped_neighbor_ix,"
    <<"mapped_neighbor_iy,mapped_neighbor_iz,raw_neighbor_material,"
    <<"mapped_neighbor_material,stored_q,stored_velocity_coefficient,"
    <<"expected_solid_link_from_mapped_material\n";
  for(const auto& point:std::array<SeamPoint,3>{seamPoints[0],seamPoints[8],seamPoints[9]}){
    auto cell=block.get(point.p);
    for(int i=0;i<D::q;++i){
      const auto c=descriptors::c<D>(i);
      LatticeR<3> raw{point.p[0]+c[0],point.p[1]+c[1],point.p[2]+c[2]};
      const bool crosses=raw[0]<0||raw[0]>=48;
      LatticeR<3> mapped{wrapX(raw[0]),raw[1],raw[2]};
      const int rawMaterial=g.getMaterial(raw),mappedMaterial=g.getMaterial(mapped);
      linkMap<<point.name<<','<<point.p[0]<<','<<point.p[1]<<','<<point.p[2]
        <<','<<i<<','<<c[0]<<','<<c[1]<<','<<c[2]<<','<<descriptors::opposite<D>(i)
        <<','<<raw[0]<<','<<raw[1]<<','<<raw[2]<<','<<crosses<<','<<mapped[0]
        <<','<<mapped[1]<<','<<mapped[2]<<','<<rawMaterial<<','<<mappedMaterial
        <<','<<cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i)
        <<','<<cell.template getFieldComponent<descriptors::BOUZIDI_VELOCITY>(i)
        <<','<<(mappedMaterial==2||mappedMaterial==3)<<'\n';
    }
  }
  std::ofstream summary(outDir/"run_record.txt");
  summary<<"run_id="<<runId<<'\n'
         <<"command=./explicit_piston_periodic_seam_diag\n"
         <<"steps=220\ntrace_window=180..220\n"
         <<"intersection_low_cells="<<marked[0]<<'\n'
         <<"intersection_high_cells="<<marked[1]<<'\n'
         <<"material_conversion_enabled=false\nexit_code=0\n"
         <<"exit_reason=targeted_periodic_seam_trace_completed\n";
  return 0;
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1)return 2;
  return runSeamDiagnostic();
}
