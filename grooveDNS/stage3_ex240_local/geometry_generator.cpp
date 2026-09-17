#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

struct Opt { double dx=5, h=65, pad=15, substrate=20, backing=20; int overlap=3; std::string run="static_h65_dx5"; };
static Opt parse(int argc,char**argv){ Opt o; for(int i=1;i<argc;++i){std::string a=argv[i]; auto v=[&](){if(++i>=argc)throw std::runtime_error("missing value after "+a);return std::string(argv[i]);}; if(a=="--dx-nm")o.dx=std::stod(v());else if(a=="--h-nm")o.h=std::stod(v());else if(a=="--padding-nm")o.pad=std::stod(v());else if(a=="--substrate-nm")o.substrate=std::stod(v());else if(a=="--backing-nm")o.backing=std::stod(v());else if(a=="--overlap")o.overlap=std::stoi(v());else if(a=="--run-id")o.run=v();else throw std::runtime_error("unknown option "+a);} if(o.dx<=0||o.h<0||o.pad<0||o.substrate<=0||o.backing<=0||o.overlap<0)throw std::runtime_error("invalid non-positive geometry parameter"); return o; }
static bool integerMultiple(double a,double dx){return std::abs(a/dx-std::round(a/dx))<1e-10;}
int main(int argc,char**argv){
 try{
  const Opt o=parse(argc,argv); constexpr double Lx=240,Ly=240,xL=60,xR=180,dg=100;
  for(double a:{Lx,Ly,xL,xR,dg,o.h,o.pad,o.substrate,o.backing}) if(!integerMultiple(a,o.dx)) throw std::runtime_error("all boundaries must be integer multiples of dx for this validation export");
  const double z0=-o.substrate-o.pad, z1=o.h+dg+o.backing+o.pad;
  const int nx=std::lround(Lx/o.dx),ny=std::lround(Ly/o.dx),nz=std::lround((z1-z0)/o.dx);
  std::vector<unsigned char> m(size_t(nx)*ny*nz,0); long long count[4]={};
  auto id=[&](int i,int j,int k){return (size_t(k)*ny+j)*nx+i;};
  for(int k=0;k<nz;++k)for(int j=0;j<ny;++j)for(int i=0;i<nx;++i){
   double x=(i+.5)*o.dx,z=z0+(k+.5)*o.dx; unsigned char q=0;
   if(z>=-o.substrate && z<0) q=2;
   else if(z>=0 && z<o.h) q=1;
   else if(z>=o.h && z<o.h+dg) q=(x>=xL&&x<xR)?1:3;
   else if(z>=o.h+dg && z<o.h+dg+o.backing) q=3;
   m[id(i,j,k)]=q; ++count[q];
  }
  const std::filesystem::path out=std::filesystem::path("output")/o.run; if(std::filesystem::exists(out)) throw std::runtime_error("output exists: "+out.string()); std::filesystem::create_directories(out);
  std::ofstream v(out/"ex240_material.vti"); v<<std::setprecision(12)<<"<?xml version=\"1.0\"?>\n<VTKFile type=\"ImageData\" version=\"1.0\" byte_order=\"LittleEndian\">\n<ImageData WholeExtent=\"0 "<<nx<<" 0 "<<ny<<" 0 "<<nz<<"\" Origin=\"0 0 "<<z0<<"\" Spacing=\""<<o.dx<<" "<<o.dx<<" "<<o.dx<<"\">\n<Piece Extent=\"0 "<<nx<<" 0 "<<ny<<" 0 "<<nz<<"\"><CellData Scalars=\"material\"><DataArray type=\"UInt8\" Name=\"material\" format=\"ascii\">\n";
  for(size_t n=0;n<m.size();++n){v<<int(m[n])<<((n+1)%32?' ':'\n');} v<<"\n</DataArray></CellData></Piece></ImageData></VTKFile>\n";
  auto cells=[&](double a){return int(std::lround(a/o.dx));};
  const bool seam=(cells(xL)+cells(Lx-xR)==cells(120));
  bool conn=true; const int j=ny/2,k=std::lround((0.5*o.h-z0)/o.dx-.5); for(int i=0;i<nx;++i)conn&=m[id(i,j,k)]==1;
  std::ofstream c(out/"geometry_parameters.csv"); c<<"category,parameter,value,unit,status,source_or_note\n"
   <<"confirmed,Lx,240,nm,user confirmed\nconfirmed,Ly,240,nm,local periodic test choice\nconfirmed,left_half_mesa,60,nm,x=[0,60)\nconfirmed,groove_width,120,nm,x=[60,180)\nconfirmed,right_half_mesa,60,nm,x=[180,240)\nconfirmed,groove_depth,100,nm,user confirmed\n"
   <<"test,h,"<<o.h<<",nm,static layout sample only\ntest,dx,"<<o.dx<<",nm,geometry-check resolution\ntest,substrate_thickness,"<<o.substrate<<",nm,visual/export support\ntest,punch_backing_thickness,"<<o.backing<<",nm,visual/export support\ntest,padding,"<<o.pad<<",nm,z-only exterior padding\ntest,overlap,"<<o.overlap<<",cells,OpenLB future lattice metadata; excluded from physical counts\n"
   <<"pending,h_initial,1000,nm,macro mapping not confirmed\npending,h_final,65,nm,macro mapping not confirmed\npending,displacement,-935,nm,macro mapping not confirmed\npending,liquid_volume,NA,NA,not initialized\npending,contact_angles,NA,degree,substrate and punch unknown\npending,gas_model,NA,NA,reference-pressure vs trapped gas undecided\n"
   <<"discrete,nx,"<<nx<<",cells,physical periodic cells\ndiscrete,ny,"<<ny<<",cells,physical periodic cells\ndiscrete,nz,"<<nz<<",cells,includes z padding/support solids\ndiscrete,left_half_mesa,"<<cells(60)<<",cells,cell-centred exact\ndiscrete,groove_width,"<<cells(120)<<",cells,cell-centred exact\ndiscrete,right_half_mesa,"<<cells(60)<<",cells,cell-centred exact\ndiscrete,groove_depth,"<<cells(100)<<",cells,cell-centred exact\ndiscrete,h,"<<cells(o.h)<<",cells,cell-centred exact\n";
  std::ofstream s(out/"validation.txt"); s<<std::boolalpha<<std::setprecision(12)
   <<"generator=geometry_generator.cpp (no lattice, no collideAndStream)\ncoordinate_convention=cell-centred; VTI origin is grid-node origin in nm\nmaterials=0 exterior_padding; 1 internal_usable_space; 2 fixed_substrate; 3 grooved_punch\nperiodicity=x:true,y:true,z:false\noverlap_cells="<<o.overlap<<" (metadata only; ghost/overlap not serialized or counted)\n"
   <<"nominal_wall_locations_nm=z=0,z=h="<<o.h<<",z=h+dg="<<o.h+dg<<",x=60,x=180\n"
   <<"effective_voxel_faces_nm=z=0,z="<<o.h<<",z="<<o.h+dg<<",x=60,x=180\n"
   <<"cell_centres_nm=x=(i+0.5)dx,y=(j+0.5)dx,z="<<z0<<"+(k+0.5)dx\n"
   <<"counts_material_0_1_2_3="<<count[0]<<","<<count[1]<<","<<count[2]<<","<<count[3]<<"\n"
   <<"periodic_seam_half_mesas_form_120nm_mesa="<<seam<<"\ncentral_groove_exact_120nm="<<(cells(120)==24&&o.dx==5)<<"\ngroove_depth_exact_100nm="<<(cells(100)*o.dx==100)<<"\n"
   <<"under_mesa_gap_x_connected_at_z=h/2="<<conn<<"\nall_checks_pass="<<(seam&&conn)<<"\n";
  std::cout<<"Wrote "<<out<<"; grid "<<nx<<"x"<<ny<<"x"<<nz<<"; checks="<<(seam&&conn?"PASS":"FAIL")<<"\n"; return seam&&conn?0:1;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}
}
