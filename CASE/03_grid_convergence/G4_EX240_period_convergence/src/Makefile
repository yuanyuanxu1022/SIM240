CASE_ROOT := ..
OLB_ROOT := /home/dell/openlb
GENERATOR := $(CASE_ROOT)/scripts/generate_period_source.py
FROZEN := ../../../02_geometry_transport/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp
NX_LIST := 1 2 4 8
MODES := serial mpi
A_TAGS := a5e4 a1e5 a2e5

CXX := mpic++
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION=\"5953d8a-dirty\" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDE_FLAGS := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib \
  -I$(OLB_ROOT)/external/tinyxml2
LDFLAGS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib \
  -lz -ltinyxml2 -lpthread

# Keep all generated sources (reproducible artifacts; SHAs recorded in manifests).
.SECONDARY:

.PHONY: all generate clean verify-deltas check-identity

all: verify-deltas $(foreach nx,$(NX_LIST),$(foreach mode,$(MODES),$(foreach tag,$(A_TAGS),$(CASE_ROOT)/build/g4_nx$(nx)_$(mode)_$(tag))))

generate: $(foreach nx,$(NX_LIST),$(foreach mode,$(MODES),$(CASE_ROOT)/build/generated/g4_nx$(nx)_$(mode).cpp))

# --- base sources: generator from SHA-pinned frozen G2 source ----------------

$(CASE_ROOT)/build/generated/g4_nx%_serial.cpp: $(GENERATOR) $(FROZEN)
	@mkdir -p $(dir $@)
	python3 $(GENERATOR) --nx $* --mode serial --output $@

$(CASE_ROOT)/build/generated/g4_nx%_mpi.cpp: $(GENERATOR) $(FROZEN)
	@mkdir -p $(dir $@)
	python3 $(GENERATOR) --nx $* --mode mpi --output $@

# --- acceleration variants via sed (force-linearity pattern) -----------------

$(CASE_ROOT)/build/generated/g4_nx%_a5e4.cpp: $(CASE_ROOT)/build/generated/g4_nx%.cpp
	sed 's/constexpr T acceleration = 1.0e5;/constexpr T acceleration = 5.0e4;/' $< > $@

$(CASE_ROOT)/build/generated/g4_nx%_a2e5.cpp: $(CASE_ROOT)/build/generated/g4_nx%.cpp
	sed 's/constexpr T acceleration = 1.0e5;/constexpr T acceleration = 2.0e5;/' $< > $@

# --- binaries: 24 = NX x {serial,mpi} x {a5e4,a1e5,a2e5} ----------------------

define BIN_RULE
$(CASE_ROOT)/build/g4_nx$(1)_$(2)_$(3): $(CASE_ROOT)/build/generated/$(4)
	@mkdir -p $$(dir $$@)
	$$(CXX) $$(CXXFLAGS) $$(INCLUDE_FLAGS) -MMD -MP -MF $$@.d -c $$< -o $$@.o
	$$(CXX) $$@.o -o $$@ $$(LDFLAGS)
endef

$(foreach nx,$(NX_LIST),$(foreach mode,$(MODES),\
  $(eval $(call BIN_RULE,$(nx),$(mode),a1e5,g4_nx$(nx)_$(mode).cpp))\
  $(eval $(call BIN_RULE,$(nx),$(mode),a5e4,g4_nx$(nx)_$(mode)_a5e4.cpp))\
  $(eval $(call BIN_RULE,$(nx),$(mode),a2e5,g4_nx$(nx)_$(mode)_a2e5.cpp))))

# --- audits -------------------------------------------------------------------

verify-deltas: generate
	python3 $(CASE_ROOT)/scripts/verify_deltas.py --build-dir $(CASE_ROOT)/build/generated

check-identity: generate
	@echo "identity check is part of verify-deltas (nx1 serial whitelist)"

clean:
	$(RM) $(CASE_ROOT)/build/g4_nx* $(CASE_ROOT)/build/generated/g4_nx*.cpp
