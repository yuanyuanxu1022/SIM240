#include <olb.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <typeinfo>

using namespace olb;

using T = double;
using D = descriptors::D3Q19<descriptors::BOUZIDI_DISTANCE,
                             descriptors::BOUZIDI_VELOCITY>;

constexpr T dx=5e-9, dt=1e-11, Lx=240e-9, Ly=240e-9;
constexpr T grooveDepth=100e-9, rhoPhys=1000., nuPhys=1e-6;
constexpr int overlap=3, trajectorySteps=10000, regressionSteps=650;
constexpr T machLimit=.05, rhoMinLimit=.8, rhoMaxLimit=1.2;

class PeriodicXOutside final : public IndicatorF3D<T> {
public:
  PeriodicXOutside()
  {
    this->_myMin={-1e9,-1e9,-1e9};
    this->_myMax={1e9,1e9,1e9};
    this->getName()="PeriodicXOutside";
  }
  bool operator()(bool output[1], const T r[3]) override
  {
    const T eps=dx*1e-6;
    output[0]=r[1]<dx/2-eps || r[1]>Ly-dx/2+eps
           || r[2]<-dx/2-eps || r[2]>192.5e-9+eps;
    return true;
  }
};

T smooth5(T s)
{
  s=std::clamp(s,T(0),T(1));
  return 10*s*s*s-15*s*s*s*s+6*s*s*s*s*s;
}
T dSmooth5(T s)
{
  s=std::clamp(s,T(0),T(1));
  return 30*s*s*(1-s)*(1-s);
}
T hAt(int step,bool moving)
{
  return moving ? 75e-9-10e-9*smooth5(T(step)/trajectorySteps) : 75e-9;
}
T wallSpeed(int step,bool moving)
{
  return moving ? -10e-9/(trajectorySteps*dt)
                    *dSmooth5((T(step)-T(.5))/trajectorySteps)
                : 0;
}
bool punch(T x,T z,T h)
{
  return z>=((x<60e-9||x>=180e-9)?h:h+grooveDepth);
}
int materialAt(const Vector<T,3>&r)
{
  if(r[2]<0) return 2;
  if(punch(r[0],r[2],75e-9)) return 3;
  if(r[1]<dx) return 4;
  if(r[1]>Ly-dx) return 5;
  return 1;
}
bool isFluidMaterial(int m)
{
  return m==1||m==4||m==5||m==6||m==7;
}

template<class G>
std::array<long long,8> materialCounts(G& geometry)
{
  std::array<long long,8> counts{};
  for(int iC=0;iC<geometry.getLoadBalancer().size();++iC){
    auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p){
      const int m=g.getMaterial(p);
      if(m>=0&&m<8) ++counts[m];
    });
  }
  return counts;
}

// Mark only pressure-plane cells that also own a solid Bouzidi link.  Materials
// 6/7 retain pressure-boundary ownership, but use Zou-He's missing-population
// reconstruction instead of LocalPressure's all-population RLB reconstruction.
template<class G>
std::array<int,2> markIntersectionPressureCells(G& geometry)
{
  std::array<int,2> marked{};
  for(int iC=0;iC<geometry.getLoadBalancer().size();++iC){
    auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p){
      const int m=g.getMaterial(p);
      if(m!=4&&m!=5) return;
      bool touchesSolidLink=false;
      for(int iPop=1;iPop<D::q;++iPop){
        const auto c=descriptors::c<D>(iPop);
        const int neighborMaterial=g.getMaterial(p+c);
        if(neighborMaterial==2||neighborMaterial==3){
          touchesSolidLink=true;
        }
      }
      if(touchesSolidLink){
        g.set(p,m==4?6:7);
        ++marked[m==4?0:1];
      }
    });
  }
  geometry.communicate();
  return marked;
}

template<class L,class G>
std::array<int,5> updateLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,lpSolidDual=0,zouHeSolidDual=0,ownershipErrors=0;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC){
    auto& block=lattice.getBlock(iC);
    auto& g=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p){
      auto cell=block.get(p);
      for(int iPop=0;iPop<D::q;++iPop){
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(iPop,-1);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(iPop,0);
      }
      const int m=g.getMaterial(p);
      if(!isFluidMaterial(m)) return;
      const auto r=g.getPhysR(p);
      bool anySolidLink=false;
      for(int iPop=1;iPop<D::q;++iPop){
        const auto c=descriptors::c<D>(iPop);
        const int sm=g.getMaterial(p+c);
        if(sm!=2&&sm!=3) continue;
        T q=.5,velocityCoefficient=0;
        if(sm==3){
          T lo=0,hi=1;
          for(int i=0;i<50;++i){
            const T a=(lo+hi)/2;
            if(punch(r[0]+a*dx*c[0],r[2]+a*dx*c[2],h)) hi=a;
            else lo=a;
          }
          q=(lo+hi)/2;
          velocityCoefficient=c[2]*uWall*dt/dx;
        }
        if(!(q>=0&&q<=1)){
          ++invalid;
        }else{
          cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(iPop,q);
          cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(
            iPop,velocityCoefficient);
          ++active;
          anySolidLink=true;
        }
      }
      if(anySolidLink&&(m==4||m==5)) ++lpSolidDual;
      if(anySolidLink&&(m==6||m==7)) ++zouHeSolidDual;
    });
  }
  lattice.communicate();
  // In the frozen pre-conversion interval, every pressure/punch intersection
  // cell must be assigned to exactly one of the two pressure closures.
  if(zouHeSolidDual>0 && lpSolidDual>0) ++ownershipErrors;
  return {active,invalid,lpSolidDual,zouHeSolidDual,ownershipErrors};
}

struct Stats {
  long long fluidNodes=0;
  T mass=0,volume=0,rhoMin=1e300,rhoMax=-1e300,maxU=0;
  T lowOut=0,highOut=0;
  int maxIx=0,maxIy=0,maxIz=0,maxMaterial=0;
  bool finite=true;
};

template<class L,class G>
Stats computeStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter)
{
  Stats s;
  for(int iC=0;iC<lattice.getLoadBalancer().size();++iC){
    auto& block=lattice.getBlock(iC);
    auto& g=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p){
      const int m=g.getMaterial(p);
      if(!isFluidMaterial(m)) return;
      auto cell=block.get(p);
      T u[3]{};
      cell.computeU(u);
      const T rho=cell.computeRho();
      const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      ++s.fluidNodes;
      s.volume+=dx*dx*dx;
      s.mass+=rho*rhoPhys*dx*dx*dx;
      s.rhoMin=std::min(s.rhoMin,rho);
      s.rhoMax=std::max(s.rhoMax,rho);
      if(speed>s.maxU){
        s.maxU=speed;s.maxIx=p[0];s.maxIy=p[1];s.maxIz=p[2];s.maxMaterial=m;
      }
      s.finite &= std::isfinite(rho)&&std::isfinite(speed);
      for(int iPop=0;iPop<D::q;++iPop) s.finite&=std::isfinite(cell[iPop]);
      const T uyPhys=converter.getPhysVelocity(u[1]);
      if(m==4||m==6) s.lowOut-=rho*rhoPhys*uyPhys*dx*dx;
      if(m==5||m==7) s.highOut+=rho*rhoPhys*uyPhys*dx*dx;
    });
  }
  return s;
}

template<class B,class G>
void writeCell(std::ofstream& out,B& block,G& geometry,LatticeR<3> p,int step)
{
  auto cell=block.get(p);
  T u[3]{};cell.computeU(u);
  T rhoDirect=1,j[3]{};
  for(int iPop=0;iPop<D::q;++iPop){
    rhoDirect+=cell[iPop];
    const auto c=descriptors::c<D>(iPop);
    for(int iD=0;iD<3;++iD)j[iD]+=cell[iPop]*c[iD];
  }
  out<<step<<','<<p[0]<<','<<p[1]<<','<<p[2]<<','<<geometry.getMaterial(p)
     <<','<<cell.computeRho()<<','<<u[0]<<','<<u[1]<<','<<u[2]
     <<','<<std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2])/std::sqrt(T(1)/3)
     <<','<<rhoDirect<<','<<j[0]/rhoDirect<<','<<j[1]/rhoDirect<<','<<j[2]/rhoDirect;
  for(int iPop=0;iPop<D::q;++iPop)out<<','<<cell[iPop];
  out<<'\n';
}

void writeCellHeader(std::ofstream& out)
{
  out<<"step,ix,iy,iz,material,rho_boundary,ux_boundary,uy_boundary,uz_boundary,"
     <<"Mach_boundary,rho_direct,ux_direct,uy_direct,uz_direct";
  for(int i=0;i<D::q;++i)out<<",f"<<i;
  out<<'\n';
}

int run(bool fixedB)
{
  const bool moving=!fixedB;
  const bool intersectionFix=!fixedB;
  const std::string runId=fixedB
    ? "boundary_intersection_fix_B650_v3_20260907"
    : "boundary_intersection_fix_C650_v3_20260907";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){
    std::cerr<<"Refusing to overwrite "<<outDir<<'\n';return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log");
  log<<std::setprecision(17)<<std::boolalpha;
  try{
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
    if(intersectionFix) marked=markIntersectionPressureCells(geometry);
    const auto initialMaterialCounts=materialCounts(geometry);

    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
    boundary::set<T,D,boundary::LocalPressure<T,D,BGKdynamics<T,D>>>(
      lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
    if(intersectionFix){
      boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
        lattice,geometry.getMaterialIndicator(6),geometry.getMaterialIndicator(1),outside);
      boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
        lattice,geometry.getMaterialIndicator(7),geometry.getMaterialIndicator(1),outside);
    }
    dynamics::set<NoDynamics>(lattice,geometry,2);
    dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
    for(int m:{1,4,5,6,7}) lattice.iniEquilibrium(geometry,m,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();

    std::ofstream diagnostics(outDir/"diagnostics.csv");
    diagnostics<<std::setprecision(17)
      <<"step,time_s,h_nm,wall_speed_m_s,active_links,invalid_links,"
      <<"LocalPressure_Bouzidi_dual_cells,ZouHe_Bouzidi_dual_cells,ownership_errors,"
      <<"fluid_nodes,fluid_volume_m3,raw_fluid_mass_kg,raw_mass_relative_change,"
      <<"low_outward_flux_kg_s,high_outward_flux_kg_s,net_outward_flux_kg_s,"
      <<"cumulative_outward_mass_kg,mass_balance_residual_kg,"
      <<"relative_mass_balance_residual,rho_min,rho_max,max_speed_m_s,max_Mach,"
      <<"max_ix,max_iy,max_iz,max_material,finite,material_conversions\n";
    std::ofstream dualHistory(outDir/"cell_0_0_15_history.csv");
    std::ofstream alarmHistory(outDir/"cell_0_0_14_history.csv");
    dualHistory<<std::setprecision(17);alarmHistory<<std::setprecision(17);
    writeCellHeader(dualHistory);writeCellHeader(alarmHistory);

    Stats initial=computeStats(lattice,geometry,converter),previous=initial,current=initial;
    T cumulativeOut=0,maxAbsResidual=0,maxMach=0,minRho=1e300,maxRho=-1e300;
    int firstMach=-1,firstRho=-1,firstNonfinite=-1,maxInvalid=0,maxOwnership=0;
    int globalMaxIx=0,globalMaxIy=0,globalMaxIz=0,globalMaxMaterial=0;
    T globalMaxSpeed=0;
    auto& block=lattice.getBlock(0);
    auto& blockGeometry=geometry.getBlockGeometry(0);
    for(int step=0;step<=regressionSteps;++step){
      const auto links=updateLinks(lattice,geometry,hAt(step,moving),wallSpeed(step,moving));
      maxInvalid=std::max(maxInvalid,links[1]);
      maxOwnership=std::max(maxOwnership,links[4]);
      if(step) lattice.collideAndStream();
      current=computeStats(lattice,geometry,converter);
      if(step){
        cumulativeOut += T(.5)*((previous.lowOut+previous.highOut)
                              +(current.lowOut+current.highOut))*dt;
      }
      const T residual=current.mass-initial.mass+cumulativeOut;
      const T mach=current.maxU/std::sqrt(T(1)/3);
      maxAbsResidual=std::max(maxAbsResidual,std::abs(residual/initial.mass));
      minRho=std::min(minRho,current.rhoMin);
      maxRho=std::max(maxRho,current.rhoMax);
      maxMach=std::max(maxMach,mach);
      if(current.maxU>globalMaxSpeed){
        globalMaxSpeed=current.maxU;globalMaxIx=current.maxIx;globalMaxIy=current.maxIy;
        globalMaxIz=current.maxIz;globalMaxMaterial=current.maxMaterial;
      }
      if(firstMach<0&&mach>machLimit)firstMach=step;
      if(firstRho<0&&(current.rhoMin<rhoMinLimit||current.rhoMax>rhoMaxLimit))firstRho=step;
      if(firstNonfinite<0&&!current.finite)firstNonfinite=step;
      diagnostics<<step<<','<<step*dt<<','<<hAt(step,moving)*1e9<<','
        <<wallSpeed(step,moving)<<','<<links[0]<<','<<links[1]<<','<<links[2]<<','
        <<links[3]<<','<<links[4]<<','<<current.fluidNodes<<','<<current.volume<<','
        <<current.mass<<','<<(current.mass-initial.mass)/initial.mass<<','
        <<current.lowOut<<','<<current.highOut<<','<<(current.lowOut+current.highOut)
        <<','<<cumulativeOut<<','<<residual<<','<<residual/initial.mass<<','
        <<current.rhoMin<<','<<current.rhoMax<<','
        <<converter.getPhysVelocity(current.maxU)<<','<<mach<<','<<current.maxIx<<','
        <<current.maxIy<<','<<current.maxIz<<','<<current.maxMaterial<<','
        <<current.finite<<",0\n";
      writeCell(dualHistory,block,blockGeometry,{0,0,15},step);
      writeCell(alarmHistory,block,blockGeometry,{0,0,14},step);
      previous=current;
      if(!current.finite) break;
    }
    const T finalResidual=current.mass-initial.mass+cumulativeOut;
    const bool noMaterialChange=materialCounts(geometry)==initialMaterialCounts;
    const bool pass=current.finite&&firstMach<0&&firstRho<0&&maxInvalid==0
                 &&maxOwnership==0&&noMaterialChange;
    std::ofstream result(outDir/"result.txt");
    result<<std::setprecision(17)<<std::boolalpha
      <<"run_id="<<runId<<'\n'
      <<"case="<<(fixedB?"B_original_fixed_LocalPressure":"C_fixed_intersection_ZouHe")<<'\n'
      <<"PASS="<<pass<<'\n'
      <<"steps_requested="<<regressionSteps<<'\n'
      <<"steps_completed="<<(firstNonfinite<0?regressionSteps:firstNonfinite)<<'\n'
      <<"intersection_low_cells="<<marked[0]<<'\n'
      <<"intersection_high_cells="<<marked[1]<<'\n'
      <<"max_Mach="<<maxMach<<'\n'
      <<"first_Mach_over_0.05_step="<<firstMach<<'\n'
      <<"rho_range="<<minRho<<','<<maxRho<<'\n'
      <<"first_rho_outside_0.8_1.2_step="<<firstRho<<'\n'
      <<"first_nonfinite_step="<<firstNonfinite<<'\n'
      <<"max_speed_m_s="<<converter.getPhysVelocity(globalMaxSpeed)<<'\n'
      <<"max_speed_location="<<globalMaxIx<<','<<globalMaxIy<<','<<globalMaxIz<<'\n'
      <<"max_speed_material="<<globalMaxMaterial<<'\n'
      <<"initial_raw_fluid_mass_kg="<<initial.mass<<'\n'
      <<"final_raw_fluid_mass_kg="<<current.mass<<'\n'
      <<"cumulative_outward_mass_kg="<<cumulativeOut<<'\n'
      <<"final_relative_mass_balance_residual="<<finalResidual/initial.mass<<'\n'
      <<"max_abs_relative_mass_balance_residual="<<maxAbsResidual<<'\n'
      <<"max_invalid_links="<<maxInvalid<<'\n'
      <<"max_ownership_errors="<<maxOwnership<<'\n'
      <<"material_conversions=0\n"
      <<"material_field_unchanged="<<noMaterialChange<<'\n'
      <<"exit_code="<<(pass?0:3)<<'\n'
      <<"exit_reason="<<(pass?"all_frozen_650_step_checks_passed":
                           "one_or_more_frozen_650_step_checks_failed")<<'\n';
    std::ofstream record(outDir/"run_record.txt");
    record<<"run_id="<<runId<<'\n'
          <<"command=./explicit_piston_boundary_intersection_fix "
          <<(fixedB?"B":"Cfix")<<'\n'
          <<"exit_code="<<(pass?0:3)<<'\n'
          <<"exit_reason="<<(pass?"all_frozen_650_step_checks_passed":
                               "one_or_more_frozen_650_step_checks_failed")<<'\n';
    log<<"completed=true\nPASS="<<pass<<"\nexit_code="<<(pass?0:3)<<'\n';
    return pass?0:3;
  }catch(const std::exception& e){
    log<<"completed=false\nexception="<<e.what()<<"\nexit_code=4\n";
    std::cerr<<e.what()<<'\n';return 4;
  }
}

int main(int argc,char**argv)
{
  initialize(&argc,&argv);
  if(singleton::mpi().getSize()!=1||argc!=2)return 2;
  const std::string mode=argv[1];
  if(mode=="B")return run(true);
  if(mode=="Cfix")return run(false);
  return 2;
}
