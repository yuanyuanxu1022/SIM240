# First-paper static geometry and pressure-baseline helpers.
# Former moving-boundary targets are retained only in Makefile.second_paper_local.
EXAMPLE = static_lattice_integration
OLB_ROOT := /home/dell/openlb
include $(OLB_ROOT)/default.mk

# The geometry generator also has main(); compile the requested translation unit only.
.PHONY: openlb-static
openlb-static:
	$(MAKE) static_lattice_integration CPP_FILES=static_lattice_integration.cpp OBJ_FILES=static_lattice_integration.o

.PHONY: openlb-pressure-baseline
openlb-pressure-baseline:
	$(MAKE) periodic_pressure_baseline EXAMPLE=periodic_pressure_baseline CPP_FILES=periodic_pressure_baseline.cpp OBJ_FILES=periodic_pressure_baseline.o
