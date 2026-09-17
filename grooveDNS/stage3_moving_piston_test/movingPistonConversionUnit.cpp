#include "movingPistonConversion.h"
#include <fstream>
#include <iostream>
#include <cmath>
#include <numeric>
int main() {
  auto cells=makePreset();
  // Synthetic successful conversion: source interface transfers to two
  // partially empty interface receivers.
  cells[37]={Phase::Interface,0.5,0.5}; cells[38]={Phase::Interface,0.25,0.25};
  double m0=0,v0=0; for(auto& x:cells){m0+=x.mass;v0+=x.epsilon;}
  bool ok=conservativeConvert(cells,37,{38});
  double m1=0,v1=0; for(auto& x:cells){m1+=x.mass;v1+=x.epsilon;}
  if(!ok || std::abs(m1-m0)>1e-12 || std::abs(v1-v0)>1e-12) return 1;
  std::ofstream out("movingPistonConversion_unit.csv");
  out<<"t,z_p_m,covered,attempted,rejected,mass_before,mass_after,volume_before,volume_after,mass_delta,volume_delta,status\n";
  for(int i=0;i<=10;++i) {
    auto p=pistonState(0.1*i); auto a=auditConversion(cells,p.z);
    out<<p.t<<","<<p.z<<","<<a.covered<<","<<a.attempted<<","<<a.rejected<<","<<a.massBefore<<","<<a.massAfter<<","<<a.volBefore<<","<<a.volAfter<<","<<a.massAfter-a.massBefore<<","<<a.volAfter-a.volBefore<<",conservative_audit\n";
  }
  // Insufficient-capacity case must reject atomically.
  auto failCase=makePreset(); double mf=0,vf=0; for(auto& x:failCase){mf+=x.mass;vf+=x.epsilon;}
  if(conservativeConvert(failCase,39,{36}) || std::abs(mf-std::accumulate(failCase.begin(),failCase.end(),0.0,[](double s,const Cell& x){return s+x.mass;}))>1e-12) return 1;
  std::cout<<"M3 conservative redistribution unit test passed\n";
  return 0;
}
