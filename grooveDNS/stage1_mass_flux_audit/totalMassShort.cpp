#include <olb.h>
#include "auditCase.h"
#include <fstream>
#include <iomanip>
#include <cmath>
using namespace olb;

int main(int argc,char** argv){
  initialize(&argc,&argv);
  MyCase::ParametersD p; setDefaultParameters(p);
  p.set<parameters::BODY_FORCE_ACCEL>(0.0);
  Mesh mesh=createMesh(p); MyCase c(p,mesh); prepareGeometry(c); prepareLattice(c); setInitialValues(c);
  auto& g=c.getGeometry(); auto& l=c.getLattice(NavierStokes{}); auto& conv=l.getUnitConverter();
  const double dx=conv.getPhysDeltaX(), dV=dx*dx*dx, rho0=conv.getPhysDensity();
  std::ofstream out("total_mass_short.csv"); out<<"step,physical_time_s,total_mass_kg,total_mass_relative_drift,liquid_mass_kg,liquid_mass_relative_drift,max_density_deviation,fluid_volume_m3\n";
  double M0=0, ML0=0; bool finite=true;
  for(int step=0; step<=10; ++step){
    if(step>0) l.collideAndStream();
    double sumR=0,sumL=0,maxDev=0; std::size_t nFluid=0;
    for(int iC=0;iC<l.getLoadBalancer().size();++iC){ auto& b=l.getBlock(iC); auto& bg=g.getBlockGeometry(iC);
      b.forCoreSpatialLocations([&](auto x,auto y,auto z){ int m=bg.getMaterial(x,y,z); auto cell=b.get({x,y,z}); double r=cell.computeRho(); if(!std::isfinite(r)){finite=false;return;} sumR+=r; if(m==1){sumL+=r; ++nFluid;} maxDev=std::max(maxDev,std::abs(r-1.0)); }); }
    double totalMass=sumR*rho0*dV, liquidMass=sumL*rho0*dV; if(step==0){M0=totalMass;ML0=liquidMass;}
    out<<step<<","<<std::setprecision(16)<<step*conv.getPhysDeltaT()<<","<<totalMass<<","<<std::abs(totalMass-M0)/M0<<","<<liquidMass<<","<<std::abs(liquidMass-ML0)/ML0<<","<<maxDev<<","<<nFluid*dV<<"\n";
    if(!finite){std::cerr<<"non-finite rho at step "<<step<<"\n"; return 2;}
  }
  std::cout<<"wrote total_mass_short.csv; steps=10; finite="<<finite<<"; overlap_excluded=true; qy=not_implemented\n";
  return 0;
}
