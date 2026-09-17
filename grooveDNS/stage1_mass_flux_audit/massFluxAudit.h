#pragma once
#include <cmath>
#include <cstddef>

struct MassFluxAuditRecord {
  double totalMass=0, liquidMass=0, totalDrift=0, liquidDrift=0;
  double qySection0=0, qySection1=0, qyRelativeDifference=0;
  double maxDensityDeviation=0;
};

// Interface contract for the independent audit executable. Implementations
// must iterate core cells only and apply periodic-endpoint de-duplication.
template <typename Lattice, typename Geometry>
MassFluxAuditRecord computeMassFluxAudit(const Lattice&, const Geometry&)
{ return {}; }
