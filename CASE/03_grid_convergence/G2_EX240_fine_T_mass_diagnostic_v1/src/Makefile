# Preparation only. No default build and no simulation target.
CXX := mpic++
OLB_ROOT := /home/dell/openlb
TARGET := ../build/fine_T_diagnostic
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION=\"882924a9cfc8dcdf82909e39530789cb6f5ebcc4\" -pthread \
  -DPARALLEL_MODE_MPI -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDES := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib -I$(OLB_ROOT)/external/tinyxml2
LIBS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib -lz -ltinyxml2 -lpthread

.PHONY: help compile
help:
	@printf '%s\n' 'Preparation only. Compilation requires a later authorized task and ALLOW_BUILD=1.'

compile:
	@test "$(ALLOW_BUILD)" = 1 || { printf '%s\n' 'Build not enabled'; exit 2; }
	python3 -B ../scripts/check_static.py --check-bound-inputs
	@test ! -e $(TARGET) || { printf '%s\n' 'Refusing to overwrite diagnostic binary'; exit 2; }
	mkdir -p ../build
	$(CXX) $(CXXFLAGS) $(INCLUDES) fine_T_diagnostic.cpp -o $(TARGET) $(LIBS)
