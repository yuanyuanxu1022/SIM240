CXX = mpic++
CXXFLAGS ?= -O3 -std=c++20 -DOLB_VERSION=\"5953d8a-dirty\" -DPARALLEL_MODE_MPI -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
OLB_ROOT ?= /home/dell/openlb
all: twoSectionFluxShort
twoSectionFluxShort: twoSectionFluxShort.cpp auditCase.h
	$(CXX) $(CXXFLAGS) -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib -I$(OLB_ROOT)/external/tinyxml2 twoSectionFluxShort.cpp -L$(OLB_ROOT)/build/lib -L$(OLB_ROOT)/external/lib -lolbcore -lpthread -lz -ltinyxml2 -o $@
