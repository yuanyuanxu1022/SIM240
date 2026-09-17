CASE_ROOT := ..
OLB_ROOT := /home/dell/openlb
TARGET := $(CASE_ROOT)/build/case01_geometry_check
OBJECT := $(CASE_ROOT)/build/case01_geometry_check.o
DEPEND := $(CASE_ROOT)/build/case01_geometry_check.d
SOURCE := case01_geometry_check.cpp
FORMAL_TARGET := $(CASE_ROOT)/build/case01_poiseuille
FORMAL_OBJECT := $(CASE_ROOT)/build/case01_poiseuille.o
FORMAL_DEPEND := $(CASE_ROOT)/build/case01_poiseuille.d
FORMAL_SOURCE := case01_poiseuille.cpp

CXX := mpic++
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION=\"5953d8a-dirty\" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDE_FLAGS := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib \
  -I$(OLB_ROOT)/external/tinyxml2
LDFLAGS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib \
  -lz -ltinyxml2 -lpthread

.PHONY: all clean dry-run

all: $(TARGET) $(FORMAL_TARGET)

$(TARGET): $(OBJECT)
	$(CXX) $(OBJECT) -o $@ $(LDFLAGS)

$(OBJECT): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -MMD -MP -MF $(DEPEND) -c $< -o $@

$(FORMAL_TARGET): $(FORMAL_OBJECT)
	$(CXX) $(FORMAL_OBJECT) -o $@ $(LDFLAGS)

$(FORMAL_OBJECT): $(FORMAL_SOURCE)
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -MMD -MP -MF $(FORMAL_DEPEND) -c $< -o $@

dry-run:
	$(MAKE) --dry-run all

clean:
	$(RM) $(TARGET) $(OBJECT) $(DEPEND) $(FORMAL_TARGET) $(FORMAL_OBJECT) $(FORMAL_DEPEND)

-include $(DEPEND) $(FORMAL_DEPEND)
