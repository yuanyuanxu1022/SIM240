EXAMPLE = movingPistonT0
OLB_ROOT := /home/dell/openlb
include $(OLB_ROOT)/default.mk

freeSphereRes96: freeSphereRes96.o
	$(CXX) freeSphereRes96.o -o $@ -lolbcore $(LDFLAGS)

freeSphereRes96.o: freeSphereMinimal.cpp stage3FreeSphereCase.h dropletStatistics.h dropletInitializer.h
	$(CXX) $(CXXFLAGS) $(INCLUDE_FLAGS) -DFREE_SPHERE_RES96 -c freeSphereMinimal.cpp -o $@
