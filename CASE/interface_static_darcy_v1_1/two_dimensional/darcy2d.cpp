// SDI-v1: cell-centred conservative 2-D finite-volume pressure solver.
// No analytic field is used in assembly, initialisation, or reconstruction.
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs = std::filesystem;
using V = std::vector<double>;
double dot(const V& a,const V& b) { double s=0; for(size_t i=0;i<a.size();++i)s+=a[i]*b[i]; return s; }
double l1(const V& a) { double s=0;for(double x:a)s+=std::abs(x);return s; }
struct Face { int owner, neighbour; std::string patch; double x,y,sx,sy,c,pb,phi=0,phiU=0; };
int main(int argc,char** argv) try {
    std::string input,out; bool audit=false;
    for(int i=1;i<argc;++i) {
        std::string s=argv[i];
        if(s=="--audit-only")audit=true;
        else if((s=="--input"||s=="--output")&&i+1<argc) (s=="--input"?input:out)=argv[++i];
        else throw std::runtime_error("Unknown/missing argument: "+s);
    }
    if(input.empty()||(!audit&&out.empty()))throw std::runtime_error("--input and --output required (or --audit-only)");
    std::ifstream in(input); if(!in)throw std::runtime_error("Cannot read input");
    std::map<std::string,double> d;std::string key;double value;
    while(in>>key>>value) if(!std::isfinite(value)||!d.emplace(key,value).second)throw std::runtime_error("Invalid/duplicate input");
    if(!in.eof())throw std::runtime_error("Malformed input");
    const std::vector<std::string> keys={"nx","ny","Lx","Ly","H","mu","Kxx","Kyy","axis","pressureLow","tolerance","maxIter"};
    if(d.size()!=keys.size())throw std::runtime_error("Unexpected input keys");
    for(const auto& k:keys)if(!d.count(k))throw std::runtime_error("Missing key: "+k);
    for(const auto& k:{"nx","ny","Lx","Ly","H","mu","Kxx","Kyy","tolerance","maxIter"})if(d[k]<=0)throw std::runtime_error("Non-positive input");
    for(const auto& k:{"nx","ny","axis","maxIter"})if(d[k]!=std::floor(d[k]))throw std::runtime_error("Integer input required");
    const int nx=d["nx"],ny=d["ny"],axis=d["axis"],maxIter=d["maxIter"];
    if(nx<2||ny<2||nx>256||ny>256||(axis!=0&&axis!=1)||maxIter>2000||d["tolerance"]>1e-12)throw std::runtime_error("Outside SDI-v1 limits");
    const int n=nx*ny; const double Lx=d["Lx"],Ly=d["Ly"],H=d["H"],mu=d["mu"],dx=Lx/nx,dy=Ly/ny;
    const double kx=d["Kxx"]/mu,ky=d["Kyy"]/mu,pLow=d["pressureLow"];
    if(audit){std::cout<<std::setprecision(17)<<"{\"audit_only\":true,\"flow_solved\":false,\"cells\":"<<n<<",\"volume_m3\":"<<Lx*Ly*H<<"}\n";return 0;}
    if(fs::exists(out))throw std::runtime_error("Output already exists; refusing overwrite");
    fs::create_directories(out);
    std::vector<Face> f;
    auto id=[&](int i,int j){return j*nx+i;};
    for(int j=0;j<ny;++j)for(int i=0;i<=nx;++i){
        bool low=i==0,high=i==nx,bnd=low||high;int o=id(low?0:i-1,j),nb=bnd?-1:id(i,j);
        f.push_back({o,nb,low?"xLow":(high?"xHigh":"internal"),i*dx,(j+.5)*dy,(low?-1:1)*dy*H,0,
                     bnd?(axis==0?2*kx*dy/dx:0):kx*dy/dx,low&&axis==0?pLow:0});
    }
    for(int j=0;j<=ny;++j)for(int i=0;i<nx;++i){
        bool low=j==0,high=j==ny,bnd=low||high;int o=id(i,low?0:j-1),nb=bnd?-1:id(i,j);
        f.push_back({o,nb,low?"yLow":(high?"yHigh":"internal"),(i+.5)*dx,j*dy,0,(low?-1:1)*dx*H,
                     bnd?(axis==1?2*ky*dx/dy:0):ky*dx/dy,low&&axis==1?pLow:0});
    }
    V diag(n,0),rhs(n,0);
    for(const auto& e:f){diag[e.owner]+=e.c;if(e.neighbour>=0)diag[e.neighbour]+=e.c;else rhs[e.owner]+=e.c*e.pb;}
    auto apply=[&](const V& x){V y(n,0);for(const auto& e:f){double a=e.c*(x[e.owner]-(e.neighbour>=0?x[e.neighbour]:0));y[e.owner]+=a;if(e.neighbour>=0)y[e.neighbour]-=a;}return y;};
    V p(n,0),r=rhs,z(n),search(n);double norm=std::max(l1(rhs),1e-300),res=l1(r)/norm;int iter=0;
    for(int k=0;k<n;++k)search[k]=z[k]=r[k]/diag[k];
    double rz=dot(r,z);
    while(res>d["tolerance"]&&iter<maxIter){
        V Ap=apply(search);double den=dot(search,Ap);if(!(den>0)||!std::isfinite(den))throw std::runtime_error("CG lost positive definiteness");
        double alpha=rz/den;for(int k=0;k<n;++k){p[k]+=alpha*search[k];r[k]-=alpha*Ap[k];}
        ++iter;res=l1(r)/norm;if(!std::isfinite(res))throw std::runtime_error("Nonfinite residual");
        if(res<=d["tolerance"])break;
        for(int k=0;k<n;++k)z[k]=r[k]/diag[k];
        double next=dot(r,z),beta=next/rz;
        for(int k=0;k<n;++k)search[k]=z[k]+beta*search[k];
        rz=next;
    }
    V Ap=apply(p);for(int k=0;k<n;++k)r[k]=rhs[k]-Ap[k];double trueRes=l1(r)/norm;
    // True residual is reported separately from recursive CG stopping residual.
    bool converged=res<=d["tolerance"]&&trueRes<=d["tolerance"];
    V jx(n,0),jy(n,0),cellR(n,0);
    for(auto& e:f){e.phi=e.c*(p[e.owner]-(e.neighbour>=0?p[e.neighbour]:e.pb));
        double sign=e.sx+e.sy>0?1:-1;double J=e.phi*sign/(e.sx!=0?dy:dx);
        (e.sx!=0?jx:jy)[e.owner]+=.5*J;
        if(e.neighbour>=0)(e.sx!=0?jx:jy)[e.neighbour]+=.5*J;
        cellR[e.owner]+=e.phi;if(e.neighbour>=0)cellR[e.neighbour]-=e.phi;
    }
    for(auto& e:f){double ux=jx[e.owner]/H,uy=jy[e.owner]/H;
        if(e.neighbour>=0){ux=.5*(ux+jx[e.neighbour]/H);uy=.5*(uy+jy[e.neighbour]/H);}
        if(e.neighbour<0&&e.c==0){if(e.sx!=0)ux=0;else uy=0;}
        e.phiU=ux*e.sx+uy*e.sy;
    }
    std::ofstream cells(fs::path(out)/"cells.csv");cells<<std::setprecision(17);
    cells<<"cell_id,x_m,y_m,z_m,volume_m3,p_Pa,Ux_m_s,Uy_m_s,Uz_m_s,Jx_m2_s,Jy_m2_s,Jz_m2_s\n";
    for(int j=0;j<ny;++j)for(int i=0;i<nx;++i){int k=id(i,j);cells<<k<<','<<(i+.5)*dx<<','<<(j+.5)*dy<<','<<H/2<<','<<dx*dy*H<<','<<p[k]<<','<<jx[k]/H<<','<<jy[k]/H<<",0,"<<jx[k]<<','<<jy[k]<<",0\n";}
    std::ofstream faces(fs::path(out)/"faces.csv");faces<<std::setprecision(17);
    faces<<"face_id,owner,neighbour,patch,x_m,y_m,z_m,Sx_m2,Sy_m2,Sz_m2,phi_m3_s,phi_U_m3_s\n";
    for(size_t k=0;k<f.size();++k){const auto& e=f[k];faces<<k<<','<<e.owner<<','<<e.neighbour<<','<<e.patch<<','<<e.x<<','<<e.y<<','<<H/2<<','<<e.sx<<','<<e.sy<<",0,"<<e.phi<<','<<e.phiU<<'\n';}
    std::ofstream stats(fs::path(out)/"solver.json");stats<<std::setprecision(17)<<"{\"solver\":\"darcy2d_CG_Jacobi\",\"flow_solved\":true,\"converged\":"<<(converged?"true":"false")<<",\"iterations\":"<<iter<<",\"normalized_residual\":"<<res<<",\"true_normalized_residual\":"<<trueRes<<",\"raw_residual_L1_m3_s\":"<<l1(r)<<",\"normalization\":\"initial_L1_rhs_zero_initial_pressure\",\"cells\":"<<n<<"}\n";
    if(!cells||!faces||!stats)throw std::runtime_error("Output write failed");
    std::cout<<std::setprecision(17)<<"iterations="<<iter<<" residual="<<res<<" true_residual="<<trueRes<<'\n';
    return converged?0:2;
}catch(const std::exception& e){std::cerr<<"SDI_ERROR: "<<e.what()<<'\n';return 1;}
