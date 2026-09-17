# SIM240 Project

## 1. Research Objective

SIM240 focuses on explicit lattice-based simulation of nanoscale groove structures using OpenLB.

The project aims to investigate hydraulic resistance differences caused by real nanoscale wall and groove geometries without replacing structures by equivalent porous resistance models.

---

## 2. Current Research Status

Completed:

- Ideal straight groove transport validation
- Transverse blockage test
- Mass conservation verification
- Grid convergence study (G2)

Current research direction:

- Fixed geometry single-phase liquid transport
- Direction-dependent hydraulic resistance
- Mechanism analysis of groove orientation effects

---

## 3. Directory Structure



CASE/
OpenLB simulation cases

grooveDNS/
Core development and validation code

analysis/
Python post-processing scripts

notebooks/
Data analysis notebooks

figures/
Paper and presentation figures

docs/
Research notes and reports


---

## 4. Main Validation

Completed validation includes:

- Geometry consistency check
- Mass conservation
- Boundary condition verification
- Grid convergence analysis

---

## 5. Current Next Steps

1. Analyze parallel/perpendicular groove hydraulic resistance.
2. Extract pressure drop and flow rate relationship.
3. Calculate permeability and resistance differences.
4. Prepare literature comparison.
5. Extend toward nanoscale mechanism analysis.

