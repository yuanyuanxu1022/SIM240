EXAMPLE = stage3Minimal
OLB_ROOT := /home/dell/openlb
include $(OLB_ROOT)/default.mk

stage3MinimalSmag: stage3MinimalSmag.o
	$(CXX) stage3MinimalSmag.o -o $@ -lolbcore $(LDFLAGS)

stage3MinimalSmag.o: stage3Minimal.cpp stage3MinimalCase.h dropletStatistics.h dropletInitializer.h
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -DSTAGE3_USE_SMAGORINSKY -c stage3Minimal.cpp -o $@

stage3MinimalRes96: stage3MinimalRes96.o
	$(CXX) stage3MinimalRes96.o -o $@ -lolbcore $(LDFLAGS)

stage3MinimalRes96.o: stage3Minimal.cpp stage3MinimalCase.h dropletStatistics.h dropletInitializer.h
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -DSTAGE3_RESOLUTION_96 -c stage3Minimal.cpp -o $@
