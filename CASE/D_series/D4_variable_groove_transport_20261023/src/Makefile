CASE_ROOT := ..
OLB_ROOT ?= /home/dell/openlb
OLB_COMMIT := $(shell git -C $(OLB_ROOT) rev-parse --short=12 HEAD)
TARGET := $(CASE_ROOT)/build/variable_groove_transport
OBJECT := $(CASE_ROOT)/build/variable_groove_transport.o
CXX := mpic++
CXXFLAGS := -O3 -Wall -Wextra -march=native -mtune=native -std=c++20 \
 -DOLB_VERSION=\"$(OLB_COMMIT)\" -pthread -DPARALLEL_MODE_MPI \
 -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDES := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib -I$(OLB_ROOT)/external/tinyxml2
LIBS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib -lz -ltinyxml2 -lpthread
.PHONY: all
all: $(TARGET)
$(TARGET): $(OBJECT)
	$(CXX) $(OBJECT) -o $@ $(LIBS)
$(OBJECT): variable_groove_transport.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -MMD -MP -MF $(OBJECT:.o=.d) -c $< -o $@
-include $(OBJECT:.o=.d)
