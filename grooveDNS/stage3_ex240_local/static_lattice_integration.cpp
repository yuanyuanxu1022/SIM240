#include <olb.h>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

using namespace olb;
using T=double;
using DESCRIPTOR=descriptors::D3Q19<>;

struct Stats { long long fluid=0,solid=0; double mass=0,maxU=0,minRho=1e300,maxRho=-1e300; bool finite=true; };

template<class LAT,class GEO> Stats sample(LAT& lat,GEO& geo){
 Stats s;
 for(int iC=0;iC<lat.getLoadBalancer().size();++iC){auto& b=lat.getBlock(iC);auto& g=geo.getBlockGeometry(iC);b.forCoreSpatialLocations([&](auto i,auto j,auto k){int m=g.getMaterial(i,j,k);if(m==1){auto c=b.get({i,j,k});T u[3]={};c.computeU(u);T rho=c.computeRho();double q=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);s.finite&=std::isfinite(rho)&&std::isfinite(q);s.mass+=rho;s.maxU=std::max(s.maxU,q);s.minRho=std::min(s.minRho,double(rho));s.maxRho=std::max(s.maxRho,double(rho));++s.fluid;}else if(m==2||m==3)++s.solid;});}
 return s;
}

int main(int argc,char**argv){
 initialize(&argc,&argv); if(singleton::mpi().getSize()!=1){std::cerr<<"single MPI rank required for audit\n";return 2;}
 const std::string run="openlb_static_h65_dx5_10step_final"; const std::filesystem::path out=std::filesystem::path("output")/run;
 if(std::filesystem::exists(out)){std::cerr<<"output exists: "<<out<<"\n";return 2;} std::filesystem::create_directories(out); singleton::directories().setOutputDir((out.string()+"/").c_str());
 constexpr T dx=5e-9,dt=1e-12,nu=1e-6,rho0=1000,Lx=240e-9,Ly=240e-9,h=65e-9,dg=100e-9;
 // Cell-centred physical nodes. One substrate layer at z=-2.5 nm gives halfway BB wall z=0.
 IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,h+dg+20e-9},{dx/2,dx/2,-dx/2});
 CuboidDecomposition<T,3> cuboids(domain,dx,1); cuboids.setPeriodicity({true,true,false});
 HeuristicLoadBalancer<T> load(cuboids); constexpr int overlap=3; SuperGeometry<T,3> geo(cuboids,load,overlap);
 for(int iC=0;iC<load.size();++iC){auto& g=geo.getBlockGeometry(iC);g.forCoreSpatialLocations([&](auto i,auto j,auto k){auto r=g.getPhysR({i,j,k});T x=r[0],z=r[2];int m;if(z<0)m=2;else if(z<h)m=1;else if(z<h+dg)m=(x>=60e-9&&x<180e-9)?1:3;else m=3;g.set({i,j,k},m);});}
 geo.communicate(); geo.checkForErrors(false);
 UnitConverter<T,DESCRIPTOR> conv(dx,dt,240e-9,1.0,nu,rho0); SuperLattice<T,DESCRIPTOR> lat(conv,cuboids,load);
 dynamics::set<BGKdynamics>(lat,geo,1); boundary::set<boundary::BounceBack>(lat,geo,2); boundary::set<boundary::BounceBack>(lat,geo,3);
 AnalyticalConst3D<T,T> one(1),zeroU(0,0,0); lat.defineRhoU(geo.getMaterialIndicator(1),one,zeroU);lat.iniEquilibrium(geo,1,one,zeroU);lat.initialize();
 SuperVTMwriter3D<T> writer("openlb_static_geometry",overlap);SuperGeometryF3D<T> gf(geo);gf.getName()="material";writer.addFunctor(gf);writer.createMasterFile();writer.write(0);
 auto before=sample(lat,geo); long long materialBefore[4]={};for(int iC=0;iC<load.size();++iC){auto&g=geo.getBlockGeometry(iC);g.forCoreSpatialLocations([&](auto i,auto j,auto k){int m=g.getMaterial(i,j,k);if(m>=0&&m<4)++materialBefore[m];});}
 std::ofstream csv(out/"lattice_statistics.csv");csv<<"step,time_s,fluid_nodes,solid_nodes,mass_lattice,relative_mass_drift,max_speed_m_per_s,min_rho_lattice,max_rho_lattice,finite,material_unchanged\n"<<std::setprecision(16);
 Stats final=before;for(int step=0;step<=10;++step){if(step)lat.collideAndStream();auto s=sample(lat,geo);final=s;long long now[4]={};for(int iC=0;iC<load.size();++iC){auto&g=geo.getBlockGeometry(iC);g.forCoreSpatialLocations([&](auto i,auto j,auto k){int m=g.getMaterial(i,j,k);if(m>=0&&m<4)++now[m];});}bool same=std::equal(std::begin(now),std::end(now),std::begin(materialBefore));csv<<step<<","<<step*dt<<","<<s.fluid<<","<<s.solid<<","<<s.mass<<","<<(s.mass-before.mass)/before.mass<<","<<conv.getPhysVelocity(s.maxU)<<","<<s.minRho<<","<<s.maxRho<<","<<s.finite<<","<<same<<"\n";}
 // Actual coordinate census and topological tests.
 std::array<long long,4> n{};T fmin[3]={1e9,1e9,1e9},fmax[3]={-1e9,-1e9,-1e9};bool connected=true;int nx=0,ny=0,nz=0,leftHalf=0,groove=0,rightHalf=0;
 auto& g=geo.getBlockGeometry(0);auto e=g.getExtent();nx=e[0];ny=e[1];nz=e[2];
 g.forCoreSpatialLocations([&](auto i,auto j,auto k){int m=g.getMaterial(i,j,k);if(m>=0&&m<4)++n[m];auto r=g.getPhysR({i,j,k});if(m==1)for(int d=0;d<3;++d){fmin[d]=std::min(fmin[d],r[d]);fmax[d]=std::max(fmax[d],r[d]);}if(std::abs(r[2]-32.5e-9)<1e-12)connected&=(m==1);if(std::abs(r[1]-2.5e-9)<1e-12&&std::abs(r[2]-102.5e-9)<1e-12){if(r[0]<60e-9&&m==3)++leftHalf;else if(r[0]<180e-9&&m==1)++groove;else if(m==3)++rightHalf;}});
 bool seam=(leftHalf==12&&groove==24&&rightHalf==12);
 std::ofstream val(out/"openlb_geometry_validation.txt");val<<std::boolalpha<<std::setprecision(16)
  <<"uses_real_SuperGeometry=true\nuses_real_SuperLattice=true\ndescriptor=D3Q19\nperiodicity=x:true,y:true,z:false\noverlap_cells="<<overlap<<"\npadding=OpenLB block padding/overlap only; excluded by forCoreSpatialLocations\n"
  <<"core_dimensions="<<nx<<","<<ny<<","<<nz<<"\nmaterial_counts_0_1_2_3="<<n[0]<<","<<n[1]<<","<<n[2]<<","<<n[3]<<"\nfluid_center_min_m="<<fmin[0]<<","<<fmin[1]<<","<<fmin[2]<<"\nfluid_center_max_m="<<fmax[0]<<","<<fmax[1]<<","<<fmax[2]<<"\n"
  <<"effective_halfway_bounceback_walls_nm=z:0,65,165;x:60,180\nunder_mesa_x_connected_at_z_32.5nm="<<connected<<"\nseam_plane_counts_left_solid_central_fluid_right_solid="<<leftHalf<<","<<groove<<","<<rightHalf<<"\nperiodic_half_mesas_form_120nm_full_mesa="<<seam<<"\n";
 std::ofstream cmd(out/"run_record.txt");cmd<<"run_id="<<run<<"\ncommand=./static_lattice_integration\nsteps=10\nexit_reason=completed_fixed_10_steps\nexit_code=0\nno_force=true\ninitial_rho_lattice=1\ninitial_velocity=0 0 0\nh_nm=65 (test only)\ndx_nm=5 (test only)\n";
 std::ofstream log(out/"integration.log");log<<std::boolalpha<<std::setprecision(16)<<"OpenLB version="<<OLB_VERSION<<"\nMPI ranks=1\nrun_id="<<run<<"\nSuperGeometry=true\nSuperLattice=true\nperiodicity=true,true,false\nsteps_completed=10\nfluid_nodes="<<final.fluid<<"\nsolid_nodes="<<final.solid<<"\nfinal_mass_lattice="<<final.mass<<"\nrelative_mass_drift="<<(final.mass-before.mass)/before.mass<<"\nmax_speed_m_per_s="<<conv.getPhysVelocity(final.maxU)<<"\nrho_range_lattice="<<final.minRho<<","<<final.maxRho<<"\nfinite="<<final.finite<<"\nexit_reason=completed_fixed_10_steps\nexit_code=0\n";
 std::cout<<"completed "<<run<<" fluid="<<before.fluid<<" solid="<<before.solid<<"\n";return 0;
}
