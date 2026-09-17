# SIM240 Current Status

## 1. Research Objective

SIM240 uses OpenLB to perform explicit lattice-based simulation of nanoscale groove structures.

The objective is to investigate hydraulic resistance differences caused by real nanoscale wall and groove geometries without replacing structures by equivalent porous resistance models.

---

## 2. Current Geometry

Main groove structure:

- Periodic straight groove
- 60 nm half platform
- 120 nm groove region
- 60 nm half platform
- Groove depth: 100 nm

---

## 3. Completed Work

### Geometry and Solver Validation

- Real geometry imported into OpenLB
- Lattice conversion verified
- Boundary condition checked

### Transport Validation

Completed:

- Straight groove transport
- Transverse blockage test
- Mass conservation verification
- Grid convergence study (G2)

---

## 4. Current Research Task

Current focus:

Direction-dependent hydraulic resistance.

Compare:

- Parallel groove flow
- Perpendicular groove flow

Analyze:

- Pressure drop
- Flow rate
- Hydraulic resistance
- Permeability difference

---

## 5. Main Simulation Structure

```text
SIM240/
├── CASE/
│   └── OpenLB simulation cases
│
├── grooveDNS/
│   └── Core development and validation
│
├── analysis/
│   └── Data processing scripts
│
├── figures/
│   └── Visualization results
│
└── docs/
    └── Research documentation

```

## 6. Next Steps

1. Complete parallel/perpendicular resistance comparison.
2. Extract pressure-flow relationship.
3. Calculate hydraulic resistance and permeability.
4. Compare with existing literature.
5. Analyze nanoscale transport mechanisms.
