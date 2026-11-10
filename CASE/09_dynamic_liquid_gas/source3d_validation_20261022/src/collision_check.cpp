#include "dimension_corrected_ch.h"
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>

using namespace olb;
using namespace olb::descriptors;
using TestD2 = D2Q9<SOURCE,VELOCITY,CHEM_POTENTIAL>;
using TestD3 = D3Q19<FORCE,SOURCE,SOURCE_OLD,PHIWETTING,VELOCITY,OLD_PHIU,STATISTIC,CHEM_POTENTIAL,BOUNDARY>;
int checks=0, failures=0;
double maxError=0;
void check(double got, double expected, const char* label) {
  ++checks;
  const double error=std::abs(got-expected);
  maxError=std::max(maxError,error);
  if (!std::isfinite(got) || error>1e-12) {
    ++failures;
    std::cerr<<label<<" got="<<got<<" expected="<<expected<<'\n';
  }
}
template<typename D, typename Dyn, bool Optimized>
CellD<double,D> collide(CellD<double,D> c, double omega) {
  ParametersOfOperatorD<double,D,Dyn> params;
  params.template set<OMEGA>(omega);
  if constexpr(Optimized) dynamics::CSE<Dyn>{}.collide(c,params);
  else Dyn{}.collide(c,params);
  return c;
}
template<typename D>
void exercise() {
  using Old=WellBalancedCahnHilliardBGKdynamics<double,D>;
  using New=sim240::CorrectedDynamics<double,D>;
  static_assert(dynamics::is_cse_optimized_v<Old>);
  static_assert(!dynamics::is_cse_optimized_v<New>);
  int trials=0;
  for(double tau:{0.6,1.,1.4}) for(double phi:{0.2,0.5,0.8})
  for(double mu:{-0.004,0.,0.003}) for(double source:{-0.0002,0.,0.0002})
  for(bool neq:{false,true}) {
    CellD<double,D> input;
    input.template setField<CHEM_POTENTIAL>(mu);
    input.template setField<SOURCE>(source);
    for(int a=0;a<D::d;++a) input.template getFieldComponent<VELOCITY>(a)=0.003*(a+1);
    for(int i=0;i<D::q;++i) {
      const double w=descriptors::t<double,D>(i);
      input[i]=(i==0?phi-(1-w)*mu:w*mu)-w;
    }
    if(neq) { input[1]+=0.0003;input[2]-=0.0003; }
    auto zero=input;zero.template setField<SOURCE>(0.);
    auto og=collide<D,Old,false>(input,1/tau), oc=collide<D,Old,true>(input,1/tau);
    auto ng=collide<D,New,false>(input,1/tau), nc=collide<D,New,true>(input,1/tau);
    auto oz=collide<D,Old,true>(zero,1/tau), nz=collide<D,New,true>(zero,1/tau);
    double old0=0,new0=0;
    std::array<double,D::d> old1{},new1{};
    std::array<std::array<double,D::d>,D::d> old2{},new2{};
    for(int i=0;i<D::q;++i) {
      check(og[i],oc[i],"old generic versus CSE");
      check(ng[i],nc[i],"new generic versus CSE fallback");
      check(oz[i],nz[i],"zero source unchanged");
      if constexpr(D::d==2) check(oc[i],nc[i],"D2 unchanged");
      const double od=oc[i]-oz[i],nd=nc[i]-nz[i];
      old0+=od;new0+=nd;
      for(int a=0;a<D::d;++a) {
        const int ca=descriptors::c<D>(i,a);
        old1[a]+=ca*od;new1[a]+=ca*nd;
        for(int b=0;b<D::d;++b) {
          const int cb=descriptors::c<D>(i,b);
          old2[a][b]+=ca*cb*od;new2[a][b]+=ca*cb*nd;
        }
      }
    }
    check(new0,-source,"new zeroth moment");
    check(old0,(D::d==3?-0.5:-1.)*source,"old defect control");
    if(tau==1. && phi==.5 && mu==0. && source==.0002 && !neq) {
      std::cout<<"sample dimension="<<D::d<<" S="<<source
               <<" old_m0="<<old0<<" new_m0="<<new0
               <<" old_m2xx="<<old2[0][0]<<" new_m2xx="<<new2[0][0]<<'\n';
    }
    for(int a=0;a<D::d;++a) {
      check(old1[a],0.,"old first");check(new1[a],0.,"new first");
      for(int b=0;b<D::d;++b) {
        check(new2[a][b],0.,"new second");
        check(old2[a][b],D::d==3&&a==b?source/6.:0.,"old second");
      }
    }
    ++trials;
  }
  std::cout<<"dimension="<<D::d<<" trials="<<trials<<" old_cse=true new_cse=false\n";
}
int main() {
  try {
    std::cout<<std::setprecision(17);
    exercise<TestD2>();exercise<TestD3>();
    std::cout<<"checks="<<checks<<" failures="<<failures<<" max_abs_error="<<maxError<<'\n';
    std::cout<<"COLLISION_CONTRACT="<<(failures?"FAIL":"PASS")<<"\n"
             <<"TRANSPORT_TEST=NOT_RUN\nPHYSICAL_GATE=NOT_EVALUATED\n";
    return failures?2:0;
  } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 3; }
}
