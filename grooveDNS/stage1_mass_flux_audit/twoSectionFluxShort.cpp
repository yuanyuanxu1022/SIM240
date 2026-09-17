#include <olb.h>
#include "auditCase.h"
#include <fstream>
#include <iomanip>
#include <cmath>
using namespace olb;
int main(int argc,char**argv){
 initialize(&argc,&argv); MyCase::ParametersD p; setDefaultParameters(p); p.set<parameters::BODY_FORCE_ACCEL>(1e8);
 Mesh mesh=createMesh(p); MyCase c(p,mesh); prepareGeometry(c); prepareLattice(c); setInitialValues(c);
 auto& g=c.getGeometry(); auto& l=c.getLattice(NavierStokes{}); auto& conv=l.getUnitConverter();
 const double dx=conv.getPhysDeltaX(), area=dx*dx, Ly=p.get<parameters::DOMAIN_LY>();
 const double y1=0.25*Ly, y2=0.50*Ly; std::ofstream out("two_section_flux_short.csv");
 out<<"step,time_s,Qy_section1_m3_s,Qy_section2_m3_s,section_flux_relative_difference,uy_app_section1_m_s,uy_app_section2_m_s,n1,n2,y1_m,y2_m,area_per_node_m2\n";
 for(int step=0;step<=10;++step){ if(step>0) l.collideAndStream(); double q[2]={0,0}; std::size_t n[2]={0,0};
  for(int iC=0;iC<l.getLoadBalancer().size();++iC){auto& b=l.getBlock(iC); auto& bg=g.getBlockGeometry(iC); b.forCoreSpatialLocations([&](auto x,auto y,auto z){int m=bg.getMaterial(x,y,z); if(m!=1)return; auto pos=bg.getPhysR({x,y,z}); int k=-1; if(std::abs(pos[1]-y1)<0.25*dx)k=0; else if(std::abs(pos[1]-y2)<0.25*dx)k=1; if(k<0)return; double u[3]; b.get({x,y,z}).computeU(u); double uy=u[1]*conv.getConversionFactorVelocity(); if(std::isfinite(uy)){q[k]+=uy*area; ++n[k];}});}
  double rel=std::max(std::abs(q[0]),std::abs(q[1]))>0?std::abs(q[0]-q[1])/std::max(std::abs(q[0]),std::abs(q[1])):0.; double a1=n[0]*area,a2=n[1]*area;
  out<<step<<","<<std::setprecision(16)<<step*conv.getPhysDeltaT()<<","<<q[0]<<","<<q[1]<<","<<rel<<","<<(a1?q[0]/a1:0)<<","<<(a2?q[1]/a2:0)<<","<<n[0]<<","<<n[1]<<","<<y1<<","<<y2<<","<<area<<"\n";
 }
 std::cout<<"wrote two_section_flux_short.csv; overlap_excluded=true; periodic_endpoint_excluded=true; steps=10\n"; return 0;
}
