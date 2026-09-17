/*  grooveDns.cpp — main entry for the SIM-EC1XT240 abstract straight-groove DNS.
 *
 *  Minimal closed loop: steady, single-phase, incompressible, Newtonian flow
 *  along straight grooves driven by a constant body force; computes B_yy.
 */

#include <olb.h>
#include "auditCase.h"
#include "massFluxAudit.h"

using namespace olb;

int main(int argc, char* argv[]) {
  OstreamManager clout(std::cout, "main");

  initialize(&argc, &argv);

  // geometry-only mode: generate + write the material field, no lattice/flow.
  bool geometryOnly = false;
  for (int i = 1; i < argc; ++i) {
    if (std::string(argv[i]) == "--geometry-only") {
      geometryOnly = true;
    }
  }

  MyCase::ParametersD params;
  setDefaultParameters(params);
  params.fromCLI(argc, argv);

  // separate output dir for geometry verification so it never mixes with DNS output
  singleton::directories().setOutputDir(geometryOnly ? "./verify/" : "./output/");

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

  simulate(myCase);

  return 0;
}
