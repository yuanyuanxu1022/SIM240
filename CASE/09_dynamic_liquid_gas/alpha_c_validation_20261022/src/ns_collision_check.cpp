#include <olb.h>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
using namespace olb;
using namespace olb::descriptors;
using D=D3Q19<RHO,NABLARHO,FORCE,EXTERNAL_FORCE,TAU_EFF>;
using Dyn=MultiPhaseIncompressibleBGKdynamics<double,D>;
using V=std::array<double,3>;
int failures=0,checks=0,trials=0;
double maxError=0;
void check(double a,double b,const char* what){
  ++checks; double e=std::abs(a-b); maxError=std::max(maxError,e);
  if(!std::isfinite(a)||!std::isfinite(b)||e>1e-12){++failures;std::cerr<<what<<" "<<a<<" != "<<b<<'\n';}
}
V raw(const CellD<double,D>& cell){V j{};for(int i=0;i<19;++i)for(int a=0;a<3;++a)j[a]+=c<D>(i,a)*cell[i];return j;}
std::array<double,19> eq(double rho,const V& u,double p){
  std::array<double,19> f{};double u2=0;for(auto v:u)u2+=v*v;
  for(int i=0;i<19;++i){double cu=0;for(int a=0;a<3;++a)cu+=c<D>(i,a)*u[a];
    double w=t<double,D>(i);f[i]=i==0?3*p*(w-1)-1.5*rho*w*u2:3*w*(p+rho*(cu+1.5*cu*cu-.5*u2));}
  return f;
}
template<bool CSE> CellD<double,D> applyCollision(CellD<double,D> cell){
 ParametersOfOperatorD<double,D,Dyn> par;par.set<OMEGA>(1.); // overwritten from TAU_EFF in actual collision
 if constexpr(CSE)dynamics::CSE<Dyn>{}.collide(cell,par);else Dyn{}.collide(cell,par);
 return cell;
}
int main(int argc,char**argv){
 try{
  if(argc!=2)throw std::runtime_error("usage: ns_collision_check new_output_csv");
  if(std::ifstream(argv[1]).good())throw std::runtime_error("refusing overwrite");
  std::ofstream log(argv[1]);log<<std::setprecision(17)<<"trial,rho,tau,force_sign,neq,tiny,axis,j_before,j_after,j_expected,p_recovered,p_expected,u_recovered,u_expected,raw_cut_correction\n";
  const V velocity{.002,-.003,.001}, gradient{.0003,-.0002,.0001},forcebase{.0002,-.0001,.0003};
  for(double rho:{.0012,.1,1.})for(double tau:{1.,1.25})for(int sign:{-1,0,1})for(bool neq:{false,true})for(bool tiny:{false,true}){
   CellD<double,D> input;V force{},gr{},u0=tiny?V{.5e-15,-.7e-15,1.5e-15}:velocity;
   for(int a=0;a<3;++a){force[a]=sign*forcebase[a];gr[a]=tiny?0.:gradient[a];}
   input.setField<RHO>(rho);input.setField<TAU_EFF>(tau);input.setField<FORCE>(Vector<double,3>{force[0],force[1],force[2]});input.setField<NABLARHO>(Vector<double,3>{gr[0],gr[1],gr[2]});
   auto f=eq(rho,u0,.0007);for(int i=0;i<19;++i)input[i]=f[i];
   if(neq&&!tiny){input[1]+=.00001;input[10]+=.00001;input[0]-=.00002;}
   auto j=raw(input);V u{},cut{};
   for(int a=0;a<3;++a){double v=j[a]/rho;double snapped=std::abs(v)<1e-15?0.:v;cut[a]=rho*(snapped-v);u[a]=snapped+.5*force[a];}
   double ug=0,u2=0,sp=0;for(int a=0;a<3;++a){ug+=u[a]*gr[a];u2+=u[a]*u[a];}for(int i=1;i<19;++i)sp+=input[i];
   double p=(sp+.5*ug-.5*rho*u2)/2.; // cs2/(1-w0)=1/2, rho*s0=-rho*u2/2
   double gotp;V gotu{};Dyn::MomentaF{}.computeRhoU(input,gotp,gotu);
   check(gotp,p,"pressure recovery");for(int a=0;a<3;++a)check(gotu[a],u[a],"half force velocity");
   auto expected=eq(rho,u,p);double om=1/tau;
   for(int i=0;i<19;++i){double cu=0,cf=0,cgr=0;for(int a=0;a<3;++a){cu+=c<D>(i,a)*u[a];cf+=c<D>(i,a)*force[a];cgr+=c<D>(i,a)*gr[a];}
    expected[i]=(1-om)*input[i]+om*expected[i]+(1-.5*om)*3*t<double,D>(i)*(rho*cf+cu*cgr);}
   auto gen=applyCollision<false>(input),opt=applyCollision<true>(input);auto jnew=raw(opt);
   for(int i=0;i<19;++i){check(gen[i],opt[i],"NS generic versus CSE");check(opt[i],expected[i],"NS independent population formula");}
   for(int a=0;a<3;++a){double jp=j[a]+rho*force[a]+om*cut[a];check(jnew[a],jp,"NS raw momentum increment");
    log<<trials<<','<<rho<<','<<tau<<','<<sign<<','<<neq<<','<<tiny<<','<<a<<','<<j[a]<<','<<jnew[a]<<','<<jp<<','<<gotp<<','<<p<<','<<gotu[a]<<','<<u[a]<<','<<cut[a]<<'\n';}
   ++trials;
  }
  std::cout<<std::setprecision(17)<<"NS_cse_optimized="<<dynamics::is_cse_optimized_v<Dyn><<" trials="<<trials<<" checks="<<checks<<" failures="<<failures<<" max_abs_error="<<maxError<<"\nPHYSICAL_GATE=NOT_EVALUATED\n";
  return failures?2:0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 3;}
}
