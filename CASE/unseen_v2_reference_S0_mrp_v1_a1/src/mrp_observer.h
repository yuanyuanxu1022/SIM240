#pragma once
// URV-MRP-v1: scalar observer arithmetic and lossless same-call rho capture.
// No OpenLB types, lattice reads, collision, or time stepping in this file.
#include <algorithm>
#include <array>
#include <bit>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <xmmintrin.h>
#include "capture_schedule.h"

namespace mrp {

__attribute__((noinline, noipa, optimize("fp-contract=off")))
double legacyMass(double rho, double rhoPhys, double dx, double mass)
{
  // Volatile binary64 stores are deliberate rounding barriers, local to this
  // observer. Explicit fma is still fused with fp-contract=off.
  volatile double p1 = rho * rhoPhys;
  volatile double p2 = p1 * dx;
  volatile double p3 = p2 * dx;
  return std::fma(p3, dx, mass);
}

inline void require(bool ok, const char* message) {
  if (!ok) throw std::runtime_error(message);
}
inline std::string bits(double value) {
  std::ostringstream out;
  out << std::hex << std::setfill('0') << std::setw(16)
      << std::bit_cast<std::uint64_t>(value);
  return out.str();
}

class DensityCapture {
  static constexpr std::size_t count = 57600;
  std::filesystem::path directory;
  std::string runId, direction, phase;
  double rhoPhys, dx, time = 0;
  int step = 0, rounding;
  unsigned fpControl;
  std::set<int> planned, saved;
  std::vector<double> latest;
  std::vector<std::array<int,4>> coordinates;
  std::size_t ordinal = 0;
  bool mapComplete = false, initialSaved = false;
  std::string values, environment, executable;
  std::vector<std::string> records;

  void fpCheck() const {
    require(std::fegetround() == rounding &&
            (_mm_getcsr() & 0xffc0u) == fpControl,
            "MRP floating-point control changed");
  }
  void checkedWrite(const std::filesystem::path& path, const std::string& text) {
    require(!std::filesystem::exists(path), "MRP refuses output overwrite");
    std::ofstream out(path, std::ios::binary);
    out.exceptions(std::ios::failbit | std::ios::badbit);
    out.write(text.data(), static_cast<std::streamsize>(text.size()));
    out.close();
  }
  void writeRawIndex() {
    const auto target = directory/"rho_capture_raw.json";
    const auto temporary = directory/"rho_capture_raw.pending";
    std::ostringstream out;
    out << "{\"protocol_id\":\"URV-MRP-v1\",\"run_id\":\"" << runId
        << "\",\"direction\":\"" << direction
        << "\",\"native_executable\":\"" << executable
        << "\",\"map_file\":\"core_index_map.csv\",\"records\":[";
    for (std::size_t i=0; i<records.size(); ++i) {
      if (i) out << ',';
      out << records[i];
    }
    out << "]}\n";
    checkedWrite(temporary,out.str());
    std::filesystem::rename(temporary,target);
  }
  void saveLatest() {
    fpCheck();
    const std::string file = phase+"_"+std::to_string(step)+".rho64";
    require(!std::filesystem::exists(directory/file), "MRP duplicate rho capture");
    std::ofstream out(directory/file,std::ios::binary);
    out.exceptions(std::ios::failbit | std::ios::badbit);
    out.write(reinterpret_cast<const char*>(latest.data()),count*sizeof(double));
    out.close();
    std::ostringstream row;
    row << std::setprecision(17) << "{\"phase\":\"" << phase
        << "\",\"step\":" << step << ",\"time_s\":" << time
        << ",\"time_hex64\":\"" << bits(time)
        << "\",\"nodes\":" << count << ",\"file\":\"" << file
        << "\",\"dtype\":\"<f8\",\"rho_phys_hex64\":\"" << bits(rhoPhys)
        << "\",\"dx_hex64\":\"" << bits(dx) << "\"," << values
        << ',' << environment << '}';
    records.push_back(row.str());
    writeRawIndex();
  }

public:
  DensityCapture(const std::filesystem::path& output, const std::string& id,
                 int drive, double density, double spacing)
    : directory(output/"mass_capture"),runId(id),
      direction(drive==1?"P":"T"),rhoPhys(density),dx(spacing),
      rounding(std::fegetround()),fpControl(_mm_getcsr() & 0xffc0u),
      planned(captureSteps(drive)),latest(count)
  {
    require(std::endian::native==std::endian::little && sizeof(double)==8 &&
            std::numeric_limits<double>::is_iec559, "MRP requires LE binary64");
    require(rounding==FE_TONEAREST, "MRP requires nearest-even rounding");
    require(std::filesystem::create_directory(directory), "MRP output exists");
    coordinates.reserve(count);
    executable=std::filesystem::read_symlink("/proc/self/exe").string();
    // JSON-safe by construction of normal project paths; reject unusual paths.
    require(executable.find_first_of("\"\\\n\r") == std::string::npos,
            "MRP executable path not JSON safe");
    std::ostringstream env;
    env << "\"fe_round\":" << rounding << ",\"mxcsr_control\":" << fpControl
        << ",\"double_bytes\":8,\"iec559\":true,\"cpu_fma\":"
        << (__builtin_cpu_supports("fma")?"true":"false");
    environment=env.str();
  }

  void begin(const std::string& callPhase, int callStep, double callTime) {
    fpCheck();
    require(callPhase=="initial_reference" || callPhase=="diagnostic", "MRP phase");
    phase=callPhase;step=callStep;time=callTime;ordinal=0;
  }

  __attribute__((noinline,noipa))
  void append(int cuboid,int x,int y,int z,double rho) {
    require(ordinal<count && std::isfinite(rho) && rho>0, "MRP invalid rho/count");
    const std::array<int,4> coordinate{cuboid,x,y,z};
    if (!mapComplete) coordinates.push_back(coordinate);
    else require(coordinates[ordinal]==coordinate, "MRP core order changed");
    latest[ordinal++]=rho; // exact copy of the rho consumed by this measure
  }

  template<class Measurement>
  void finish(const Measurement& state) {
    fpCheck();
    require(ordinal==count && state.fluidNodes==static_cast<long long>(count),
            "MRP incomplete core capture");
    if (!mapComplete) {
      require(std::set<std::array<int,4>>(coordinates.begin(),coordinates.end()).size()==count,
              "MRP duplicate core coordinate");
      std::ostringstream map;
      map << "ordinal,cuboid,iX,iY,iZ,material\n";
      for (std::size_t i=0;i<count;++i) {
        map << i;
        for (int coordinate:coordinates[i]) map << ',' << coordinate;
        map << ",1\n";
      }
      checkedWrite(directory/"core_index_map.csv",map.str());
      mapComplete=true;
    }
    values="\"native_mass_hex64\":\""+bits(state.mass)+
      "\",\"native_corrected_mass_hex64\":\""+bits(state.correctedMass)+
      "\",\"native_density_delta_hex64\":\""+bits(state.densityDelta)+
      "\",\"native_volume_hex64\":\""+bits(state.volume)+"\"";
    if (phase=="initial_reference") {
      require(step==0 && !initialSaved, "MRP duplicate initial reference");
      saveLatest();initialSaved=true;
    } else if (planned.count(step)) {
      require(saved.insert(step).second, "MRP duplicate diagnostic step");
      saveLatest();
    }
  }

  void actualFinal(int finalStep) {
    require(phase=="diagnostic" && step==finalStep, "MRP final is not latest measure");
    if (!saved.count(step)) {saveLatest();saved.insert(step);}
    require(initialSaved && std::includes(saved.begin(),saved.end(),planned.begin(),planned.end()),
            "MRP missing planned density captures; no extension or retry permitted");
  }
};
} // namespace mrp
