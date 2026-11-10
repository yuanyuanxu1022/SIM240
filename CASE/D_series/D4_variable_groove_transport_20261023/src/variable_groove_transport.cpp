#include <olb.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <sstream>
#include <cctype>

using namespace olb;

namespace {

using T = double;
using DESCRIPTOR = descriptors::D3Q19<descriptors::FORCE>;

// Isolated D4 parameterization of the D2 kernel. See the new protocol.
// Boundary, collision, force and flux definitions are retained.
T dx = 5.0e-9;
constexpr T tau = 1.0;
constexpr T rhoPhys = 1000.0;
T nuPhys = 1.0e-6;
T muPhys = rhoPhys * nuPhys;
T acceleration = 1.0e5;
T lx = 240.0e-9;
T ly = 240.0e-9;
T mesaGap = 75.0e-9;
T grooveDepth = 100.0e-9;
T grooveStart = 60.0e-9;
T grooveEnd = 180.0e-9;
T areaPlan = lx * ly;
T nominalVolume = areaPlan * mesaGap
  + (grooveEnd - grooveStart) * ly * grooveDepth;
T referenceHeight = nominalVolume / areaPlan;
T smoothK0 = mesaGap * mesaGap * mesaGap / 12.0;
T dt = (tau - 0.5) * dx * dx / (3.0 * nuPhys);
int nx = 48;
int ny = 48;
constexpr int overlap = 3;
int convergenceWindow = 1000;
int maximumSteps = 60000;
constexpr T relativeStdTolerance = 1.0e-6;
constexpr T relativeSpanTolerance = 5.0e-6;
constexpr T massTolerance = 1.0e-10;
constexpr T densityTolerance = 1.0e-6;
constexpr T machTolerance = 0.05;
constexpr T sectionTolerance = 1.0e-5;
constexpr T crossFluxTolerance = 1.0e-12;
constexpr T qTolerance = 1.0e-10;
constexpr T volumeRoundoffTolerance = 1.0e-10;

struct Parameters {
  std::string mode;
  std::string caseId;
  std::string runId;
  std::vector<T> frameTimes;
  std::filesystem::path configFile;
  std::string directionName;
  int drive = -1;
  double thetaDeg = 0.0;
  double fx = 0.0;
  double fy = 1.0;
  std::filesystem::path outputDirectory;
};

struct BoundaryAudit {
  long long candidateLinks = 0;
  long long validDistanceLinks = 0;
  long long installedLinks = 0;
  long long geometricFallbacks = 0;
  long long missingFluidNeighbourFallbacks = 0;
  long long unresolvedLinks = 0;
  T qMin = std::numeric_limits<T>::infinity();
  T qMax = -std::numeric_limits<T>::infinity();
  T installedQMin = std::numeric_limits<T>::infinity();
  T installedQMax = -std::numeric_limits<T>::infinity();
  bool pass = false;
};

struct Measurement {
  long long fluidNodes = 0;
  T volume = 0.0;
  T mass = 0.0;
  T densityIntegral = 0.0;
  T maxDensityDeviation = 0.0;
  T maxLatticeSpeed = 0.0;
  T pressureMin = std::numeric_limits<T>::infinity();
  T pressureMax = -std::numeric_limits<T>::infinity();
  std::array<T, 3> integratedVelocity{};
  std::array<T, 3> meanVelocity{};
  std::array<T, 3> fluxJ{};
  T sectionQ1 = 0.0;
  T sectionQ2 = 0.0;
  bool finite = true;
};

struct FluxWindow {
  std::deque<T> main;
  std::deque<T> cross;

  void add(T mainValue, T crossValue)
  {
    main.push_back(mainValue);
    cross.push_back(crossValue);
    if (static_cast<int>(main.size()) > convergenceWindow) {
      main.pop_front();
      cross.pop_front();
    }
  }

  bool full() const
  {
    return static_cast<int>(main.size()) == convergenceWindow;
  }

  void metrics(T& relativeStd, T& relativeSpan, T& crossMaximum) const
  {
    const T mean = std::accumulate(main.begin(), main.end(), T{}) / main.size();
    T squared = 0.0;
    for (T value : main) {
      squared += (value - mean) * (value - mean);
    }
    relativeStd = std::sqrt(squared / (main.size() - 1)) / std::abs(mean);
    const auto extrema = std::minmax_element(main.begin(), main.end());
    relativeSpan = (*extrema.second - *extrema.first) / std::abs(mean);
    crossMaximum = 0.0;
    for (T value : cross) {
      crossMaximum = std::max(crossMaximum, std::abs(value));
    }
  }
};


std::map<std::string,std::string> readConfig(const std::filesystem::path& path)
{
  std::ifstream file(path);
  if (!file) throw std::runtime_error("cannot read configuration/manifest");
  std::map<std::string,std::string> values;
  std::string line;
  while (std::getline(file,line)) {
    if (line.empty() || line[0]=='#') continue;
    const auto pos=line.find('=');
    if (pos==std::string::npos || pos==0) throw std::runtime_error("invalid key=value record");
    const auto key=line.substr(0,pos);
    if (!values.emplace(key,line.substr(pos+1)).second) throw std::runtime_error("duplicate key: "+key);
  }
  return values;
}

double number(const std::map<std::string,std::string>& c,const std::string& key)
{
  std::size_t used=0;
  const auto& value=c.at(key);
  const double v=std::stod(value,&used);
  if (used!=value.size() || !std::isfinite(v)) throw std::runtime_error("invalid finite number: "+key);
  return v;
}

Parameters parseParameters(int argc, char* argv[])
{
  if (argc!=2) throw std::runtime_error("usage: variable_groove_transport CONFIG.txt");
  Parameters p;
  p.configFile=std::filesystem::absolute(argv[1]);
  const auto c=readConfig(p.configFile);
  const std::set<std::string> allowed={"mode","run_id","output_directory","direction",
    "dx_nm","h_nm","d_nm","w_nm","period_nm","Ly_nm","nu_m2_s",
    "acceleration_m_s2","window_tstar","max_time_H_diffusion","frame_tstar"};
  for (const auto& [key,value]:c) if (!allowed.count(key)) throw std::runtime_error("unknown key: "+key);
  for (const auto& key:allowed) if (!c.count(key)) throw std::runtime_error("missing key: "+key);
  p.mode=c.at("mode");
  if (p.mode!="describe" && p.mode!="precheck" && p.mode!="initialize" && p.mode!="steady")
    throw std::runtime_error("invalid mode");
  p.runId=c.at("run_id");
  if (p.runId.empty() || p.runId.size()>220 || !std::all_of(p.runId.begin(),p.runId.end(),[](unsigned char v){return std::isalnum(v)||v=='_'||v=='-'||v=='.';}))
    throw std::runtime_error("invalid run_id");
  p.caseId=p.runId;
  if (c.at("output_directory").empty()) throw std::runtime_error("empty output directory");
  p.outputDirectory=std::filesystem::absolute(c.at("output_directory"));
  dx=number(c,"dx_nm")*1e-9;
  mesaGap=number(c,"h_nm")*1e-9;
  grooveDepth=number(c,"d_nm")*1e-9;
  const T width=number(c,"w_nm")*1e-9;
  lx=number(c,"period_nm")*1e-9;
  ly=number(c,"Ly_nm")*1e-9;
  nuPhys=number(c,"nu_m2_s");
  acceleration=number(c,"acceleration_m_s2");
  if (!(dx>0 && mesaGap>0 && grooveDepth>=0 && width>0 && lx>width && ly>0 && nuPhys>0 && acceleration>0))
    throw std::runtime_error("nonpositive/invalid geometry or material");
  grooveStart=(lx-width)/2;
  grooveEnd=(lx+width)/2;
  for (const T length: {lx,ly,mesaGap,grooveDepth,width,grooveStart}) {
    const T n=length/dx;
    if (n>100000 || std::abs(n-std::round(n))>1e-8)
      throw std::runtime_error("geometry must align with lattice cell boundaries");
  }
  nx=static_cast<int>(std::llround(lx/dx));
  ny=static_cast<int>(std::llround(ly/dx));
  if (nx<16 || ny<16) throw std::runtime_error("too few periodic cells for section checks");
  areaPlan=lx*ly;
  nominalVolume=areaPlan*mesaGap+width*ly*grooveDepth;
  referenceHeight=nominalVolume/areaPlan;
  smoothK0=mesaGap*mesaGap*mesaGap/12;
  muPhys=rhoPhys*nuPhys;
  dt=(tau-.5)*dx*dx/(3*nuPhys);
  const T window=number(c,"window_tstar"), cap=number(c,"max_time_H_diffusion");
  if (!(window>0 && cap>window)) throw std::runtime_error("invalid observation times");
  const T windowSteps=std::ceil(window*mesaGap*mesaGap/(nuPhys*dt)-1e-9);
  const T capSteps=std::ceil(cap*std::pow(mesaGap+grooveDepth,2)/(nuPhys*dt)-1e-9);
  if (!(windowSteps>=2 && capSteps>windowSteps && capSteps<2000000000)) throw std::runtime_error("invalid step limits");
  convergenceWindow=static_cast<int>(windowSteps);
  maximumSteps=static_cast<int>(capSteps);
  const auto direction=c.at("direction");
  if (direction=="P") {p.drive=1;p.fx=0;p.fy=1;p.directionName="parallel";}
  else if (direction=="T") {p.drive=0;p.fx=1;p.fy=0;p.directionName="perpendicular";}
  else throw std::runtime_error("direction must be P or T");
  std::stringstream frames(c.at("frame_tstar"));
  std::string part;
  while (std::getline(frames,part,',')) {
    std::map<std::string,std::string> value{{"time",part}};
    const T t=number(value,"time");
    if (t<0 || (!p.frameTimes.empty() && t<=p.frameTimes.back())) throw std::runtime_error("frame times must be increasing nonnegative");
    p.frameTimes.push_back(t);
  }
  if (p.frameTimes.empty() || p.frameTimes.front()!=0 || c.at("frame_tstar").back()==',')
    throw std::runtime_error("frame schedule must begin at zero and have no trailing comma");
  return p;
}

void effectiveConfig(const Parameters& p)
{
  std::ofstream out(p.outputDirectory/"effective_config.txt");
  out<<std::setprecision(17)<<"run_id="<<p.runId<<'\n'<<"mode="<<p.mode<<'\n'
    <<"h_m="<<mesaGap<<'\n'<<"d_m="<<grooveDepth<<'\n'<<"w_m="<<grooveEnd-grooveStart<<'\n'
    <<"Lx_m="<<lx<<'\n'<<"Ly_m="<<ly<<'\n'<<"phi="<<(grooveEnd-grooveStart)/lx<<'\n'
    <<"dx_m="<<dx<<'\n'<<"dt_s="<<dt<<'\n'<<"nx="<<nx<<'\n'<<"ny="<<ny<<'\n'
    <<"nominal_volume_m3="<<nominalVolume<<'\n'<<"plan_area_m2="<<areaPlan<<'\n'
    <<"window_steps="<<convergenceWindow<<'\n'<<"maximum_steps="<<maximumSteps<<'\n'
    <<"acceleration_m_s2="<<acceleration<<'\n'<<"nu_m2_s="<<nuPhys<<'\n'
    <<"formal_simulation="<<(p.mode=="steady"?"true":"false")<<'\n'
    <<"direction="<<p.directionName<<'\n';
}

T wrapX(T x)
{
  x = std::fmod(x, lx);
  return x < 0.0 ? x + lx : x;
}

bool inGroove(T x)
{
  const T wrapped = wrapX(x);
  return wrapped >= grooveStart && wrapped < grooveEnd;
}

T upperWall(T x)
{
  return inGroove(x) ? mesaGap + grooveDepth : mesaGap;
}

int materialAt(const Vector<T, 3>& position)
{
  if (position[2] < 0.0) {
    return 2;
  }
  if (position[2] >= upperWall(position[0])) {
    return 3;
  }
  return 1;
}

class ExactEX240FluidIndicator final : public IndicatorCuboid3D<T> {
public:
  ExactEX240FluidIndicator()
    : IndicatorCuboid3D<T>(
        {lx + 4.0 * dx, ly + 4.0 * dx, mesaGap + grooveDepth},
        {-2.0 * dx, -2.0 * dx, 0.0})
  { }

  bool distance(
    T& distance,
    const Vector<T, 3>& origin,
    const Vector<T, 3>& direction,
    int = -1) override
  {
    T best = std::numeric_limits<T>::infinity();
    const T epsilon = 1.0e-12;
    auto accept = [&](T lambda) {
      if (lambda >= -epsilon && lambda <= 1.0 + epsilon) {
        best = std::min(best, std::max(T{}, lambda));
      }
    };

    if (direction[2] < 0.0) {
      accept((0.0 - origin[2]) / direction[2]);
    }
    if (direction[2] > 0.0) {
      for (T wallZ : {mesaGap, mesaGap + grooveDepth}) {
        const T lambda = (wallZ - origin[2]) / direction[2];
        if (lambda < -epsilon || lambda > 1.0 + epsilon) {
          continue;
        }
        const T xHit = origin[0] + lambda * direction[0];
        const bool horizontalExists = grooveDepth == 0.0 || (wallZ == mesaGap ? !inGroove(xHit) : inGroove(xHit));
        if (horizontalExists) {
          accept(lambda);
        }
      }
    }

    if (direction[0] != 0.0) {
      for (int image = -1; image <= 1; ++image) {
        for (T wallX : {grooveStart + image * lx, grooveEnd + image * lx}) {
          const T lambda = (wallX - origin[0]) / direction[0];
          if (lambda < -epsilon || lambda > 1.0 + epsilon) {
            continue;
          }
          const T zHit = origin[2] + lambda * direction[2];
          if (zHit >= mesaGap - epsilon
              && zHit <= mesaGap + grooveDepth + epsilon) {
            accept(lambda);
          }
        }
      }
    }

    if (!std::isfinite(best)) {
      return false;
    }
    // All EX240 walls are exactly halfway between the adjacent fluid and
    // solid nodes.  Snap round-off-sized deviations to the exact analytical
    // intersection so OpenLB selects its q <= 0.5 Bouzidi branch consistently.
    if (std::abs(best - 0.5) <= qTolerance) {
      best = 0.5;
    }
    distance = best * util::norm<3>(direction);
    return std::isfinite(distance);
  }
};

int wrapIndex(int value, int extent)
{
  value %= extent;
  return value < 0 ? value + extent : value;
}

Vector<int, 3> wrapPeriodicXY(Vector<int, 3> latticeR)
{
  latticeR[0] = wrapIndex(latticeR[0], nx);
  latticeR[1] = wrapIndex(latticeR[1], ny);
  return latticeR;
}

template <typename GEOMETRY>
std::array<long long, 4> countMaterials(GEOMETRY& geometry)
{
  std::array<long long, 4> counts{};
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      const int material = block.getMaterial(latticeR);
      if (material >= 0 && material < static_cast<int>(counts.size())) {
        ++counts[material];
      }
    });
  }
  return counts;
}

template <typename GEOMETRY>
BoundaryAudit auditGeometryLinks(
  GEOMETRY& geometry,
  IndicatorF3D<T>& analyticalBoundary)
{
  BoundaryAudit audit;
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> fluidR) {
      if (block.getMaterial(fluidR) != 1) {
        return;
      }
      const Vector<T, 3> origin = block.getPhysR(fluidR);
      for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
        const auto c = descriptors::c<DESCRIPTOR>(iPop);
        const Vector<int, 3> solidR(fluidR + c);
        const int material = block.getMaterial(wrapPeriodicXY(solidR));
        if (material != 2 && material != 3) {
          continue;
        }
        ++audit.candidateLinks;
        const Vector<T, 3> ray = dx * c;
        const T norm = util::norm<3>(ray);
        T wallDistance = -1.0;
        T q = -1.0;
        if (analyticalBoundary.distance(
              wallDistance, origin.data(), ray, block.getIcGlob())) {
          q = wallDistance / norm;
        }
        if (!(q > 0.0 && q <= 1.0 + qTolerance)) {
          ++audit.geometricFallbacks;
        }
        else {
          ++audit.validDistanceLinks;
          audit.qMin = std::min(audit.qMin, q);
          audit.qMax = std::max(audit.qMax, q);
        }
        // OpenLB reads the second fluid-side node only in the q > 0.5
        // Bouzidi branch.  Counting it for q <= 0.5 incorrectly flags
        // concave step-corner links that use the local q <= 0.5 formula.
        if (q > 0.5) {
          const Vector<int, 3> fluidSideR(fluidR - c);
          if (!block.isInside(fluidSideR)
              || block.getMaterial(wrapPeriodicXY(fluidSideR)) != 1) {
            ++audit.missingFluidNeighbourFallbacks;
          }
        }
      }
    });
  }
  return audit;
}

template <typename LATTICE, typename GEOMETRY>
void auditInstalledDistances(
  LATTICE& lattice,
  GEOMETRY& geometry,
  BoundaryAudit& audit)
{
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      const auto distances = block.get(latticeR)
        .template getFieldPointer<descriptors::BOUZIDI_DISTANCE>();
      for (int iPop = 1; iPop < DESCRIPTOR::q; ++iPop) {
        if (distances[iPop] > 0.0) {
          ++audit.installedLinks;
          audit.installedQMin = std::min(audit.installedQMin, distances[iPop]);
          audit.installedQMax = std::max(audit.installedQMax, distances[iPop]);
          if (distances[iPop] > 1.0 + qTolerance) {
            ++audit.unresolvedLinks;
          }
        }
      }
    });
  }
  audit.pass = audit.candidateLinks > 0
    && audit.validDistanceLinks == audit.candidateLinks
    && audit.installedLinks == audit.candidateLinks
    && audit.geometricFallbacks == 0
    && audit.missingFluidNeighbourFallbacks == 0
    && audit.unresolvedLinks == 0
    && std::abs(audit.installedQMin - audit.qMin) <= qTolerance
    && std::abs(audit.installedQMax - audit.qMax) <= qTolerance;
}

void writeBoundaryAudit(
  const std::filesystem::path& path,
  const BoundaryAudit& audit,
  const std::array<long long, 4>& materials,
  bool geometryPass)
{
  std::ofstream out(path);
  out << std::setprecision(17) << std::boolalpha
      << "geometry_PASS=" << geometryPass << '\n'
      << "q_audit_PASS=" << audit.pass << '\n'
      << "material_0=" << materials[0] << '\n'
      << "material_1=" << materials[1] << '\n'
      << "material_2=" << materials[2] << '\n'
      << "material_3=" << materials[3] << '\n'
      << "candidate_links=" << audit.candidateLinks << '\n'
      << "valid_distance_links=" << audit.validDistanceLinks << '\n'
      << "installed_links=" << audit.installedLinks << '\n'
      << "q_min=" << audit.qMin << '\n'
      << "q_max=" << audit.qMax << '\n'
      << "installed_q_min=" << audit.installedQMin << '\n'
      << "installed_q_max=" << audit.installedQMax << '\n'
      << "geometric_fallback_count=" << audit.geometricFallbacks << '\n'
      << "missing_fluid_neighbour_fallback_count="
      << audit.missingFluidNeighbourFallbacks << '\n'
      << "unresolved_link_count=" << audit.unresolvedLinks << '\n';
}

template <typename LATTICE, typename GEOMETRY>
Measurement measure(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  int drive,
  T fx,
  T fy)
{
  Measurement value;
  const int section1 = drive == 0 ? nx / 8 : ny / 4;
  const int section2 = drive == 0 ? nx / 2 : 3 * ny / 4;
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      auto cell = block.get(latticeR);
      T uLat[3]{};
      cell.computeU(uLat);
      const T rho = cell.computeRho();
      const T speedLat = std::sqrt(
        uLat[0] * uLat[0] + uLat[1] * uLat[1] + uLat[2] * uLat[2]);
      const T pressure = converter.getPhysPressure(
        (rho - 1.0) / descriptors::invCs2<T, DESCRIPTOR>());
      ++value.fluidNodes;
      value.volume += dx * dx * dx;
      value.mass += rho * rhoPhys * dx * dx * dx;
      value.densityIntegral += rho * dx * dx * dx;
      value.maxDensityDeviation = std::max(
        value.maxDensityDeviation, std::abs(rho - 1.0));
      value.maxLatticeSpeed = std::max(value.maxLatticeSpeed, speedLat);
      value.pressureMin = std::min(value.pressureMin, pressure);
      value.pressureMax = std::max(value.pressureMax, pressure);
      value.finite = value.finite && std::isfinite(rho)
        && std::isfinite(speedLat) && std::isfinite(pressure);
      for (int iD = 0; iD < 3; ++iD) {
        const T uPhys = converter.getPhysVelocity(uLat[iD]);
        value.integratedVelocity[iD] += uPhys * dx * dx * dx;
        value.finite = value.finite && std::isfinite(uPhys);
      }
      // Section consistency check must integrate the flux component normal
      // to each section (u_x on x-sections, u_y on y-sections), NOT the
      // projection onto the drive direction: only the normal component is
      // conserved across parallel sections in steady state.
      const T sectionVelocity = drive == 0
        ? converter.getPhysVelocity(uLat[0])
        : converter.getPhysVelocity(uLat[1]);
      const int coordinate = drive == 0 ? latticeR[0] : latticeR[1];
      if (coordinate == section1) {
        value.sectionQ1 += sectionVelocity * dx * dx;
      }
      if (coordinate == section2) {
        value.sectionQ2 += sectionVelocity * dx * dx;
      }
    });
  }
  for (int iD = 0; iD < 3; ++iD) {
    value.meanVelocity[iD] = value.integratedVelocity[iD] / value.volume;
    value.fluxJ[iD] = value.integratedVelocity[iD] / areaPlan;
  }
  return value;
}

template <typename LATTICE, typename GEOMETRY>
void writeFinalProfiles(
  LATTICE& lattice,
  GEOMETRY& geometry,
  const UnitConverter<T, DESCRIPTOR>& converter,
  const Parameters& p)
{
  const int slices = p.drive == 0 ? nx : ny;
  std::vector<T> rhoSum(slices, 0.0);
  std::vector<T> pressureSum(slices, 0.0);
  std::vector<T> velocitySum(slices, 0.0);
  std::vector<T> phiSum(slices, 0.0);
  std::vector<long long> counts(slices, 0);
  std::ofstream field(p.outputDirectory / "field_slice.csv");
  field << std::setprecision(17)
        << "x,z,ux,uy,uz,speed,rho,pressure,Phi,material\n";

  lattice.setProcessingContext(ProcessingContext::Evaluation);
  for (int iC = 0; iC < geometry.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    BlockLatticePhysDissipation3D<T, DESCRIPTOR> dissipation(block, converter);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      if (blockGeometry.getMaterial(latticeR) != 1) {
        return;
      }
      auto cell = block.get(latticeR);
      T uLat[3]{};
      cell.computeU(uLat);
      const T rho = cell.computeRho();
      const T pressure = converter.getPhysPressure(
        (rho - 1.0) / descriptors::invCs2<T, DESCRIPTOR>());
      std::array<T, 3> velocity{};
      T speedSquared = 0.0;
      for (int iD = 0; iD < 3; ++iD) {
        velocity[iD] = converter.getPhysVelocity(uLat[iD]);
        speedSquared += velocity[iD] * velocity[iD];
      }
      int input[3]{latticeR[0], latticeR[1], latticeR[2]};
      T epsilon[1]{};
      dissipation(epsilon, input);
      const T phi = rhoPhys * epsilon[0];
      const int slice = p.drive == 0 ? latticeR[0] : latticeR[1];
      rhoSum[slice] += rho;
      pressureSum[slice] += pressure;
      velocitySum[slice] += velocity[0] * p.fx + velocity[1] * p.fy;
      phiSum[slice] += phi;
      ++counts[slice];

      if (latticeR[1] == ny / 2) {
        const Vector<T, 3> position = blockGeometry.getPhysR(latticeR);
        field << position[0] << ',' << position[2] << ','
              << velocity[0] << ',' << velocity[1] << ',' << velocity[2] << ','
              << std::sqrt(speedSquared) << ',' << rho << ',' << pressure << ','
              << phi << ",1\n";
      }
    });
  }

  std::ofstream pressure(p.outputDirectory / "pressure_profile.csv");
  std::ofstream velocity(p.outputDirectory / "velocity_profile.csv");
  std::ofstream energy(p.outputDirectory / "energy_dissipation.csv");
  pressure << std::setprecision(17) << "position,rho,pressure\n";
  velocity << std::setprecision(17) << "position,velocity\n";
  energy << std::setprecision(17) << "position,Phi\n";
  for (int i = 0; i < slices; ++i) {
    if (counts[i] == 0) {
      continue;
    }
    const T position = (i + 0.5) * dx;
    pressure << position << ',' << rhoSum[i] / counts[i] << ','
             << pressureSum[i] / counts[i] << '\n';
    velocity << position << ',' << velocitySum[i] / counts[i] << '\n';
    energy << position << ',' << phiSum[i] / counts[i] << '\n';
  }
}

} // namespace

int main(int argc, char* argv[])
{
  initialize(&argc, &argv);
  std::cout << std::setprecision(17) << std::boolalpha;
  Parameters p;
  try {
    p = parseParameters(argc, argv);
  }
  catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
  if (singleton::mpi().getSize() != 1) {
    std::cerr << "variable groove solver currently requires exactly one MPI rank\n";
    return 2;
  }
  try {
    const auto manifest=readConfig(p.outputDirectory/"run_manifest.txt");
    if (manifest.at("run_id")!=p.runId || manifest.at("mode")!=p.mode)
      throw std::runtime_error("manifest run_id/mode mismatch");
    if (std::filesystem::exists(p.outputDirectory/"result.txt") || std::filesystem::exists(p.outputDirectory/"effective_config.txt"))
      throw std::runtime_error("refusing to overwrite existing output");
    effectiveConfig(p);
  } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 2;}
  if (p.mode=="describe") return 0;
  singleton::directories().setOutputDir((p.outputDirectory.string() + "/").c_str());

  const T domainTop = mesaGap + grooveDepth + 4.0 * dx;
  IndicatorCuboid3D<T> domain(
    {lx - dx, ly - dx, domainTop},
    {0.5 * dx, 0.5 * dx, -0.5 * dx});
  CuboidDecomposition<T, 3> cuboids(domain, dx, 1);
  cuboids.setPeriodicity({true, true, false});
  HeuristicLoadBalancer<T> loadBalancer(cuboids);
  SuperGeometry<T, 3> geometry(cuboids, loadBalancer, overlap);
  geometry.setWriteIncrementalVTK(false);
  for (int iC = 0; iC < loadBalancer.size(); ++iC) {
    auto& block = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](LatticeR<3> latticeR) {
      block.set(latticeR, materialAt(block.getPhysR(latticeR)));
    });
  }
  geometry.rename(0, 0);
  geometry.communicate();
  const bool geometryErrors = geometry.checkForErrors(false);
  const auto initialMaterials = countMaterials(geometry);
  const long long expectedFluidNodes =
    static_cast<long long>(nx) * ny * static_cast<long long>(std::round(mesaGap / dx))
    + static_cast<long long>(std::round((grooveEnd - grooveStart) / dx)) * ny
      * static_cast<long long>(std::round(grooveDepth / dx));
  const bool geometryPass = !geometryErrors
    && initialMaterials[1] == expectedFluidNodes;

  UnitConverter<T, DESCRIPTOR> converter(dx, dt, lx, 1.0, nuPhys, rhoPhys);
  const bool converterPass = std::abs(converter.getLatticeRelaxationTime() - tau) <= 1.0e-12;
  SuperLattice<T, DESCRIPTOR> lattice(converter, cuboids, loadBalancer);
  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);
  ExactEX240FluidIndicator exactGeometry;
  BoundaryAudit boundaryAudit = auditGeometryLinks(geometry, exactGeometry);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 2, exactGeometry);
  setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>(
    lattice, geometry, 3, exactGeometry);
  auditInstalledDistances(lattice, geometry, boundaryAudit);
  writeBoundaryAudit(
    p.outputDirectory / "boundary_audit.txt",
    boundaryAudit,
    initialMaterials,
    geometryPass);

  const bool precheckPass = geometryPass && converterPass && boundaryAudit.pass;
  if (p.mode == "precheck") {
    std::ofstream result(p.outputDirectory / "result.txt");
    result << std::setprecision(17) << std::boolalpha
           << "case=" << p.caseId << '\n'
           << "run_id=" << p.runId << '\n'
           << "direction=" << p.directionName << '\n'
           << "formal_simulation=false\n"
           << "collide_and_stream_calls=0\n"
           << "geometry_PASS=" << geometryPass << '\n'
           << "converter_PASS=" << converterPass << '\n'
           << "q_audit_PASS=" << boundaryAudit.pass << '\n'
           << "fluid_nodes=" << initialMaterials[1] << '\n'
           << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
           << "installed_links=" << boundaryAudit.installedLinks << '\n'
           << "q_min=" << boundaryAudit.qMin << '\n'
           << "q_max=" << boundaryAudit.qMax << '\n'
           << "fallback_count="
           << boundaryAudit.geometricFallbacks
                + boundaryAudit.missingFluidNeighbourFallbacks << '\n'
           << "exit_code=" << (precheckPass ? 0 : 3) << '\n';
    std::cout << "precheck_PASS=" << precheckPass
              << " links=" << boundaryAudit.installedLinks
              << " q=[" << boundaryAudit.qMin << ',' << boundaryAudit.qMax << "]\n";
    return precheckPass ? 0 : 3;
  }

  if (!precheckPass) {
    std::cerr << "steady run blocked by geometry/converter/boundary precheck\n";
    return 3;
  }

  AnalyticalConst3D<T, T> one(1.0);
  AnalyticalConst3D<T, T> zeroVelocity(0.0, 0.0, 0.0);
  lattice.defineRhoU(geometry.getMaterialIndicator(1), one, zeroVelocity);
  lattice.iniEquilibrium(geometry, 1, one, zeroVelocity);
  Vector<T, 3> force{0.0, 0.0, 0.0};
  force[0] = acceleration * dt * dt / dx * p.fx;
  force[1] = acceleration * dt * dt / dx * p.fy;
  force[2] = 0.0;
  fields::set<descriptors::FORCE>(
    lattice, geometry.getMaterialIndicator(1), force);
  lattice.setParameter<descriptors::OMEGA>(
    converter.getLatticeRelaxationFrequency());
  lattice.initialize();

  SuperVTMwriter3D<T> writer("variable_groove_" + p.directionName, overlap);
  SuperGeometryF3D<T> material(geometry);
  material.getName() = "material";
  SuperLatticePhysVelocity3D<T, DESCRIPTOR> velocity(lattice, converter);
  velocity.getName() = "velocity_m_s";
  SuperLatticePhysPressure3D<T, DESCRIPTOR> pressure(lattice, converter);
  pressure.getName() = "pressure_Pa";
  SuperLatticePhysDissipation3D<T, DESCRIPTOR> dissipation(lattice, converter);
  dissipation.getName() = "dissipation_m2_s3";
  writer.addFunctor(material);
  writer.addFunctor(velocity);
  writer.addFunctor(pressure);
  writer.addFunctor(dissipation);
  writer.createMasterFile();
  std::ofstream frameIndex(p.outputDirectory/"frame_index.csv");
  frameIndex<<"step,time_s,tstar,reason\n"<<std::setprecision(17);
  std::set<int> written;
  auto writeFrame=[&](int step,const std::string& reason) {
    if (written.insert(step).second) {
      lattice.setProcessingContext(ProcessingContext::Evaluation);
      writer.write(step);
      frameIndex<<step<<','<<step*dt<<','<<nuPhys*step*dt/(mesaGap*mesaGap)<<','<<reason<<'\n';
      frameIndex.flush();
    }
  };
  writeFrame(0,"initial");
  if (p.mode=="initialize") {
    const auto zero=measure(lattice,geometry,converter,p.drive,p.fx,p.fy);
    writeFinalProfiles(lattice,geometry,converter,p);
    std::ofstream result(p.outputDirectory/"result.txt");
    result<<std::setprecision(17)<<std::boolalpha<<"run_id="<<p.runId<<'\n'
      <<"formal_simulation=false\ncollide_and_stream_calls=0\nsteps_completed=0\n"
      <<"NUMERICAL_GATE=NOT_EVALUATED\nRESULT_PASS=false\n"
      <<"geometry_PASS="<<geometryPass<<'\n'<<"q_audit_PASS="<<boundaryAudit.pass<<'\n'
      <<"finite="<<zero.finite<<'\n'<<"fluid_nodes="<<zero.fluidNodes<<'\n'
      <<"fluid_volume_m3="<<zero.volume<<'\n'<<"nominal_volume_m3="<<nominalVolume<<'\n'
      <<"frames_written="<<written.size()<<'\n';
    return zero.finite?0:3;
  }
  std::size_t nextFrame=1;

  const Measurement initial = measure(lattice, geometry, converter, p.drive, p.fx, p.fy);
  const bool initialVolumePass = initial.fluidNodes == expectedFluidNodes
    && std::abs(initial.volume - nominalVolume) / nominalVolume
         <= volumeRoundoffTolerance;
  std::ofstream diagnostics(p.outputDirectory / "diagnostics.csv");
  diagnostics << std::setprecision(17)
    << "step,J,rho,Mach,mass,time_s,mass_error,max_density_deviation,"
       "Jx,Jy,Jz,Q_section1,Q_section2,section_relative_difference,"
       "pressure_min,pressure_max,window_rel_std,window_rel_span,"
       "window_cross_abs_max,finite\n";

  FluxWindow window;
  T maxMassError = 0.0;
  T maxDensityDeviation = 0.0;
  T maxMach = 0.0;
  T windowStd = std::numeric_limits<T>::infinity();
  T windowSpan = std::numeric_limits<T>::infinity();
  T windowCross = std::numeric_limits<T>::infinity();
  bool converged = false;
  int finalStep = 0;

  for (int step = 0; step <= maximumSteps; ++step) {
    if (step > 0) {
      lattice.collideAndStream();
    }
    const Measurement state = measure(lattice, geometry, converter, p.drive, p.fx, p.fy);
    const T massError = (state.mass - initial.mass) / initial.mass;
    const T mach = state.maxLatticeSpeed / std::sqrt(T(1.0 / 3.0));
    const T sectionDenominator = std::max(
      std::abs(state.sectionQ1), std::abs(state.sectionQ2));
    const T sectionDifference = sectionDenominator > 0.0
      ? std::abs(state.sectionQ1 - state.sectionQ2) / sectionDenominator : 0.0;
    const T mainFlux = p.fx * state.fluxJ[0] + p.fy * state.fluxJ[1];
    const T crossFlux = -p.fy * state.fluxJ[0] + p.fx * state.fluxJ[1];
    window.add(mainFlux, crossFlux);
    if (window.full()) {
      window.metrics(windowStd, windowSpan, windowCross);
    }
    maxMassError = std::max(maxMassError, std::abs(massError));
    maxDensityDeviation = std::max(
      maxDensityDeviation, state.maxDensityDeviation);
    maxMach = std::max(maxMach, mach);
    diagnostics << step << ',' << mainFlux << ','
                << state.densityIntegral / state.volume << ',' << mach << ','
                << state.mass << ',' << step * dt << ',' << massError << ','
                << state.maxDensityDeviation << ',' << state.fluxJ[0] << ','
                << state.fluxJ[1] << ',' << state.fluxJ[2] << ','
                << state.sectionQ1 << ',' << state.sectionQ2 << ','
                << sectionDifference << ',' << state.pressureMin << ','
                << state.pressureMax << ','
                << (window.full() ? windowStd : -1.0) << ','
                << (window.full() ? windowSpan : -1.0) << ','
                << (window.full() ? windowCross : -1.0) << ','
                << state.finite << '\n';
    const T actualTstar=nuPhys*step*dt/(mesaGap*mesaGap);
    while (nextFrame<p.frameTimes.size() && actualTstar+1e-12>=p.frameTimes[nextFrame]) {
      writeFrame(step,"scheduled");
      ++nextFrame;
    }
    finalStep = step;
    if (window.full()
        && windowStd <= relativeStdTolerance
        && windowSpan <= relativeSpanTolerance
        && windowCross <= crossFluxTolerance) {
      converged = true;
      break;
    }
  }

  const Measurement final = measure(lattice, geometry, converter, p.drive, p.fx, p.fy);
  writeFrame(finalStep,converged?"converged_final":"unconverged_final");
  std::ofstream schedule(p.outputDirectory/"frame_schedule.csv");
  schedule<<"requested_tstar,target_step,reached\n"<<std::setprecision(17);
  for (T target:p.frameTimes) {
    const auto targetStep=static_cast<long long>(std::ceil(target*mesaGap*mesaGap/(nuPhys*dt)-1e-9));
    schedule<<target<<','<<targetStep<<','<<(targetStep<=finalStep)<<'\n';
  }
  writeFinalProfiles(lattice, geometry, converter, p);
  const auto finalMaterials = countMaterials(geometry);
  const bool materialUnchanged = finalMaterials == initialMaterials;
  const T sectionDenominator = std::max(
    std::abs(final.sectionQ1), std::abs(final.sectionQ2));
  const T sectionDifference = sectionDenominator > 0.0
    ? std::abs(final.sectionQ1 - final.sectionQ2) / sectionDenominator : 0.0;
  const T mainJ = p.fx * final.fluxJ[0] + p.fy * final.fluxJ[1];
  const T effectiveK = muPhys * mainJ / (rhoPhys * acceleration);
  const T resistance = rhoPhys * acceleration / mainJ;
  const bool pass = initialVolumePass
    && boundaryAudit.pass
    && materialUnchanged
    && final.finite
    && converged
    && maxMassError < massTolerance
    && maxDensityDeviation <= densityTolerance
    && maxMach < machTolerance
    && windowCross <= crossFluxTolerance
    && sectionDifference <= sectionTolerance
    && mainJ > 0.0;

  std::ofstream summary(p.outputDirectory / "result_summary.csv");
  summary << std::setprecision(17)
          << "Case,direction,dx,tau,force,J,Keff,R_eff,Mach,mass_error\n"
          << p.caseId << ',' << p.directionName << ',' << dx << ',' << tau << ','
          << acceleration << ',' << mainJ << ',' << effectiveK << ','
          << resistance << ',' << maxMach << ',' << maxMassError << '\n';

  std::ofstream result(p.outputDirectory / "result.txt");
  result << std::setprecision(17) << std::boolalpha
         << "case=" << p.caseId << '\n'
         << "direction=" << p.directionName << '\n'
         << "run_id=" << p.runId << '\n'
         << "formal_simulation=true\n"
         << "geometry_PASS=" << geometryPass << '\n'
         << "NUMERICAL_GATE=" << (pass?"PASS":"FAIL") << '\n'
         << "RESULT_PASS=false\n"
         << "PASS=" << pass << '\n'
         << "frames_written=" << written.size() << '\n'
         << "window_steps=" << convergenceWindow << '\n'
         << "maximum_steps=" << maximumSteps << '\n' 
         << "converged=" << converged << '\n'
         << "steps_completed=" << finalStep << '\n'
         << "Lx_m=" << lx << '\n'
         << "Ly_m=" << ly << '\n'
         << "mesa_gap_m=" << mesaGap << '\n'
         << "groove_depth_m=" << grooveDepth << '\n'
         << "groove_width_m=" << grooveEnd - grooveStart << '\n'
         << "H_ref_m=" << referenceHeight << '\n'
         << "dx_m=" << dx << '\n'
         << "dt_s=" << dt << '\n'
         << "tau=" << converter.getLatticeRelaxationTime() << '\n'
         << "descriptor=D3Q19_FORCE\n"
         << "collision=ForcedBGK\n"
         << "wall_boundary=Bouzidi_zero_velocity_exact_EX240\n"
         << "periodicity=x_y\n"
         << "acceleration_m_s2=" << acceleration << '\n'
         << "rho_phys_kg_m3=" << rhoPhys << '\n'
         << "nu_phys_m2_s=" << nuPhys << '\n'
         << "mu_phys_Pa_s=" << muPhys << '\n'
         << "force_lattice=" << force[0] << ',' << force[1] << ',' << force[2] << '\n'
         << "fluid_nodes=" << final.fluidNodes << '\n'
         << "fluid_volume_m3=" << final.volume << '\n'
         << "nominal_volume_m3=" << nominalVolume << '\n'
         << "candidate_links=" << boundaryAudit.candidateLinks << '\n'
         << "installed_links=" << boundaryAudit.installedLinks << '\n'
         << "q_min=" << boundaryAudit.qMin << '\n'
         << "q_max=" << boundaryAudit.qMax << '\n'
         << "fallback_count="
         << boundaryAudit.geometricFallbacks
              + boundaryAudit.missingFluidNeighbourFallbacks << '\n'
         << "unresolved_links=" << boundaryAudit.unresolvedLinks << '\n'
         << "max_mass_abs_relative=" << maxMassError << '\n'
         << "max_density_deviation=" << maxDensityDeviation << '\n'
         << "max_Mach=" << maxMach << '\n'
         << "pressure_range_Pa=" << final.pressureMin << ',' << final.pressureMax << '\n'
         << "J_vector_m2_s=" << final.fluxJ[0] << ',' << final.fluxJ[1] << ','
         << final.fluxJ[2] << '\n'
         << "J_main_m2_s=" << mainJ << '\n'
         << "Keff_m3=" << effectiveK << '\n'
         << "K0_smooth_h_m3=" << smoothK0 << '\n'
         << "Keff_over_K0=" << effectiveK / smoothK0 << '\n'
         << "R_eff_Pa_s_per_m3=" << resistance << '\n'
         << "Q_sections_m3_s=" << final.sectionQ1 << ',' << final.sectionQ2 << '\n'
         << "section_relative_difference=" << sectionDifference << '\n'
         << "window_main_rel_std=" << windowStd << '\n'
         << "window_main_rel_span=" << windowSpan << '\n'
         << "window_cross_abs_max=" << windowCross << '\n'
         << "material_unchanged=" << materialUnchanged << '\n'
         << "finite=" << final.finite << '\n'
         << "exit_code=" << (pass ? 0 : 3) << '\n';
  std::cout << "case=" << p.caseId << " PASS=" << pass
            << " step=" << finalStep << " J=" << mainJ
            << " Keff=" << effectiveK << '\n';
  return pass ? 0 : 3;
}
