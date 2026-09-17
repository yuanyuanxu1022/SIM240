#pragma once
#include <cmath>
#include <algorithm>
#include <vector>

struct PistonState { double t, xi, z, disp, velocity; };

inline PistonState pistonState(double t, double duration=1.0,
                               double zInitial=200e-9, double finalDisp=-10e-9)
{
  double xi = duration>0 ? std::clamp(t/duration,0.0,1.0) : 1.0;
  double s = 10*std::pow(xi,3)-15*std::pow(xi,4)+6*std::pow(xi,5);
  double ds = (duration>0) ? (30*xi*xi*std::pow(1-xi,2)/duration) : 0.0;
  return {t,xi,zInitial+finalDisp*s,finalDisp*s,finalDisp*ds};
}

inline std::vector<int> coveredPistonZ(double zP, double dx=5e-9,
                                       double zMin=0, double zMax=200e-9)
{
  std::vector<int> cells;
  int n=static_cast<int>(std::llround((zMax-zMin)/dx));
  for(int iz=0; iz<=n; ++iz) if (zMin+iz*dx >= zP-1e-15) cells.push_back(iz);
  return cells;
}
