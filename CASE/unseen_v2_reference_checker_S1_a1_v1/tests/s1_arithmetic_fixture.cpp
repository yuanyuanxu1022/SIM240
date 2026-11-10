// SOFTWARE ONLY: no OpenLB, lattice or flow advancement.
#include "mrp_observer.h"
extern "C" double s1_mass_step(double rho, double density, double dx, double mass) {
  return mrp::legacyMass(rho,density,dx,mass);
}
extern "C" void s1_volume_prefixes(double dx, double* output, int count) {
  double volume = 0;
  for (int i=0; i<count; ++i) {
    const volatile double roundedCellVolume = dx * dx * dx;
    volume += roundedCellVolume;
    output[i] = volume;
  }
}
