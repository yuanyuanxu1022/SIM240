/*  grooveDns.cpp — main entry for the SIM-EC1XT240 abstract straight-groove DNS.
 *
 *  Minimal closed loop: steady, single-phase, incompressible, Newtonian flow
 *  along straight grooves driven by a constant body force; computes B_yy.
 */

#include <olb.h>
#include "case.h"

using namespace olb;

int main(int argc, char* argv[]) {
  OstreamManager clout(std::cout, "main");

  initialize(&argc, &argv);

  // geometry-only mode: generate + write the material field, no lattice/flow.
  bool geometryOnly = false;
  // transverse blocking check mode: apply +x body force and verify B_xx = 0.
  bool checkBxx = false;
  for (int i = 1; i < argc; ++i) {
    if (std::string(argv[i]) == "--geometry-only") {
      geometryOnly = true;
    } else if (std::string(argv[i]) == "--CHECK_BXX") {
      checkBxx = true;
    }
  }

  MyCase::ParametersD params;
  setDefaultParameters(params);
  params.fromCLI(argc, argv);
  if (checkBxx) {
    params.set<olb::parameters::CHECK_BXX>(1);
  }

  // separate output dir for geometry verification so it never mixes with DNS output
  singleton::directories().setOutputDir(geometryOnly ? "./verify/" : "./tmp/");

  Mesh mesh = createMesh(params);

  MyCase myCase(params, mesh);

  prepareGeometry(myCase);

  if (geometryOnly) {
    writeMaterialVtk(myCase);
    clout << "Geometry-only mode: material field written to verify/, "
          << "stopping before lattice/flow." << std::endl;
    return 0;
  }

  prepareLattice(myCase);
  setInitialValues(myCase);

  if (checkBxx) {
    simulateCheckBxx(myCase);
  } else {
    simulate(myCase);
  }

  return 0;
}
