// R2-XY 面内最小验证：固定间隙 h=75 nm 受限液区在显式 EX240 沟槽上的毛细铺展
// 协议：CASE/plans/SIM240_液滴R2-XY最小验证协议_20261015.md (v1.0)
// 复用：F1 精确 EX240 几何（x↔y 转置后：槽条沿 y 周期 48 格、槽轴沿 x、槽深 20 格、
//       凸台间隙 15 格、全部壁面 q=0.5）+ step6G 相场 well-balanced CH 两相框架
//       （tanh 初值 + Laplace 压力、材料 2/3 双侧润湿边界）。
#include <olb.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <regex>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <vector>

using namespace olb;
using namespace olb::descriptors;
using namespace olb::names;
using T=double;

using PhaseCase=Case<
  NavierStokes,Lattice<T,D3Q19<RHO,NABLARHO,FORCE,EXTERNAL_FORCE,TAU_EFF>>,
  Component1,Lattice<T,D3Q19<FORCE,SOURCE,SOURCE_OLD,PHIWETTING,VELOCITY,OLD_PHIU,STATISTIC,CHEM_POTENTIAL,BOUNDARY>>
>;
using NSDynamics=MultiPhaseIncompressibleBGKdynamics<T,PhaseCase::descriptor_t_of<NavierStokes>>;
using CHDynamics=WellBalancedCahnHilliardBGKdynamics<T,PhaseCase::descriptor_t_of<Component1>>;
using MixtureRules=LinearTauViscosity;
using Coupling=WellBalancedCahnHilliardPostProcessor<MixtureRules>;

// ---- 几何与物理常数（格子单位；1 格 = dx = 5 nm）----
constexpr T pi=3.1415926535897932384626433832795;
constexpr int NX=579,NY=576,NZ=38;      // x: 2 端盖固壁各 1 格 + 576 流体；y: 周期 576；z: 1 基板 + 35/15 流体 + 模具
constexpr T SUB_Z=0.5;                  // 基板顶面 z=0.5（0 nm）
constexpr T MESA_Z=15.5;                // 凸台面 z=15.5（75 nm）
constexpr T GROOVE_Z=35.5;              // 槽顶 z=35.5（175 nm）
constexpr T CAP_X0=0.5,CAP_X1=576.5;     // x 端盖固壁（0 / 2880 nm）
constexpr int PERIOD=48;                // 周期 48 格（240 nm）
constexpr T GY0=12.5,GY1=36.5;          // 槽条 y∈[12.5,36.5) mod 48（槽宽 24 格 = 120 nm）
constexpr int NSTRIP=12;                // 12 条槽
constexpr T tauL=1.,tauG=.8,tauPhase=1.,rhoL=1.,rhoG=1.,sigma=.01,interfaceWidth=4.;
constexpr T thetaDeg=60.;               // 接触角 60°（理想基准，非实测；THETA=pi-theta 口径同 step6G）
constexpr T dxNm=5.;                    // 1 格 = 5 nm
constexpr T PATCH_A=96.;                // 足迹半宽 96 格 = 480 nm（0.96 μm 直径 = 4 周期）
constexpr T CX=288.5;                   // 足迹中心 x = 1440 nm（域中心）
constexpr T hEq=25.;                    // 等效高度 25 格 = 125 nm（h_eq=75+50）
const T pIn=2.*sigma*std::cos(thetaDeg*pi/180.)/hEq; // Laplace 压力初值 4e-4（std::cos 非 constexpr）

// ---- 全局归约（OpenLB 的 reduceAndBcast 模板未对 long long/std::array 显式实例化，直接用 MPI）----
namespace comm {
  inline void sum(double& v) { MPI_Allreduce(MPI_IN_PLACE,&v,1,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD); }
  inline void sum(long long& v) { MPI_Allreduce(MPI_IN_PLACE,&v,1,MPI_LONG_LONG,MPI_SUM,MPI_COMM_WORLD); }
  inline void min(double& v) { MPI_Allreduce(MPI_IN_PLACE,&v,1,MPI_DOUBLE,MPI_MIN,MPI_COMM_WORLD); }
  inline void max(double& v) { MPI_Allreduce(MPI_IN_PLACE,&v,1,MPI_DOUBLE,MPI_MAX,MPI_COMM_WORLD); }
  inline void max(long long& v) { MPI_Allreduce(MPI_IN_PLACE,&v,1,MPI_LONG_LONG,MPI_MAX,MPI_COMM_WORLD); }
  inline void sum(std::array<double,NSTRIP>& v) { MPI_Allreduce(MPI_IN_PLACE,v.data(),NSTRIP,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD); }
  inline void sum(std::array<long long,4>& v) { MPI_Allreduce(MPI_IN_PLACE,v.data(),4,MPI_LONG_LONG,MPI_SUM,MPI_COMM_WORLD); }
  inline void land(int& v) { MPI_Allreduce(MPI_IN_PLACE,&v,1,MPI_INT,MPI_LAND,MPI_COMM_WORLD); }
}

// ---- 几何：槽条沿 y 周期、槽轴沿 x（F1 的 x↔y 转置）----
bool inGrooveL(T y)
{
  T yw=std::fmod(y,T(PERIOD));
  if (yw<0) yw+=PERIOD;
  return yw>=GY0&&yw<GY1;
}

T upperWallL(T y)
{
  return inGrooveL(y)?GROOVE_Z:MESA_Z;
}

int materialAtL(T x,T y,T z)
{
  if (z<SUB_Z) return 2;                // 基板
  if (x<CAP_X0||x>=CAP_X1) return 4;    // x 端盖：人为壁面，材料 4（无滑移 + 中性角，
                                        // 不挂 60° 润湿——润湿处理器在端盖三重凹角产生伪影尖峰）
  if (z>=upperWallL(y)) return 3;       // 带图案模具
  return 1;                             // 流体
}

class ExactEX240R2XYIndicator final : public IndicatorCuboid3D<T> {
public:
  ExactEX240R2XYIndicator()
    : IndicatorCuboid3D<T>({T(NX),T(NY),T(NZ)},{0,0,0}) { }

  bool distance(T& distance,const Vector<T,3>& origin,const Vector<T,3>& direction,int=-1) override
  {
    T best=std::numeric_limits<T>::infinity();
    const T epsilon=1e-12;
    auto accept=[&](T lambda) {
      if (lambda>=-epsilon&&lambda<=1.0+epsilon) best=std::min(best,std::max(T{},lambda));
    };
    if (direction[2]<0) accept((SUB_Z-origin[2])/direction[2]);
    if (direction[2]>0) {
      for (T wallZ: {MESA_Z,GROOVE_Z}) {
        const T lambda=(wallZ-origin[2])/direction[2];
        if (lambda<-epsilon||lambda>1.0+epsilon) continue;
        const T yHit=origin[1]+lambda*direction[1];
        const bool exists=wallZ==MESA_Z?!inGrooveL(yHit):inGrooveL(yHit);
        if (exists) accept(lambda);
      }
    }
    if (direction[1]!=0) {
      // 每条射线只可能命中 y0±1 范围内的槽侧壁（λ∈[0,1]）→ 按邻近条裁剪，避免扫全部 24 条
      const int kMin=std::max(0,int(std::floor((origin[1]-std::abs(direction[1])-GY0)/T(PERIOD)))-1);
      const int kMax=std::min(NSTRIP-1,int(std::ceil((origin[1]+std::abs(direction[1])-GY0)/T(PERIOD)))+1);
      for (int k=kMin;k<=kMax;++k) {
        for (T wallY: {GY0+T(k*PERIOD),GY1+T(k*PERIOD)}) {
          const T lambda=(wallY-origin[1])/direction[1];
          if (lambda<-epsilon||lambda>1.0+epsilon) continue;
          const T zHit=origin[2]+lambda*direction[2];
          if (zHit>=MESA_Z-epsilon&&zHit<=GROOVE_Z+epsilon) accept(lambda);
        }
      }
    }
    if (direction[0]!=0) {
      for (T wallX: {CAP_X0,CAP_X1}) {
        const T lambda=(wallX-origin[0])/direction[0];
        if (lambda<-epsilon||lambda>1.0+epsilon) continue;
        const T yHit=origin[1]+lambda*direction[1];
        const T zHit=origin[2]+lambda*direction[2];
        if (zHit>=SUB_Z-epsilon&&zHit<=upperWallL(yHit)+epsilon) accept(lambda);
      }
    }
    if (!std::isfinite(best)) return false;
    // 全部壁面位于半格处（60/180/75/100/240/2880 nm 均为 5 nm 整数倍）→ q=0.5 分支对齐
    if (std::abs(best-0.5)<=1e-10) best=0.5;
    distance=best*util::norm<3>(direction);
    return std::isfinite(distance);
  }
};

// ---- 润湿边界用"表面固体"指示器 ----
// setBouzidiWellBalanced 对每个固体格按 face 流体邻居求和法向，深层固体格法向为 {0,0,0}，
// 上游 promisePostProcessorForNormal 会抛 "Invalid normal"。因此只把"有流体面邻居"的
// 表面固体格交给润湿 setter；深层格与纯对角角点格跳过（其 PHIWETTING 保持初值静态近似）。
template<typename T>
class BlockSurfaceSolidIndicator3D final : public BlockIndicatorF3D<T> {
  std::vector<int> _materials;
public:
  BlockSurfaceSolidIndicator3D(BlockGeometry<T,3>& blockGeometry,std::vector<int> materials)
    : BlockIndicatorF3D<T>(blockGeometry),_materials(std::move(materials)) {}
  bool operator()(bool output[],const int input[]) override
  {
    output[0]=false;
    const auto& blockGeometry=this->getBlockGeometry();
    const int current=blockGeometry.getMaterial({input[0],input[1],input[2]});
    const bool isSolid=std::any_of(_materials.begin(),_materials.end(),[current](int m){return current==m;});
    if (!isSolid) return true;
    for (int i=0;i<3;++i) for (int d=-1;d<=1;d+=2) {
      LatticeR<3> n{input[0],input[1],input[2]}; n[i]+=d;
      if (blockGeometry.isInside(n)&&blockGeometry.getMaterial(n)==1) { output[0]=true; return true; }
    }
    return true;
  }
  // 包围盒取整块（保守；仅作优化提示用）
  Vector<int,3> getMin() override
  {
    return Vector<int,3>{
      this->getBlockGeometry().getPadding(),
      this->getBlockGeometry().getPadding(),
      this->getBlockGeometry().getPadding()};
  }
  Vector<int,3> getMax() override
  {
    return Vector<int,3>{
      this->getBlockGeometry().getNx()-this->getBlockGeometry().getPadding()-1,
      this->getBlockGeometry().getNy()-this->getBlockGeometry().getPadding()-1,
      this->getBlockGeometry().getNz()-this->getBlockGeometry().getPadding()-1};
  }
};

template<typename T>
class SuperSurfaceSolidIndicator3D final : public SuperIndicatorF3D<T> {
public:
  SuperSurfaceSolidIndicator3D(SuperGeometry<T,3>& geometry,std::vector<int> materials)
    : SuperIndicatorF3D<T>(geometry)
  {
    for (int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
      this->_blockF.emplace_back(new BlockSurfaceSolidIndicator3D<T>(geometry.getBlockGeometry(iC),materials));
    }
  }
};

// ---- 几何审计（多块 MPI 安全：仅用块内 getMaterial，y 周期经 overlap 交换）----
struct BoundaryAudit {
  long long candidateLinks=0,validDistanceLinks=0,installedLinks=0,geometricFallbacks=0,
    missingFluidNeighbourFallbacks=0,unresolvedLinks=0;
  T qMin=std::numeric_limits<T>::infinity(),qMax=-std::numeric_limits<T>::infinity();
  bool pass=false;
};

template <typename GEOMETRY>
std::array<long long,4> countMaterials(GEOMETRY& geometry)
{
  std::array<long long,4> counts{};
  for (int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
    auto& block=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      const int material=block.getMaterial(latticeR);
      if (material>=0&&material<4) ++counts[material];
    });
  }
  comm::sum(counts);
  return counts;
}

template <typename GEOMETRY>
BoundaryAudit auditGeometryLinks(GEOMETRY& geometry,IndicatorF3D<T>& analyticalBoundary)
{
  using NSD=PhaseCase::descriptor_t_of<NavierStokes>;
  BoundaryAudit audit;
  for (int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
    auto& block=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> fluidR) {
      if (block.getMaterial(fluidR)!=1) return;
      const Vector<T,3> origin=block.getPhysR(fluidR);
      for (int iPop=1;iPop<NSD::q;++iPop) {
        const auto c=descriptors::c<NSD>(iPop);
        const Vector<int,3> solidR(fluidR+c);
        if (!block.isInside(solidR)) continue;
        const int material=block.getMaterial(solidR);
        if (material!=2&&material!=3&&material!=4) continue;
        ++audit.candidateLinks;
        const Vector<T,3> ray=T{1}*c;
        const T norm=util::norm<3>(ray);
        T wallDistance=-1.,q=-1.;
        if (analyticalBoundary.distance(wallDistance,origin.data(),ray,block.getIcGlob())) q=wallDistance/norm;
        if (!(q>0.0&&q<=1.0+1e-10)) ++audit.geometricFallbacks;
        else {
          ++audit.validDistanceLinks;
          audit.qMin=std::min(audit.qMin,q); audit.qMax=std::max(audit.qMax,q);
        }
        if (q>0.5) {
          const Vector<int,3> fluidSideR(fluidR-c);
          if (!block.isInside(fluidSideR)||block.getMaterial(fluidSideR)!=1) ++audit.missingFluidNeighbourFallbacks;
        }
      }
    });
  }
  comm::sum(audit.candidateLinks);
  comm::sum(audit.validDistanceLinks);
  comm::sum(audit.geometricFallbacks);
  comm::sum(audit.missingFluidNeighbourFallbacks);
  comm::min(audit.qMin);
  comm::max(audit.qMax);
  return audit;
}

template <typename LATTICE,typename GEOMETRY>
void auditInstalledDistances(LATTICE& lattice,GEOMETRY& geometry,BoundaryAudit& audit)
{
  using NSD=PhaseCase::descriptor_t_of<NavierStokes>;
  for (int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
    auto& block=lattice.getBlock(iC);
    auto& blockGeometry=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR)!=1) return;
      const auto distances=block.get(latticeR).template getFieldPointer<BOUZIDI_DISTANCE>();
      for (int iPop=1;iPop<NSD::q;++iPop) {
        if (distances[iPop]>0.0) {
          ++audit.installedLinks;
          if (distances[iPop]>1.0+1e-10) ++audit.unresolvedLinks;
        }
      }
    });
  }
  comm::sum(audit.installedLinks);
  comm::sum(audit.unresolvedLinks);
  audit.pass=audit.candidateLinks>0
    &&audit.validDistanceLinks==audit.candidateLinks
    &&audit.installedLinks==audit.candidateLinks
    &&audit.geometricFallbacks==0
    &&audit.missingFluidNeighbourFallbacks==0
    &&audit.unresolvedLinks==0;
}

// ---- 命令行 ----
struct Options {
  std::string mode="run",runId,centerPhase="groove";
  int maxSteps=200,vtkInterval=0;
};

Options parse(int argc,char** argv)
{
  Options o;
  for (int i=1;i<argc;++i) {
    std::string key=argv[i];
    auto value=[&](){ if (++i>=argc) throw std::runtime_error("missing value after "+key); return std::string(argv[i]); };
    if (key=="--mode") o.mode=value();
    else if (key=="--run-id") o.runId=value();
    else if (key=="--max-steps") o.maxSteps=std::stoi(value());
    else if (key=="--vtk-interval") o.vtkInterval=std::stoi(value());
    else if (key=="--center-phase") o.centerPhase=value();
    else throw std::runtime_error("unknown option "+key);
  }
  if (o.mode!="audit"&&o.mode!="run") throw std::runtime_error("--mode must be audit or run");
  if (!std::regex_match(o.runId,std::regex("[A-Za-z0-9][A-Za-z0-9_-]*"))) throw std::runtime_error("--run-id is required");
  if (o.centerPhase!="groove"&&o.centerPhase!="land"&&o.centerPhase!="aligned")
    throw std::runtime_error("--center-phase must be groove, land or aligned");
  return o;
}

// ---- 初值 functor：受限液区（4×4 周期足迹，tanh 平衡剖面 + 弯月面形状）----
// 足迹为带圆角的方形（rounded-box SDF，圆角半径 r=24 格=120 nm）。
// 关键：边缘不是竖直 tanh 墙，而是按每列局部柱高 h 的平衡弯月面
// （圆弧半径 R=h/(2cosθ)，θ=60°）：竖直墙在壁面处与润湿角 90°vs60° 奇异，
// 会造成接触线处 CH 过冲持续增长（实测 φ_max 1.105→1.174→1.239）。弯月面修正
// m(z)=R-sqrt(R²-(z-h/2)²)，接触点较中高前伸 R(1-sinθ)（润湿型，液体沿壁前伸）。
template<typename T>
T roundedBoxSdf(T dx,T dy,T a,T r)
{
  const T dxa=std::abs(dx)-(a-r);
  const T dya=std::abs(dy)-(a-r);
  return std::hypot(std::max(dxa,T{}),std::max(dya,T{}))+std::min(T{},std::max(dxa,dya))-r;
}

template<typename T>
T meniscusOffset(T z,T h)
{
  const T theta=T{60}*pi/T{180};
  const T R=h/(T{2}*std::cos(theta));     // 60° → R=h
  const T dz=z-(SUB_Z+h/T{2});
  const T sq=R*R-dz*dz;
  if (sq<=0) return R*(T{1}-std::sin(theta));
  return R-std::sqrt(sq);
}

template<typename T>
class ConfinedPatchPhaseF3D final : public AnalyticalF3D<T,T> {
  T _cx,_cy,_a,_w,_r;
public:
  ConfinedPatchPhaseF3D(T cx,T cy,T a,T w,T r): AnalyticalF3D<T,T>(1),_cx(cx),_cy(cy),_a(a),_w(w),_r(r) {}
  bool operator()(T output[],const T x[]) override
  {
    const T h=inGrooveL(x[1])?T{35}:T{15}; // 局部柱高（槽 35 / 台 15 格）
    const T d=roundedBoxSdf(x[0]-_cx,x[1]-_cy,_a,_r)+meniscusOffset(x[2],h);
    output[0]=T(.5)*(1+std::tanh(T(2)*d/_w)); // phi=0 液体 / 1 气体
    return true;
  }
};

template<typename T>
class PatchLaplacePressureF3D final : public AnalyticalF3D<T,T> {
  T _cx,_cy,_a,_w,_pIn,_r;
public:
  PatchLaplacePressureF3D(T cx,T cy,T a,T w,T pIn,T r): AnalyticalF3D<T,T>(1),_cx(cx),_cy(cy),_a(a),_w(w),_pIn(pIn),_r(r) {}
  bool operator()(T output[],const T x[]) override
  {
    const T h=inGrooveL(x[1])?T{35}:T{15};
    const T d=roundedBoxSdf(x[0]-_cx,x[1]-_cy,_a,_r)+meniscusOffset(x[2],h);
    output[0]=_pIn*T(.5)*(1-std::tanh(T(2)*d/_w)); // p=pIn*(1-phi)，口径同 E0
    return true;
  }
};

// ---- 几何与格子准备 ----
void prepareGeometry(PhaseCase& c)
{
  auto& geometry=c.getGeometry();
  geometry.setWriteIncrementalVTK(false); // innerClean 会触发增量 VTK 写，12.7M 格串行写极慢（F1 同款设置）
  for (int iC=0;iC<geometry.getLoadBalancer().size();++iC) {
    auto& block=geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      const Vector<T,3> position=block.getPhysR(latticeR);
      block.set(latticeR,materialAtL(position[0],position[1],position[2]));
    });
  }
  geometry.rename(0,0);
  geometry.innerClean();
  geometry.communicate();
}

void prepareLattice(PhaseCase& c)
{
  auto& geometry=c.getGeometry();
  auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  using NSD=PhaseCase::descriptor_t_of<NavierStokes>;
  ns.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,NSD>>(NX,tauL,T(NX),T(0),T(1./6.),T(1));
  ch.setUnitConverter(ns.getUnitConverter());
  dynamics::set<NSDynamics>(ns,geometry.getMaterialIndicator({1}));
  dynamics::set<CHDynamics>(ch,geometry.getMaterialIndicator({1}));
  ExactEX240R2XYIndicator exact;
  setBouzidiBoundary(ns,geometry,2,exact);
  setBouzidiBoundary(ns,geometry,3,exact);
  setBouzidiBoundary(ns,geometry,4,exact);
  setBouzidiBoundary(ch,geometry,4,exact); // 端盖：CH 中性 Bouzidi（必需：无此则端盖泄漏质量，漂移 6.2e-4→7.7e-3/步）
  auto bulk=geometry.getMaterialIndicator(1);
  setBouzidiWellBalanced(ch,
    FunctorPtr<SuperIndicatorF3D<T>>(std::unique_ptr<SuperIndicatorF3D<T>>(new SuperSurfaceSolidIndicator3D<T>(geometry,std::vector<int>{2}))),
    FunctorPtr<SuperIndicatorF3D<T>>(std::unique_ptr<SuperIndicatorF3D<T>>(new SuperIndicatorMaterial3D<T>(geometry,std::vector<int>{1}))),
    exact);
  setBouzidiWellBalanced(ch,
    FunctorPtr<SuperIndicatorF3D<T>>(std::unique_ptr<SuperIndicatorF3D<T>>(new SuperSurfaceSolidIndicator3D<T>(geometry,std::vector<int>{3}))),
    FunctorPtr<SuperIndicatorF3D<T>>(std::unique_ptr<SuperIndicatorF3D<T>>(new SuperIndicatorMaterial3D<T>(geometry,std::vector<int>{1}))),
    exact);
  ch.addPostProcessor<stage::PostStream>(bulk,meta::id<RhoWettingStatistics>());
  auto& coupling=c.setCouplingOperator("Coupling",Coupling{},names::NavierStokes{},ns,names::Component1{},ch);
  coupling.restrictTo(bulk);
  coupling.setParameter<MixtureRules::TAUS>({tauG,tauL});
  coupling.setParameter<MixtureRules::RHOS>({rhoG,rhoL});
  ch.addPostProcessor<stage::ChemPotCalc>(meta::id<ChemPotentialPhaseFieldProcessor>());
  ns.setParameter<OMEGA>(T(1)/tauL); ch.setParameter<OMEGA>(T(1)/tauPhase);
  ch.setParameter<THETA>(pi-thetaDeg*pi/T(180));
  ch.setParameter<INTERFACE_WIDTH>(interfaceWidth); ch.setParameter<SCALAR>(sigma);
  auto& communicator=ch.getCommunicator(stage::PreCoupling());
  communicator.requestOverlap(2); communicator.requestField<STATISTIC>();
  communicator.requestField<PHIWETTING>(); communicator.requestField<CHEM_POTENTIAL>(); communicator.exchangeRequests();
}

void initializeFields(PhaseCase& c,const Options& opt)
{
  auto& geometry=c.getGeometry(); auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  const T cy=opt.centerPhase=="groove"?T(312.5):(opt.centerPhase=="land"?T(288.5):T(288.0));
  AnalyticalConst3D<T,T> zero(0),one(1),two(2),three(3),zeroVelocity(0,0,0),
    rhoV(rhoG),rhoLiq(rhoL),tauV(tauG),tauLiq(tauL);
  ConfinedPatchPhaseF3D<T> phi(CX,cy,PATCH_A,interfaceWidth,T{24});
  PatchLaplacePressureF3D<T> pInit(CX,cy,PATCH_A,interfaceWidth,pIn,T{24});
  AnalyticalIdentity3D<T,T> rhoMix(rhoV+(rhoLiq-rhoV)*phi); // rhoL=rhoG=1 等密度
  AnalyticalIdentity3D<T,T> tauMix(tauV+(tauLiq-tauV)*phi);
  // 先全块（含 padding/overlap）置 φ=1（气）、u=0：
  // 1 格厚基板的润湿处理器读 neighbor(-normal)=基板下方 padding 格的 CH computeRho，
  // padding 内存未初始化（=0）会污染全底层的化学势（官方示例的壁均≥2格厚，无此问题）。
  for (int iC=0;iC<ns.getLoadBalancer().size();++iC) {
    auto& nb=ns.getBlock(iC); auto& hb=ch.getBlock(iC);
    nb.forSpatialLocations([&](LatticeR<3> r){ T rho=1.,u[3]={0,0,0}; nb.get(r).defineRhoU(rho,u); });
    hb.forSpatialLocations([&](LatticeR<3> r){ T rho=1.,u[3]={0,0,0}; hb.get(r).defineRhoU(rho,u); });
  }
  auto all=geometry.getMaterialIndicator({0,1,2,3,4}); // 含端盖：固体格 PHIWETTING/STATISTIC 必须初始化，否则流体格读到垃圾值
  auto bulk=geometry.getMaterialIndicator(1);
  ns.defineRhoU(all,pInit,zeroVelocity); ns.iniEquilibrium(all,pInit,zeroVelocity);
  ch.defineRhoU(all,phi,zeroVelocity); ch.iniEquilibrium(all,phi,zeroVelocity);
  fields::set<RHO>(ns,all,rhoMix); fields::set<TAU_EFF>(ns,bulk,tauMix);
  fields::set<EXTERNAL_FORCE>(ns,all,zeroVelocity);
  fields::set<SOURCE>(ch,bulk,zero); fields::set<SOURCE_OLD>(ch,bulk,zero);
  fields::set<PHIWETTING>(ch,bulk,phi); fields::set<CHEM_POTENTIAL>(ch,bulk,zero);
  fields::set<VELOCITY>(ch,bulk,zeroVelocity); fields::set<OLD_PHIU>(ch,bulk,zero); // initialize() 会读 VELOCITY 场
  fields::set<BOUNDARY>(ch,bulk,zero);
  fields::set<BOUNDARY>(ch,geometry.getMaterialIndicator(2),two);
  fields::set<BOUNDARY>(ch,geometry.getMaterialIndicator(3),three);
  fields::set<BOUNDARY>(ch,geometry.getMaterialIndicator(4),two); // 端盖（BOUNDARY 非零即排除梯度方向）
  ch.executePostProcessors(stage::PreCoupling()); ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.executePostProcessors(stage::ChemPotCalc()); ch.getCommunicator(stage::PreCoupling()).communicate();
  if (singleton::mpi().isMainProcessor()) {
    T s1=0; for (int q=0;q<19;++q) s1+=ch.getBlock(0).get({2,0,1})[q];
    std::cerr<<"dbg4 afterChemPot: PW(2,0,1)="<<ch.getBlock(0).get({2,0,1}).template getField<PHIWETTING>()<<" sumF="<<s1<<'\n';
  }
  ns.initialize(); ch.initialize();
  // ch.initialize() 会污染 PHIWETTING（实测 PW: 1→7/6、Σf: 0→1/6，官方示例/step6G 同款路径）：
  // 重设 PW 并重跑润湿处理器 + 化学势，再重建平衡，保证启动态自洽。
  fields::set<PHIWETTING>(ch,bulk,phi);
  ch.iniEquilibrium(all,phi,zeroVelocity);
  ch.executePostProcessors(stage::PreCoupling()); ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.executePostProcessors(stage::ChemPotCalc()); ch.getCommunicator(stage::PreCoupling()).communicate();
  ch.iniEquilibrium(all,phi,zeroVelocity); ch.getCommunicator(stage::PreCoupling()).communicate();
}

void advance(PhaseCase& c)
{
  auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  ns.collideAndStream(); ch.collideAndStream();
  ch.getCommunicator(stage::PreCoupling()).communicate(); ch.executePostProcessors(stage::PreCoupling());
  ch.getCommunicator(stage::PreCoupling()).communicate(); ch.executePostProcessors(stage::ChemPotCalc());
  ch.getCommunicator(stage::PreCoupling()).communicate(); c.getOperator("Coupling").apply();
}

// ---- 观测 ----
struct Stats {
  T phaseAmount=0,phiMin=1e9,phiMax=-1e9,rhoMin=1e9,rhoMax=-1e9,maxU=0;
  T volOut=0,qPar1=0,qPar2=0,qPerp1=0,qPerp2=0;
  T xMin=1e9,xMax=-1e9,yMin=1e9,yMax=-1e9;
  std::array<T,NSTRIP> vliqGroove{},vliqGap{};
  std::array<T,8> firstBad{}; // x,y,z,lattice(0=NS,1=CH),q,value,phi,p（诊断用）
  std::array<T,4> peakCell{}; // 峰值速度格：x,y,z,speed（诊断用）
  long long nFluid=0; bool finite=true;
};

Stats measure(PhaseCase& c,const Options& opt)
{
  Stats s; auto& geometry=c.getGeometry(); auto& ns=c.getLattice(NavierStokes{}); auto& ch=c.getLattice(Component1{});
  const T cy=opt.centerPhase=="groove"?T(312.5):(opt.centerPhase=="land"?T(288.5):T(288.0));
  for (int iC=0;iC<ns.getLoadBalancer().size();++iC) {
    auto& g=geometry.getBlockGeometry(iC); auto& n=ns.getBlock(iC); auto& h=ch.getBlock(iC);
    n.forCoreSpatialLocations([&](LatticeR<3> r) {
      if (g.getMaterial(r)!=1) return;
      auto nc=n.get(r); auto hc=h.get(r);
      const T phi=hc.computeRho(); const T liquid=T(1)-phi;
      const T rho=nc.template getField<RHO>();
      T u[3]{}; nc.computeU(u);
      const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      s.finite=s.finite&&std::isfinite(phi)&&std::isfinite(rho)&&std::isfinite(speed);
      for (int q=0;q<19;++q) s.finite=s.finite&&std::isfinite(nc[q])&&std::isfinite(hc[q]);
      if (!s.finite&&!s.firstBad[0]) {
        for (int q=0;q<19;++q) {
          if (!std::isfinite(nc[q])) { s.firstBad={T(r[0]),T(r[1]),T(r[2]),T(0),T(q),nc[q],hc.computeRho(),nc.computeRho()}; break; }
          if (!std::isfinite(hc[q])) { s.firstBad={T(r[0]),T(r[1]),T(r[2]),T(1),T(q),hc[q],hc.computeRho(),nc.computeRho()}; break; }
        }
        if (!s.firstBad[0]) s.firstBad={T(r[0]),T(r[1]),T(r[2]),T(2),T(-1),speed,phi,rho};
      }
      const T x=r[0],y=r[1],z=r[2];
      s.phaseAmount+=liquid; ++s.nFluid;
      s.phiMin=std::min(s.phiMin,phi); s.phiMax=std::max(s.phiMax,phi);
      s.rhoMin=std::min(s.rhoMin,rho); s.rhoMax=std::max(s.rhoMax,rho); s.maxU=std::max(s.maxU,speed);
      if (speed>s.peakCell[3]) s.peakCell={T(r[0]),T(r[1]),T(r[2]),speed};
      if (r[2]==1&&r[1]==0&&r[0]==2&&singleton::mpi().getRank()==0) {
        // 探查基板固体格(2,0,0)的润湿处理器产物与流体格(2,0,1)的 Σf
        auto hc0=ch.getBlock(iC).get({2,0,0});
        T sumF=0; for (int q=0;q<19;++q) sumF+=hc[q];
        std::cerr<<"dbg3 substrate(2,0,0): PW="<<hc0.template getField<PHIWETTING>()
          <<" STAT="<<hc0.template getFieldComponent<STATISTIC>(0)
          <<" CP="<<hc0.template getField<CHEM_POTENTIAL>()
          <<" fluid(2,0,1) sumF="<<sumF<<" PW="<<hc.template getField<PHIWETTING>()<<'\n';
      }
      if (r[2]==2&&r[1]==0&&(r[0]==2||r[0]==575)) {
        const T mu=hc.template getField<CHEM_POTENTIAL>();
        T pwMin=1e9,pwMax=-1e9; int badN=-1;
        using CHD=PhaseCase::descriptor_t_of<Component1>;
        for (int q=0;q<CHD::q;++q) {
          const T pw=hc.neighbor(descriptors::c<CHD>(q)).template getField<PHIWETTING>();
          pwMin=std::min(pwMin,pw); pwMax=std::max(pwMax,pw);
          if (pw<0||pw>1.5) badN=q;
        }
        const T ownPw=hc.template getField<PHIWETTING>();
        std::cerr<<"dbg rank"<<singleton::mpi().getRank()<<" cell("<<r[0]<<",0,2): phi="<<phi<<" ownPw="<<ownPw
          <<" nbPwRange=["<<pwMin<<','<<pwMax<<"] badN="<<badN<<" mu="<<mu;
        if (badN>=0) {
          const auto cb=descriptors::c<CHD>(badN);
          std::cerr<<" badNc=("<<cb[0]<<','<<cb[1]<<','<<cb[2]<<")";
        }
        if (singleton::mpi().getRank()==0&&r[0]==2&&pwMax>T(1.2)) {
          std::cerr<<"dbg2 rank0 cell(2,0,2) allNb:";
          for (int q=0;q<CHD::q;++q) {
            const auto cb=descriptors::c<CHD>(q);
            const T pw=hc.neighbor(cb).template getField<PHIWETTING>();
            if (pw>T(1.01)||pw<T(.99)) std::cerr<<" q"<<q<<"("<<cb[0]<<','<<cb[1]<<','<<cb[2]<<")="<<pw;
          }
          std::cerr<<'\n';
        }
        std::cerr<<'\n';
      }
      const int k=int(y)/PERIOD;
      const T yw=y-T(k*PERIOD);
      if (k>=0&&k<NSTRIP&&yw>=13&&yw<36) {
        if (z>=16) s.vliqGroove[k]+=liquid; else s.vliqGap[k]+=liquid;
      }
      if (std::max(std::abs(x-CX),std::abs(y-cy))>PATCH_A) s.volOut+=liquid;
      if (x==180) s.qPar1+=u[0];
      if (x==396) s.qPar2+=u[0];
      if (y==204) s.qPerp1+=u[1];
      if (y==420) s.qPerp2+=u[1];
      if (phi<T(.5)&&std::abs(y-cy)<=T(1)) { s.xMin=std::min(s.xMin,x); s.xMax=std::max(s.xMax,x); }
      if (phi<T(.5)&&std::abs(x-CX)<=T(1)) { s.yMin=std::min(s.yMin,y); s.yMax=std::max(s.yMax,y); }
    });
  }
  comm::sum(s.phaseAmount);
  comm::min(s.phiMin); comm::max(s.phiMax);
  comm::min(s.rhoMin); comm::max(s.rhoMax);
  comm::max(s.maxU);
  comm::sum(s.volOut);
  comm::sum(s.qPar1); comm::sum(s.qPar2);
  comm::sum(s.qPerp1); comm::sum(s.qPerp2);
  comm::min(s.xMin); comm::max(s.xMax);
  comm::min(s.yMin); comm::max(s.yMax);
  comm::sum(s.vliqGroove); comm::sum(s.vliqGap);
  comm::sum(s.nFluid);
  int fin=s.finite?1:0; comm::land(fin); s.finite=fin!=0;
  return s;
}

// ---- 主程序 ----
int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  Options opt; try { opt=parse(argc,argv); } catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 2; }
  const bool master=singleton::mpi().isMainProcessor();
  const auto out=std::filesystem::path("output")/opt.runId;
  if (master) {
    if (std::filesystem::exists(out)) { std::cerr<<"refusing to overwrite existing run\n"; return 2; }
    std::filesystem::create_directories(out);
  }
  singleton::mpi().barrier();
  singleton::directories().setOutputDir((out.string()+"/").c_str());

  IndicatorCuboid3D<T> domain({T(NX),T(NY),T(NZ)},{0,0,0});
  Mesh<T,3> mesh(domain,T(1),singleton::mpi().getSize());
  mesh.setOverlap(3);
  mesh.getCuboidDecomposition().setPeriodicity(Vector<bool,3>{false,true,false});
  PhaseCase::ParametersD parameters; PhaseCase c(parameters,mesh);

  try {
    prepareGeometry(c);
    const bool geometryErrors=c.getGeometry().checkForErrors(false);
    const auto materials=countMaterials(c.getGeometry());
    constexpr long long expectedFluidNodes=8303040; // 576×577×15 + 576×288×20（cuboid n=extent/dx+1：580×577×39）
    const bool geometryPass=!geometryErrors&&materials[1]==expectedFluidNodes;
    prepareLattice(c);
    ExactEX240R2XYIndicator exact;
    BoundaryAudit audit=auditGeometryLinks(c.getGeometry(),exact);
    auditInstalledDistances(c.getLattice(NavierStokes{}),c.getGeometry(),audit);
    if (master) {
      std::ofstream ba(out/"boundary_audit.txt"); ba<<std::setprecision(17)<<std::boolalpha
        <<"geometry_PASS="<<geometryPass<<"\nq_audit_PASS="<<audit.pass
        <<"\nmaterial_0="<<materials[0]<<"\nmaterial_1="<<materials[1]
        <<"\nmaterial_2="<<materials[2]<<"\nmaterial_3="<<materials[3]
        <<"\ncandidate_links="<<audit.candidateLinks<<"\nvalid_distance_links="<<audit.validDistanceLinks
        <<"\ninstalled_links="<<audit.installedLinks<<"\nq_min="<<audit.qMin<<"\nq_max="<<audit.qMax
        <<"\ngeometric_fallback_count="<<audit.geometricFallbacks
        <<"\nmissing_fluid_neighbour_fallback_count="<<audit.missingFluidNeighbourFallbacks
        <<"\nunresolved_link_count="<<audit.unresolvedLinks<<"\nranks="<<singleton::mpi().getSize()<<'\n';
    }
    if (!geometryPass||!audit.pass) {
      if (master) std::cerr<<"geometry or boundary audit FAILED\n";
      return 3;
    }
    if (opt.mode=="audit") {
      if (master) std::cout<<"geometry_PASS=true q_audit_PASS=true fluid="<<materials[1]<<'\n';
      return 0;
    }

    initializeFields(c,opt);
    const Stats initial=measure(c,opt);
    if (master) {
      std::ofstream params(out/"parameters.txt"); params<<std::setprecision(17)
        <<"case=R2XY_confined_patch\nmodel=well_balanced_cahn_hilliard\n"
        <<"dimensions_lattice="<<NX<<','<<NY<<','<<NZ<<"\nranks="<<singleton::mpi().getSize()
        <<"\ndx_nm="<<dxNm<<"\nperiod_nm=240\ngroove_width_nm=120\ngroove_depth_nm=100\nmesa_gap_nm=75\n"
        <<"footprint_half_nm=480\nfootprint_center_x_nm=1440\nfootprint_center_y_nm="<<((opt.centerPhase=="groove"?T(312.5):(opt.centerPhase=="land"?T(288.5):T(288.0)))*dxNm-T(2.5))
        <<"\ncenter_phase="<<opt.centerPhase<<"\ncontact_angle_deg="<<thetaDeg
        <<"\ntau_liquid="<<tauL<<"\ntau_gas="<<tauG<<"\ntau_phase="<<tauPhase
        <<"\nrho_liquid_lattice="<<rhoL<<"\nrho_gas_lattice="<<rhoG<<"\nsurface_tension_lattice="<<sigma
        <<"\ninterface_width_lattice="<<interfaceWidth<<"\ninit_pressure_lattice="<<pIn
        <<"\nunit_convention=match_sigma(dt=2.04e-10s,mu_eff=2e-5Pa_s,per_20261015_protocol_2.8a,formal_run_前确认)\n";
    }
    // history
    std::ofstream csv; long long peakRss=0;
    if (master) {
      csv.open(out/"history.csv"); csv<<std::setprecision(17)
        <<"step,phase_amount,phase_amount_relative_drift,phi_min,phi_max,rho_min,rho_max,max_velocity_lattice,max_Mach,"
        <<"Lpar_nm,Lperp_nm,Qpar_pair,Qperp_pair,Qpar_section1,Qpar_section2,Qperp_section1,Qperp_section2,"
        <<"V_out_nm3,Fg_total";
      for (int k=0;k<NSTRIP;++k) csv<<",Fg_strip"<<k;
      csv<<",finite\n";
    }
    T maxMassDrift=0,maxMach=0; bool allFinite=true; int finalStep=0;
    double tAdvance=0.,tMeasure=0.;
    for (int step=0;step<=opt.maxSteps;++step) {
      const auto t0=std::chrono::steady_clock::now();
      if (step) advance(c);
      const auto t1=std::chrono::steady_clock::now();
      const Stats s=measure(c,opt);
      const auto t2=std::chrono::steady_clock::now();
      if (step) tAdvance+=std::chrono::duration<double>(t1-t0).count();
      tMeasure+=std::chrono::duration<double>(t2-t1).count();
      if (!s.finite) std::cerr<<"firstBad(rank"<<singleton::mpi().getRank()<<"): xyz="<<s.firstBad[0]<<','<<s.firstBad[1]<<','<<s.firstBad[2]
        <<" lattice="<<s.firstBad[3]<<" q="<<s.firstBad[4]<<" value="<<s.firstBad[5]
        <<" phi="<<s.firstBad[6]<<" p="<<s.firstBad[7]<<'\n';
      if ((step==1||step==2)&&s.peakCell[3]>T(1e-3)) std::cerr<<"peakCell(rank"<<singleton::mpi().getRank()<<"): xyz="<<s.peakCell[0]<<','<<s.peakCell[1]<<','<<s.peakCell[2]
        <<" speed="<<s.peakCell[3]<<'\n';
      const T drift=(s.phaseAmount-initial.phaseAmount)/initial.phaseAmount;
      const T mach=s.maxU/std::sqrt(T(1)/3);
      maxMassDrift=std::max(maxMassDrift,std::abs(drift)); maxMach=std::max(maxMach,mach);
      allFinite=allFinite&&s.finite;
      const T lpar=s.xMin<=s.xMax?(s.xMax-s.xMin+T(1))*dxNm/T(2):T(0);
      const T lperp=s.yMin<=s.yMax?(s.yMax-s.yMin+T(1))*dxNm/T(2):T(0);
      const T qParPair=(s.qPar2-s.qPar1)/T(2),qPerpPair=(s.qPerp2-s.qPerp1)/T(2);
      T fgTotal=0;
      const T vg=T(24)*T(576)*T(20);
      for (int k=0;k<NSTRIP;++k) fgTotal+=s.vliqGroove[k]/vg;
      fgTotal/=NSTRIP;
      if (master) {
        csv<<step<<','<<s.phaseAmount<<','<<drift<<','<<s.phiMin<<','<<s.phiMax<<','<<s.rhoMin<<','<<s.rhoMax
           <<','<<s.maxU<<','<<mach<<','<<lpar<<','<<lperp<<','<<qParPair<<','<<qPerpPair
           <<','<<s.qPar1<<','<<s.qPar2<<','<<s.qPerp1<<','<<s.qPerp2
           <<','<<s.volOut*dxNm*dxNm*dxNm<<','<<fgTotal;
        for (int k=0;k<NSTRIP;++k) csv<<','<<s.vliqGroove[k]/vg;
        csv<<','<<s.finite<<'\n';
      }
      finalStep=step;
      // 中断条件：有限性 + 发散级越界。Mach 启动段阈值 0.08（放宽）：
      // 端盖/基板边界邻域存在启动伪影（开放项，见短段报告），其 Mach≈0.05 属局部瞬态；
      // 正式门槛仍按协议 §5：Mach≤0.05 判读（见 NUMERICAL_GATE）。
      if (!s.finite||mach>T(.08)||s.rhoMin<T(.8)||s.rhoMax>T(1.2)||s.phiMin<T(-.2)||s.phiMax>T(1.2)) break;
    }
    rusage usage{}; getrusage(RUSAGE_SELF,&usage); peakRss=usage.ru_maxrss;
    comm::max(peakRss);
    const bool numericalGate=finalStep==opt.maxSteps&&allFinite&&maxMach<=T(.05)
      &&maxMassDrift<=T(1e-3);
    if (master) {
      std::ofstream result(out/"result.txt"); result<<std::setprecision(17)<<std::boolalpha
        <<"NUMERICAL_GATE="<<numericalGate<<"\nRESULT_PASS="<<numericalGate<<"\ngeometry_PASS=true\n"
        <<"steps_completed="<<finalStep<<"\nranks="<<singleton::mpi().getSize()
        <<"\ncells_total="<<static_cast<long long>(NX)*NY*NZ<<"\nfluid_cells="<<initial.nFluid
        <<"\nmax_phase_amount_relative_drift="<<maxMassDrift<<"\nmax_Mach="<<maxMach
        <<"\nphi_range="<<initial.phiMin<<','<<initial.phiMax<<"\nfinite="<<allFinite
        <<"\nadvance_seconds_per_step="<<tAdvance/finalStep<<"\nmeasure_seconds_per_step="<<tMeasure/(finalStep+1)
        <<"\nadvance_seconds_total="<<tAdvance<<"\npeak_rss_kb_per_rank="<<peakRss
        <<"\ninitial_phase_amount="<<initial.phaseAmount<<"\ninitial_V_out_nm3="<<initial.volOut*dxNm*dxNm*dxNm
        <<"\nshort_run="<<(opt.maxSteps<=200?"true":"false")<<"\nexit_code="<<(numericalGate?0:3)<<'\n';
      std::ofstream manifest(out/"run_manifest.txt"); manifest
        <<"run_id="<<opt.runId<<"\ncommand=mpirun -np "<<singleton::mpi().getSize()<<" ./r2xy_confined_patch --mode run --run-id "<<opt.runId
        <<" --max-steps "<<opt.maxSteps<<" --vtk-interval "<<opt.vtkInterval<<" --center-phase "<<opt.centerPhase
        <<"\nopenlb_head=882924a9cfc8dcdf82909e39530789cb6f5ebcc4\nexit_code="<<(numericalGate?0:3)<<'\n';
      std::cout<<opt.runId<<" NUMERICAL_GATE="<<numericalGate<<" step="<<finalStep
               <<" advance_s/step="<<tAdvance/finalStep<<" peak_rss_kb="<<peakRss<<'\n';
    }
    return numericalGate?0:3;
  } catch (const std::exception& e) {
    if (master) { std::ofstream log(out/"run.log"); log<<e.what()<<'\n'; std::cerr<<e.what()<<'\n'; }
    return 4;
  }
}
