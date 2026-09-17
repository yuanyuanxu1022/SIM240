EXAMPLE = sim_ec1xt240_right_angle_freesurface
OLB_ROOT := /home/dell/openlb
include $(OLB_ROOT)/default.mk

.PHONY: build
build:
	$(MAKE) $(EXAMPLE) EXAMPLE=$(EXAMPLE) CPP_FILES=$(EXAMPLE).cpp OBJ_FILES=$(EXAMPLE).o
