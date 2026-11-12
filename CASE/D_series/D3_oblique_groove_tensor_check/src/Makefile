CASE_ROOT := ..
OLB_ROOT := /home/dell/openlb
TARGET := $(CASE_ROOT)/build/d3_oblique_groove_tensor_check
OBJECT := $(CASE_ROOT)/build/d3_oblique_groove_tensor_check.o
DEPEND := $(CASE_ROOT)/build/d3_oblique_groove_tensor_check.d
SOURCE := d3_oblique_groove_tensor_check.cpp

CXX := mpic++
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION=\"5953d8a-dirty\" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDE_FLAGS := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib \
  -I$(OLB_ROOT)/external/tinyxml2
LDFLAGS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib \
  -lz -ltinyxml2 -lpthread

.PHONY: all clean dry-run

all: $(TARGET)

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
