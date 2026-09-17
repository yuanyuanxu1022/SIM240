EXAMPLE = topology_transaction_test
OLB_ROOT := /home/dell/openlb
include $(OLB_ROOT)/default.mk

.PHONY: phase2-first-conversion
phase2-first-conversion:
	$(MAKE) first_material_conversion_test EXAMPLE=first_material_conversion_test CPP_FILES=first_material_conversion_test.cpp OBJ_FILES=first_material_conversion_test.o

.PHONY: mass-audit-consistency
mass-audit-consistency:
	$(MAKE) mass_audit_consistency_test EXAMPLE=mass_audit_consistency_test CPP_FILES=mass_audit_consistency_test.cpp OBJ_FILES=mass_audit_consistency_test.o

.PHONY: step5d-population-strategies
step5d-population-strategies:
	$(MAKE) step5D_population_strategy_test EXAMPLE=step5D_population_strategy_test CPP_FILES=step5D_population_strategy_test.cpp OBJ_FILES=step5D_population_strategy_test.o

.PHONY: step5e-link-ledger
step5e-link-ledger:
	$(MAKE) step5E_link_mass_ledger EXAMPLE=step5E_link_mass_ledger CPP_FILES=step5E_link_mass_ledger.cpp OBJ_FILES=step5E_link_mass_ledger.o

.PHONY: step5f-link-transition
step5f-link-transition:
	$(MAKE) step5F_link_transition_fix EXAMPLE=step5F_link_transition_fix CPP_FILES=step5F_link_transition_fix.cpp OBJ_FILES=step5F_link_transition_fix.o
