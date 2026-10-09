# SIM240 G2 Resistance Analysis

## Objective

Analyze hydraulic resistance difference between:

- Parallel groove transport
- Perpendicular groove transport

based on explicit OpenLB nanoscale groove simulations.

---

## Input Cases

Current cases:

- EX240_parallel
- EX240_perpendicular
- Smooth75 baseline

Grid levels:

- dx = 5 nm
- dx = 2.5 nm
- dx = 1.25 nm

---

## Extracted Quantities

Main parameters:

- Pressure drop ΔP
- Flow rate Q
- Hydraulic resistance R

where:

R = ΔP / Q

Permeability:

K = function(μ, Q, ΔP, geometry)

---

## Analysis Workflow

CASE results

↓

Data extraction

↓

Resistance calculation

↓

Grid convergence evaluation

↓

Publication figures


---

## Outputs

Generated:

- Resistance comparison
- Grid convergence plots
- Pressure-flow curves
- Parallel/perpendicular ratio