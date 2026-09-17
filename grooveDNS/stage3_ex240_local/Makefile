EXAMPLE = static_lattice_integration
OLB_ROOT := /home/dell/openlb
include $(OLB_ROOT)/default.mk

# OpenLB's default.mk links every *.cpp in the directory.  This wrapper limits
# the real-lattice executable to its own translation unit because the preserved
# voxel generator also contains an independent main().
.PHONY: openlb-static
openlb-static:
	$(MAKE) static_lattice_integration CPP_FILES=static_lattice_integration.cpp OBJ_FILES=static_lattice_integration.o

.PHONY: openlb-moving
openlb-moving:
	$(MAKE) moving_punch_open_drain EXAMPLE=moving_punch_open_drain CPP_FILES=moving_punch_open_drain.cpp OBJ_FILES=moving_punch_open_drain.o

.PHONY: openlb-pressure-baseline
openlb-pressure-baseline:
	$(MAKE) periodic_pressure_baseline EXAMPLE=periodic_pressure_baseline CPP_FILES=periodic_pressure_baseline.cpp OBJ_FILES=periodic_pressure_baseline.o

.PHONY: openlb-explicit-piston
openlb-explicit-piston:
	$(MAKE) explicit_piston_10nm EXAMPLE=explicit_piston_10nm CPP_FILES=explicit_piston_10nm.cpp OBJ_FILES=explicit_piston_10nm.o

.PHONY: openlb-boundary-diag
openlb-boundary-diag:
	$(MAKE) explicit_piston_boundary_intersection_diag EXAMPLE=explicit_piston_boundary_intersection_diag CPP_FILES=explicit_piston_boundary_intersection_diag.cpp OBJ_FILES=explicit_piston_boundary_intersection_diag.o

.PHONY: openlb-operator-trace
openlb-operator-trace:
	$(MAKE) explicit_piston_operator_population_trace EXAMPLE=explicit_piston_operator_population_trace CPP_FILES=explicit_piston_operator_population_trace.cpp OBJ_FILES=explicit_piston_operator_population_trace.o

.PHONY: openlb-boundary-fix
openlb-boundary-fix:
	$(MAKE) explicit_piston_boundary_intersection_fix EXAMPLE=explicit_piston_boundary_intersection_fix CPP_FILES=explicit_piston_boundary_intersection_fix.cpp OBJ_FILES=explicit_piston_boundary_intersection_fix.o

.PHONY: openlb-periodic-seam-diag
openlb-periodic-seam-diag:
	$(MAKE) explicit_piston_periodic_seam_diag EXAMPLE=explicit_piston_periodic_seam_diag CPP_FILES=explicit_piston_periodic_seam_diag.cpp OBJ_FILES=explicit_piston_periodic_seam_diag.o

.PHONY: openlb-periodic-seam-control
openlb-periodic-seam-control:
	$(MAKE) explicit_piston_periodic_seam_phase_control EXAMPLE=explicit_piston_periodic_seam_phase_control CPP_FILES=explicit_piston_periodic_seam_phase_control.cpp OBJ_FILES=explicit_piston_periodic_seam_phase_control.o

.PHONY: openlb-periodic-seam-fix
openlb-periodic-seam-fix:
	$(MAKE) explicit_piston_periodic_seam_fix EXAMPLE=explicit_piston_periodic_seam_fix CPP_FILES=explicit_piston_periodic_seam_fix.cpp OBJ_FILES=explicit_piston_periodic_seam_fix.o

.PHONY: openlb-f3-reverse-trace
openlb-f3-reverse-trace:
	$(MAKE) explicit_piston_f3_reverse_trace EXAMPLE=explicit_piston_f3_reverse_trace CPP_FILES=explicit_piston_f3_reverse_trace.cpp OBJ_FILES=explicit_piston_f3_reverse_trace.o

.PHONY: openlb-localpressure-nonzero
openlb-localpressure-nonzero:
	$(MAKE) explicit_localpressure_nonzero_baseline EXAMPLE=explicit_localpressure_nonzero_baseline CPP_FILES=explicit_localpressure_nonzero_baseline.cpp OBJ_FILES=explicit_localpressure_nonzero_baseline.o

.PHONY: openlb-separated-control
openlb-separated-control:
	$(MAKE) explicit_piston_pressure_separated_control EXAMPLE=explicit_piston_pressure_separated_control CPP_FILES=explicit_piston_pressure_separated_control.cpp OBJ_FILES=explicit_piston_pressure_separated_control.o

.PHONY: openlb-zouhe-pressure-candidate
openlb-zouhe-pressure-candidate:
	$(MAKE) explicit_piston_zouhe_pressure_candidate EXAMPLE=explicit_piston_zouhe_pressure_candidate CPP_FILES=explicit_piston_zouhe_pressure_candidate.cpp OBJ_FILES=explicit_piston_zouhe_pressure_candidate.o

.PHONY: openlb-zouhe-preconversion-longrun
openlb-zouhe-preconversion-longrun:
	$(MAKE) explicit_piston_zouhe_preconversion_longrun EXAMPLE=explicit_piston_zouhe_preconversion_longrun CPP_FILES=explicit_piston_zouhe_preconversion_longrun.cpp OBJ_FILES=explicit_piston_zouhe_preconversion_longrun.o

.PHONY: openlb-zouhe-mass-drift-diagnosis
openlb-zouhe-mass-drift-diagnosis:
	$(MAKE) explicit_piston_zouhe_mass_drift_diagnosis EXAMPLE=explicit_piston_zouhe_mass_drift_diagnosis CPP_FILES=explicit_piston_zouhe_mass_drift_diagnosis.cpp OBJ_FILES=explicit_piston_zouhe_mass_drift_diagnosis.o

.PHONY: openlb-zouhe-moving-control-volume
openlb-zouhe-moving-control-volume:
	$(MAKE) explicit_piston_zouhe_moving_control_volume_longrun EXAMPLE=explicit_piston_zouhe_moving_control_volume_longrun CPP_FILES=explicit_piston_zouhe_moving_control_volume_longrun.cpp OBJ_FILES=explicit_piston_zouhe_moving_control_volume_longrun.o

.PHONY: openlb-single-conversion-ledger
openlb-single-conversion-ledger:
	$(MAKE) explicit_piston_single_conversion_ledger EXAMPLE=explicit_piston_single_conversion_ledger CPP_FILES=explicit_piston_single_conversion_ledger.cpp OBJ_FILES=explicit_piston_single_conversion_ledger.o

.PHONY: openlb-step5-geometry-visualization
openlb-step5-geometry-visualization:
	$(MAKE) step5_geometry_visualization_export EXAMPLE=step5_geometry_visualization_export CPP_FILES=step5_geometry_visualization_export.cpp OBJ_FILES=step5_geometry_visualization_export.o

.PHONY: openlb-conversion-root-cause-diag
openlb-conversion-root-cause-diag:
	$(MAKE) explicit_piston_conversion_root_cause_diag EXAMPLE=explicit_piston_conversion_root_cause_diag CPP_FILES=explicit_piston_conversion_root_cause_diag.cpp OBJ_FILES=explicit_piston_conversion_root_cause_diag.o

.PHONY: openlb-conversion-repair-candidate
openlb-conversion-repair-candidate:
	$(MAKE) explicit_piston_conversion_repair_candidate EXAMPLE=explicit_piston_conversion_repair_candidate CPP_FILES=explicit_piston_conversion_repair_candidate.cpp OBJ_FILES=explicit_piston_conversion_repair_candidate.o

.PHONY: openlb-conversion-repair-candidate-b
openlb-conversion-repair-candidate-b:
	$(MAKE) explicit_piston_conversion_repair_candidate_b EXAMPLE=explicit_piston_conversion_repair_candidate_b CPP_FILES=explicit_piston_conversion_repair_candidate_b.cpp OBJ_FILES=explicit_piston_conversion_repair_candidate_b.o

.PHONY: openlb-moving-boundary-compression
openlb-moving-boundary-compression:
	$(MAKE) explicit_piston_moving_boundary_compression EXAMPLE=explicit_piston_moving_boundary_compression CPP_FILES=explicit_piston_moving_boundary_compression.cpp OBJ_FILES=explicit_piston_moving_boundary_compression.o

.PHONY: openlb-virtual-link-moving-geometry
openlb-virtual-link-moving-geometry:
	$(MAKE) explicit_piston_virtual_link_moving_geometry EXAMPLE=explicit_piston_virtual_link_moving_geometry CPP_FILES=explicit_piston_virtual_link_moving_geometry.cpp OBJ_FILES=explicit_piston_virtual_link_moving_geometry.o

geometry_generator: geometry_generator.cpp
	g++ -O2 -std=c++17 -Wall -Wextra -pedantic $< -o $@
