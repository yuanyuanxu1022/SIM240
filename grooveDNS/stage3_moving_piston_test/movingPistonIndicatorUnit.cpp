#include "movingPistonIndicator.h"
#include <algorithm>
#include <fstream>
#include <iostream>

int main() {
  const double dt=0.1, z0=200e-9, disp=-10e-9;
  std::ofstream out("movingPistonIndicator_unit.csv");
  out<<"t,xi,z_p_m,displacement_m,wall_velocity_m_per_s,covered_z_indices\n";
  double previous=z0; bool monotone=true;
  for(int i=0;i<=10;++i) {
    auto s=pistonState(i*dt,1.0,z0,disp);
    monotone = monotone && s.z<=previous+1e-20; previous=s.z;
    out<<s.t<<","<<s.xi<<","<<s.z<<","<<s.disp<<","<<s.velocity<<",\"";
    auto cells=coveredPistonZ(s.z);
    for(std::size_t j=0;j<cells.size();++j) { if(j) out<<" "; out<<cells[j]; }
    out<<"\"\n";
  }
  if(!monotone || std::abs(pistonState(0,1,z0,disp).disp)>1e-18 ||
     std::abs(pistonState(1,1,z0,disp).disp-disp)>1e-18) return 1;
  std::cout<<"movingPistonIndicator unit test compiled; checks encoded\n";
  return 0;
}
