CASE_ROOT := ..
BASE_CASE := ../../G2_EX240_single_period_transport
BASE_SOURCE := $(BASE_CASE)/src/g2_ex240_single_period_transport.cpp
OLB_ROOT := /home/dell/openlb
BUILD_DIR := $(CASE_ROOT)/build

SOURCE_5E4 := $(BUILD_DIR)/g2_ex240_a5e4.cpp
SOURCE_2E5 := $(BUILD_DIR)/g2_ex240_a2e5.cpp
TARGET_5E4 := $(BUILD_DIR)/g2_ex240_a5e4
TARGET_2E5 := $(BUILD_DIR)/g2_ex240_a2e5
OBJECT_5E4 := $(BUILD_DIR)/g2_ex240_a5e4.o
OBJECT_2E5 := $(BUILD_DIR)/g2_ex240_a2e5.o

CXX := mpic++
CXXFLAGS := -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION=\"5953d8a-dirty\" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
INCLUDE_FLAGS := -I$(OLB_ROOT)/src -I$(OLB_ROOT)/external/zlib \
  -I$(OLB_ROOT)/external/tinyxml2
LDFLAGS := -L$(OLB_ROOT)/build/lib -lolbcore -L$(OLB_ROOT)/external/lib \
  -lz -ltinyxml2 -lpthread

.PHONY: all clean verify-deltas

all: $(TARGET_5E4) $(TARGET_2E5) verify-deltas

$(BUILD_DIR):
	mkdir -p $@

$(SOURCE_5E4): $(BASE_SOURCE) | $(BUILD_DIR)
	sed 's/constexpr T acceleration = 1\.0e5;/constexpr T acceleration = 5.0e4;/' $< > $@

$(SOURCE_2E5): $(BASE_SOURCE) | $(BUILD_DIR)
	sed 's/constexpr T acceleration = 1\.0e5;/constexpr T acceleration = 2.0e5;/' $< > $@

$(OBJECT_5E4): $(SOURCE_5E4)
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -c $< -o $@

$(OBJECT_2E5): $(SOURCE_2E5)
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -c $< -o $@

$(TARGET_5E4): $(OBJECT_5E4)
	$(CXX) $< -o $@ $(LDFLAGS)

$(TARGET_2E5): $(OBJECT_2E5)
	$(CXX) $< -o $@ $(LDFLAGS)

verify-deltas: $(SOURCE_5E4) $(SOURCE_2E5)
	@diff_count_5e4=$$(diff -U0 $(BASE_SOURCE) $(SOURCE_5E4) | grep -E '^[+-]constexpr T acceleration' | wc -l); \
	diff_count_2e5=$$(diff -U0 $(BASE_SOURCE) $(SOURCE_2E5) | grep -E '^[+-]constexpr T acceleration' | wc -l); \
	test "$$diff_count_5e4" -eq 2; test "$$diff_count_2e5" -eq 2

clean:
	$(RM) $(SOURCE_5E4) $(SOURCE_2E5) $(OBJECT_5E4) $(OBJECT_2E5) \
	  $(TARGET_5E4) $(TARGET_2E5)
