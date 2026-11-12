CXX := mpic++
OLB_ROOT := /home/dell/openlb
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 -pthread -DPARALLEL_MODE_MPI -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double -DOLB_VERSION=\"882924a9cfc8dcdf82909e39530789cb6f5ebcc4\"
INCLUDES := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib -I$(OLB_ROOT)/external/tinyxml2
LIBS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib -lz -ltinyxml2 -lpthread
.PHONY: compile
compile:
	@test ! -e ../build/fine_T_statfix_C || { printf '%s\n' 'Refuse binary overwrite'; exit 2; }
	mkdir -p ../build
	$(CXX) $(CXXFLAGS) $(INCLUDES) fine_T_statfix_C.cpp -o ../build/fine_T_statfix_C $(LIBS)
