#include <olb.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>

using namespace olb;
using T = double;
using DESCRIPTOR = descriptors::D3Q27<
  descriptors::FORCE,
  FreeSurface::MASS,
  FreeSurface::EPSILON,
  FreeSurface::CELL_TYPE,
  FreeSurface::CELL_FLAGS,
  FreeSurface::TEMP_MASS_EXCHANGE,
  FreeSurface::PREVIOUS_VELOCITY,
  FreeSurface::HAS_INTERFACE_NBRS>;

constexpr T dx=5e-9, dt=1e-12, Lx=240e-9, Ly=240e-9;
constexpr T gap=65e-9, grooveDepth=100e-9, rhoPhys=1000., nu=1e-6;
constexpr T sigma=0.0309;
constexpr T stripLo=60e-9, stripHi=180e-9;
constexpr int overlap=3;
constexpr T grooveVolume=43200e-18*grooveDepth;
constexpr T transitionThreshold=1e-3;
constexpr T epsilonAuditTolerance=transitionThreshold+1e-8;

bool inGroovePlan(const Vector<T,3>& r)
{
  return (r[0]>=stripLo && r[0]<stripHi)
      || (r[1]>=stripLo && r[1]<stripHi);
}

bool inJunctionPlan(const Vector<T,3>& r)
{
  return r[0]>=stripLo && r[0]<stripHi
      && r[1]>=stripLo && r[1]<stripHi;
}

int materialAt(const Vector<T,3>& r)
{
  if (r[2]<0) return 2;
  const T ceiling=inGroovePlan(r) ? gap+grooveDepth : gap;
  return r[2]>=ceiling ? 3 : 1;
}

struct InitialFreeSurfaceField final : public AnalyticalF3D<T,T> {
  enum class Kind { CellType, Fraction };
  Kind kind;
  explicit InitialFreeSurfaceField(Kind value) : AnalyticalF3D<T,T>(1), kind(value) { }
  bool operator()(T output[],const T x[]) override {
    Vector<T,3> r{x[0],x[1],x[2]};
    T fraction=0;
    int type=static_cast<int>(FreeSurface::Type::Gas);
    if (r[2]<gap) {
      fraction=1;
      type=static_cast<int>(FreeSurface::Type::Fluid);
    } else if (inGroovePlan(r) && r[2]<gap+dx) {
      // One cell-thick seed interface at the groove mouth.
      fraction=T(0.5);
      type=static_cast<int>(FreeSurface::Type::Interface);
    }
    output[0]=kind==Kind::CellType ? T(type) : fraction;
    return true;
  }
};

struct Options {
  std::string runId;
  int maxSteps=8000;
  int vtkInterval=500;
  bool shortRun=false;
};

Options parseOptions(int argc,char** argv)
{
  Options o;
  for (int i=1;i<argc;++i) {
    const std::string key=argv[i];
    auto value=[&]() {
      if (++i>=argc) throw std::runtime_error("missing value after "+key);
      return std::string(argv[i]);
    };
    if (key=="--run-id") o.runId=value();
    else if (key=="--max-steps") o.maxSteps=std::stoi(value());
    else if (key=="--vtk-interval") o.vtkInterval=std::stoi(value());
    else if (key=="--short") o.shortRun=true;
    else throw std::runtime_error("unknown option "+key);
  }
  if (!std::regex_match(o.runId,std::regex("[A-Za-z0-9][A-Za-z0-9_-]*")))
    throw std::runtime_error("--run-id is required");
  if (o.maxSteps<1 || o.vtkInterval<1) throw std::runtime_error("invalid step count or interval");
  return o;
}

template<class GEO>
std::array<long long,4> materialCounts(GEO& geometry)
{
  std::array<long long,4> count{};
  for (int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
    auto& block=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      const int m=block.getMaterial(p);
      if (m>=0 && m<4) ++count[m];
    });
  }
  return count;
}

struct Stats {
  long long nFluid=0,nInterface=0,nGas=0,nSolid=0;
  T liquidMassLattice=0,liquidVolume=0,grooveLiquidVolume=0;
  T junctionLiquidVolume=0,armLiquidVolume=0;
  T rhoMin=std::numeric_limits<T>::max(),rhoMax=std::numeric_limits<T>::lowest();
  T epsilonMin=std::numeric_limits<T>::max(),epsilonMax=std::numeric_limits<T>::lowest();
  T maxULat=0,interfaceMeanZ=0,interfaceMaxZ=0,interfaceWeight=0;
  bool finite=true;
};

template<class LAT,class GEO>
Stats measure(LAT& lattice,GEO& geometry)
{
  Stats s;
  const T dx3=dx*dx*dx;
  for (int iC=0;iC<lattice.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC);
    auto& geo=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      const int material=geo.getMaterial(p);
      if (material==2 || material==3) { ++s.nSolid; return; }
      if (material!=1) return;
      auto cell=block.get(p);
      const T eps=cell.template getField<FreeSurface::EPSILON>();
      const T mass=cell.template getField<FreeSurface::MASS>();
      const int type=static_cast<int>(cell.template getField<FreeSurface::CELL_TYPE>());
      T u[3]{}; cell.computeU(u); const T rho=cell.computeRho();
      const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      s.finite &= std::isfinite(eps)&&std::isfinite(mass)&&std::isfinite(rho)&&std::isfinite(speed);
      for (int q=0;q<DESCRIPTOR::q;++q) s.finite &= std::isfinite(cell[q]);
      s.epsilonMin=std::min(s.epsilonMin,eps); s.epsilonMax=std::max(s.epsilonMax,eps);
      s.rhoMin=std::min(s.rhoMin,rho); s.rhoMax=std::max(s.rhoMax,rho);
      s.maxULat=std::max(s.maxULat,speed); s.liquidMassLattice+=mass;
      const T volume=eps*dx3; s.liquidVolume+=volume;
      const Vector<T,3> r=geo.getPhysR(p);
      if (inGroovePlan(r) && r[2]>=gap) {
        s.grooveLiquidVolume+=volume;
        if (inJunctionPlan(r)) s.junctionLiquidVolume+=volume;
        else s.armLiquidVolume+=volume;
      }
      if (type==static_cast<int>(FreeSurface::Type::Fluid)) ++s.nFluid;
      else if (type==static_cast<int>(FreeSurface::Type::Interface)) {
        ++s.nInterface; s.interfaceMeanZ+=eps*r[2]; s.interfaceWeight+=eps;
        s.interfaceMaxZ=std::max(s.interfaceMaxZ,r[2]);
      } else if (type==static_cast<int>(FreeSurface::Type::Gas)) ++s.nGas;
    });
  }
  if (s.interfaceWeight>0) s.interfaceMeanZ/=s.interfaceWeight;
  return s;
}

template<class LAT,class GEO>
void writeVtk(LAT& lattice,GEO& geometry,const UnitConverter<T,DESCRIPTOR>& converter,
              const std::string& name,int step,bool createMaster)
{
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  SuperVTMwriter3D<T> writer(name,overlap);
  SuperGeometryF3D<T> material(geometry); material.getName()="material";
  SuperLatticePhysVelocity3D<T,DESCRIPTOR> velocity(lattice,converter); velocity.getName()="velocity_m_s";
  SuperLatticePhysPressure3D<T,DESCRIPTOR> pressure(lattice,converter); pressure.getName()="pressure_Pa";
  SuperLatticeExternalScalarField3D<T,DESCRIPTOR,FreeSurface::EPSILON> epsilon(lattice); epsilon.getName()="liquid_volume_fraction";
  SuperLatticeExternalScalarField3D<T,DESCRIPTOR,FreeSurface::CELL_TYPE> type(lattice); type.getName()="free_surface_cell_type";
  SuperLatticeExternalScalarField3D<T,DESCRIPTOR,FreeSurface::MASS> mass(lattice); mass.getName()="free_surface_mass";
  writer.addFunctor(material); writer.addFunctor(velocity); writer.addFunctor(pressure);
  writer.addFunctor(epsilon); writer.addFunctor(type); writer.addFunctor(mass);
  if (createMaster) writer.createMasterFile();
  writer.write(step);
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if (singleton::mpi().getSize()!=1) { std::cerr<<"single rank required\n"; return 2; }
  Options opt;
  try { opt=parseOptions(argc,argv); }
  catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 2; }

  const auto out=std::filesystem::path("output")/opt.runId;
  if (std::filesystem::exists(out)) { std::cerr<<"output exists: "<<out<<'\n'; return 2; }
  std::filesystem::create_directories(out);
  singleton::directories().setOutputDir((out.string()+"/").c_str());
  std::ofstream log(out/"run.log"); log<<std::setprecision(17)<<std::boolalpha;

  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,gap+grooveDepth+20e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1); cuboids.setPeriodicity({true,true,false});
    HeuristicLoadBalancer<T> load(cuboids); SuperGeometry<T,3> geometry(cuboids,load,overlap);
    for (int iC=0;iC<load.size();++iC) {
      auto& block=geometry.getBlockGeometry(iC);
      block.forCoreSpatialLocations([&](LatticeR<3> p) { block.set(p,materialAt(block.getPhysR(p))); });
    }
    geometry.communicate(); geometry.checkForErrors(false);
    const auto initialMaterials=materialCounts(geometry);

    UnitConverter<T,DESCRIPTOR> converter(dx,dt,240e-9,1.,nu,rhoPhys);
    SuperLattice<T,DESCRIPTOR> lattice(converter,cuboids,load);
    dynamics::set<ForcedBGKdynamics>(lattice,geometry,1);
    boundary::set<boundary::BounceBack>(lattice,geometry,2);
    boundary::set<boundary::BounceBack>(lattice,geometry,3);
    lattice.setParameter<descriptors::OMEGA>(converter.getLatticeRelaxationFrequency());

    AnalyticalConst3D<T,T> zero(0),one(1),zeros(0,0,0),solidType(T(static_cast<int>(FreeSurface::Type::Solid)));
    for (int material : {1,2,3}) {
      lattice.defineField<FreeSurface::MASS>(geometry,material,zero);
      lattice.defineField<FreeSurface::EPSILON>(geometry,material,zero);
      lattice.defineField<FreeSurface::CELL_TYPE>(geometry,material,zero);
      lattice.defineField<FreeSurface::CELL_FLAGS>(geometry,material,zero);
      lattice.defineField<FreeSurface::TEMP_MASS_EXCHANGE>(geometry,material,zeros);
      lattice.defineField<FreeSurface::PREVIOUS_VELOCITY>(geometry,material,zeros);
      lattice.defineField<FreeSurface::HAS_INTERFACE_NBRS>(geometry,material,one);
      lattice.defineField<descriptors::FORCE>(geometry,material,zeros);
    }
    InitialFreeSurfaceField initialType(InitialFreeSurfaceField::Kind::CellType);
    InitialFreeSurfaceField initialFraction(InitialFreeSurfaceField::Kind::Fraction);
    lattice.defineField<FreeSurface::CELL_TYPE>(geometry,1,initialType);
    lattice.defineField<FreeSurface::EPSILON>(geometry,1,initialFraction);
    lattice.defineField<FreeSurface::MASS>(geometry,1,initialFraction);
    for (int material : {2,3}) {
      lattice.defineField<FreeSurface::CELL_TYPE>(geometry,material,solidType);
      lattice.defineField<FreeSurface::EPSILON>(geometry,material,one);
    }
    lattice.defineRhoU(geometry.getMaterialIndicator(1),one,zeros);
    lattice.iniEquilibrium(geometry,1,one,zeros);

    static FreeSurface3DSetup<T,DESCRIPTOR> freeSurface(lattice);
    freeSurface.addPostProcessor();
    FreeSurface::initialize(lattice);
    lattice.initialize();
    const T sigmaLattice=dt*dt/(rhoPhys*dx*dx*dx)*sigma;
    lattice.setParameter<FreeSurface::DROP_ISOLATED_CELLS>(true);
    lattice.setParameter<FreeSurface::TRANSITION>(transitionThreshold);
    lattice.setParameter<FreeSurface::LONELY_THRESHOLD>(T(1));
    lattice.setParameter<FreeSurface::HAS_SURFACE_TENSION>(true);
    lattice.setParameter<FreeSurface::SURFACE_TENSION_PARAMETER>(sigmaLattice);
    lattice.setParameter<FreeSurface::FORCE_DENSITY>({0,0,0});

    const Stats initial=measure(lattice,geometry);
    std::ofstream params(out/"parameters.txt"); params<<std::setprecision(17)
      <<"model=SIM-EC1XT240\ngeometry=orthogonal_cross_junction\ngap_m="<<gap
      <<"\ngroove_depth_m="<<grooveDepth<<"\ndx_m="<<dx<<"\ndt_s="<<dt
      <<"\ntau="<<converter.getLatticeRelaxationTime()<<"\nrho_kg_m3="<<rhoPhys
      <<"\nnu_m2_s="<<nu<<"\nsurface_tension_N_m="<<sigma
      <<"\nsurface_tension_lattice="<<sigmaLattice
      <<"\nfree_surface_transition_threshold="<<transitionThreshold
      <<"\nepsilon_audit_tolerance="<<epsilonAuditTolerance
      <<"\nperiodicity=x_y\nz_boundary=fixed_bounceback\nforce=zero"
      <<"\nwetting_model=solid_epsilon_1_fully_wetting_tendency"
      <<"\ncontact_angle_degrees=not_prescribed_or_calibrated"
      <<"\ngas_model=fixed_reference_pressure_free_surface_state_not_resolved_gas_dynamics"
      <<"\ninitial_liquid=full_gap_plus_half_filled_one_cell_interface_at_groove_mouth\n";

    std::ofstream csv(out/"fill_fraction_history.csv"); csv<<std::setprecision(17)
      <<"step,time_s,liquid_volume_m3,liquid_mass_kg,liquid_mass_relative_drift,groove_liquid_volume_m3,groove_total_volume_m3,fill_fraction,junction_fill_fraction,arm_fill_fraction,interface_mean_z_nm,interface_max_z_nm,n_fluid,n_interface,n_gas,n_solid,rho_min,rho_max,max_speed_m_s,max_Mach,epsilon_min,epsilon_max,finite,material_unchanged\n";
    std::ofstream snapshots(out/"key_snapshots.csv"); snapshots<<"label,step,time_s,fill_fraction,junction_fill_fraction,arm_fill_fraction\n";
    const std::string vtkName="sim_ec1xt240_step6E_freesurface";
    writeVtk(lattice,geometry,converter,vtkName,0,true);
    snapshots<<"initial,0,0,"<<initial.grooveLiquidVolume/grooveVolume<<','
             <<initial.junctionLiquidVolume/(14400e-18*grooveDepth)<<','
             <<initial.armLiquidVolume/(28800e-18*grooveDepth)<<'\n';
    std::set<int> vtkSteps{0};
    bool wroteEntry=false,wroteSide=false;
    T maxMassDrift=0,maxMach=0,rhoMinAll=initial.rhoMin,rhoMaxAll=initial.rhoMax;
    T maxFillStepChange=0,previousFill=initial.grooveLiquidVolume/grooveVolume;
    int signReversals=0,lastSign=0,finalStep=0;
    const int limit=opt.maxSteps;
    for (int step=0;step<=limit;++step) {
      if (step) lattice.collideAndStream();
      const Stats state=measure(lattice,geometry);
      const T fill=state.grooveLiquidVolume/grooveVolume;
      const T junctionFill=state.junctionLiquidVolume/(14400e-18*grooveDepth);
      const T armFill=state.armLiquidVolume/(28800e-18*grooveDepth);
      const T massDrift=(state.liquidMassLattice-initial.liquidMassLattice)/initial.liquidMassLattice;
      const T mach=state.maxULat/std::sqrt(T(1)/3);
      maxMassDrift=std::max(maxMassDrift,std::abs(massDrift)); maxMach=std::max(maxMach,mach);
      rhoMinAll=std::min(rhoMinAll,state.rhoMin); rhoMaxAll=std::max(rhoMaxAll,state.rhoMax);
      if (step) {
        const T delta=fill-previousFill; maxFillStepChange=std::max(maxFillStepChange,std::abs(delta));
        const int sign=(delta>T(1e-10))?1:(delta<T(-1e-10))?-1:0;
        if (sign && lastSign && sign!=lastSign) ++signReversals;
        if (sign) lastSign=sign;
      }
      previousFill=fill;
      const bool same=materialCounts(geometry)==initialMaterials;
      csv<<step<<','<<step*dt<<','<<state.liquidVolume<<','<<state.liquidMassLattice*rhoPhys*dx*dx*dx<<','
        <<massDrift<<','<<state.grooveLiquidVolume<<','<<grooveVolume<<','<<fill<<','<<junctionFill<<','<<armFill<<','
        <<state.interfaceMeanZ*1e9<<','<<state.interfaceMaxZ*1e9<<','<<state.nFluid<<','<<state.nInterface<<','
        <<state.nGas<<','<<state.nSolid<<','<<state.rhoMin<<','<<state.rhoMax<<','
        <<converter.getPhysVelocity(state.maxULat)<<','<<mach<<','<<state.epsilonMin<<','<<state.epsilonMax<<','
        <<state.finite<<','<<same<<'\n';
      auto snapshot=[&](const char* label) {
        if (!vtkSteps.count(step)) { writeVtk(lattice,geometry,converter,vtkName,step,false); vtkSteps.insert(step); }
        snapshots<<label<<','<<step<<','<<step*dt<<','<<fill<<','<<junctionFill<<','<<armFill<<'\n';
      };
      if (!wroteEntry && fill>=initial.grooveLiquidVolume/grooveVolume+T(0.02)) { snapshot("entered_cross_junction"); wroteEntry=true; }
      if (!wroteSide && armFill>=initial.armLiquidVolume/(28800e-18*grooveDepth)+T(0.05)) { snapshot("side_arm_filling"); wroteSide=true; }
      if (step>0 && step%opt.vtkInterval==0 && !vtkSteps.count(step)) {
        writeVtk(lattice,geometry,converter,vtkName,step,false); vtkSteps.insert(step);
      }
      finalStep=step;
      if (!state.finite || state.epsilonMin<-epsilonAuditTolerance || state.epsilonMax>T(1)+epsilonAuditTolerance
          || mach>T(0.05) || state.rhoMin<T(0.8) || state.rhoMax>T(1.2) || !same) break;
    }
    const Stats final=measure(lattice,geometry);
    const T finalFill=final.grooveLiquidVolume/grooveVolume;
    if (!vtkSteps.count(finalStep)) writeVtk(lattice,geometry,converter,vtkName,finalStep,false);
    snapshots<<"final_or_stop,"<<finalStep<<','<<finalStep*dt<<','<<finalFill<<','
      <<final.junctionLiquidVolume/(14400e-18*grooveDepth)<<','
      <<final.armLiquidVolume/(28800e-18*grooveDepth)<<'\n';
    const bool same=materialCounts(geometry)==initialMaterials;
    const bool stable=finalStep==limit&&final.finite&&same&&maxMach<=T(0.05)
      &&rhoMinAll>=T(0.8)&&rhoMaxAll<=T(1.2)
      &&maxMassDrift<=T(5e-3)&&final.epsilonMin>=-epsilonAuditTolerance
      &&final.epsilonMax<=T(1)+epsilonAuditTolerance
      &&maxFillStepChange<=T(0.02);
    const bool filling=finalFill>=initial.grooveLiquidVolume/grooveVolume+T(0.01);
    // The short gate checks initialization and numerical stability only; a
    // measurable capillary filling response is required from the formal run.
    const bool pass=opt.shortRun ? stable : (stable&&filling);
    std::ofstream result(out/"result.txt"); result<<std::setprecision(17)<<std::boolalpha
      <<"PASS="<<pass<<"\nstable="<<stable<<"\nfilling_observed="<<filling
      <<"\nsteps_completed="<<finalStep<<"\ntime_s="<<finalStep*dt
      <<"\ninitial_fill_fraction="<<initial.grooveLiquidVolume/grooveVolume
      <<"\nfinal_fill_fraction="<<finalFill
      <<"\nfinal_junction_fill_fraction="<<final.junctionLiquidVolume/(14400e-18*grooveDepth)
      <<"\nfinal_arm_fill_fraction="<<final.armLiquidVolume/(28800e-18*grooveDepth)
      <<"\nmax_liquid_mass_relative_drift="<<maxMassDrift
      <<"\nrho_range="<<rhoMinAll<<','<<rhoMaxAll<<"\nmax_Mach="<<maxMach
      <<"\nmax_speed_m_s="<<converter.getPhysVelocity(maxMach*std::sqrt(T(1)/3))
      <<"\nmax_abs_fill_step_change="<<maxFillStepChange<<"\nfill_delta_sign_reversals="<<signReversals
      <<"\nmaterial_unchanged="<<same<<"\nfinite="<<final.finite
      <<"\nexit_code="<<(pass?0:3)<<"\nexit_reason="
      <<(pass?(opt.shortRun?"short_stability_gate_pass":"fixed_duration_acceptance_pass")
               :"stability_or_filling_threshold_failure")<<'\n';
    std::ofstream manifest(out/"run_manifest.txt"); manifest
      <<"model=SIM-EC1XT240\nrun_id="<<opt.runId
      <<"\ncommand=mpirun -np 1 ./sim_ec1xt240_right_angle_freesurface --run-id "<<opt.runId
      <<" --max-steps "<<opt.maxSteps<<" --vtk-interval "<<opt.vtkInterval<<(opt.shortRun?" --short":"")
      <<"\nsource=sim_ec1xt240_right_angle_freesurface.cpp\nopenlb=5953d8a-dirty"
      <<"\nexit_code="<<(pass?0:3)<<'\n';
    log<<"PASS="<<pass<<" steps="<<finalStep<<" fill="<<finalFill<<" max_mass_drift="<<maxMassDrift
       <<" max_Mach="<<maxMach<<" rho="<<rhoMinAll<<','<<rhoMaxAll<<'\n';
    std::cout<<opt.runId<<" PASS="<<pass<<" step="<<finalStep<<" fill="<<finalFill<<'\n';
    return pass?0:3;
  } catch (const std::exception& e) {
    log<<"exception="<<e.what()<<"\nexit_code=4\n"; std::cerr<<e.what()<<'\n'; return 4;
  }
}
