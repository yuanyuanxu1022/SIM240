#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

constexpr T separatedLy=280e-9;
constexpr int separatedNy=56;
constexpr T movingY0=20e-9,movingY1=260e-9;

class SeparatedOutside final : public IndicatorF3D<T> {
public:
  SeparatedOutside()
  {
    this->_myMin={-1e9,-1e9,-1e9};this->_myMax={1e9,1e9,1e9};
    this->getName()="SeparatedOutside";
  }
  bool operator()(bool output[1],const T r[3]) override
  {
    const T eps=dx*1e-6;
    output[0]=r[1]<dx/2-eps||r[1]>separatedLy-dx/2+eps
             ||r[2]<-dx/2-eps||r[2]>192.5e-9+eps;
    return true;
  }
};

int sepWrapX(int ix)
{
  int wrapped=ix%48;return wrapped<0?wrapped+48:wrapped;
}

bool inMovingFootprint(T y)
{
  return y>=movingY0&&y<movingY1;
}

bool movingPunch(T x,T y,T z,T h)
{
  return inMovingFootprint(y)&&punch(x,z,h);
}

int separatedMaterialAt(const Vector<T,3>& r)
{
  if(r[2]<0)return 2;
  if(punch(r[0],r[2],75e-9))return inMovingFootprint(r[1])?3:8;
  if(r[1]<dx)return 4;
  if(r[1]>separatedLy-dx)return 5;
  return 1;
}

bool separatedFluid(int m)
{
  return m==1||m==4||m==5||m==6||m==7;
}

template<class G>
std::array<int,2> markSeparatedPressureIntersections(G& geometry)
{
  std::array<int,2> marked{};
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    const int m=g.getMaterial(p);if(m!=4&&m!=5)return;
    bool touches=false;
    for(int i=1;i<D::q;++i){
      auto n=p+descriptors::c<D>(i);
      if(n[0]<0||n[0]>=48)n[0]=sepWrapX(n[0]);
      const int sm=g.getMaterial(n);touches|=sm==2||sm==3||sm==8;
    }
    if(touches){g.set(p,m==4?6:7);++marked[m==4?0:1];}
  });
  geometry.communicate();return marked;
}

struct SepLinks {
  int active=0,invalid=0,movingActive=0,pressureMovingDual=0;
  int minPressureToMovingLink=100000;
};

template<class L,class G>
SepLinks updateSeparatedLinks(L& lattice,G& geometry,T h,T uWall)
{
  SepLinks count;
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p){
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i){
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
    }
    const int m=g.getMaterial(p);if(!separatedFluid(m))return;
    bool ownsMoving=false;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i){
      const auto c=descriptors::c<D>(i);auto n=p+c;
      if(n[0]<0||n[0]>=48)n[0]=sepWrapX(n[0]);
      const int sm=g.getMaterial(n);if(sm!=2&&sm!=3&&sm!=8)continue;
      T q=.5,velocityCoefficient=0;
      if(sm==3){
        T lo=0,hi=1;
        for(int k=0;k<50;++k){
          const T a=(lo+hi)/2;
          T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;
          const T y=r[1]+a*dx*c[1],z=r[2]+a*dx*c[2];
          if(movingPunch(x,y,z,h))hi=a;else lo=a;
        }
        q=(lo+hi)/2;velocityCoefficient=c[2]*uWall*dt/dx;
        ownsMoving=true;++count.movingActive;
      }
      if(!(q>=0&&q<=1))++count.invalid;
      else{
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,
                                                                       velocityCoefficient);
        ++count.active;
      }
    }
    if(ownsMoving){
      const int distance=std::min(p[1],separatedNy-1-p[1]);
      count.minPressureToMovingLink=std::min(count.minPressureToMovingLink,distance);
      if(m==4||m==5||m==6||m==7)++count.pressureMovingDual;
    }
  });
  lattice.communicate();return count;
}

struct SepStats {
  T mass=0,rhoMin=1e300,rhoMax=-1e300,maxU=0,lowOut=0,highOut=0;
  int maxIx=0,maxIy=0,maxIz=0,maxMaterial=0;bool finite=true;
};

template<class L,class G>
SepStats separatedStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter)
{
  SepStats s;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){
    const int m=g.getMaterial(p);if(!separatedFluid(m))return;
    auto cell=block.get(p);T u[3]{};cell.computeU(u);const T rho=cell.computeRho();
    const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
    s.mass+=rho*rhoPhys*dx*dx*dx;s.rhoMin=std::min(s.rhoMin,rho);
    s.rhoMax=std::max(s.rhoMax,rho);
    if(speed>s.maxU){s.maxU=speed;s.maxIx=p[0];s.maxIy=p[1];s.maxIz=p[2];s.maxMaterial=m;}
    s.finite&=std::isfinite(rho)&&std::isfinite(speed);
    for(int i=0;i<D::q;++i)s.finite&=std::isfinite(cell[i]);
    const T uy=converter.getPhysVelocity(u[1]);
    if(m==4||m==6)s.lowOut-=rho*rhoPhys*uy*dx*dx;
    if(m==5||m==7)s.highOut+=rho*rhoPhys*uy*dx*dx;
  });
  return s;
}

template<class B,class G>
void writeSepCell(std::ofstream& out,B& block,G& g,int step,const char* name,
                  LatticeR<3> p)
{
  auto cell=block.get(p);T u[3]{};cell.computeU(u);
  out<<step<<','<<name<<','<<p[0]<<','<<p[1]<<','<<p[2]<<','<<g.getMaterial(p)
     <<','<<cell.computeRho()<<','<<u[0]<<','<<u[1]<<','<<u[2]<<','
     <<std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2])/std::sqrt(T(1)/3);
  for(int i=0;i<D::q;++i)out<<','<<cell[i];
  out<<'\n';
}

int runSeparatedControl()
{
  const std::string runId="moving_piston_pressure_separated_C650_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"Refusing to overwrite\n";return 2;}
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  IndicatorCuboid3D<T> domain({Lx-dx,separatedLy-dx,195e-9},{dx/2,dx/2,-dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,separatedMaterialAt(g.getPhysR(p)));});
  geometry.communicate();const auto marked=markSeparatedPressureIntersections(geometry);
  const auto initialCounts=materialCounts(geometry);
  SuperIndicatorFfromIndicatorF3D<T> outside(new SeparatedOutside,geometry);
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
  dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);
  dynamics::set<NoDynamics>(lattice,geometry,8);
  AnalyticalConst3D<T,T> one(1),zero(0,0,0);
  lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
  for(int m:{1,4,5,6,7})lattice.iniEquilibrium(geometry,m,one,zero);
  lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
  lattice.initialize();

  std::ofstream csv(outDir/"diagnostics.csv");csv<<std::setprecision(17)
    <<"step,time_s,h_nm,wall_speed_m_s,active_links,moving_links,invalid_links,"
      "pressure_moving_dual_cells,min_pressure_plane_distance_to_moving_link_cells,"
      "mass_kg,mass_relative_change,low_outward_flux_kg_s,high_outward_flux_kg_s,"
      "net_outward_flux_kg_s,cumulative_outward_mass_kg,mass_balance_residual_kg,"
      "relative_mass_balance_residual,rho_min,rho_max,max_speed_m_s,max_Mach,"
      "max_ix,max_iy,max_iz,max_material,finite,material_conversions\n";
  std::ofstream hist(outDir/"local_cells_history.csv");hist<<std::setprecision(17)
    <<"step,cell_name,ix,iy,iz,material,rho,ux,uy,uz,Mach";
  for(int i=0;i<D::q;++i)hist<<",f"<<i;
  hist<<'\n';
  auto& block=lattice.getBlock(0);
  SepStats initial=separatedStats(lattice,geometry,converter),previous=initial,current=initial;
  T cumulative=0,maxMach=0,minRho=1e300,maxRho=-1e300,maxResidual=0;
  int firstMach=-1,firstRho=-1,firstNonfinite=-1,maxInvalid=0,maxDual=0,minDistance=100000;
  int globalIx=0,globalIy=0,globalIz=0,globalMaterial=0;T globalMaxU=0;
  for(int step=0;step<=650;++step){
    const auto links=updateSeparatedLinks(lattice,geometry,hAt(step,true),wallSpeed(step,true));
    maxInvalid=std::max(maxInvalid,links.invalid);maxDual=std::max(maxDual,links.pressureMovingDual);
    minDistance=std::min(minDistance,links.minPressureToMovingLink);
    if(step)lattice.collideAndStream();
    current=separatedStats(lattice,geometry,converter);
    if(step)cumulative+=T(.5)*((previous.lowOut+previous.highOut)
                              +(current.lowOut+current.highOut))*dt;
    const T residual=current.mass-initial.mass+cumulative;
    const T mach=current.maxU/std::sqrt(T(1)/3);
    maxMach=std::max(maxMach,mach);minRho=std::min(minRho,current.rhoMin);
    maxRho=std::max(maxRho,current.rhoMax);maxResidual=std::max(maxResidual,std::abs(residual/initial.mass));
    if(current.maxU>globalMaxU){globalMaxU=current.maxU;globalIx=current.maxIx;globalIy=current.maxIy;
      globalIz=current.maxIz;globalMaterial=current.maxMaterial;}
    if(firstMach<0&&mach>machLimit)firstMach=step;
    if(firstRho<0&&(current.rhoMin<rhoMinLimit||current.rhoMax>rhoMaxLimit))firstRho=step;
    if(firstNonfinite<0&&!current.finite)firstNonfinite=step;
    csv<<step<<','<<step*dt<<','<<hAt(step,true)*1e9<<','<<wallSpeed(step,true)
       <<','<<links.active<<','<<links.movingActive<<','<<links.invalid<<','
       <<links.pressureMovingDual<<','<<links.minPressureToMovingLink<<','
       <<current.mass<<','<<(current.mass-initial.mass)/initial.mass<<','
       <<current.lowOut<<','<<current.highOut<<','<<(current.lowOut+current.highOut)
       <<','<<cumulative<<','<<residual<<','<<residual/initial.mass<<','
       <<current.rhoMin<<','<<current.rhoMax<<','<<converter.getPhysVelocity(current.maxU)
       <<','<<mach<<','<<current.maxIx<<','<<current.maxIy<<','<<current.maxIz<<','
       <<current.maxMaterial<<','<<current.finite<<",0\n";
    writeSepCell(hist,block,g,step,"pressure_low_under_mesa",{0,0,13});
    writeSepCell(hist,block,g,step,"buffer_y1",{0,1,13});
    writeSepCell(hist,block,g,step,"buffer_y2",{0,2,13});
    writeSepCell(hist,block,g,step,"moving_link_near_side",{0,3,13});
    writeSepCell(hist,block,g,step,"moving_region_y4",{0,4,13});
    previous=current;if(!current.finite)break;
  }
  const bool materialUnchanged=materialCounts(geometry)==initialCounts;
  const bool pass=current.finite&&firstMach<0&&firstRho<0&&maxInvalid==0&&maxDual==0
                 &&materialUnchanged;
  std::ofstream result(outDir/"result.txt");result<<std::setprecision(17)<<std::boolalpha
    <<"run_id="<<runId<<"\nPASS="<<pass<<"\nsteps_completed="
    <<(firstNonfinite<0?650:firstNonfinite)<<"\nseparated_Ly_nm="<<separatedLy*1e9
    <<"\nmoving_footprint_y_nm=20,260\nordinary_fluid_layers_between_pressure_and_moving_link=2\n"
    <<"min_lattice_index_distance_pressure_to_moving_link="<<minDistance
    <<"\npressure_moving_dual_cells_max="<<maxDual
    <<"\nintersection_low_cells="<<marked[0]<<"\nintersection_high_cells="<<marked[1]
    <<"\nmax_Mach="<<maxMach<<"\nfirst_Mach_over_0.05_step="<<firstMach
    <<"\nrho_range="<<minRho<<','<<maxRho
    <<"\nfirst_rho_outside_0.8_1.2_step="<<firstRho
    <<"\nfirst_nonfinite_step="<<firstNonfinite
    <<"\nmax_speed_m_s="<<converter.getPhysVelocity(globalMaxU)
    <<"\nmax_speed_location="<<globalIx<<','<<globalIy<<','<<globalIz
    <<"\nmax_speed_material="<<globalMaterial
    <<"\ninitial_mass_kg="<<initial.mass<<"\nfinal_mass_kg="<<current.mass
    <<"\nmax_abs_relative_mass_balance_residual="<<maxResidual
    <<"\nmax_invalid_links="<<maxInvalid<<"\nmaterial_conversions=0\nmaterial_field_unchanged="
    <<materialUnchanged<<"\nexit_code="<<(pass?0:3)<<'\n';
  std::ofstream record(outDir/"run_record.txt");record
    <<"run_id="<<runId<<"\ncommand=./explicit_piston_pressure_separated_control\n"
    <<"steps=650\nmaterial_conversion_enabled=false\nwall_trajectory_identical_to_C=true\n"
    <<"exit_code="<<(pass?0:3)<<'\n';
  return pass?0:3;
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)return 2;
  return runSeparatedControl();
}
