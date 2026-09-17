#define main visualization_boundary_base_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <set>
#include <tuple>
#include <vector>

constexpr int visConversionStep=3595;

int visWrapX(int i){int q=i%48;return q<0?q+48:q;}

int visMaterialAt(const Vector<T,3>& r,T h)
{
  if(r[2]<0)return 2;
  if(punch(r[0],r[2],h))return 3;
  if(r[1]<dx)return 4;
  if(r[1]>Ly-dx)return 5;
  return 1;
}

template<class L,class G>
std::array<int,4> visUpdateLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,recovered=0,falseSolid=0;
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p){
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i){
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
    }
    if(!isFluidMaterial(g.getMaterial(p)))return;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i){
      const auto c=descriptors::c<D>(i);auto raw=p+c,mapped=raw;
      const bool crosses=raw[0]<0||raw[0]>=48;
      if(crosses)mapped[0]=visWrapX(raw[0]);
      const int rawM=g.getMaterial(raw),solidM=crosses?g.getMaterial(mapped):rawM;
      if(crosses&&(solidM==2||solidM==3)&&rawM!=2&&rawM!=3)++recovered;
      if(crosses&&(rawM==2||rawM==3)&&solidM!=2&&solidM!=3)++falseSolid;
      if(solidM!=2&&solidM!=3)continue;
      T q=.5,vc=0;
      if(solidM==3){
        T lo=0,hi=1;
        for(int k=0;k<50;++k){
          const T a=(lo+hi)/2;
          T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;
          if(punch(x,r[2]+a*dx*c[2],h))hi=a;else lo=a;
        }
        q=(lo+hi)/2;vc=c[2]*uWall*dt/dx;
      }
      if(!(q>=0&&q<=1))++invalid;
      else{
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,vc);
        ++active;
      }
    }
  });
  lattice.communicate();return{active,invalid,recovered,falseSolid};
}

template<class L,class G>
long long visConvert(L& lattice,G& geometry,T h)
{
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  struct Source{LatticeR<3> p;T rho;std::array<T,D::q> f;};
  std::vector<Source> sources;
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    if(isFluidMaterial(g.getMaterial(p))&&visMaterialAt(g.getPhysR(p),h)==3){
      auto cell=block.get(p);Source s{p,cell.computeRho(),{}};
      for(int i=0;i<D::q;++i){s.f[i]=cell[i];}
      sources.push_back(s);
    }
  });
  const std::array<Vector<int,3>,5> offsets{
    Vector<int,3>{0,0,-1},Vector<int,3>{1,0,-1},Vector<int,3>{-1,0,-1},
    Vector<int,3>{0,1,-1},Vector<int,3>{0,-1,-1}};
  for(const auto& source:sources){
    std::vector<LatticeR<3>> receivers;
    for(const auto& d:offsets){
      LatticeR<3> q=source.p+d;q[0]=visWrapX(q[0]);
      if(q[1]<0||q[1]>=48)continue;
      if(isFluidMaterial(g.getMaterial(q))&&visMaterialAt(g.getPhysR(q),h)!=3)receivers.push_back(q);
    }
    if(receivers.empty())throw std::runtime_error("visualization replay conversion receiver missing");
    const T alpha=std::clamp((std::min(source.p[2]*dx,((source.p[0]<12||source.p[0]>=36)?h:h+grooveDepth))
                             -std::max((source.p[2]-1)*dx,T(0)))/dx,T(0),T(1));
    for(const auto& q:receivers){
      auto dst=block.get(q);
      for(int i=0;i<D::q;++i)dst[i]+=alpha*(source.f[i]+descriptors::t<T,D>(i))/receivers.size();
    }
  }
  for(const auto& source:sources){g.set(source.p,3);block.template defineDynamics<NoDynamics>(source.p);}
  geometry.communicate();lattice.communicate();return sources.size();
}

void writePunchVtp(const std::filesystem::path& path,T h)
{
  const T nm=1e9;
  struct Quad{T x0,x1,z0,z1;bool vertical;};
  const std::array<Quad,5> q{{
    {0,60e-9,h,h,false},{180e-9,240e-9,h,h,false},
    {60e-9,180e-9,h+grooveDepth,h+grooveDepth,false},
    {60e-9,60e-9,h,h+grooveDepth,true},{180e-9,180e-9,h,h+grooveDepth,true}}};
  std::ofstream out(path);out<<std::setprecision(17);
  out<<"<?xml version=\"1.0\"?>\n<VTKFile type=\"PolyData\" version=\"1.0\" byte_order=\"LittleEndian\">\n"
       "<PolyData><Piece NumberOfPoints=\"20\" NumberOfPolys=\"5\"><Points>\n"
       "<DataArray type=\"Float64\" NumberOfComponents=\"3\" format=\"ascii\">\n";
  for(const auto& a:q){
    if(a.vertical)out<<a.x0*nm<<" 0 "<<a.z0*nm<<' '<<a.x0*nm<<' '<<Ly*nm<<' '<<a.z0*nm<<' '
                     <<a.x1*nm<<' '<<Ly*nm<<' '<<a.z1*nm<<' '<<a.x1*nm<<" 0 "<<a.z1*nm<<'\n';
    else out<<a.x0*nm<<" 0 "<<a.z0*nm<<' '<<a.x1*nm<<" 0 "<<a.z0*nm<<' '
            <<a.x1*nm<<' '<<Ly*nm<<' '<<a.z1*nm<<' '<<a.x0*nm<<' '<<Ly*nm<<' '<<a.z1*nm<<'\n';
  }
  out<<"</DataArray></Points><Polys><DataArray type=\"Int32\" Name=\"connectivity\" format=\"ascii\">";
  for(int i=0;i<5;++i)out<<4*i<<' '<<4*i+1<<' '<<4*i+2<<' '<<4*i+3<<' ';
  out<<"</DataArray><DataArray type=\"Int32\" Name=\"offsets\" format=\"ascii\">4 8 12 16 20"
       "</DataArray></Polys><CellData Scalars=\"surface_id\"><DataArray type=\"Int32\" Name=\"surface_id\" format=\"ascii\">1 1 2 3 4"
       "</DataArray></CellData></Piece></PolyData></VTKFile>\n";
}

template<class L,class G>
void writeState(const std::string& name,L& lattice,G& geometry,
                const UnitConverter<T,D>& converter,const std::filesystem::path& out,T h)
{
  SuperVTMwriter3D<T> writer(name,overlap);
  SuperGeometryF3D<T> material(geometry);material.getName()="material";
  SuperLatticeDensity3D<T,D> density(lattice);density.getName()="rho_lattice";
  SuperLatticePhysVelocity3D<T,D> velocity(lattice,converter);velocity.getName()="velocity_m_s";
  SuperLatticePhysPressure3D<T,D> pressure(lattice,converter);pressure.getName()="pressure_Pa";
  writer.addFunctor(material);writer.addFunctor(density);writer.addFunctor(velocity);writer.addFunctor(pressure);
  writer.createMasterFile();writer.write(0);
  writePunchVtp(out/(name+"_continuous_punch_nm.vtp"),h);
}

template<class G>
void auditState(std::ofstream& out,const std::string& state,G& geometry,T h,int active,int invalid,int recovered,int falseSolid)
{
  auto counts=materialCounts(geometry);auto& g=geometry.getBlockGeometry(0);
  long long mismatch=0,holes=0,seamMismatch=0;
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    if(g.getMaterial(p)!=visMaterialAt(g.getPhysR(p),h))++mismatch;
    if(isFluidMaterial(g.getMaterial(p))&&p[2]>=0&&p[2]<39){
      if(g.getMaterial({visWrapX(p[0]-1),p[1],p[2]})==0||g.getMaterial({visWrapX(p[0]+1),p[1],p[2]})==0)++holes;
    }
  });
  for(int iy=0;iy<48;++iy)for(int iz=0;iz<40;++iz)
    if(g.getMaterial({0,iy,iz})!=g.getMaterial({47,iy,iz}))++seamMismatch;
  out<<state<<','<<h*1e9<<','<<counts[0]<<','<<counts[1]<<','<<counts[2]<<','<<counts[3]
     <<','<<counts[4]<<','<<counts[5]<<','<<active<<','<<invalid<<','<<recovered<<','<<falseSolid
     <<','<<mismatch<<','<<holes<<','<<seamMismatch<<'\n';
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)return 2;
  const std::string runId="step5_geometry_visualization_v1_20260908";
  const auto out=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(out)){std::cerr<<"Refusing to overwrite "<<out<<'\n';return 2;}
  std::filesystem::create_directories(out);singleton::directories().setOutputDir((out.string()+"/").c_str());
  try{
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> load(cuboids);SuperGeometry<T,3> geometry(cuboids,load,overlap);
    auto& g=geometry.getBlockGeometry(0);g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,materialAt(g.getPhysR(p)));});geometry.communicate();
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);SuperLattice<T,D> lattice(converter,cuboids,load);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for(int m:{1,4,5})lattice.iniEquilibrium(geometry,m,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});lattice.initialize();
    lattice.defineRho(geometry,4,one);lattice.defineRho(geometry,5,one);lattice.communicate();
    std::ofstream audit(out/"geometry_visualization_audit.csv");
    audit<<"state,h_nm,material0,material1,material2,material3,material4,material5,active_links,invalid_links,recovered_periodic_links,false_solid_links,material_mismatch,fluid_holes,seam_material_mismatch\n";
    auto links=visUpdateLinks(lattice,geometry,75e-9,0);auditState(audit,"initial",geometry,75e-9,links[0],links[1],links[2],links[3]);
    writeState("state_initial",lattice,geometry,converter,out,75e-9);
    for(int step=1;step<visConversionStep;++step){
      const T h=hAt(step,true);links=visUpdateLinks(lattice,geometry,h,wallSpeed(step,true));lattice.collideAndStream();
    }
    const T hPre=hAt(visConversionStep-1,true);auditState(audit,"pre_conversion",geometry,hPre,links[0],links[1],links[2],links[3]);
    writeState("state_pre_conversion",lattice,geometry,converter,out,hPre);
    const T hPost=hAt(visConversionStep,true);const long long converted=visConvert(lattice,geometry,hPost);
    links=visUpdateLinks(lattice,geometry,hPost,wallSpeed(visConversionStep,true));lattice.collideAndStream();
    auditState(audit,"post_conversion",geometry,hPost,links[0],links[1],links[2],links[3]);
    writeState("state_post_conversion",lattice,geometry,converter,out,hPost);
    std::ofstream index(out/"visualization_state_index.csv");
    index<<"state,step,time_s,h_nm,displacement_nm,converted_nodes,field_basename,surface_file\n"
         <<"initial,0,0,75,0,0,state_initial,state_initial_continuous_punch_nm.vtp\n"
         <<"pre_conversion,"<<visConversionStep-1<<','<<(visConversionStep-1)*dt<<','<<hPre*1e9<<','<<(75e-9-hPre)*1e9<<",0,state_pre_conversion,state_pre_conversion_continuous_punch_nm.vtp\n"
         <<"post_conversion,"<<visConversionStep<<','<<visConversionStep*dt<<','<<hPost*1e9<<','<<(75e-9-hPost)*1e9<<','<<converted<<",state_post_conversion,state_post_conversion_continuous_punch_nm.vtp\n";
    std::ofstream record(out/"run_record.txt");record<<"run_id="<<runId<<"\ncommand=mpirun -np 1 ./step5_geometry_visualization_export\n"
      <<"purpose=visualization_replay_only\nlast_step="<<visConversionStep<<"\nconverted_nodes="<<converted
      <<"\nstep6_executed=false\nexit_code="<<(converted==2304&&links[1]==0&&links[3]==0?0:3)<<'\n';
    return converted==2304&&links[1]==0&&links[3]==0?0:3;
  }catch(const std::exception& e){std::ofstream(out/"failure.txt")<<e.what()<<'\n';std::cerr<<e.what()<<'\n';return 4;}
}
