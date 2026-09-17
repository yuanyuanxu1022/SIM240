CASE_ROOT := ..
OLB_ROOT := /home/dell/openlb
BUILD_DIR := $(CASE_ROOT)/build
GENERATED_DIR := $(BUILD_DIR)/generated
GENERATOR := generate_step3_sources.py
BASE_EX := ../../G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp
BASE_SMOOTH := ../../G1_Poiseuille_Bouzidi_Validation/src/g1_poiseuille_bouzidi_validation.cpp

CXX := mpic++
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION=\"5953d8a-dirty\" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDE_FLAGS := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib \
  -I$(OLB_ROOT)/external/tinyxml2
LDFLAGS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib \
  -lz -ltinyxml2 -lpthread

EX_TAGS := 5 2p5 1p25
EX_TARGETS := $(addprefix $(BUILD_DIR)/g2_ex240_dx,$(EX_TAGS))
SMOOTH_TARGET := $(BUILD_DIR)/g2_smooth75_step3
TARGETS := $(SMOOTH_TARGET) $(EX_TARGETS)

.PHONY: all generate dry-run

all: $(TARGETS)

generate: $(GENERATED_DIR)/.sources.stamp

$(GENERATED_DIR)/.sources.stamp: $(GENERATOR) $(BASE_EX) $(BASE_SMOOTH)
	@mkdir -p $(GENERATED_DIR)
	python3 $(GENERATOR) --output-dir $(GENERATED_DIR)
	@touch $@
	@touch $(GENERATED_DIR)/g2_smooth75_step3.cpp \
	  $(addprefix $(GENERATED_DIR)/g2_ex240_dx,$(addsuffix .cpp,$(EX_TAGS)))

$(SMOOTH_TARGET): $(GENERATED_DIR)/g2_smooth75_step3.cpp $(GENERATED_DIR)/.sources.stamp Makefile
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) $< -o $@ $(LDFLAGS)

$(BUILD_DIR)/g2_ex240_dx%: $(GENERATED_DIR)/g2_ex240_dx%.cpp $(GENERATED_DIR)/.sources.stamp Makefile
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) $< -o $@ $(LDFLAGS)

$(GENERATED_DIR)/g2_smooth75_step3.cpp $(addprefix $(GENERATED_DIR)/g2_ex240_dx,$(addsuffix .cpp,$(EX_TAGS))): $(GENERATED_DIR)/.sources.stamp
	@test -f $@

dry-run:
	$(MAKE) --dry-run all
