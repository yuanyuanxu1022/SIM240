// Isolated SIM240 diagnostic adapter. Shared OpenLB sources are not modified.
// Based on OpenLB forcing::WellBalancedCahnHilliard (GPL-2.0-or-later).
// Ju et al., arXiv:2311.10827, Eq. (2.18): trace(I) is the spatial dimension.
#pragma once
#include <olb.h>

namespace sim240 {
struct DimensionCorrectedCH : olb::forcing::WellBalancedCahnHilliard {
  static std::string getName() { return "SIM240_DimensionCorrectedCH_v1"; }

  template <typename D, typename MOMENTA, typename EQUILIBRIUM, typename COLLISION>
  struct combined_collision {
    using MomentaF = typename MOMENTA::template type<D>;
    using CollisionO = typename COLLISION::template type<D,MOMENTA,EQUILIBRIUM>;
    static_assert(D::d == 2 || D::d == 3);
    static_assert(COLLISION::parameters::template contains<olb::descriptors::OMEGA>());

    template <typename CELL, typename PARAMETERS, typename V=typename CELL::value_t>
    olb::CellStatistic<V> apply(CELL& cell, PARAMETERS& parameters) any_platform {
      V phi = MomentaF().computeRho(cell);
      CollisionO().apply(cell, parameters);
      const auto source = cell.template getField<olb::descriptors::SOURCE>();
      const auto u = cell.template getField<olb::descriptors::VELOCITY>();
      for (int i=0; i<D::q; ++i) {
        V cc{};
        for (int a=0; a<D::d; ++a) cc += olb::descriptors::c<D>(i,a)*olb::descriptors::c<D>(i,a);
        // The sole mathematical change from the upstream generic collision:
        const V coefficient = -V(D::d+2)/V(2)
          + V(0.5)*olb::descriptors::invCs2<V,D>()*cc;
        cell[i] += coefficient*olb::descriptors::t<V,D>(i)*source;
      }
      return {phi, olb::util::normSqr<V,D::d>(u)};
    }
  };
};

template <typename T, typename D>
using CorrectedDynamics = olb::dynamics::Tuple<T,D,
  olb::momenta::ExternalVelocityTuple,
  olb::equilibria::CahnHilliardZerothOrder,
  olb::collision::BGK, DimensionCorrectedCH>;
} // namespace sim240
