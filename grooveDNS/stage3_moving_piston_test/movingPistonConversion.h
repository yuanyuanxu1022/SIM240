#pragma once
#include "movingPistonIndicator.h"
#include <vector>
#include <cmath>

enum class Phase { Gas, Interface, Fluid, Solid };
struct Cell { Phase phase; double epsilon; double mass; };

inline std::vector<Cell> makePreset(int n=41) {
  std::vector<Cell> c(n);
  for (int z=0; z<n; ++z) {
    c[z] = (z<39) ? Cell{Phase::Fluid,1.0,1.0} :
           (z==39 ? Cell{Phase::Interface,0.5,0.5} : Cell{Phase::Gas,0.0,0.0});
  }
  return c;
}

struct ConversionAudit { int covered=0, attempted=0, rejected=0; double massBefore=0,massAfter=0,volBefore=0,volAfter=0; };

inline bool conservativeConvert(std::vector<Cell>& c, int source, const std::vector<int>& receivers,
                                double dx=5e-9) {
  const double m=c[source].mass, v=c[source].epsilon;
  double cap=0; for(int j:receivers) cap += std::max(0.0,1.0-c[j].epsilon);
  if (cap+1e-14 < v) return false;
  std::vector<double> add(receivers.size()); double rem=v;
  for(std::size_t n=0;n<receivers.size();++n) {
    int j=receivers[n]; double cj=std::max(0.0,1.0-c[j].epsilon);
    add[n]=std::min(cj, rem); rem-=add[n];
  }
  if(rem>1e-12) return false;
  for(std::size_t n=0;n<receivers.size();++n) { c[receivers[n]].epsilon+=add[n]; c[receivers[n]].mass+=m*(add[n]/v); }
  c[source]={Phase::Solid,0.0,0.0};
  for(auto& x:c) if(x.epsilon < -1e-12 || x.epsilon > 1+1e-12) return false;
  (void)dx; return true;
}

inline ConversionAudit auditConversion(const std::vector<Cell>& c, double zP, double dx=5e-9) {
  ConversionAudit a;
  for (const auto& x:c) { a.massBefore+=x.mass; a.volBefore+=x.epsilon*dx*dx*dx; }
  for (int iz=0; iz<(int)c.size(); ++iz) if (iz*dx >= zP-1e-15) {
    ++a.covered;
    if (c[iz].phase==Phase::Fluid || c[iz].phase==Phase::Interface) { ++a.attempted; ++a.rejected; }
  }
  a.massAfter=a.massBefore; a.volAfter=a.volBefore; // no unsafe conversion performed
  return a;
}
