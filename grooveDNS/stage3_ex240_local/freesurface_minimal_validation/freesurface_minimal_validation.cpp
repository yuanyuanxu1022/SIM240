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

constexpr T dx=5e-9, dt=1e-12, rhoPhys=1000., nu=1e-6, sigma=0.0309;
constexpr int overlap=3;
constexpr T transitionThreshold=1e-3;
constexpr T epsilonTolerance=transitionThreshold+1e-8;
constexpr T pi=3.1415926535897932384626433832795;

// Exact sub-cell volume sampler reused from the verified stage3_free_sphere_test
// initializer. Values are ordered as gas, interface and fluid.
template <typename U>
class ExactSphereVolumeField3D final : public AnalyticalF3D<U,U> {
  std::array<U,3> c; U r,spacing; std::array<U,3> values;
public:
  ExactSphereVolumeField3D(std::array<U,3> center,U radius,U dx,std::array<U,3> v)
    : AnalyticalF3D<U,U>(1),c(center),r(radius),spacing(dx),values(v) { }
  bool operator()(U out[],const U x[]) override {
    constexpr int N=8; int inside=0;
    for (int i=0;i<N;++i) for (int j=0;j<N;++j) for (int k=0;k<N;++k) {
      const U sx=x[0]+((U(i)+U(0.5))/U(N)-U(0.5))*spacing;
      const U sy=x[1]+((U(j)+U(0.5))/U(N)-U(0.5))*spacing;
      const U sz=x[2]+((U(k)+U(0.5))/U(N)-U(0.5))*spacing;
      const U a=sx-c[0],b=sy-c[1],d=sz-c[2];
      inside += a*a+b*b+d*d<=r*r;
    }
    const U f=U(inside)/U(N*N*N);
    if (values[0]==U(0)&&values[1]==U(1)&&values[2]==U(2))
      out[0]=f<=U(0)?values[0]:(f>=U(1)?values[2]:values[1]);
    else out[0]=f;
    return true;
  }
};

struct Options {
  std::string mode,runId;
  int maxSteps=-1,vtkInterval=-1;
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
    if (key=="--case") o.mode=value();
    else if (key=="--run-id") o.runId=value();
    else if (key=="--max-steps") o.maxSteps=std::stoi(value());
    else if (key=="--vtk-interval") o.vtkInterval=std::stoi(value());
    else if (key=="--short") o.shortRun=true;
    else throw std::runtime_error("unknown option "+key);
  }
  if (o.mode!="droplet" && o.mode!="capillary") throw std::runtime_error("--case must be droplet or capillary");
  if (!std::regex_match(o.runId,std::regex("[A-Za-z0-9][A-Za-z0-9_-]*"))) throw std::runtime_error("--run-id is required");
  if (o.maxSteps<0) o.maxSteps=o.shortRun?100:(o.mode=="droplet"?2000:4000);
  if (o.vtkInterval<0) o.vtkInterval=o.shortRun?100:(o.mode=="droplet"?200:400);
  if (o.maxSteps<1 || o.vtkInterval<1) throw std::runtime_error("invalid step count or interval");
  return o;
}

struct CapillaryInitialField final : public AnalyticalF3D<T,T> {
  enum class Kind { Type,Fraction } kind;
  explicit CapillaryInitialField(Kind k) : AnalyticalF3D<T,T>(1),kind(k) { }
  bool operator()(T out[],const T x[]) override {
    T fraction=0;
    int type=static_cast<int>(FreeSurface::Type::Gas);
    if (x[2]<60e-9) {
      fraction=1; type=static_cast<int>(FreeSurface::Type::Fluid);
    } else if (x[2]<65e-9) {
      fraction=T(0.5); type=static_cast<int>(FreeSurface::Type::Interface);
    }
    out[0]=kind==Kind::Type ? T(type) : fraction;
    return true;
  }
};

int capillaryMaterial(const Vector<T,3>& r)
{
  if (r[2]<0 || r[2]>=160e-9 || r[0]<5e-9 || r[0]>=195e-9) return 2;
  const bool wall=(r[0]>=60e-9&&r[0]<70e-9)||(r[0]>=130e-9&&r[0]<140e-9);
  if (wall && r[2]>=60e-9) return 2;
  return 1;
}

template<class GEO>
std::array<long long,3> materialCounts(GEO& geometry)
{
  std::array<long long,3> count{};
  for (int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
    auto& block=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      const int m=block.getMaterial(p); if (m>=0&&m<3) ++count[m];
    });
  }
  return count;
}

struct Stats {
  long long nFluid=0,nInterface=0,nGas=0,nSolid=0;
  T mass=0,liquidVolume=0,rhoMin=std::numeric_limits<T>::max();
  T rhoMax=std::numeric_limits<T>::lowest(),epsilonMin=std::numeric_limits<T>::max();
  T epsilonMax=std::numeric_limits<T>::lowest(),maxULat=0;
  T cx=0,cy=0,cz=0,weight=0,minX=1,maxX=0,minY=1,maxY=0,minZ=1,maxZ=0;
  T slotLiquid=0,slotInterfaceMaxZ=0,outsideInterfaceMaxZ=0;
  bool finite=true;
};

template<class LAT,class GEO>
Stats measure(LAT& lattice,GEO& geometry,const std::string& mode)
{
  Stats s; const T dx3=dx*dx*dx;
  for (int iC=0;iC<lattice.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC); auto& geo=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> p) {
      const int material=geo.getMaterial(p);
      if (material==2) { ++s.nSolid; return; }
      if (material!=1) return;
      auto cell=block.get(p);
      const T eps=cell.template getField<FreeSurface::EPSILON>();
      const T mass=cell.template getField<FreeSurface::MASS>();
      const int type=static_cast<int>(cell.template getField<FreeSurface::CELL_TYPE>());
      T u[3]{}; cell.computeU(u); const T rho=cell.computeRho();
      const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      s.finite &= std::isfinite(eps)&&std::isfinite(mass)&&std::isfinite(rho)&&std::isfinite(speed);
      for (int q=0;q<DESCRIPTOR::q;++q) s.finite &= std::isfinite(cell[q]);
      s.mass+=mass; s.liquidVolume+=eps*dx3;
      s.rhoMin=std::min(s.rhoMin,rho); s.rhoMax=std::max(s.rhoMax,rho);
      s.epsilonMin=std::min(s.epsilonMin,eps); s.epsilonMax=std::max(s.epsilonMax,eps);
      s.maxULat=std::max(s.maxULat,speed);
      const Vector<T,3> r=geo.getPhysR(p);
      if (eps>0) {
        s.cx+=eps*r[0]; s.cy+=eps*r[1]; s.cz+=eps*r[2]; s.weight+=eps;
        s.minX=std::min(s.minX,r[0]); s.maxX=std::max(s.maxX,r[0]);
        s.minY=std::min(s.minY,r[1]); s.maxY=std::max(s.maxY,r[1]);
        s.minZ=std::min(s.minZ,r[2]); s.maxZ=std::max(s.maxZ,r[2]);
      }
      if (mode=="capillary" && r[2]>=60e-9 && r[2]<160e-9) {
        if (r[0]>=70e-9&&r[0]<130e-9) {
          s.slotLiquid+=eps*dx3;
          if (type==static_cast<int>(FreeSurface::Type::Interface)) s.slotInterfaceMaxZ=std::max(s.slotInterfaceMaxZ,r[2]);
        } else if ((r[0]>=5e-9&&r[0]<60e-9)||(r[0]>=140e-9&&r[0]<195e-9)) {
          if (type==static_cast<int>(FreeSurface::Type::Interface)) s.outsideInterfaceMaxZ=std::max(s.outsideInterfaceMaxZ,r[2]);
        }
      }
      if (type==static_cast<int>(FreeSurface::Type::Fluid)) ++s.nFluid;
      else if (type==static_cast<int>(FreeSurface::Type::Interface)) ++s.nInterface;
      else if (type==static_cast<int>(FreeSurface::Type::Gas)) ++s.nGas;
    });
  }
  if (s.weight>0) { s.cx/=s.weight; s.cy/=s.weight; s.cz/=s.weight; }
  return s;
}

template<class LAT,class GEO>
void writeVtk(LAT& lattice,GEO& geometry,const UnitConverter<T,DESCRIPTOR>& converter,
              const std::string& name,int step,bool master)
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
  if (master) writer.createMasterFile();
  writer.write(step);
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if (singleton::mpi().getSize()!=1) { std::cerr<<"single rank required\n"; return 2; }
  Options opt; try { opt=parseOptions(argc,argv); }
  catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 2; }
  const auto out=std::filesystem::path("output")/opt.runId;
  if (std::filesystem::exists(out)) { std::cerr<<"output exists: "<<out<<'\n'; return 2; }
  std::filesystem::create_directories(out);
  singleton::directories().setOutputDir((out.string()+"/").c_str());
  std::ofstream log(out/"run.log"); log<<std::setprecision(17)<<std::boolalpha;
  try {
    const bool droplet=opt.mode=="droplet";
    const Vector<T,3> extent=droplet?Vector<T,3>{235e-9,235e-9,235e-9}:Vector<T,3>{195e-9,35e-9,165e-9};
    const Vector<T,3> origin=droplet?Vector<T,3>{2.5e-9,2.5e-9,2.5e-9}:Vector<T,3>{2.5e-9,2.5e-9,-2.5e-9};
    IndicatorCuboid3D<T> domain(extent,origin);
    CuboidDecomposition<T,3> cuboids(domain,dx,1);
    cuboids.setPeriodicity(droplet?Vector<bool,3>{true,true,true}:Vector<bool,3>{false,true,false});
    HeuristicLoadBalancer<T> load(cuboids); SuperGeometry<T,3> geometry(cuboids,load,overlap);
    for (int iC=0;iC<load.size();++iC) {
      auto& block=geometry.getBlockGeometry(iC);
      block.forCoreSpatialLocations([&](LatticeR<3> p) { block.set(p,droplet?1:capillaryMaterial(block.getPhysR(p))); });
    }
    geometry.communicate(); geometry.checkForErrors(false); const auto initialMaterials=materialCounts(geometry);
    UnitConverter<T,DESCRIPTOR> converter(dx,dt,240e-9,1.,nu,rhoPhys);
    SuperLattice<T,DESCRIPTOR> lattice(converter,cuboids,load);
    dynamics::set<ForcedBGKdynamics>(lattice,geometry,1);
    if (!droplet) boundary::set<boundary::BounceBack>(lattice,geometry,2);
    lattice.setParameter<descriptors::OMEGA>(converter.getLatticeRelaxationFrequency());
    AnalyticalConst3D<T,T> zero(0),one(1),zeros(0,0,0),solidType(T(static_cast<int>(FreeSurface::Type::Solid)));
    for (int material : droplet?std::array<int,2>{1,1}:std::array<int,2>{1,2}) {
      lattice.defineField<FreeSurface::MASS>(geometry,material,zero);
      lattice.defineField<FreeSurface::EPSILON>(geometry,material,zero);
      lattice.defineField<FreeSurface::CELL_TYPE>(geometry,material,zero);
      lattice.defineField<FreeSurface::CELL_FLAGS>(geometry,material,zero);
      lattice.defineField<FreeSurface::TEMP_MASS_EXCHANGE>(geometry,material,zeros);
      lattice.defineField<FreeSurface::PREVIOUS_VELOCITY>(geometry,material,zeros);
      lattice.defineField<FreeSurface::HAS_INTERFACE_NBRS>(geometry,material,one);
      lattice.defineField<descriptors::FORCE>(geometry,material,zeros);
    }
    if (droplet) {
      ExactSphereVolumeField3D<T> typeField({120e-9,120e-9,120e-9},60e-9,dx,{0,1,2});
      ExactSphereVolumeField3D<T> fractionField({120e-9,120e-9,120e-9},60e-9,dx,{0,0.5,1});
      lattice.defineField<FreeSurface::CELL_TYPE>(geometry,1,typeField);
      lattice.defineField<FreeSurface::EPSILON>(geometry,1,fractionField);
      lattice.defineField<FreeSurface::MASS>(geometry,1,fractionField);
    } else {
      CapillaryInitialField typeField(CapillaryInitialField::Kind::Type),fractionField(CapillaryInitialField::Kind::Fraction);
      lattice.defineField<FreeSurface::CELL_TYPE>(geometry,1,typeField);
      lattice.defineField<FreeSurface::EPSILON>(geometry,1,fractionField);
      lattice.defineField<FreeSurface::MASS>(geometry,1,fractionField);
      lattice.defineField<FreeSurface::CELL_TYPE>(geometry,2,solidType);
      lattice.defineField<FreeSurface::EPSILON>(geometry,2,one);
    }
    lattice.defineRhoU(geometry.getMaterialIndicator(1),one,zeros);
    lattice.iniEquilibrium(geometry,1,one,zeros);
    static FreeSurface3DSetup<T,DESCRIPTOR> freeSurface(lattice);
    freeSurface.addPostProcessor(); FreeSurface::initialize(lattice); lattice.initialize();
    const T sigmaLat=dt*dt/(rhoPhys*dx*dx*dx)*sigma;
    lattice.setParameter<FreeSurface::DROP_ISOLATED_CELLS>(true);
    lattice.setParameter<FreeSurface::TRANSITION>(transitionThreshold);
    lattice.setParameter<FreeSurface::LONELY_THRESHOLD>(T(1));
    lattice.setParameter<FreeSurface::HAS_SURFACE_TENSION>(true);
    lattice.setParameter<FreeSurface::SURFACE_TENSION_PARAMETER>(sigmaLat);
    lattice.setParameter<FreeSurface::FORCE_DENSITY>({0,0,0});

    const Stats initial=measure(lattice,geometry,opt.mode);
    const T slotVolume=60e-9*40e-9*100e-9;
    std::ofstream params(out/"parameters.txt"); params<<std::setprecision(17)
      <<"case="<<opt.mode<<"\ngeometry="<<(droplet?"periodic_cube_spherical_droplet":"rectangular_capillary_above_connected_bath")
      <<"\ndx_m="<<dx<<"\ndt_s="<<dt<<"\ntau="<<converter.getLatticeRelaxationTime()
      <<"\nrho_kg_m3="<<rhoPhys<<"\nnu_m2_s="<<nu<<"\nsurface_tension_N_m="<<sigma
      <<"\nsurface_tension_lattice="<<sigmaLat<<"\ntransition="<<transitionThreshold
      <<"\nwetting="<<(droplet?"none":"solid_epsilon_1_qualitative_wetting")
      <<"\ncontact_angle_degrees=not_prescribed_or_calibrated\ngas_model=fixed_reference_pressure_free_surface_state\n";
    std::ofstream csv(out/"history.csv"); csv<<std::setprecision(17)
      <<"step,time_s,liquid_mass_kg,liquid_mass_relative_drift,liquid_volume_m3,equivalent_radius_nm,center_x_nm,center_y_nm,center_z_nm,bbox_x_nm,bbox_y_nm,bbox_z_nm,slot_liquid_volume_m3,slot_total_volume_m3,slot_fill_fraction,slot_interface_max_z_nm,outside_interface_max_z_nm,capillary_rise_nm,n_fluid,n_interface,n_gas,n_solid,rho_min,rho_max,max_speed_m_s,max_Mach,epsilon_min,epsilon_max,finite,material_unchanged\n";
    const std::string vtkName=droplet?"minimal_static_droplet":"minimal_rectangular_capillary";
    writeVtk(lattice,geometry,converter,vtkName,0,true);
    T maxMassDrift=0,maxMach=0,rhoMinAll=initial.rhoMin,rhoMaxAll=initial.rhoMax,maxRadiusDrift=0,maxCenterDrift=0,maxBBoxAnisotropy=0,maxFillStep=0;
    T previousFill=initial.slotLiquid/slotVolume; int finalStep=0; bool allFinite=true,materialsSame=true;
    for (int step=0;step<=opt.maxSteps;++step) {
      if (step) lattice.collideAndStream();
      const Stats s=measure(lattice,geometry,opt.mode);
      const T drift=(s.mass-initial.mass)/initial.mass;
      const T mach=s.maxULat/std::sqrt(T(1)/3);
      const T req=std::cbrt(T(3)*s.liquidVolume/(T(4)*pi));
      const T req0=std::cbrt(T(3)*initial.liquidVolume/(T(4)*pi));
      const T centerDrift=std::sqrt((s.cx-initial.cx)*(s.cx-initial.cx)+(s.cy-initial.cy)*(s.cy-initial.cy)+(s.cz-initial.cz)*(s.cz-initial.cz));
      const T bx=s.maxX-s.minX+dx,by=s.maxY-s.minY+dx,bz=s.maxZ-s.minZ+dx;
      const T anis=std::max({bx,by,bz})-std::min({bx,by,bz});
      const T fill=s.slotLiquid/slotVolume,rise=s.slotInterfaceMaxZ-s.outsideInterfaceMaxZ;
      if (step) maxFillStep=std::max(maxFillStep,std::abs(fill-previousFill));
      previousFill=fill;
      maxMassDrift=std::max(maxMassDrift,std::abs(drift)); maxMach=std::max(maxMach,mach);
      rhoMinAll=std::min(rhoMinAll,s.rhoMin); rhoMaxAll=std::max(rhoMaxAll,s.rhoMax);
      maxRadiusDrift=std::max(maxRadiusDrift,std::abs(req-req0)/req0);
      maxCenterDrift=std::max(maxCenterDrift,centerDrift); maxBBoxAnisotropy=std::max(maxBBoxAnisotropy,anis);
      materialsSame=materialsSame&&(materialCounts(geometry)==initialMaterials); allFinite=allFinite&&s.finite;
      csv<<step<<','<<step*dt<<','<<s.mass*rhoPhys*dx*dx*dx<<','<<drift<<','<<s.liquidVolume<<','<<req*1e9<<','
        <<s.cx*1e9<<','<<s.cy*1e9<<','<<s.cz*1e9<<','<<bx*1e9<<','<<by*1e9<<','<<bz*1e9<<','
        <<s.slotLiquid<<','<<slotVolume<<','<<fill<<','<<s.slotInterfaceMaxZ*1e9<<','<<s.outsideInterfaceMaxZ*1e9<<','<<rise*1e9<<','
        <<s.nFluid<<','<<s.nInterface<<','<<s.nGas<<','<<s.nSolid<<','<<s.rhoMin<<','<<s.rhoMax<<','
        <<converter.getPhysVelocity(s.maxULat)<<','<<mach<<','<<s.epsilonMin<<','<<s.epsilonMax<<','<<s.finite<<','<<materialsSame<<'\n';
      if (step&&step%opt.vtkInterval==0) writeVtk(lattice,geometry,converter,vtkName,step,false);
      finalStep=step;
      if (!s.finite || s.epsilonMin<-epsilonTolerance || s.epsilonMax>T(1)+epsilonTolerance || mach>T(0.05) || s.rhoMin<T(0.8) || s.rhoMax>T(1.2) || !materialsSame) break;
    }
    const Stats final=measure(lattice,geometry,opt.mode); if (finalStep%opt.vtkInterval) writeVtk(lattice,geometry,converter,vtkName,finalStep,false);
    const T finalFill=final.slotLiquid/slotVolume;
    const T finalRise=final.slotInterfaceMaxZ-final.outsideInterfaceMaxZ;
    const bool stable=finalStep==opt.maxSteps&&allFinite&&materialsSame&&maxMach<=T(0.05)&&rhoMinAll>=T(0.8)&&rhoMaxAll<=T(1.2)&&maxMassDrift<=T(5e-3)&&final.epsilonMin>=-epsilonTolerance&&final.epsilonMax<=T(1)+epsilonTolerance;
    const bool shapePass=!droplet||(maxRadiusDrift<=T(5e-3)&&maxCenterDrift<=dx&&maxBBoxAnisotropy<=T(2)*dx);
    const bool responsePass=droplet||(finalFill>=initial.slotLiquid/slotVolume+T(0.01)&&finalRise>=dx&&maxFillStep<=T(0.02));
    const bool pass=stable&&shapePass&&(opt.shortRun||responsePass);
    std::ofstream result(out/"result.txt"); result<<std::setprecision(17)<<std::boolalpha
      <<"PASS="<<pass<<"\nstable="<<stable<<"\nshape_pass="<<shapePass<<"\nwetting_response_pass="<<responsePass
      <<"\nsteps_completed="<<finalStep<<"\nmax_mass_relative_drift="<<maxMassDrift<<"\nmax_Mach="<<maxMach
      <<"\nrho_min="<<rhoMinAll<<"\nrho_max="<<rhoMaxAll<<"\nmax_equivalent_radius_relative_drift="<<maxRadiusDrift
      <<"\nmax_center_drift_nm="<<maxCenterDrift*1e9<<"\nmax_bbox_anisotropy_nm="<<maxBBoxAnisotropy*1e9
      <<"\ninitial_slot_fill="<<initial.slotLiquid/slotVolume<<"\nfinal_slot_fill="<<finalFill
      <<"\nfinal_capillary_rise_nm="<<finalRise*1e9<<"\nmax_abs_fill_step_change="<<maxFillStep
      <<"\nfinite="<<allFinite<<"\nmaterial_unchanged="<<materialsSame<<"\nexit_code="<<(pass?0:3)<<'\n';
    std::ofstream manifest(out/"run_manifest.txt"); manifest<<"run_id="<<opt.runId<<"\ncase="<<opt.mode
      <<"\ncommand=mpirun -np 1 ./freesurface_minimal_validation --case "<<opt.mode<<" --run-id "<<opt.runId
      <<" --max-steps "<<opt.maxSteps<<" --vtk-interval "<<opt.vtkInterval<<(opt.shortRun?" --short":"")
      <<"\nsource=freesurface_minimal_validation.cpp\nopenlb=5953d8a-dirty\nexit_code="<<(pass?0:3)<<'\n';
    log<<"PASS="<<pass<<" steps="<<finalStep<<" max_mass_drift="<<maxMassDrift<<" max_Mach="<<maxMach<<" rho="<<rhoMinAll<<','<<rhoMaxAll<<'\n';
    std::cout<<opt.runId<<" PASS="<<pass<<" step="<<finalStep<<'\n'; return pass?0:3;
  } catch (const std::exception& e) { log<<"exception="<<e.what()<<"\nexit_code=4\n"; std::cerr<<e.what()<<'\n'; return 4; }
}
