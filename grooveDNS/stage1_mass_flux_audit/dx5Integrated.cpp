#include <olb.h>
#include "auditCase.h"
#include <fstream>
#include <iomanip>
#include <cmath>
using namespace olb;

int main(int argc,char** argv){
 initialize(&argc,&argv); MyCase::ParametersD p; setDefaultParameters(p); p.fromCLI(argc,argv); p.set<parameters::BODY_FORCE_ACCEL>(1e8);
 std::string run="dx5_integrated"; for(int i=1;i<argc-1;++i) if(std::string(argv[i])=="--run-id") run=argv[i+1];
 singleton::directories().setOutputDir("./output/"+run+"/"); Mesh mesh=createMesh(p); MyCase c(p,mesh); prepareGeometry(c); prepareLattice(c); setInitialValues(c);
 auto& g=c.getGeometry(); auto& l=c.getLattice(NavierStokes{}); auto& conv=l.getUnitConverter(); double dx=conv.getPhysDeltaX(),dV=dx*dx*dx, rhoP=conv.getPhysDensity(), Ly=p.get<parameters::DOMAIN_LY>();
 std::ofstream audit("./output/"+run+"/mass_flux_diagnostic.csv"); audit<<"step,time_s,fluid_nodes,fluid_volume_m3,fluid_mass_kg,fluid_mass_signed_rel,fluid_mass_abs_rel,max_density_deviation,Qy_sec1_m3_s,Qy_sec2_m3_s,Qy_section_rel_diff,Qy_volume_m3_s,Byy_nm2\n";
 double M0=0; using T=MyCase::value_t; using D=MyCase::descriptor_t_of<NavierStokes>;
 auto measure=[&](std::size_t step,double Qvol,double Byy){double mass=0;std::size_t nf=0;double md=0,q[2]={0,0};std::size_t n[2]={0,0}; double ys[2]={0.25*Ly,0.5*Ly};
  for(int iC=0;iC<l.getLoadBalancer().size();++iC){auto& b=l.getBlock(iC);auto& bg=g.getBlockGeometry(iC);b.forCoreSpatialLocations([&](auto x,auto y,auto z){int m=bg.getMaterial(x,y,z);auto cell=b.get({x,y,z});double r=cell.computeRho();if(m==1){mass+=r*rhoP*dV;++nf;md=std::max(md,std::abs(r-1.));auto pos=bg.getPhysR({x,y,z});for(int k=0;k<2;++k)if(std::abs(pos[1]-ys[k])<0.25*dx){double u[3];cell.computeU(u);q[k]+=u[1]*conv.getConversionFactorVelocity()*dx*dx;++n[k];}}});}
  if(step==0)M0=mass;double rel=std::max(std::abs(q[0]),std::abs(q[1]))>0?std::abs(q[0]-q[1])/std::max(std::abs(q[0]),std::abs(q[1])):0.;double signedRel=(mass-M0)/M0;audit<<step<<","<<std::setprecision(16)<<step*conv.getPhysDeltaT()<<","<<nf<<","<<nf*dV<<","<<mass<<","<<signedRel<<","<<std::abs(signedRel)<<","<<md<<","<<q[0]<<","<<q[1]<<","<<rel<<","<<Qvol<<","<<Byy*1e18<<"\n";};
 l.setProcessingContext(ProcessingContext::Evaluation); using Dsc=MyCase::descriptor_t_of<NavierStokes>; SuperLatticePhysVelocity3D<T,Dsc> vel(l,conv); SuperIntegral3D<T> vi(vel,g,1); SuperMax3D<T> mv(vel,g,1); std::ofstream flow("./output/"+run+"/flowrate.dat"); util::ValueTracer<T> tr(conv.getLatticeTime(p.get<parameters::INTERVAL_CONVERGENCE_CHECK>()),p.get<parameters::CONVERGENCE_PRECISION>(),"Qy");
 for(std::size_t s=0;s<conv.getLatticeTime(p.get<parameters::MAX_PHYS_T>());++s){l.collideAndStream(); double f=getResults(c,s,flow,tr,vel,vi,mv); double byy=(rhoP*p.get<parameters::BODY_FORCE_ACCEL>()>0)?(rhoP*conv.getPhysViscosity()*f/(rhoP*p.get<parameters::BODY_FORCE_ACCEL>()*p.get<parameters::CHANNEL_HEIGHT>()*(((p.get<parameters::NUM_GROOVES>()+1)*p.get<parameters::WALL_WIDTH>()+p.get<parameters::NUM_GROOVES>()*p.get<parameters::GROOVE_WIDTH>())))):0.0; measure(s,f,byy); if(tr.hasConverged()){break;}}
 std::cout<<"integrated diagnostic written to ./output/"<<run<<"/mass_flux_diagnostic.csv\n"; return 0;
}
