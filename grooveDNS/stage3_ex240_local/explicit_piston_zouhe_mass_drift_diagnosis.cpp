#define main frozen_boundary_intersection_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <numeric>

constexpr int mdSteps = 2000;
constexpr T mdNominalInitialVolume = Lx*Ly*75e-9 + 120e-9*Ly*grooveDepth;
constexpr T mdZ1DeltaRho=2e-6;
constexpr int mdZ1N=16;
constexpr T mdZ1Length=(mdZ1N-1)*dx;

class MDZ1Outside final : public IndicatorF3D<T> {
public:
  MDZ1Outside()
  {
    this->_myMin={-1e9,-1e9,-1e9};
    this->_myMax={1e9,1e9,1e9};
    this->getName()="MDZ1Outside";
  }
  bool operator()(bool out[1],const T r[3]) override
  {
    const T eps=dx*1e-6;
    out[0]=r[1]<dx/2-eps || r[1]>mdZ1Length+dx/2+eps;
    return true;
  }
};

class MDZ1Rho final : public AnalyticalF3D<T,T> {
public:
  MDZ1Rho():AnalyticalF3D<T,T>(1) { this->getName()="MDZ1Rho"; }
  bool operator()(T out[1],const T r[3]) override
  {
    out[0]=1+mdZ1DeltaRho/T(2)-mdZ1DeltaRho*r[1]/mdZ1Length;
    return true;
  }
};

int mdWrapX(int ix)
{
  const int wrapped=ix%48;
  return wrapped<0 ? wrapped+48 : wrapped;
}

template<class L,class G>
std::array<int,4> mdUpdatePeriodicLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,recovered=0,falseSolid=0;
  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p) {
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i) {
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
    }
    if(!isFluidMaterial(g.getMaterial(p))) return;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i) {
      const auto c=descriptors::c<D>(i);
      auto raw=p+c,mapped=raw;
      const bool crosses=raw[0]<0||raw[0]>=48;
      if(crosses) mapped[0]=mdWrapX(raw[0]);
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
          T x=r[0]+a*dx*c[0];
          x=std::fmod(x,Lx);
          if(x<0) x+=Lx;
          if(punch(x,r[2]+a*dx*c[2],h)) hi=a; else lo=a;
        }
        q=(lo+hi)/2;
        velocityCoefficient=c[2]*uWall*dt/dx;
      }
      if(!(q>=0&&q<=1)) {
        ++invalid;
      } else {
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(
          i,velocityCoefficient);
        ++active;
      }
    }
  });
  lattice.communicate();
  return {active,invalid,recovered,falseSolid};
}

template<class L,class G>
void mdSetAllZouHePressure(L& lattice,G& geometry,
                           SuperIndicatorFfromIndicatorF3D<T>& outside)
{
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
}

struct MDMassState {
  long long fluidCells = 0;
  T mass = 0;
  T rhoSum = 0;
  T rhoMin = std::numeric_limits<T>::max();
  T rhoMax = -std::numeric_limits<T>::max();
  T maxU = 0;
  T macroOutRate = 0;
  bool finite = true;
};

template<class L, class G, class FluidPredicate>
MDMassState mdState(L& lattice, G& geometry,
                    const UnitConverter<T,D>& converter,
                    FluidPredicate isFluid)
{
  MDMassState s;
  auto& block = lattice.getBlock(0);
  auto& g = geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material = g.getMaterial(p);
    if (!isFluid(material)) return;
    auto cell = block.get(p);
    T u[3]{};
    cell.computeU(u);
    const T rho = cell.computeRho();
    const T speed = std::sqrt(u[0]*u[0] + u[1]*u[1] + u[2]*u[2]);
    ++s.fluidCells;
    s.rhoSum += rho;
    s.mass += rho*rhoPhys*dx*dx*dx;
    s.rhoMin = std::min(s.rhoMin,rho);
    s.rhoMax = std::max(s.rhoMax,rho);
    s.maxU = std::max(s.maxU,speed);
    s.finite = s.finite && std::isfinite(rho) && std::isfinite(speed);
    for (int iPop=0; iPop<D::q; ++iPop) {
      s.finite = s.finite && std::isfinite(cell[iPop]);
    }
    const T uyPhys = converter.getPhysVelocity(u[1]);
    if (material==4) s.macroOutRate -= rho*rhoPhys*uyPhys*dx*dx;
    if (material==5) s.macroOutRate += rho*rhoPhys*uyPhys*dx*dx;
  });
  return s;
}

// Net mass carried across the two pressure planes by the post-collision
// populations during one lattice step. OpenLB stores shifted populations
// f_i=F_i-w_i; the weight offsets cancel between opposite +/-y sets, but they
// are restored explicitly here so that the definition remains auditable.
template<class L, class G>
T mdPopulationOutMassStep(L& lattice, G& geometry)
{
  T latticeMass = 0;
  auto& block = lattice.getBlock(0);
  auto& g = geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material = g.getMaterial(p);
    if (material!=4 && material!=5) return;
    auto cell = block.get(p);
    for (int iPop=0; iPop<D::q; ++iPop) {
      const int cy = descriptors::c<D>(iPop,1);
      if (cy==0) continue;
      const T fullPopulation = cell[iPop] + descriptors::t<T,D>(iPop);
      const int outwardSign = material==4 ? -cy : cy;
      latticeMass += outwardSign*fullPopulation;
    }
  });
  return latticeMass*rhoPhys*dx*dx*dx;
}

void mdHeader(std::ofstream& out)
{
  out << "case,step,physical_time_s,displacement_nm,wall_velocity_m_s,"
         "total_lattice_mass_kg,average_rho,min_rho,max_rho,max_Mach,"
         "macro_out_mass_step_kg,macro_out_mass_cumulative_kg,"
         "population_out_mass_step_kg,population_out_mass_cumulative_kg,"
         "R_macro_kg,R_macro_relative,R_population_kg,R_population_relative,"
         "mass_pre_collision_kg,mass_post_collision_kg,mass_post_full_step_kg,"
         "collision_mass_increment_kg,stream_bouzidi_mass_increment_kg,"
         "continuous_fluid_volume_m3,swept_volume_m3,"
         "nominal_lattice_fluid_volume_m3,fluid_material_cell_count,"
         "illegal_links,material_conversions,finite\n";
}

void mdRow(std::ofstream& out, const std::string& label, int step,
           T displacement, T wallVelocity, const MDMassState& state,
           T macroStep, T macroCumulative, T populationStep,
           T populationCumulative, T initialMass,
           T preCollisionMass, T postCollisionMass,
           T continuousVolume, T sweptVolume, int illegalLinks)
{
  const T rMacro = state.mass-initialMass+macroCumulative;
  const T rPopulation = state.mass-initialMass+populationCumulative;
  out << label << ',' << step << ',' << step*dt << ',' << displacement*1e9
      << ',' << wallVelocity << ',' << state.mass << ','
      << state.rhoSum/state.fluidCells << ',' << state.rhoMin << ','
      << state.rhoMax << ',' << state.maxU/std::sqrt(T(1)/3) << ','
      << macroStep << ',' << macroCumulative << ',' << populationStep << ','
      << populationCumulative << ',' << rMacro << ',' << rMacro/initialMass
      << ',' << rPopulation << ',' << rPopulation/initialMass << ','
      << preCollisionMass << ',' << postCollisionMass << ',' << state.mass
      << ',' << postCollisionMass-preCollisionMass << ','
      << state.mass-postCollisionMass << ',' << continuousVolume << ','
      << sweptVolume << ','
      << state.fluidCells*dx*dx*dx << ',' << state.fluidCells << ','
      << illegalLinks << ",0," << state.finite << '\n';
}

template<class L, class G, class FluidPredicate>
bool mdAdvanceAndRecord(L& lattice, G& geometry,
                        const UnitConverter<T,D>& converter,
                        FluidPredicate isFluid, std::ofstream& csv,
                        const std::string& label, int step,
                        T displacement, T wallVelocity, T continuousVolume,
                        T sweptVolume,
                        int illegalLinks, bool hasPressure,
                        const MDMassState& initial, MDMassState& previous,
                        T& macroCumulative, T& populationCumulative)
{
  const auto pre = mdState(lattice,geometry,converter,isFluid);
  lattice.collide();
  const auto postCollision = mdState(lattice,geometry,converter,isFluid);
  const T populationStep = hasPressure
    ? mdPopulationOutMassStep(lattice,geometry) : T(0);
  lattice.AndStream();
  const auto current = mdState(lattice,geometry,converter,isFluid);
  const T macroStep = T(.5)*(previous.macroOutRate+current.macroOutRate)*dt;
  macroCumulative += macroStep;
  populationCumulative += populationStep;
  mdRow(csv,label,step,displacement,wallVelocity,current,macroStep,
        macroCumulative,populationStep,populationCumulative,initial.mass,
        pre.mass,postCollision.mass,continuousVolume,sweptVolume,illegalLinks);
  previous = current;
  return current.finite;
}

int mdRunOriginal(bool movingClosed)
{
  const std::string label = movingClosed ? "M2_moving_closed" : "M0_fixed_zero";
  const std::string runId = movingClosed
    ? "mass_drift_M2_moving_closed_2000_20260908"
    : "mass_drift_M0_zouhe_fixed_zero_2000_20260908";
  const auto outDir = std::filesystem::path("output")/runId;
  if (std::filesystem::exists(outDir)) {
    std::cerr << "Refusing to overwrite " << outDir << '\n';
    return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log");
  log << std::setprecision(17) << std::boolalpha;
  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);
    cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g = geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      g.set(p,materialAt(g.getPhysR(p)));
    });
    geometry.communicate();
    const auto initialCounts = materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    if (movingClosed) {
      boundary::set<boundary::BounceBack>(lattice,geometry,4);
      boundary::set<boundary::BounceBack>(lattice,geometry,5);
    } else {
      mdSetAllZouHePressure(lattice,geometry,outside);
    }
    dynamics::set<NoDynamics>(lattice,geometry,2);
    dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for (int material : {1,4,5}) {
      lattice.iniEquilibrium(geometry,material,one,zero);
    }
    lattice.addPostProcessor<stage::PostStream>(
      meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();
    if (!movingClosed) {
      lattice.defineRho(geometry,4,one);
      lattice.defineRho(geometry,5,one);
    }
    lattice.communicate();

    std::ofstream csv(outDir/"mass_drift_history.csv");
    csv << std::setprecision(17) << std::boolalpha;
    mdHeader(csv);
    const auto fluid = [](int material) { return isFluidMaterial(material); };
    auto initial = mdState(lattice,geometry,converter,fluid);
    auto previous = initial;
    T macroCumulative=0,populationCumulative=0;
    mdRow(csv,label,0,0,0,initial,0,0,0,0,initial.mass,initial.mass,
          initial.mass,mdNominalInitialVolume,0,0);
    int completed=0,maxIllegal=0;
    bool finite=true;
    for (int step=1; step<=mdSteps; ++step) {
      const T h = movingClosed ? hAt(step,true) : 75e-9;
      const T wallVelocity = movingClosed ? wallSpeed(step,true) : T(0);
      const auto links = mdUpdatePeriodicLinks(lattice,geometry,h,wallVelocity);
      const int illegal = links[1]+links[3];
      maxIllegal = std::max(maxIllegal,illegal);
      const T displacement = 75e-9-h;
      const T continuousVolume = mdNominalInitialVolume-Lx*Ly*displacement;
      finite = mdAdvanceAndRecord(lattice,geometry,converter,fluid,csv,label,
        step,displacement,wallVelocity,continuousVolume,
        mdNominalInitialVolume-continuousVolume,illegal,!movingClosed,
        initial,previous,macroCumulative,populationCumulative);
      completed=step;
      if (!finite) break;
    }
    const bool unchanged = materialCounts(geometry)==initialCounts;
    std::ofstream result(outDir/"result.txt");
    result << std::setprecision(17) << std::boolalpha
      << "run_id=" << runId << "\ncase=" << label
      << "\nsteps_requested=" << mdSteps << "\nsteps_completed=" << completed
      << "\nfinite=" << finite << "\nmaterial_field_unchanged=" << unchanged
      << "\nmaterial_conversions=0\nmax_illegal_links=" << maxIllegal
      << "\ninitial_mass_kg=" << initial.mass
      << "\nfinal_mass_kg=" << previous.mass
      << "\nfinal_mass_relative_change=" << (previous.mass-initial.mass)/initial.mass
      << "\nfinal_macro_residual_relative="
      << (previous.mass-initial.mass+macroCumulative)/initial.mass
      << "\nfinal_population_residual_relative="
      << (previous.mass-initial.mass+populationCumulative)/initial.mass
      << "\nfinal_displacement_nm="
      << (movingClosed ? (75e-9-hAt(completed,true))*1e9 : 0)
      << "\nexit_code=" << ((finite&&unchanged&&maxIllegal==0&&completed==mdSteps)?0:3)
      << '\n';
    const int code=(finite&&unchanged&&maxIllegal==0&&completed==mdSteps)?0:3;
    std::ofstream record(outDir/"run_record.txt");
    record << "run_id=" << runId << "\ncommand=mpirun -np 1 "
      << "./explicit_piston_zouhe_mass_drift_diagnosis "
      << (movingClosed?"M2":"M0") << "\nsteps=2000\nexit_code=" << code << '\n';
    log << "completed_steps=" << completed << "\nexit_code=" << code << '\n';
    return code;
  } catch (const std::exception& e) {
    log << "exception=" << e.what() << "\nexit_code=4\n";
    std::ofstream(outDir/"failure.txt") << e.what() << '\n';
    return 4;
  }
}

int mdRunM1()
{
  const std::string label="M1_fixed_weak_nonzero";
  const std::string runId="mass_drift_M1_zouhe_fixed_nonzero_2000_v2_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if (std::filesystem::exists(outDir)) {
    std::cerr << "Refusing to overwrite " << outDir << '\n';
    return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log");
  try {
    IndicatorCuboid3D<T> domain({mdZ1Length,mdZ1Length,mdZ1Length},
                                {dx/2,dx/2,dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);
    cuboids.setPeriodicity({true,false,true});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p) {
      g.set(p,p[1]==0?4:(p[1]==mdZ1N-1?5:1));
    });
    geometry.communicate();
    const auto initialCounts=materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new MDZ1Outside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    mdSetAllZouHePressure(lattice,geometry,outside);
    MDZ1Rho rhoProfile;
    AnalyticalConst3D<T,T> zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),rhoProfile,zero);
    for (int material : {1,4,5}) {
      lattice.iniEquilibrium(geometry,material,rhoProfile,zero);
    }
    lattice.initialize();
    AnalyticalConst3D<T,T> rhoLow(1+mdZ1DeltaRho/T(2));
    AnalyticalConst3D<T,T> rhoHigh(1-mdZ1DeltaRho/T(2));
    lattice.defineRho(geometry,4,rhoLow);
    lattice.defineRho(geometry,5,rhoHigh);
    lattice.communicate();

    std::ofstream csv(outDir/"mass_drift_history.csv");
    csv << std::setprecision(17) << std::boolalpha;
    mdHeader(csv);
    const auto fluid=[](int material) {
      return material==1||material==4||material==5;
    };
    auto initial=mdState(lattice,geometry,converter,fluid);
    auto previous=initial;
    const T continuousVolume=initial.fluidCells*dx*dx*dx;
    T macroCumulative=0,populationCumulative=0;
    mdRow(csv,label,0,0,0,initial,0,0,0,0,initial.mass,initial.mass,
          initial.mass,continuousVolume,0,0);
    int completed=0;
    bool finite=true;
    for (int step=1;step<=mdSteps;++step) {
      finite=mdAdvanceAndRecord(lattice,geometry,converter,fluid,csv,label,
        step,0,0,continuousVolume,0,0,true,initial,previous,macroCumulative,
        populationCumulative);
      completed=step;
      if (!finite) break;
    }
    const bool unchanged=materialCounts(geometry)==initialCounts;
    const int code=(finite&&unchanged&&completed==mdSteps)?0:3;
    std::ofstream result(outDir/"result.txt");
    result << std::setprecision(17) << std::boolalpha
      << "run_id=" << runId << "\ncase=" << label
      << "\nsteps_requested=2000\nsteps_completed=" << completed
      << "\nfinite=" << finite << "\nmaterial_field_unchanged=" << unchanged
      << "\nmaterial_conversions=0\ninitial_mass_kg=" << initial.mass
      << "\nfinal_mass_kg=" << previous.mass
      << "\nfinal_mass_relative_change=" << (previous.mass-initial.mass)/initial.mass
      << "\nfinal_macro_residual_relative="
      << (previous.mass-initial.mass+macroCumulative)/initial.mass
      << "\nfinal_population_residual_relative="
      << (previous.mass-initial.mass+populationCumulative)/initial.mass
      << "\nexit_code=" << code << '\n';
    std::ofstream record(outDir/"run_record.txt");
    record << "run_id=" << runId << "\ncommand=mpirun -np 1 "
      << "./explicit_piston_zouhe_mass_drift_diagnosis M1"
      << "\nsteps=2000\nexit_code=" << code << '\n';
    log << "completed_steps=" << completed << "\nexit_code=" << code << '\n';
    return code;
  } catch (const std::exception& e) {
    log << "exception=" << e.what() << "\nexit_code=4\n";
    std::ofstream(outDir/"failure.txt") << e.what() << '\n';
    return 4;
  }
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if (singleton::mpi().getSize()!=1 || argc!=2) return 2;
  const std::string mode=argv[1];
  if (mode=="M0") return mdRunOriginal(false);
  if (mode=="M1") return mdRunM1();
  if (mode=="M2") return mdRunOriginal(true);
  return 2;
}
