#pragma once

// Read-only observer. This header has no OpenLB state-mutating API.
#include <algorithm>
#include <array>
#include <bit>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <stdexcept>
#include <vector>

namespace fine_t_mass {
inline constexpr int lastStep = 4000;
inline constexpr std::array<int, 9> snapshotSteps{0,119,120,624,625,626,3732,3733,4000};
inline constexpr std::uint64_t expectedNodes = 3686400;
inline constexpr std::uint64_t expectedCore = 192ULL*192*145;
static_assert(sizeof(double) == 8 && std::numeric_limits<double>::is_iec559);
static_assert(std::endian::native == std::endian::little,
              "Snapshot schema v1 requires little-endian IEEE binary64");

struct Neumaier {
  double sum = 0.0, correction = 0.0;
  void add(double value) {
    const double next = sum + value;
    correction += std::abs(sum) >= std::abs(value)
      ? (sum-next)+value : (value-next)+sum;
    sum = next;
  }
  double value() const { return sum + correction; }
};

inline std::ofstream newFile(const std::filesystem::path& path, bool binary=false) {
  if (std::filesystem::exists(path)) throw std::runtime_error("Diagnostic refuses overwrite: " + path.string());
  std::ofstream out;
  out.exceptions(std::ios::failbit | std::ios::badbit);
  out.open(path, std::ios::out | (binary ? std::ios::binary : std::ios::openmode{}));
  return out;
}
template<class T> void binaryWrite(std::ofstream& out, const T& value) {
  out.write(reinterpret_cast<const char*>(&value), sizeof(value));
}
inline void hashWord(std::uint64_t& hash, std::uint64_t word) {
  for (int i=0; i<8; ++i) {
    hash ^= (word >> (8*i)) & 255ULL;
    hash *= 1099511628211ULL; // uint64 wrap is intentional
  }
}

class Observer {
  std::filesystem::path directory;
  std::ofstream csv;
  int step = -1, rows = 0, peakStep = -1;
  std::array<std::uint64_t,4> materials{}, initialMaterials{};
  std::uint64_t coreCount=0, hash=0, initialHash=0, lastId=0;
  bool haveId=false, lastFluid=false, finite=true, densityRecorded=false;
  std::uint64_t filmNodes=0, recessNodes=0, rhoMinId=0, rhoMaxId=0;
  double rhoMin=0, rhoMax=0;
  long double filmDelta=0, recessDelta=0, maxReconstruction=0;
  Neumaier massComp{}, rhoComp{}, deltaComp{};
  long double massLong=0, rhoLong=0, deltaLong=0;
  long double m0Comp=0, m0Long=0, delta0=0, legacy0=0, bias0=0;
  long double maxStable=0, maxComp=0, maxLong=0, maxAgreement=0;
  double peakLegacy=-1;
  std::vector<std::uint64_t> mask;
  std::vector<double> rhoBuffer, peakRho;

  void writeSnapshot(int snapshotStep, const std::vector<double>& rho, bool peak=false) {
    const auto name = peak ? "peak_rho.bin" : "rho_step_" + std::to_string(snapshotStep) + ".bin";
    auto out = newFile(directory/name, true);
    out.write("FTMRHO1\0", 8);
    binaryWrite(out, static_cast<std::int32_t>(snapshotStep));
    binaryWrite(out, static_cast<std::uint64_t>(rho.size()));
    binaryWrite(out, initialHash);
    out.write(reinterpret_cast<const char*>(rho.data()), rho.size()*sizeof(double));
    out.close();
  }
  void writeMask() {
    auto out = newFile(directory/"fluid_mask.bin", true);
    out.write("FTMMASK1", 8);
    binaryWrite(out, static_cast<std::uint64_t>(mask.size()));
    binaryWrite(out, initialHash);
    for (std::int32_t n : {192,192,145}) binaryWrite(out,n);
    out.write(reinterpret_cast<const char*>(mask.data()), mask.size()*sizeof(std::uint64_t));
    out.close();
  }
public:
  explicit Observer(const std::filesystem::path& output)
    : directory(output/"mass_snapshots"), csv(newFile(output/"mass_ledger.csv")) {
    if (!std::filesystem::create_directory(directory)) throw std::runtime_error("Snapshot directory already exists");
    mask.reserve(expectedNodes); rhoBuffer.reserve(expectedNodes); peakRho.reserve(expectedNodes);
    csv << std::setprecision(std::numeric_limits<long double>::max_digits10)
      << "step,time_s,core_nodes,material0,material1,material2,material3,material_hash,"
         "legacy_M0_kg,legacy_M_kg,legacy_e,legacy_peak,volume_seq_m3,density_integral_seq,"
         "nominal_M_kg,mass_neumaier_kg,mass_long_double_kg,rho_neumaier,rho_long_double,"
         "delta_neumaier,delta_long_double,M0_neumaier_kg,M0_long_double_kg,delta0,"
         "e_neumaier,e_long_double,e_delta,max_e_neumaier,max_e_long_double,max_e_delta,"
         "bias_t_kg,bias0_kg,reconstruction_residual,agreement_relative,"
         "double_mant_dig,long_double_mant_dig,Jx,Jy,Jz,Q1,Q2,Mach,rho_min,rho_max,finite,"
         "film_nodes,recess_nodes,film_delta,recess_delta,rho_min_id,rho_max_id,nominal_volume_m3\n";
  }
  void begin(int nextStep) {
    if (nextStep != rows || nextStep > lastStep) throw std::runtime_error("Non-contiguous diagnostic step");
    step=nextStep; materials={}; coreCount=0; hash=14695981039346656037ULL;
    haveId=false; finite=true; densityRecorded=false; rhoBuffer.clear();
    filmNodes=0; recessNodes=0; filmDelta=0; recessDelta=0;
    massComp={}; rhoComp={}; deltaComp={}; massLong=0; rhoLong=0; deltaLong=0;
  }
  void shape(int cuboid, int sx, int sy, int sz) const {
    if (cuboid != 0 || sx != 192 || sy != 192 || sz != 145)
      throw std::runtime_error("Unexpected diagnostic core decomposition");
  }
  void material(int cuboid, int x, int y, int z, int value) {
    if (cuboid != 0 || x<0 || x>=192 || y<0 || y>=192 || z<0 || z>=145 || value<0 || value>3)
      throw std::runtime_error("Invalid core material coordinate");
    if (haveId && lastFluid && !densityRecorded)
      throw std::runtime_error("Missing fluid density observation");
    const std::uint64_t id = (static_cast<std::uint64_t>(x)*192+y)*145+z;
    if (haveId && id <= lastId) throw std::runtime_error("Duplicate/out-of-order core ID");
    lastId=id; haveId=true; lastFluid=(value==1); densityRecorded=false; ++coreCount; ++materials[value];
    hashWord(hash,id); hashWord(hash,static_cast<std::uint64_t>(value));
  }
  void density(double rho, double rhoPhysical, double spacing) {
    if (!haveId || !lastFluid || densityRecorded)
      throw std::runtime_error("Invalid or duplicate fluid density observation");
    if (rhoPhysical!=1000.0 || spacing!=1.25e-9)
      throw std::runtime_error("Unexpected diagnostic physical units");
    densityRecorded=true;
    const auto index = rhoBuffer.size();
    if (index==0 || rho<rhoMin) { rhoMin=rho; rhoMinId=lastId; }
    if (index==0 || rho>rhoMax) { rhoMax=rho; rhoMaxId=lastId; }
    if (step == 0) mask.push_back(lastId);
    else if (index >= mask.size() || mask[index] != lastId) throw std::runtime_error("Fluid mask changed");
    rhoBuffer.push_back(rho);
    const double term = rho * rhoPhysical * spacing * spacing * spacing;
    massComp.add(term); rhoComp.add(rho); deltaComp.add(rho-1.0);
    const long double r=rho, rp=rhoPhysical, d=spacing;
    massLong += r*rp*d*d*d; rhoLong += r; deltaLong += r-1.0L;
    // z_phys=(z_index-0.5)*dx. material1 z=1..60 is film; above is recess.
    if (lastId%145<=60) { ++filmNodes; filmDelta+=r-1.0L; }
    else { ++recessNodes; recessDelta+=r-1.0L; }
    finite = finite && std::isfinite(rho);
  }
  template<class M>
  void record(const M& original, double originalM0, double legacyError, double legacyPeak,
              double dt, double rhoPhysical, double spacing, double mach) {
    if (coreCount != expectedCore || materials[1] != expectedNodes || rhoBuffer.size() != expectedNodes
        || original.fluidNodes != static_cast<long long>(expectedNodes))
      throw std::runtime_error("Incomplete diagnostic domain");
    if (!finite) throw std::runtime_error("Non-finite density snapshot");
    if (filmNodes!=2211840 || recessNodes!=1474560)
      throw std::runtime_error("Incomplete film/recess partition");
    const long double mc=massComp.value(), ml=massLong, dl=deltaLong, old=original.mass;
    if (step == 0) {
      initialHash=hash; initialMaterials=materials; legacy0=originalM0;
      m0Comp=mc; m0Long=ml; delta0=dl; bias0=old-mc;
      if (!(m0Comp>0 && m0Long>0) || old != legacy0) throw std::runtime_error("Invalid diagnostic M0");
      writeMask();
    }
    if (hash != initialHash || materials != initialMaterials) throw std::runtime_error("Material fingerprint changed");
    const long double ec=(mc-m0Comp)/m0Comp, el=(ml-m0Long)/m0Long;
    const long double ed=(dl-delta0)/(static_cast<long double>(expectedNodes)+delta0);
    const long double bias=old-mc, reconstruction=((mc-m0Comp)+bias-bias0)/legacy0;
    const long double residual=reconstruction-static_cast<long double>(legacyError);
    const long double agreement=std::max({std::abs(ec-el),std::abs(ec-ed),std::abs(el-ed)});
    maxReconstruction=std::max(maxReconstruction,std::abs(residual));
    maxComp=std::max(maxComp,std::abs(ec)); maxLong=std::max(maxLong,std::abs(el));
    maxStable=std::max(maxStable,std::abs(ed)); maxAgreement=std::max(maxAgreement,agreement);
    if (std::abs(legacyError)>peakLegacy) {
      peakLegacy=std::abs(legacyError); peakStep=step; peakRho=rhoBuffer;
    }
    for (int required : snapshotSteps) if (required == step) writeSnapshot(step,rhoBuffer);
    const long double d=spacing, nominal=static_cast<long double>(expectedNodes)*rhoPhysical*d*d*d;
    csv << step << ',' << step*dt << ',' << coreCount;
    for (auto n:materials) csv << ',' << n;
    csv << ',' << hash << ',' << legacy0 << ',' << old << ',' << legacyError << ',' << legacyPeak
        << ',' << original.volume << ',' << original.densityIntegral << ',' << nominal
        << ',' << mc << ',' << ml << ',' << rhoComp.value() << ',' << rhoLong
        << ',' << deltaComp.value() << ',' << dl << ',' << m0Comp << ',' << m0Long << ',' << delta0
        << ',' << ec << ',' << el << ',' << ed << ',' << maxComp << ',' << maxLong << ',' << maxStable
        << ',' << bias << ',' << bias0 << ',' << residual << ',' << agreement
        << ',' << DBL_MANT_DIG << ',' << LDBL_MANT_DIG
        << ',' << original.fluxJ[0] << ',' << original.fluxJ[1] << ',' << original.fluxJ[2]
        << ',' << original.sectionQ1 << ',' << original.sectionQ2 << ',' << mach
        << ',' << original.rhoMin << ',' << original.rhoMax << ',' << original.finite
        << ',' << filmNodes << ',' << recessNodes << ',' << filmDelta << ',' << recessDelta
        << ',' << rhoMinId << ',' << rhoMaxId << ',' << nominal/rhoPhysical << '\n';
    csv.flush();
    ++rows;
  }
  void finish(const std::filesystem::path& output, int finalStep, bool legacyPass, double legacyPeak) {
    csv.close();
    if (peakStep >= 0) writeSnapshot(peakStep,peakRho,true);
    auto out=newFile(output/"diagnostic_status.txt");
    out << std::setprecision(std::numeric_limits<long double>::max_digits10) << std::boolalpha
        << "diagnostic_only=true\nformal_reference_accepted=false\n"
        << "diagnostic_coverage_complete=" << (rows==lastStep+1 && finalStep==lastStep) << '\n'
        << "diagnostic_rows=" << rows << "\ndiagnostic_last_step=" << finalStep
        << "\nlegacy_result_PASS=" << legacyPass << "\nlegacy_mass_gate_PASS=" << (legacyPeak<1e-10)
        << "\nlegacy_max_mass_abs_relative=" << legacyPeak << "\nlegacy_peak_step=" << peakStep
        << "\nmax_e_delta=" << maxStable << "\nmax_ledger_agreement=" << maxAgreement
        << "\nmax_reconstruction_residual=" << maxReconstruction
        << "\nreconstruction_target_met=" << (maxReconstruction<=1e-13L)
        << "\nlong_double_mant_dig=" << LDBL_MANT_DIG
        << "\nhigh_precision_supported=" << (LDBL_MANT_DIG>DBL_MANT_DIG)
        << "\nledger_agreement_target_met=" << (maxAgreement<=1e-13L) << '\n';
    out.close();
  }
};
} // namespace fine_t_mass
