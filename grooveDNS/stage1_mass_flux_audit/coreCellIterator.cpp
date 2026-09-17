#include <olb.h>
#include "auditCase.h"
#include <iostream>
using namespace olb;
int main(int argc,char**argv){
  initialize(&argc,&argv); MyCase::ParametersD p; setDefaultParameters(p); p.set<parameters::BODY_FORCE_ACCEL>(0.0);
  Mesh mesh=createMesh(p); MyCase c(p,mesh); prepareGeometry(c); prepareLattice(c); setInitialValues(c);
  auto& g=c.getGeometry(); auto& l=c.getLattice(NavierStokes{}); std::size_t core=0,m0=0,m1=0,m2=0,rhoz=0; double sum=0;
  for(int iC=0;iC<l.getLoadBalancer().size();++iC){ auto& b=l.getBlock(iC); auto& bg=g.getBlockGeometry(iC); b.forCoreSpatialLocations([&](auto x,auto y,auto z){++core; int m=bg.getMaterial(x,y,z); if(m==0)++m0;else if(m==1)++m1;else if(m==2)++m2; auto cell=b.get({x,y,z}); double rho=cell.computeRho(); if(rho!=0){++rhoz;sum+=rho;}}); }
  std::cout<<"core_cells="<<core<<" material0="<<m0<<" material1="<<m1<<" material2="<<m2<<" rho_nonzero="<<rhoz<<" sum_rho="<<sum<<" overlap_excluded=true\n";
  return 0;
}
