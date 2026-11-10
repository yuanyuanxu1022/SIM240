// Isolated SIM240 alpha adapter; GPL-2.0-or-later, following OpenLB equilibrium.
// Alpha is a CH-only cell field. CHEM_POTENTIAL remains the physical chemical
// potential read by the unmodified NS coupling. Uniform alpha is frozen per run.
#pragma once
#include "dimension_corrected_ch.h"

namespace sim240 {
struct CH_ALPHA : olb::descriptors::FIELD_BASE<1> { };

struct AlphaCHEquilibrium {
  using parameters=olb::meta::list<>;
  static std::string getName() {return "SIM240_AlphaCHEquilibrium_v1";}
  template<typename D,typename MOMENTA> struct type {
    using MomentaF=typename MOMENTA::template type<D>;
    template<typename CELL,typename RHO,typename U,typename FEQ,typename V=typename CELL::value_t>
    olb::CellStatistic<V> compute(CELL& cell,RHO& phi,U& u,FEQ& feq) any_platform {
      const V effectiveMu=cell.template getField<CH_ALPHA>()
                         *cell.template getField<olb::descriptors::CHEM_POTENTIAL>();
      feq[0]=phi-(1-olb::descriptors::t<V,D>(0))*effectiveMu-olb::descriptors::t<V,D>(0);
      for(int i=1;i<D::q;++i) feq[i]=olb::descriptors::t<V,D>(i)*(effectiveMu-1);
      return {phi,olb::util::normSqr<V,D::d>(u)};
    }
    template<typename CELL,typename PARAMETERS,typename FEQ,typename V=typename CELL::value_t>
    olb::CellStatistic<V> compute(CELL& cell,PARAMETERS&,FEQ& feq) any_platform {
      V phi,u[D::d];MomentaF().computeRhoU(cell,phi,u);
      return compute(cell,phi,u,feq);
    }
  };
};

template<typename T,typename D>
using AlphaCHDynamics=olb::dynamics::Tuple<T,D,
  olb::momenta::ExternalVelocityTuple,AlphaCHEquilibrium,
  olb::collision::BGK,DimensionCorrectedCH>;
} // namespace sim240
