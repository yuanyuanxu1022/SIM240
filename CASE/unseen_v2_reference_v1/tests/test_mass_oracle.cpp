#include "mass_stats.h"
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>

int main() {
  using fine_t_stat::NeumaierSum;
  NeumaierSum sum;
  sum.add(1e16); sum.add(1); sum.add(-1e16);
  if (sum.value()!=1) return 1;
  // Integer-exact density perturbations: the long-double reference is independent
  // of the compensated algorithm. A uniform offset is not a conservation test.
  constexpr int N=100000;
  constexpr double eps=0x1p-40;
  constexpr double volumeMass=0x1p-80;
  NeumaierSum initial, mass, delta;
  double legacy=0;
  long double oracleMass=0, oracleDelta=0;
  for (int i=0;i<N;++i) {
    double rho=1+(i%3==0 ? eps : -eps);
    initial.add(volumeMass);
    mass.add(rho*volumeMass);
    delta.add(rho-1);
    legacy+=rho*volumeMass;
    oracleMass+=static_cast<long double>(rho)*volumeMass;
    oracleDelta+=static_cast<long double>(rho)-1;
  }
  if (mass.value()!=static_cast<double>(oracleMass)) return 2;
  if (delta.value()!=static_cast<double>(oracleDelta)) return 3;
  double e=(mass.value()-initial.value())/initial.value();
  double ed=delta.value()/N;
  if (std::abs(e-ed)>2*std::numeric_limits<double>::epsilon()) return 4;
  if (legacy==mass.value()) return 5; // This fixture must expose sequential loss.
  std::cout<<std::setprecision(17)<<"long_double_oracle_PASS=true\n"
           <<"corrected_error="<<e<<"\ndelta_error="<<ed
           <<"\nlegacy_minus_corrected="<<legacy-mass.value()<<"\n";
}
