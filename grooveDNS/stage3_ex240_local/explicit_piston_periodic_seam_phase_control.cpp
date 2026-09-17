#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

T wrapPhysicalX(T x)
{
  x=std::fmod(x,Lx);
  return x<0?x+Lx:x;
}

int wrapIndexX(int ix)
{
  int wrapped=ix%48;
  return wrapped<0?wrapped+48:wrapped;
}

bool shiftedPunch(T x,T z,T h)
{
  const T patternX=wrapPhysicalX(x+120e-9);
  return z>=((patternX<60e-9||patternX>=180e-9)?h:h+grooveDepth);
}

int shiftedMaterialAt(const Vector<T,3>& r)
{
  if(r[2]<0)return 2;
  if(shiftedPunch(r[0],r[2],75e-9))return 3;
  if(r[1]<dx)return 4;
  if(r[1]>Ly-dx)return 5;
  return 1;
}

template<class L,class G>
std::array<int,3> updateShiftedLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,missingMappedSolid=0;
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
        const LatticeR<3> raw=p+c;
        const LatticeR<3> mapped{wrapIndexX(raw[0]),raw[1],raw[2]};
        const int rawMaterial=g.getMaterial(raw);
        const int mappedMaterial=g.getMaterial(mapped);
        if((mappedMaterial==2||mappedMaterial==3)
           &&rawMaterial!=2&&rawMaterial!=3&&(raw[0]<0||raw[0]>=48)){
          ++missingMappedSolid;
        }
        if(rawMaterial!=2&&rawMaterial!=3)continue;
        T q=.5,velocityCoefficient=0;
        if(rawMaterial==3){
          T lo=0,hi=1;
          for(int k=0;k<50;++k){
            const T a=(lo+hi)/2;
            if(shiftedPunch(r[0]+a*dx*c[0],r[2]+a*dx*c[2],h))hi=a;
            else lo=a;
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
  lattice.communicate();return{active,invalid,missingMappedSolid};
}

int runShiftedControl()
{
  const std::string runId="periodic_seam_phase_shift_control_20260907";
  const auto outDir=std::filesystem::path("output")/runId;
  if(std::filesystem::exists(outDir)){std::cerr<<"exists\n";return 2;}
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
  CuboidDecomposition<T,3> cuboids(domain,dx,1);cuboids.setPeriodicity({true,false,false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
  for(int iC=0;iC<loadBalancer.size();++iC){
    auto& g=geometry.getBlockGeometry(iC);
    g.forCoreSpatialLocations([&](LatticeR<3> p){g.set(p,shiftedMaterialAt(g.getPhysR(p)));});
  }
  geometry.communicate();const auto marked=markIntersectionPressureCells(geometry);
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
  dynamics::set<NoDynamics>(lattice,geometry,2);dynamics::set<NoDynamics>(lattice,geometry,3);
  AnalyticalConst3D<T,T> one(1),zero(0,0,0);
  lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5,6,7}),one,zero);
  for(int m:{1,4,5,6,7})lattice.iniEquilibrium(geometry,m,one,zero);
  lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
  lattice.initialize();
  std::ofstream csv(outDir/"diagnostics.csv");
  csv<<std::setprecision(17)<<"step,h_nm,max_Mach,rho_min,rho_max,max_ix,max_iy,"
     <<"max_iz,max_material,active_links,invalid_links,missing_periodic_solid_links\n";
  int firstMach=-1,firstRho=-1;T maxMach=0,minRho=1e300,maxRho=-1e300;
  for(int step=0;step<=220;++step){
    const auto links=updateShiftedLinks(lattice,geometry,hAt(step,true),wallSpeed(step,true));
    if(step)lattice.collideAndStream();
    const auto s=computeStats(lattice,geometry,converter);
    const T mach=s.maxU/std::sqrt(T(1)/3);
    if(firstMach<0&&mach>machLimit)firstMach=step;
    if(firstRho<0&&(s.rhoMin<rhoMinLimit||s.rhoMax>rhoMaxLimit))firstRho=step;
    maxMach=std::max(maxMach,mach);minRho=std::min(minRho,s.rhoMin);maxRho=std::max(maxRho,s.rhoMax);
    csv<<step<<','<<hAt(step,true)*1e9<<','<<mach<<','<<s.rhoMin<<','<<s.rhoMax
       <<','<<s.maxIx<<','<<s.maxIy<<','<<s.maxIz<<','<<s.maxMaterial<<','
       <<links[0]<<','<<links[1]<<','<<links[2]<<'\n';
  }
  std::ofstream result(outDir/"result.txt");
  result<<std::setprecision(17)
    <<"diagnostic_only=true\npattern_phase_shift_nm=120\nx_periodic=true\n"
    <<"geometry_is_periodic_translation_of_baseline=true\nsteps=220\n"
    <<"first_Mach_over_0.05_step="<<firstMach<<'\n'
    <<"first_rho_outside_0.8_1.2_step="<<firstRho<<'\n'
    <<"max_Mach="<<maxMach<<"\nrho_range="<<minRho<<','<<maxRho<<'\n'
    <<"intersection_low_cells="<<marked[0]<<"\nintersection_high_cells="<<marked[1]
    <<"\nexit_code=0\nexit_reason=diagnostic_control_completed\n";
  std::ofstream record(outDir/"run_record.txt");
  record<<"run_id="<<runId<<"\ncommand=./explicit_piston_periodic_seam_phase_control\n"
        <<"exit_code=0\nexit_reason=diagnostic_control_completed\n";
  return 0;
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);if(singleton::mpi().getSize()!=1)return 2;
  return runShiftedControl();
}
