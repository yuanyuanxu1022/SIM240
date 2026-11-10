// SOFTWARE FIXTURE ONLY. No OpenLB, lattice, force, or collideAndStream.
#include "mrp_observer.h"
#include "mass_stats.h"
#include <string>
extern "C" double mrp_legacy_step(double rho,double density,double dx,double mass) {
  return mrp::legacyMass(rho,density,dx,mass);
}
struct SyntheticMeasurement {
  long long fluidNodes=57600;
  double mass=0,correctedMass=0,densityDelta=0,volume=0;
};
extern "C" int mrp_capture_fixture(const char* path,int wrongOrder) {
  try {
    const double dx=5.*1e-9;
    mrp::DensityCapture capture(path,"SYNTHETIC_MRP_NO_FLOW",1,1000.,dx);
    const auto emit=[&](const std::string& phase,int step) {
      capture.begin(phase,step,step*((1.-.5)*dx*dx/(3.*1e-6)));
      SyntheticMeasurement state;
      fine_t_stat::NeumaierSum corrected,delta;
      for (int x=0;x<48;++x) for (int y=0;y<48;++y)
        for (int z=1;z<16+(x>=12 && x<36?20:0);++z) {
          capture.append(0,x,y,z+(wrongOrder && step==14?1:0),1.);
          state.mass=mrp::legacyMass(1.,1000.,dx,state.mass);
          corrected.add(1.*1000.*dx*dx*dx);
          delta.add(0.);state.volume+=dx*dx*dx;
        }
      state.correctedMass=corrected.value();state.densityDelta=delta.value();
      capture.finish(state);
    };
    emit("initial_reference",0);
    for (int step:mrp::captureSteps(1)) emit("diagnostic",step);
    capture.actualFinal(4342);
    return 0;
  } catch (...) {return 2;}
}
