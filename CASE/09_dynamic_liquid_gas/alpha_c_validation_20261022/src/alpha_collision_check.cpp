#include "alpha_ch.h"
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
using namespace olb;using namespace olb::descriptors;
using TestD2=D2Q9<SOURCE,VELOCITY,CHEM_POTENTIAL,sim240::CH_ALPHA>;
using TestD3=D3Q19<SOURCE,VELOCITY,CHEM_POTENTIAL,sim240::CH_ALPHA>;
long checks=0,failures=0;double maxError=0;
void check(double a,double b){++checks;double e=std::abs(a-b);maxError=std::max(maxError,e);if(!std::isfinite(a)||!std::isfinite(b)||e>1e-12)++failures;}
template<typename D,typename Dyn,bool CSE>CellD<double,D> collide(CellD<double,D> c,double tau){
 ParametersOfOperatorD<double,D,Dyn> p;p.template set<OMEGA>(1/tau);
 if constexpr(CSE)dynamics::CSE<Dyn>{}.collide(c,p);else Dyn{}.collide(c,p);return c;
}
template<typename D>void exercise(){
 using New=sim240::AlphaCHDynamics<double,D>;using Previous=sim240::CorrectedDynamics<double,D>;
 static_assert(!dynamics::is_cse_optimized_v<New>);
 long trials=0;
 for(double alpha:{1.,4.,16.})for(double tau:{.6,1.,1.4,2.5})for(double phi:{.1,.5,.9})
 for(double mu:{-.004,0.,.003})for(double source:{-.0002,0.,.0002})for(bool neq:{false,true}){
  CellD<double,D> input;input.template setField<CHEM_POTENTIAL>(mu);input.template setField<SOURCE>(source);input.template setField<sim240::CH_ALPHA>(alpha);
  for(int a=0;a<D::d;++a)input.template getFieldComponent<VELOCITY>(a)=.003*(a+1);
  for(int i=0;i<D::q;++i){double w=t<double,D>(i);input[i]=(i==0?phi-(1-w)*alpha*mu:w*alpha*mu)-w;}
  if(neq){input[1]+=.0003;input[2]-=.0003;}
  double actualPhi=1;for(int i=0;i<D::q;++i)actualPhi+=input[i];
  auto g=collide<D,New,false>(input,tau),optimized=collide<D,New,true>(input,tau);
  auto z=input;z.template setField<SOURCE>(0.);z=collide<D,New,true>(z,tau);
  std::array<double,D::d> m1{};std::array<std::array<double,D::d>,D::d> m2{};double m0=0,eqSum=0;
  for(int i=0;i<D::q;++i){double w=t<double,D>(i),cc=0;for(int a=0;a<D::d;++a)cc+=c<D>(i,a)*c<D>(i,a);
   double feq=(i==0?actualPhi-(1-w)*alpha*mu:w*alpha*mu)-w;
   double expected=(1-1/tau)*input[i]+feq/tau+w*(-.5*(D::d+2)+1.5*cc)*source;
   check(g[i],optimized[i]);check(optimized[i],expected);eqSum+=feq+w;double b=optimized[i]-z[i];m0+=b;
   for(int a=0;a<D::d;++a){m1[a]+=c<D>(i,a)*b;for(int j=0;j<D::d;++j)m2[a][j]+=c<D>(i,a)*c<D>(i,j)*b;}
  }
  check(eqSum,actualPhi);check(m0,-source);for(int a=0;a<D::d;++a){check(m1[a],0);for(int b=0;b<D::d;++b)check(m2[a][b],0);}
  check(optimized.template getField<CHEM_POTENTIAL>(),mu);check(optimized.template getField<sim240::CH_ALPHA>(),alpha);
  if(alpha==1.){auto old=collide<D,Previous,true>(input,tau);for(int i=0;i<D::q;++i)check(old[i],optimized[i]);}
  ++trials;
 }
 std::cout<<"dimension="<<D::d<<" trials="<<trials<<" alpha=1,4,16 CSE_optimized=false generic_fallback=true\n";
}
int main(){std::cout<<std::setprecision(17);exercise<TestD2>();exercise<TestD3>();std::cout<<"checks="<<checks<<" failures="<<failures<<" max_abs_error="<<maxError<<"\nLOCAL_COLLISION_CONTRACT="<<(failures?"FAIL":"PASS")<<"\nSPACE_TRANSPORT=NOT_RUN\n";return failures?2:0;}
