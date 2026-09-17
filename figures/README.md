# SIM240 Figures

## 1. Purpose

This directory stores visualization results generated from SIM240 OpenLB simulations.

The figures are used for:

- Numerical validation
- Flow field analysis
- Hydraulic resistance comparison
- Research presentations
- Publication preparation

---

## 2. Directory Structure

```text
figures/

├── validation/
│   └── Numerical verification figures
│
├── pressure/
│   └── Pressure field visualization
│
├── velocity/
│   └── Velocity field visualization
│
├── resistance/
│   └── Hydraulic resistance analysis figures
│
└── presentation/
    └── Figures for reports and presentations
```

---

## 3. Figure Generation Workflow

```text
CASE simulation

        ↓

OpenLB output

        ↓

analysis scripts

        ↓

Figure generation

        ↓

figures/
```

---

## 4. Current Figure Categories

### Validation

Contains:

- Grid convergence figures
- Benchmark comparison
- Mass conservation verification

---

### Pressure Field

Contains:

- Pressure distribution
- Pressure drop visualization
- Flow resistance analysis

---

### Velocity Field

Contains:

- Velocity profile
- Flow direction analysis
- Groove transport visualization

---

### Resistance Analysis

Contains:

- Parallel/perpendicular resistance comparison
- Hydraulic resistance curves
- Permeability comparison

---

## 5. Naming Convention

Recommended format:

```
<case>_<quantity>_<condition>_<date>
```

Example:

```
G2_EX240_parallel_pressure_20260917.png
G2_EX240_resistance_compare_20260917.png
```

---

## 6. Current Status

Prepared:

- Figure directory structure
- Visualization workflow

Future:

- Automated figure generation
- Publication-quality plotting
- Consistent figure style
