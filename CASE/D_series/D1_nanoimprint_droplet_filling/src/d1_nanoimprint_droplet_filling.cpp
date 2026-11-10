/* d1_nanoimprint_droplet_filling.cpp  (V1，2026-10-16)
 *
 * 目的：SIM240 液滴主线的新主体算例（纳米压印·液滴·填充），
 *       采用 OpenLB 官方新框架（Case<> + ParametersD + fromCLI）。
 *
 * V1 目标：**复现 R1 平壁静滴润湿基准** —— 这是新 case 的准入 Gate。
 *   数值对齐 R1（step6G contact）：域 64×40×64、滴半径 18、θ=100°、
 *   tau 1/0.8/1、sigma 0.01、w 4、等密度；写法改为参数化。
 *   ⚠️ R1 的 PASS 不可继承，须由本算例重新确立。
 *
 * 规约依据：CASE/plans/SIM240_新case规约_20261016.md
 *   1. 不继承 R1 的 PASS —— 本算例自行验证。
 *   2. 界面模型 = well-balanced Cahn–Hilliard（WellBalancedCahnHilliardBGKdynamics）。
 *   3. 初值默认 tanh 自洽剖面 + Laplace 压力（INIT_MODE=1）；
 *      INIT_MODE=0 为官方 SmoothIndicatorSphere3D 非平衡剖面，仅用于对照。
 *   4. 模具/基板双接触角待 V3（本 V1 为单平壁，单角）。
 *
 * 冻结门槛（沿用 R1 口径，不改）：
 *   漂移 ≤1e-3 / Mach ≤0.05 / phi ∈ [−0.05,1.05] / 角误差 ≤5° / 末5次角范围 ≤2°
 */

#include <olb.h>
#include <filesystem>

using namespace olb;
using namespace olb::descriptors;
using namespace olb::names;
// 注意：不可 `using namespace olb::parameters;` —— 与 descriptors 有同名标签（如 FORCE），
// 会破坏 D3Q19<...> 的模板参数解析。一律用 parameters:: 限定。

constexpr double PI_ = 3.1415926535897932384626433832795;

// === Step 1: Declarations ===
using MyCase = Case<
  NavierStokes, Lattice<double, D3Q19<RHO,NABLARHO,FORCE,EXTERNAL_FORCE,TAU_EFF>>,
  Component1,  Lattice<double, D3Q19<FORCE,SOURCE,SOURCE_OLD,PHIWETTING,VELOCITY,OLD_PHIU,STATISTIC,CHEM_POTENTIAL,BOUNDARY>>
>;

using NSBulkDynamics = MultiPhaseIncompressibleBGKdynamics<MyCase::value_t, MyCase::descriptor_t>;
using CHBulkDynamics = WellBalancedCahnHilliardBGKdynamics<MyCase::value_t_of<Component1>, MyCase::descriptor_t_of<Component1>>;
using MixtureRules   = LinearTauViscosity;
using Coupling       = WellBalancedCahnHilliardPostProcessor<MixtureRules>;

// 参数标签（案例自定义的部分；官方已有的不得重复定义）
namespace olb::parameters {
struct THETA_MOLD         : public descriptors::FIELD_BASE<1> { };  // 模具面接触角 [deg]  (V3)
struct THETA_SUBSTRATE    : public descriptors::FIELD_BASE<1> { };  // 基板面接触角 [deg]  (V3)
struct LATTICE_RELAXATION_TIME_PF : public descriptors::FIELD_BASE<1> { };
struct LATTICE_RELAXATION_TIME_2  : public descriptors::FIELD_BASE<1> { };
struct C_RHO              : public descriptors::FIELD_BASE<1> { };
struct GAP_H              : public descriptors::FIELD_BASE<1> { };   // 凸台下间隙 [lattice] (V2)
struct PERIOD             : public descriptors::FIELD_BASE<1> { };   // 沟槽周期 [lattice]   (V2)
struct GROOVE_WIDTH       : public descriptors::FIELD_BASE<1> { };   // 槽宽 [lattice]       (V2)
struct GROOVE_DEPTH       : public descriptors::FIELD_BASE<1> { };   // 槽深 [lattice]       (V2)
struct N_PERIOD_X         : public descriptors::FIELD_BASE<1> { };   // 跨槽周期数           (V2)
struct N_PERIOD_Y         : public descriptors::FIELD_BASE<1> { };   // 沿槽周期数           (V2)
struct APPLY_OVERPRESSURE : public descriptors::FIELD_BASE<1> { };   // 超压扫描开关         (V2-Z)
struct DROPLET_RADIUS     : public descriptors::FIELD_BASE<1> { };   // 初始球半径 [lattice]
struct INIT_MODE          : public descriptors::FIELD_BASE<1> { };   // 0=官方非平衡剖面 1=tanh+Laplace
struct PERIODIC_X         : public descriptors::FIELD_BASE<1> { };
struct PERIODIC_Y         : public descriptors::FIELD_BASE<1> { };
struct PERIODIC_Z         : public descriptors::FIELD_BASE<1> { };
struct STAT_INTERVAL      : public descriptors::FIELD_BASE<1> { };   // 诊断/写盘间隔
struct NX_GRID            : public descriptors::FIELD_BASE<1> { };   // 域 x 格数（标量，可命令行覆盖）
struct NY_GRID            : public descriptors::FIELD_BASE<1> { };   // 域 y 格数
struct NZ_GRID            : public descriptors::FIELD_BASE<1> { };   // 域 z 格数
struct RUN_TAG            : public descriptors::FIELD_BASE<1> { };   // 输出子目录编号（多 run 并行不打架）
}

// === tanh 自洽初值 functor（移植自 E0/R1，见规约约束 3）===
// 模型离散平衡界面剖面 phi(d) = 0.5*(1+tanh(2d/w))，d 为到球面带符号距离（外正内负）
template<typename T>
class TanhSpherePhaseF3D final : public AnalyticalF3D<T,T> {
  Vector<T,3> _center; T _radius,_width;
public:
  TanhSpherePhaseF3D(Vector<T,3> center,T radius,T width)
    : AnalyticalF3D<T,T>(1),_center(center),_radius(radius),_width(width) {}
  bool operator()(T output[],const T x[]) override
  {
    const T dx=x[0]-_center[0], dy=x[1]-_center[1], dz=x[2]-_center[2];
    const T d=std::sqrt(dx*dx+dy*dy+dz*dz)-_radius;
    output[0]=T(.5)*(1+std::tanh(T(2)*d/_width));
    return true;
  }
};

// 静水平衡压力初值 p = pIn * (1-phi)，pIn = 2*sigma/R
template<typename T>
class LaplacePressureF3D final : public AnalyticalF3D<T,T> {
  Vector<T,3> _center; T _radius,_width,_pIn; bool _tanh;
public:
  LaplacePressureF3D(Vector<T,3> center,T radius,T width,T pIn,bool tanhProfile)
    : AnalyticalF3D<T,T>(1),_center(center),_radius(radius),_width(width),_pIn(pIn),_tanh(tanhProfile) {}
  bool operator()(T output[],const T x[]) override
  {
    const T dx=x[0]-_center[0], dy=x[1]-_center[1], dz=x[2]-_center[2];
    const T d=std::sqrt(dx*dx+dy*dy+dz*dz)-_radius;
    T solid;
    if (_tanh) { solid=T(.5)*(1-std::tanh(T(2)*d/_width)); }
    else {
      const T eps=_width/T(2);
      if (d<=-eps/T(2)) solid=1;
      else if (d>=eps/T(2)) solid=0;
      else { const T dd=d+eps/T(2); solid=std::cos(PI_/T(2)*dd/eps); solid*=solid; }
    }
    output[0]=_pIn*solid;
    return true;
  }
};

// === Step 2: Mesh ===
Mesh<MyCase::value_t,MyCase::d> createMesh(MyCase::ParametersD& params)
{
  using T = MyCase::value_t;
  Vector extent = params.get<parameters::DOMAIN_EXTENT>();
  std::vector<T> origin(3,T());
  IndicatorCuboid3D<T> cuboid(extent, origin);
  const T dx = 1.;
  Mesh<T,MyCase::d> mesh(cuboid, dx, singleton::mpi().getSize());
  mesh.setOverlap(params.get<parameters::OVERLAP>());
  // V1（复现 R1 平壁静滴）：x/z 周期、y 非周期。
  // V2+ 液滴算例须改全非周期 —— 周期边界会把液滴复制成阵列。
  mesh.getCuboidDecomposition().setPeriodicity({
    params.get<parameters::PERIODIC_X>() > 0.5,
    params.get<parameters::PERIODIC_Y>() > 0.5,
    params.get<parameters::PERIODIC_Z>() > 0.5 });
  return mesh;
}

// === Step 3: Geometry ===
void prepareGeometry(MyCase& myCase)
{
  OstreamManager clout(std::cout,"prepareGeometry");
  auto& geometry = myCase.getGeometry();
  // 官方 contactAngle3d 写法：外圈标为壁面(2)，内部标为流体(1)
  geometry.rename(0,2);
  geometry.rename(2,1,{0,1,0});
  geometry.clean();
  geometry.innerClean();
  geometry.checkForErrors();
  clout << "Prepare Geometry ... OK" << std::endl;
}

// === Step 4: Lattice ===
void prepareLattice(MyCase& myCase)
{
  OstreamManager clout(std::cout,"prepareLattice");
  using T = MyCase::value_t;
  auto& geometry = myCase.getGeometry();
  auto& params   = myCase.getParameters();
  auto& sLatticeNS = myCase.getLattice(NavierStokes{});
  auto& sLatticeCH = myCase.getLattice(Component1{});
  using NSDESCRIPTOR = MyCase::descriptor_t_of<NavierStokes>;

  const Vector extent = params.get<parameters::DOMAIN_EXTENT>();
  const T tau_l     = params.get<parameters::LATTICE_RELAXATION_TIME>();
  const T tau_g     = params.get<parameters::LATTICE_RELAXATION_TIME_2>();
  const T tau_mobil = params.get<parameters::LATTICE_RELAXATION_TIME_PF>();
  const T N         = params.get<parameters::RESOLUTION>();
  const T L_char    = params.get<parameters::PHYS_CHAR_LENGTH>();
  const T C_rho     = params.get<parameters::C_RHO>();
  const T nu_l      = params.get<parameters::NU_LIQUID>();
  const T rho_l     = params.get<parameters::RHO_LIQUID>();
  const T rho_g     = params.get<parameters::RHO_VAPOR>();
  const T sigma     = params.get<parameters::SURFACE_TENSION>();
  const T w         = params.get<parameters::INTERFACE_WIDTH>();
  const T theta     = params.get<parameters::THETA>();

  sLatticeNS.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,NSDESCRIPTOR>>(
    int{N}, tau_l, L_char, T(0), nu_l, C_rho);
  const auto& converter = sLatticeNS.getUnitConverter();
  converter.print();
  sLatticeCH.setUnitConverter(converter);

  dynamics::set<NSBulkDynamics>(sLatticeNS, geometry.getMaterialIndicator({1}));
  dynamics::set<CHBulkDynamics>(sLatticeCH, geometry.getMaterialIndicator({1}));

  auto bulk = geometry.getMaterialIndicator(1);

  std::vector<T> worigin = { -1.5, 0.5, -1.5 };
  std::vector<T> wextend = { extent[0]+2, extent[1]-2, extent[2]+2 };
  IndicatorCuboid3D<T> wallBox(wextend, worigin);
  setBouzidiBoundary(sLatticeNS, geometry, 2, wallBox);
  setBouzidiWellBalanced(sLatticeCH, geometry, 2, wallBox);

  sLatticeCH.addPostProcessor<stage::PostStream>(bulk,meta::id<RhoWettingStatistics>());

  auto& coupling = myCase.setCouplingOperator("Coupling", Coupling{},
    names::NavierStokes{}, sLatticeNS, names::Component1{}, sLatticeCH);
  coupling.restrictTo(geometry.getMaterialIndicator({1}));
  coupling.setParameter<MixtureRules::TAUS>({tau_g,tau_l});
  coupling.setParameter<MixtureRules::RHOS>({rho_g,rho_l});

  sLatticeCH.addPostProcessor<stage::ChemPotCalc>(meta::id<ChemPotentialPhaseFieldProcessor>());

  sLatticeNS.setParameter<descriptors::OMEGA>(1./tau_l);
  sLatticeCH.setParameter<descriptors::OMEGA>(1./tau_mobil);
  sLatticeCH.setParameter<descriptors::THETA>(PI_ - theta*PI_/180.);   // 官方 π−θ 约定
  sLatticeCH.setParameter<descriptors::INTERFACE_WIDTH>(w);
  sLatticeCH.setParameter<descriptors::SCALAR>(sigma);

  {
    auto& communicator = sLatticeCH.getCommunicator(stage::PreCoupling());
    communicator.requestOverlap(2);
    communicator.requestField<STATISTIC>();
    communicator.requestField<PHIWETTING>();
    communicator.requestField<CHEM_POTENTIAL>();
    communicator.exchangeRequests();
  }
  clout << "Prepare Lattice ... OK" << std::endl;
}

// === Step 5: Initial values ===
void setInitialValues(MyCase& myCase)
{
  using T = MyCase::value_t;
  auto& geometry = myCase.getGeometry();
  auto& params   = myCase.getParameters();
  auto& sLatticeNS = myCase.getLattice(NavierStokes{});
  auto& sLatticeCH = myCase.getLattice(Component1{});

  const Vector extent = params.get<parameters::DOMAIN_EXTENT>();
  const T radius = params.get<parameters::DROPLET_RADIUS>();
  const T tau_l  = params.get<parameters::LATTICE_RELAXATION_TIME>();
  const T tau_g  = params.get<parameters::LATTICE_RELAXATION_TIME_2>();
  const T rho_l  = params.get<parameters::RHO_LIQUID>();
  const T rho_g  = params.get<parameters::RHO_VAPOR>();
  const T w      = params.get<parameters::INTERFACE_WIDTH>();
  const T sigma  = params.get<parameters::SURFACE_TENSION>();
  const int initMode = int(params.get<parameters::INIT_MODE>());

  Vector<T,3> center{T(extent[0])/2, T(0), T(extent[2])/2};
  AnalyticalConst3D<T,T> zero(0.), one(1.), two(2.);
  AnalyticalConst3D<T,T> rhov(rho_g), rhol(rho_l), tauv(tau_g), taul(tau_l);
  AnalyticalConst3D<T,T> zeroVel(Vector<T,3>{0.,0.,0.});

  auto bulk  = geometry.getMaterialIndicator(1);
  auto walls = geometry.getMaterialIndicator(2);
  auto all   = geometry.getMaterialIndicator({0,1,2});

  // ---- 相位剖面 ----
  IndicatorSphere3D<T> sphere(center, radius);
  SmoothIndicatorSphere3D<T,T> smoothSphere(sphere, w/2.);
  AnalyticalIdentity3D<T,T> phiOfficial(one - smoothSphere);      // 官方：非平衡剖面
  TanhSpherePhaseF3D<T> phiTanh(center, radius, w);               // 我们：离散平衡剖面

  // ---- 压力初值 ----
  const T pIn = T(2)*sigma/radius;                                // 静水 Laplace 跳变
  LaplacePressureF3D<T> pLaplace(center, radius, w, pIn, initMode==1);
  AnalyticalF3D<T,T>& phi = (initMode==1)
    ? static_cast<AnalyticalF3D<T,T>&>(phiTanh)
    : static_cast<AnalyticalF3D<T,T>&>(phiOfficial);
  AnalyticalF3D<T,T>& pInit = (initMode==1)
    ? static_cast<AnalyticalF3D<T,T>&>(pLaplace)
    : static_cast<AnalyticalF3D<T,T>&>(zero);

  AnalyticalIdentity3D<T,T> rho(rhov + (rhol-rhov)*phi);
  AnalyticalIdentity3D<T,T> tau(tauv + (taul-tauv)*phi);

  sLatticeCH.defineRhoU(all, phi, zeroVel);
  sLatticeCH.iniEquilibrium(all, phi, zeroVel);
  sLatticeNS.defineRhoU(all, pInit, zeroVel);
  sLatticeNS.iniEquilibrium(all, pInit, zeroVel);

  fields::set<descriptors::RHO>(sLatticeNS, all, rho);
  fields::set<descriptors::TAU_EFF>(sLatticeNS, bulk, tau);
  fields::set<descriptors::SOURCE>(sLatticeCH, bulk, zero);
  fields::set<descriptors::SOURCE_OLD>(sLatticeCH, bulk, zero);
  fields::set<descriptors::PHIWETTING>(sLatticeCH, bulk, phi);
  fields::set<descriptors::CHEM_POTENTIAL>(sLatticeCH, bulk, zero);
  fields::set<descriptors::BOUNDARY>(sLatticeCH, bulk, zero);
  fields::set<descriptors::BOUNDARY>(sLatticeCH, walls, two);

  sLatticeCH.executePostProcessors(stage::PreCoupling());
  sLatticeCH.getCommunicator(stage::PreCoupling()).communicate();
  sLatticeCH.executePostProcessors(stage::ChemPotCalc());
  sLatticeCH.getCommunicator(stage::PreCoupling()).communicate();
  sLatticeNS.initialize();
  sLatticeCH.initialize();
  sLatticeCH.iniEquilibrium(all, phi, zeroVel);
  sLatticeCH.getCommunicator(stage::PreCoupling()).communicate();
}

// === 诊断 ===
struct Sample { double x,y,z,phi,p; };
struct Stats {
  double phaseAmount=0, phiMin=1e9, phiMax=-1e9, maxU=0, pInside=0, pOutside=0;
  long long nInside=0, nOutside=0, nFluid=0; bool finite=true;
  std::vector<Sample> samples;
};

Stats measure(MyCase& myCase)
{
  using T = MyCase::value_t;
  Stats s;
  auto& geometry = myCase.getGeometry();
  auto& ns = myCase.getLattice(NavierStokes{});
  auto& ch = myCase.getLattice(Component1{});
  for (int iC=0; iC<ns.getLoadBalancer().size(); ++iC) {
    auto& g = geometry.getBlockGeometry(iC);
    auto& n = ns.getBlock(iC);
    auto& h = ch.getBlock(iC);
    n.forCoreSpatialLocations([&](LatticeR<3> r) {
      const int material = g.getMaterial(r);
      if (material==2) return;
      if (material!=1) return;
      ++s.nFluid;
      auto nc = n.get(r); auto hc = h.get(r);
      const T phi = hc.computeRho();
      const T p   = nc.computeRho();
      T u[3]{}; nc.computeU(u);
      const T speed = std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      s.finite &= std::isfinite(phi) && std::isfinite(p) && std::isfinite(speed);
      s.phaseAmount += T(1)-phi;
      s.phiMin = std::min(s.phiMin,(double)phi);
      s.phiMax = std::max(s.phiMax,(double)phi);
      s.maxU   = std::max(s.maxU,(double)speed);
      if (phi < T(.1)) { s.pInside += p; ++s.nInside; }
      if (phi > T(.9)) { s.pOutside += p; ++s.nOutside; }
      const auto x = g.getPhysR(r);
      s.samples.push_back({x[0],x[1],x[2],(double)phi,(double)p});
    });
  }
  if (s.nInside)  s.pInside  /= s.nInside;
  if (s.nOutside) s.pOutside /= s.nOutside;
  return s;
}

double crossing(std::vector<std::pair<double,double>> line, bool first)
{
  std::sort(line.begin(), line.end());
  std::vector<double> roots;
  for (std::size_t i=1;i<line.size();++i) {
    const double a = line[i-1].second - .5, b = line[i].second - .5;
    if (a==0) roots.push_back(line[i-1].first);
    else if (a*b<0) roots.push_back(line[i-1].first + (line[i].first-line[i-1].first)*(-a)/(b-a));
  }
  if (roots.empty()) return std::numeric_limits<double>::quiet_NaN();
  return first ? roots.front() : roots.back();
}

// 三点定圆测接触角（移植自 R1/step6G，口径一致）
double contactAngle(const Stats& s, const Vector<double,3>& extent)
{
  std::vector<std::pair<double,double>> horizontal, vertical;
  for (const auto& a : s.samples) {
    if (std::abs(a.z - extent[2]/2.) < .25 && std::abs(a.y - 2.) < .25) horizontal.push_back({a.x,a.phi});
    if (std::abs(a.z - extent[2]/2.) < .25 && std::abs(a.x - extent[0]/2.) < .25) vertical.push_back({a.y,a.phi});
  }
  const double x1 = crossing(horizontal,true), x2 = crossing(horizontal,false);
  const double y3 = crossing(vertical,false), x3 = extent[0]/2., y12 = 2.;
  if (!(std::isfinite(x1)&&std::isfinite(x2)&&std::isfinite(y3)) || std::abs(x2-x1)<1e-12)
    return std::numeric_limits<double>::quiet_NaN();
  const double s1=x1*x1+y12*y12, s2=x2*x2+y12*y12, s3=x3*x3+y3*y3;
  const double det = x1*y12+x2*y3+x3*y12-(x2*y12+x3*y12+x1*y3);
  if (std::abs(det)<1e-12) return std::numeric_limits<double>::quiet_NaN();
  const double m12 = s1*y12+s2*y3+s3*y12-(s2*y12+s3*y12+s1*y3);
  const double m13 = s1*x2+s2*x3+s3*x1-(s2*x1+s3*x2+s1*x3);
  const double xc = .5*m12/det, yc = -.5*m13/det;
  const double r = std::hypot(x2-xc, y12-yc);
  const double arg = std::clamp(-(yc-.5)/r, -1., 1.);
  return std::acos(arg)*180./PI_;
}

void advance(MyCase& myCase)
{
  auto& ns = myCase.getLattice(NavierStokes{});
  auto& ch = myCase.getLattice(Component1{});
  ns.collideAndStream();
  ch.collideAndStream();
  ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.executePostProcessors(stage::PreCoupling());
  ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.executePostProcessors(stage::ChemPotCalc());
  ch.getCommunicator(stage::PreCoupling()).communicate();
  myCase.getOperator("Coupling").apply();
}

// === Step 6: Simulate ===
void simulate(MyCase& myCase)
{
  using T = MyCase::value_t;
  auto& params = myCase.getParameters();
  const Vector extent = params.get<parameters::DOMAIN_EXTENT>();
  const int maxT   = int(params.get<parameters::MAX_LATTICE_T>());
  const int statIt = std::max(1, int(params.get<parameters::STAT_INTERVAL>()));
  const int vtkIt  = int(params.get<parameters::LATTICE_VTK_ITER_T>());
  const T theta    = params.get<parameters::THETA>();

  OstreamManager clout(std::cout,"simulate");
  // 每个 run 独立输出子目录（多档并行时互不覆盖）
  const std::string tag = std::to_string(int(params.get<parameters::RUN_TAG>()));
  const std::string outDir = "./output/run" + tag + "/";
  std::filesystem::create_directories(outDir);
  std::ofstream hist(outDir + "history.csv");
  hist << "step,phase_amount,phase_amount_relative_drift,phi_min,phi_max,"
       << "max_Mach,contact_angle_deg,delta_pressure_lattice,finite\n";
  hist << std::setprecision(17);

  const Stats init = measure(myCase);
  const double amount0 = init.phaseAmount;
  double maxDrift = 0., maxMach = 0., phiMin = 1e9, phiMax = -1e9;
  bool finiteAll = true;
  std::vector<double> recentAngles;

  for (int iT=1; iT<=maxT; ++iT) {
    advance(myCase);
    if (iT % statIt == 0 || iT==1) {
      const Stats s = measure(myCase);
      const double drift = (s.phaseAmount - amount0)/amount0;
      const double mach  = s.maxU / std::sqrt(1./3.);
      const double angle = contactAngle(s, extent);
      maxDrift = std::max(maxDrift, std::abs(drift));
      maxMach  = std::max(maxMach, mach);
      phiMin   = std::min(phiMin, s.phiMin);
      phiMax   = std::max(phiMax, s.phiMax);
      finiteAll &= s.finite;
      if (std::isfinite(angle)) { recentAngles.push_back(angle);
        if ((int)recentAngles.size()>5) recentAngles.erase(recentAngles.begin()); }
      hist << iT << "," << s.phaseAmount << "," << drift << "," << s.phiMin << "," << s.phiMax
           << "," << mach << "," << angle << "," << (s.pInside-s.pOutside) << "," << s.finite << "\n";
    }
    if (vtkIt > 0 && iT % vtkIt == 0) {
      clout << "step " << iT << " / " << maxT << std::endl;
    }
  }
  hist.close();

  const double angleFinal = recentAngles.empty()
    ? std::numeric_limits<double>::quiet_NaN() : recentAngles.back();
  double angleRange = 0.;
  if (recentAngles.size() >= 2)
    angleRange = *std::max_element(recentAngles.begin(),recentAngles.end())
               - *std::min_element(recentAngles.begin(),recentAngles.end());

  const bool driftOk = maxDrift <= 1e-3;
  const bool machOk  = maxMach  <= 0.05;
  const bool phiOk   = (phiMin >= -0.05) && (phiMax <= 1.05);
  const bool angleOk = std::isfinite(angleFinal) && std::abs(angleFinal-theta) <= 5.;
  const bool rangeOk = angleRange <= 2.;
  const bool PASS = driftOk && machOk && phiOk && angleOk && rangeOk && finiteAll;

  std::ofstream res(outDir + "result.txt");
  res << std::setprecision(17) << std::boolalpha;
  res << "steps_completed=" << maxT << "\n"
      << "input_contact_angle_deg=" << theta << "\n"
      << "measured_contact_angle_deg=" << angleFinal << "\n"
      << "last_five_contact_angle_range_deg=" << angleRange << "\n"
      << "max_phase_amount_relative_drift=" << maxDrift << "\n"
      << "max_Mach=" << maxMach << "\n"
      << "phi_min=" << phiMin << "\nphi_max=" << phiMax << "\n"
      << "finite=" << finiteAll << "\n"
      << "drift_ok=" << driftOk << "\nmach_ok=" << machOk << "\nphi_ok=" << phiOk << "\n"
      << "angle_ok=" << angleOk << "\nrange_ok=" << rangeOk << "\n"
      << "PASS=" << PASS << "\n";
  res.close();

  clout << "---- V1 判读（冻结门槛）----" << std::endl;
  clout << "  drift      = " << maxDrift << "  (<=1e-3 : " << driftOk << ")" << std::endl;
  clout << "  max Mach   = " << maxMach  << "  (<=0.05 : " << machOk  << ")" << std::endl;
  clout << "  phi range  = [" << phiMin << "," << phiMax << "]  (in[-0.05,1.05] : " << phiOk << ")" << std::endl;
  clout << "  angle      = " << angleFinal << "  (err<=5deg : " << angleOk << ")" << std::endl;
  clout << "  angle range= " << angleRange << "  (<=2deg : " << rangeOk << ")" << std::endl;
  clout << "  PASS = " << PASS << std::endl;
}

// === Step 7: main ===
int main(int argc, char* argv[])
{
  initialize(&argc, &argv);
  MyCase::ParametersD params;

  // ---- V1：数值对齐 R1（step6G contact），写法参数化 ----
  params.set<parameters::DOMAIN_EXTENT              >({64, 40, 64});
  params.set<parameters::DROPLET_RADIUS             >(18.);
  params.set<parameters::RESOLUTION                 >(48.);
  params.set<parameters::LATTICE_RELAXATION_TIME    >(1.);     // tau liquid
  params.set<parameters::LATTICE_RELAXATION_TIME_2  >(0.8);    // tau gas  ← R1 值（官方为 0.52）
  params.set<parameters::LATTICE_RELAXATION_TIME_PF >(1.);     // tau phase
  params.set<parameters::MAX_LATTICE_T              >(6000.);
  params.set<parameters::LATTICE_VTK_ITER_T         >(500.);
  params.set<parameters::STAT_INTERVAL              >(20.);
  params.set<parameters::NX_GRID                    >(64.);   // 域尺寸标量（域向量不能命令行覆盖）
  params.set<parameters::NY_GRID                    >(40.);
  params.set<parameters::NZ_GRID                    >(64.);
  params.set<parameters::RUN_TAG                    >(0.);    // 输出子目录编号
  params.set<parameters::PHYS_CHAR_LENGTH           >(240e-9);
  params.set<parameters::C_RHO                      >(1000.);
  params.set<parameters::NU_LIQUID                  >(1.5e-5);
  params.set<parameters::RHO_LIQUID                 >(1.);
  params.set<parameters::RHO_VAPOR                  >(1.);
  params.set<parameters::SURFACE_TENSION            >(0.01);
  params.set<parameters::INTERFACE_WIDTH            >(4.);
  params.set<parameters::THETA                      >(100.);
  params.set<parameters::INIT_MODE                  >(1.);     // 1=tanh+Laplace（默认）
  // V1 复现 R1：x/z 周期、y 非周期
  params.set<parameters::PERIODIC_X                 >(1.);
  params.set<parameters::PERIODIC_Y                 >(0.);
  params.set<parameters::PERIODIC_Z                 >(1.);

  // ---- V2+ 预留（本 V1 不使用）----
  params.set<parameters::THETA_MOLD                 >(110.);
  params.set<parameters::THETA_SUBSTRATE            >(15.);
  params.set<parameters::GAP_H                      >(15.);
  params.set<parameters::PERIOD                     >(48.);
  params.set<parameters::GROOVE_WIDTH               >(24.);
  params.set<parameters::GROOVE_DEPTH               >(20.);
  params.set<parameters::N_PERIOD_X                 >(8.);
  params.set<parameters::N_PERIOD_Y                 >(8.);
  params.set<parameters::APPLY_OVERPRESSURE         >(0.);

  params.fromCLI(argc, argv);

  // 命令行给的标量域尺寸 → 组装成域向量（DOMAIN_EXTENT 是向量，fromCLI 不支持向量覆盖）
  const Vector<double,3> extentGrid = { params.get<parameters::NX_GRID>(),
                                 params.get<parameters::NY_GRID>(),
                                 params.get<parameters::NZ_GRID>() };
  params.set<parameters::DOMAIN_EXTENT>(extentGrid);

  const std::string outTag = std::to_string(int(params.get<parameters::RUN_TAG>()));
  singleton::directories().setOutputDir("./output/run" + outTag + "/");
  std::filesystem::create_directories("./output/run" + outTag + "/");

  Mesh mesh = createMesh(params);
  MyCase myCase(params, mesh);
  prepareGeometry(myCase);
  prepareLattice(myCase);
  setInitialValues(myCase);
  simulate(myCase);
  return 0;
}
