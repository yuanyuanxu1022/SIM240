CASE_ROOT := ..
OLB_ROOT := /home/dell/openlb
HEIGHT_NM ?= 75
TARGET := $(CASE_ROOT)/build/g3_ex240_h$(HEIGHT_NM)
OBJECT := $(CASE_ROOT)/build/g3_ex240_h$(HEIGHT_NM).o
DEPEND := $(CASE_ROOT)/build/g3_ex240_h$(HEIGHT_NM).d
SOURCE := $(CASE_ROOT)/build/generated/g3_ex240_h$(HEIGHT_NM).cpp
GENERATOR := $(CASE_ROOT)/scripts/generate_height_source.py

CXX := mpic++
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION=\"5953d8a-dirty\" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDE_FLAGS := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib \
  -I$(OLB_ROOT)/external/tinyxml2
LDFLAGS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib \
  -lz -ltinyxml2 -lpthread

.PHONY: all generate clean dry-run

all: $(TARGET)

generate: $(SOURCE)

$(SOURCE): $(GENERATOR) ../../../02_geometry_transport/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp

	python3 $(GENERATOR) --height-nm $(HEIGHT_NM) --output $(SOURCE)

$(TARGET): $(OBJECT)

	@mkdir -p $(dir $@)
	$(CXX) $(OBJECT) -o $@ $(LDFLAGS)

$(OBJECT): $(SOURCE)

	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -MMD -MP -MF $(DEPEND) -c $< -o $@

dry-run:

	$(MAKE) --dry-run all

clean:

	$(RM) $(TARGET) $(OBJECT) $(DEPEND)

-include $(DEPEND)
