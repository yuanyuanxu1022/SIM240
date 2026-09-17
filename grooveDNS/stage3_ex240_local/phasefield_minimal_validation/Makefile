EXAMPLE = phasefield_minimal_validation
OLB_ROOT := /home/dell/openlb
include $(OLB_ROOT)/default.mk

.PHONY: build
build:
	$(MAKE) $(EXAMPLE) EXAMPLE=$(EXAMPLE) CPP_FILES=$(EXAMPLE).cpp OBJ_FILES=$(EXAMPLE).o
