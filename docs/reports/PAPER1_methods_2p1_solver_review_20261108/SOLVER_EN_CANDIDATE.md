Solver-paragraph candidate:

Calculations use OpenLB [7] with the D3Q19 velocity set and a single-relaxation-time BGK collision model at τ=1. The force term is discretized using the Guo scheme [9]. Stationary solid walls use the linear Bouzidi–Firdaouss–Lallemand interpolated bounce-back rule [8], with wall-link intersections determined from the analytical geometry. The saved boundary-audit records have fractional wall distance q=0.5, corresponding to the halfway bounce-back limit of this rule. The audit scope and accuracy checks are described later in this section and in Section 3.

Forcing and velocity-extraction candidate (preserve stopping criteria and provenance text):

Driving is imposed through a spatially uniform, time-independent body force with acceleration magnitude a=1×10⁵ m s⁻² and corresponding force-density magnitude ρa. The main comparison uses the same magnitude; forcing checks for the reference geometry are described in §2.4. Macroscopic velocity is obtained through OpenLB computeU, including the half-time-step force correction consistent with the Guo scheme [9].
