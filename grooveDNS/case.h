/*  case.h — SIM-EC1XT240 straight-groove DNS (minimal closed loop)
 *
 *  Purpose
 *  -------
 *  Abstract the nanostructure as a few straight grooves and compute the
 *  equivalent along-groove flow conductance B_yy from a single-phase,
 *  incompressible, Newtonian DNS.
 *
 *  Geometry (transverse cross section in x-z; flow/groove direction is y)
 *  ----------------------------------------------------------------------
 *  Explicit transverse layout (x), all segments full channel height Lz=65 nm:
 *
 *      wall | groove | wall | groove | wall
 *     120nm   120nm   120nm   120nm   120nm      -> Lx = 600 nm
 *
 *  - x is NOT periodic: the left/right outer sides are the no-slip solid walls.
 *  - y is periodic (groove/flow direction), Ly = 240 nm.
 *  - z top & bottom are no-slip solid walls (channel height Lz = 65 nm).
 *  - Fluid fills the 2 grooves only (material 1); everything else solid (2).
 *
 *  Driving: constant body force (force density) in +y, equivalent to a pressure
 *  gradient dp/dy = -f_y.
 *
 *  Constitutive model
 *  ------------------
 *    q_y = -(B_yy / mu) * dp/dy      ->      B_yy = - mu * q_y / (dp/dy)
 *    with q_y = Q_y / A_cell  [m/s]  (superficial / Darcy velocity),
 *    A_cell = Lx * Hfluid (full unit-cell cross-section incl. solid walls)
 *    => B_yy in [m^2]
 *
 *  Body-force <-> pressure-gradient equivalence:
 *    dp/dy = -rho * a_y,   a_y = F_lat * dx / dt^2   (F_lat = lattice body force)
 *    hence  B_yy = mu * q_y / (rho * a_y)
 *
 *  The driving is prescribed by the physical acceleration a_y (BODY_FORCE_ACCEL);
 *  the lattice body force is derived as F_lat = a_y * dt^2 / dx.
 *
 *  No surface tension / contact angle / free surface / VOF / imprinting motion.
 *
 *  Geometry verification mode: run with --geometry-only to stop after
 *  prepareGeometry (no lattice, no flow) and write the material field only.
 */

#include <olb.h>
#include <fstream>
#include <iomanip>

using namespace olb;
using namespace olb::names;

// --- custom parameter keys (in physical SI units unless stated otherwise) ---
namespace olb::parameters {

struct WALL_WIDTH     : public descriptors::FIELD_BASE<1> { };  // solid wall width [m] (120 nm)
struct GROOVE_WIDTH   : public descriptors::FIELD_BASE<1> { };  // fluid groove width [m] (120 nm)
struct CHANNEL_HEIGHT : public descriptors::FIELD_BASE<1> { };  // channel height Lz [m] (65 nm)
struct DOMAIN_LY      : public descriptors::FIELD_BASE<1> { };  // groove-direction length Ly [m] (240 nm)
struct NUM_GROOVES    : public descriptors::TYPED_FIELD_BASE<int,1> { }; // grooves in x (2); walls = grooves+1
struct BODY_FORCE_ACCEL : public descriptors::FIELD_BASE<1> { };  // physical acceleration a_y [m/s^2] (+y)
struct BODY_FORCE_ACCEL_X : public descriptors::FIELD_BASE<1> { }; // physical acceleration a_x [m/s^2] (+x), --CHECK_BXX mode
struct CHECK_BXX      : public descriptors::TYPED_FIELD_BASE<int,1> { }; // 0 = default B_yy, 1 = transverse blocking check

}

using MyCase = Case<
  NavierStokes, Lattice<double, descriptors::D3Q19<descriptors::FORCE>>
>;

// --- create the cuboid mesh (solid padding added top & bottom for the walls) ---
// Explicit transverse layout (x): wall | groove | wall | groove | wall,
// each segment 120 nm -> Lx = (nGrooves+1)*wall + nGrooves*groove = 600 nm.
// x is NOT periodic (left/right outer sides are the no-slip solid walls);
// y is periodic; top & bottom (z) are no-slip solid walls.
Mesh<MyCase::value_t, MyCase::d> createMesh(MyCase::ParametersD& parameters) {
  using T = MyCase::value_t;
  const T wall   = parameters.get<parameters::WALL_WIDTH>();
  const T groove = parameters.get<parameters::GROOVE_WIDTH>();
  const T H      = parameters.get<parameters::CHANNEL_HEIGHT>();  // Lz
  const T Ly     = parameters.get<parameters::DOMAIN_LY>();
  const int nG   = parameters.get<parameters::NUM_GROOVES>();
  const T dx     = parameters.get<parameters::PHYS_DELTA_X>();

  const T Lx = (nG + 1) * wall + nG * groove;   // 600 nm
  const T pad = 3. * dx;                         // solid padding above/below the fluid

  IndicatorCuboid3D<T> domain(
    Vector<T,3>{Lx, Ly, H + 2*pad},    // extend
    Vector<T,3>{0., 0., -pad}          // origin
  );

  Mesh<T, MyCase::d> mesh(domain, dx, singleton::mpi().getSize());
  mesh.setOverlap(parameters.get<parameters::OVERLAP>());
  mesh.getCuboidDecomposition().setPeriodicity({false, true, false}); // x NOT periodic, y periodic
  return mesh;
}

// --- material numbers: 1 = fluid, 2 = solid (no-slip wall) ---
void prepareGeometry(MyCase& myCase) {
  using T = MyCase::value_t;
  OstreamManager clout(std::cout, "prepareGeometry");

  auto& parameters = myCase.getParameters();
  auto& geometry   = myCase.getGeometry();

  const T wall   = parameters.get<parameters::WALL_WIDTH>();
  const T groove = parameters.get<parameters::GROOVE_WIDTH>();
  const T H      = parameters.get<parameters::CHANNEL_HEIGHT>();
  const T Ly     = parameters.get<parameters::DOMAIN_LY>();
  const int nG   = parameters.get<parameters::NUM_GROOVES>();
  const T dx     = parameters.get<parameters::PHYS_DELTA_X>();

  // everything defaults to solid (2)
  geometry.rename(0, 2);

  // carve the fluid grooves (full channel height), one per groove segment:
  //   groove g occupies cells [ x0, x0+groove ), with x0 = (g+1)*wall + g*groove.
  //
  // OpenLB nodes sit at cell *corners* (physR = origin + latticeR*dx), and
  // IndicatorCuboid3D::operator() uses a relative-epsilon tolerance.  Because a
  // cuboid bound that lands exactly on a node position can drop that boundary
  // node to floating-point round-off, we widen each fluid groove by half a node
  // on both open ends of the non-periodic directions.
  //
  // x (non-periodic): groove = [x0 - half, x0 + groove - half] -> the wall/groove
  // boundaries land *between* nodes -> exactly 24 nodes (120 nm) per groove and
  // per wall (120 nm = 24 dx at dx = 5 nm).
  //
  // z (non-periodic): groove = [-half, H + half] -> the fluid spans exactly
  // H = 65 nm (13 cells at dx = 5 nm, i.e. 14 corner nodes z = 0 .. 65 nm).  The
  // discrete liquid height is then exactly 65 nm with no snapping.
  //
  // y (periodic): groove kept FULL [0, Ly] (both periodic boundary nodes y=0
  // and y=Ly belong to the same physical point and must carry the same material).
  const T half = 0.5 * dx;
  for (int g = 0; g < nG; ++g) {
    const T x0 = (g + 1) * wall + g * groove;
    IndicatorCuboid3D<T> grooveInd(
      Vector<T,3>{groove, Ly, H + 2 * half}, Vector<T,3>{x0 - half, 0., -half});
    geometry.rename(2, 1, grooveInd);
  }

  // NOTE: no geometry.clean() here — clean() strips solid (2) that is not
  // directly adjacent to fluid, thinning the 120 nm walls to 1-node shells.
  // We keep the full solid walls so the material field shows the explicit
  // wall-groove-wall-groove-wall structure.
  geometry.innerClean();
  geometry.checkForErrors();
  geometry.print();

  clout << "Prepare Geometry ... OK" << std::endl;
}

// --- lattice: BGK dynamics on fluid, bounce-back on solid ---
void prepareLattice(MyCase& myCase) {
  OstreamManager clout(std::cout, "prepareLattice");
  using T = MyCase::value_t;
  using DESCRIPTOR = MyCase::descriptor_t_of<NavierStokes>;

  auto& parameters = myCase.getParameters();
  auto& lattice    = myCase.getLattice(NavierStokes{});
  auto& geometry   = myCase.getGeometry();

  lattice.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,DESCRIPTOR>>(
    int {parameters.get<parameters::RESOLUTION>()},               // voxels per char length
    (T)  parameters.get<parameters::LATTICE_RELAXATION_TIME>(),   // tau
    (T)  parameters.get<parameters::PHYS_CHAR_LENGTH>(),          // reference length [m]
    (T)  parameters.get<parameters::PHYS_CHAR_VELOCITY>(),        // reference velocity [m/s]
    (T)  parameters.get<parameters::PHYS_CHAR_VISCOSITY>(),       // kinematic viscosity [m^2/s]
    (T)  parameters.get<parameters::PHYS_CHAR_DENSITY>()          // density [kg/m^3]
  );
  lattice.getUnitConverter().print();

  dynamics::set<ForcedBGKdynamics>(lattice, geometry, 1);          // fluid
  boundary::set<boundary::BounceBack>(lattice, geometry, 2);       // solid no-slip

  clout << "Prepare Lattice ... OK" << std::endl;
}

// --- body force + initialization ---
void setInitialValues(MyCase& myCase) {
  using T = MyCase::value_t;
  using DESCRIPTOR = MyCase::descriptor_t_of<NavierStokes>;

  auto& parameters = myCase.getParameters();
  auto& lattice    = myCase.getLattice(NavierStokes{});
  auto& geometry   = myCase.getGeometry();
  auto& converter  = lattice.getUnitConverter();

  // prescribed physical acceleration -> lattice body force F = a * dt^2/dx.
  // Default (B_yy): +y force; --CHECK_BXX: +x force (transverse blocking check).
  const T dx = converter.getPhysDeltaX();
  const T dt = converter.getPhysDeltaT();
  Vector<T,3> force{0., 0., 0.};
  if (parameters.get<parameters::CHECK_BXX>() != 0) {
    const T ax = parameters.get<parameters::BODY_FORCE_ACCEL_X>();
    force = Vector<T,3>{ax * dt * dt / dx, 0., 0.};
  } else {
    const T ay = parameters.get<parameters::BODY_FORCE_ACCEL>();
    force = Vector<T,3>{0., ay * dt * dt / dx, 0.};
  }
  fields::set<descriptors::FORCE>(lattice, geometry.getMaterialIndicator(1), force);

  lattice.setParameter<descriptors::OMEGA>(converter.getLatticeRelaxationFrequency());
  lattice.initialize();
}

// --- one output/measurement step; returns total volumetric flow Q_y [m^3/s] ---
// The velocity/integral/max functors are constructed ONCE in simulate() and passed
// in, so the (expensive) functor-tree allocation is not repeated every step.
MyCase::value_t getResults(MyCase& myCase, std::size_t iT,
                           std::ofstream& flowFile,
                           util::ValueTracer<MyCase::value_t>& tracer,
                           SuperLatticePhysVelocity3D<MyCase::value_t,MyCase::descriptor_t_of<NavierStokes>>& velocity,
                           SuperIntegral3D<MyCase::value_t>& volIntegral,
                           SuperMax3D<MyCase::value_t>& maxVel)
{
  using T = MyCase::value_t;
  using DESCRIPTOR = MyCase::descriptor_t_of<NavierStokes>;
  OstreamManager clout(std::cout, "getResults");

  auto& parameters = myCase.getParameters();
  auto& lattice    = myCase.getLattice(NavierStokes{});
  auto& geometry   = myCase.getGeometry();
  auto& converter  = lattice.getUnitConverter();

  const T wall   = parameters.get<parameters::WALL_WIDTH>();
  const T groove = parameters.get<parameters::GROOVE_WIDTH>();
  const T Hfluid = parameters.get<parameters::CHANNEL_HEIGHT>();   // 65 nm
  const int nG   = parameters.get<parameters::NUM_GROOVES>();
  const T Lx     = (nG + 1) * wall + nG * groove;                  // 600 nm
  const T Ly     = parameters.get<parameters::DOMAIN_LY>();

  // fluid properties + driving (body force <-> pressure-gradient equivalence)
  const T rho  = converter.getPhysDensity();
  const T nu   = converter.getPhysViscosity();
  const T mu   = rho * nu;
  const T ay   = parameters.get<parameters::BODY_FORCE_ACCEL>();   // acceleration [m/s^2]

  // fluid cross-section (grooves only) and full cell cross-section
  const T A_fluid = nG * groove * Hfluid;     // [m^2]
  const T A_cell  = Lx * Hfluid;              // [m^2]

  lattice.setProcessingContext(ProcessingContext::Evaluation);

  T fluxVol[3] = {0., 0., 0.};
  T maxU[3] = {0., 0., 0.};
  int dummy[1] = {0};
  volIntegral(fluxVol, dummy);
  maxVel(maxU, dummy);

  // Q_y = (volume integral of u_y) / Ly_eff   [m^3/s], exact for y-invariant flow.
  // The y-periodic lattice stores Ly/dx + 1 nodes (the node at y = Ly is the
  // periodic image of y = 0), so SuperIntegral3D sums one extra y-layer.  The
  // effective integrated length is therefore Ly + dx; dividing by (Ly + dx)
  // recovers the 2D cross-section flux, which is independent of Ly.
  const T dx           = converter.getPhysDeltaX();
  const T Qy          = fluxVol[1] / (Ly + dx);
  const T qy          = Qy / A_cell;          // superficial (Darcy) velocity [m/s]
  const T u_fluid_avg = Qy / A_fluid;         // mean fluid velocity [m/s]
  const T u_fluid_max = maxU[1];              // max fluid y-velocity [m/s]

  // B_yy from Darcy law qy = -(B_yy/mu) dp/dy with dp/dy = -rho*ay:
  //   B_yy = mu * qy / (rho * ay)   [m^2]
  const T Byy = mu * qy / (rho * ay);

  // ---- record time series (main processor only) ----
  if (singleton::mpi().isMainProcessor()) {
    flowFile << iT << " "
             << converter.getPhysTime(iT) << " "
             << Qy << " " << qy << " "
             << u_fluid_avg << " " << u_fluid_max << " "
             << Byy << "\n";
  }

  tracer.takeValue(Qy, false);

  // ---- console ----
  const T physTime = converter.getPhysTime(iT);
  if (iT % 200 == 0 || tracer.hasConverged()) {
    clout << "iT=" << iT << " t=" << physTime
          << "  Qy=" << Qy << " m^3/s  qy=" << qy
          << " m/s  uAvg=" << u_fluid_avg
          << " m/s  uMax=" << u_fluid_max
          << " m/s  B_yy=" << Byy << " m^2" << std::endl;
  }
  return Qy;
}

// --- VTK snapshot of velocity + pressure (for the field figures) ---
void writeVtk(MyCase& myCase, std::size_t iT, const std::string& name = "grooveDns") {
  using T = MyCase::value_t;
  using DESCRIPTOR = MyCase::descriptor_t_of<NavierStokes>;
  auto& lattice   = myCase.getLattice(NavierStokes{});
  auto& converter = lattice.getUnitConverter();

  lattice.setProcessingContext(ProcessingContext::Evaluation);

  SuperVTMwriter3D<T> vtmWriter(name);
  SuperLatticePhysVelocity3D<T,DESCRIPTOR> velocity(lattice, converter);
  SuperLatticePhysPressure3D<T,DESCRIPTOR> pressure(lattice, converter);
  vtmWriter.addFunctor(velocity);
  vtmWriter.addFunctor(pressure);

  if (iT == 0) {
    vtmWriter.createMasterFile();
  }
  vtmWriter.write(iT);
}

// --- explicit material-field VTK (for geometry verification) ---
void writeMaterialVtk(MyCase& myCase) {
  using T = MyCase::value_t;
  auto& geometry = myCase.getGeometry();

  SuperVTMwriter3D<T> vtmWriter("material");
  SuperGeometryF3D<T> geometryF(geometry);
  vtmWriter.addFunctor(geometryF);
  vtmWriter.createMasterFile();
  vtmWriter.write(0);
}

void simulate(MyCase& myCase) {
  using T = MyCase::value_t;
  OstreamManager clout(std::cout, "simulate");

  auto& parameters = myCase.getParameters();
  auto& lattice    = myCase.getLattice(NavierStokes{});
  auto& converter  = lattice.getUnitConverter();

  const std::size_t iTmax   = converter.getLatticeTime(parameters.get<parameters::MAX_PHYS_T>());
  const std::size_t iTcheck = converter.getLatticeTime(parameters.get<parameters::INTERVAL_CONVERGENCE_CHECK>());
  const T epsilon = parameters.get<parameters::CONVERGENCE_PRECISION>();

  // open flow-rate time-series file
  std::ofstream flowFile;
  if (singleton::mpi().isMainProcessor()) {
    flowFile.open(singleton::directories().getLogOutDir() + "flowrate.dat");
    flowFile << std::scientific << std::setprecision(15);
    flowFile << "# iT  physTime_s  Qy_m3_per_s  qy_cell_m_per_s  "
                "u_y_fluid_average_m_per_s  u_y_fluid_max_m_per_s  B_yy_m2\n";
  }

  util::ValueTracer<T> tracer(iTcheck, epsilon, "Qy");
  util::Timer<T> timer(iTmax, myCase.getGeometry().getStatistics().getNvoxel());

  clout << "starting simulation, iTmax=" << iTmax << " ..." << std::endl;
  timer.start();

  // construct the measurement functors ONCE (avoid per-step functor-tree allocation)
  using DESCRIPTOR = MyCase::descriptor_t_of<NavierStokes>;
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  SuperLatticePhysVelocity3D<T,DESCRIPTOR> velocity(lattice, converter);
  SuperIntegral3D<T> volIntegral(velocity, myCase.getGeometry(), 1);
  SuperMax3D<T> maxVel(velocity, myCase.getGeometry(), 1);

  bool converged = false;
  for (std::size_t iT = 0; iT < iTmax; ++iT) {
    lattice.collideAndStream();

    getResults(myCase, iT, flowFile, tracer, velocity, volIntegral, maxVel);

    // VTK snapshots: initial + converged
    if (iT == 0 || tracer.hasConverged()) {
      writeVtk(myCase, iT);
    }

    if (tracer.hasConverged()) {
      converged = true;
      clout << "Simulation converged at iT=" << iT << std::endl;
      break;
    }
  }

  if (!converged) {
    clout << "Reached iTmax without full convergence; using final state." << std::endl;
    writeVtk(myCase, iTmax - 1);
  }

  timer.stop();
  timer.printSummary();

  // ---- final derived quantities: B_yy (recomputed from the converged field) ----
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  T fluxVol[3] = {0.,0.,0.}; T maxU[3] = {0.,0.,0.}; int dummy[1] = {0};
  volIntegral(fluxVol, dummy);
  maxVel(maxU, dummy);

  const T wall   = parameters.get<parameters::WALL_WIDTH>();
  const T groove = parameters.get<parameters::GROOVE_WIDTH>();
  const T Hfluid = parameters.get<parameters::CHANNEL_HEIGHT>();
  const int nG   = parameters.get<parameters::NUM_GROOVES>();
  const T Lx = (nG + 1) * wall + nG * groove;
  const T Ly = parameters.get<parameters::DOMAIN_LY>();

  const T A_fluid = nG * groove * Hfluid;     // fluid cross-section [m^2]
  const T A_cell  = Lx * Hfluid;              // cell cross-section   [m^2]

  const T dx           = converter.getPhysDeltaX();
  const T Qy          = fluxVol[1] / (Ly + dx);   // [m^3/s] (see note in getResults)
  const T qy          = Qy / A_cell;          // superficial velocity [m/s]
  const T u_fluid_avg = Qy / A_fluid;         // mean fluid velocity   [m/s]
  const T u_fluid_max = maxU[1];              // max fluid y-velocity  [m/s]

  const T rho  = converter.getPhysDensity();
  const T nu   = converter.getPhysViscosity();
  const T mu   = rho * nu;

  const T ay   = parameters.get<parameters::BODY_FORCE_ACCEL>();  // acceleration [m/s^2]
  const T dpdy = -rho * ay;                   // pressure gradient [Pa/m]
  const T Byy  = -mu * qy / dpdy;             // = mu*qy/(rho*ay) [m^2]
  const T Byy_nm2 = Byy * 1e18;               // [m^2] -> [nm^2]

  // Reynolds number: single-groove hydraulic diameter + mean fluid velocity
  const T D_h  = 2. * groove * Hfluid / (groove + Hfluid);   // [m]
  const T Re   = rho * u_fluid_avg * D_h / mu;               // [-]

  // ---- mass conservation / compressibility check ----
  // The LBM is weakly compressible: the lattice density rho deviates from the
  // incompressible reference rho0 = 1 by O(Ma^2).  Report the maximum relative
  // density deviation over the fluid region as the "mass relative error".
  SuperLatticeDensity3D<T,DESCRIPTOR> density(lattice);
  SuperMax3D<T> maxRho(density, myCase.getGeometry(), 1);
  SuperMin3D<T> minRho(density, myCase.getGeometry(), 1);
  T rhoMax[1] = {0.}, rhoMin[1] = {0.}; int dm[1] = {0};
  maxRho(rhoMax, dm);
  minRho(rhoMin, dm);
  const T massRelErr = std::max(std::abs(rhoMax[0] - 1.0),
                                std::abs(rhoMin[0] - 1.0));

  clout << "\n===== RESULT (body-force-driven equivalent) =====" << std::endl;
  clout << "a_y (prescribed)     [m/s^2]     = " << ay << std::endl;
  clout << "rho*a_y = -dp/dy     [Pa/m]      = " << rho*ay << std::endl;
  clout << "dp/dy = -rho*a_y     [Pa/m]      = " << dpdy << std::endl;
  clout << "Q_y  [m^3/s]                      = " << Qy << std::endl;
  clout << "q_y  [m/s]                        = " << qy << std::endl;
  clout << "u_y_fluid_average [m/s]           = " << u_fluid_avg << std::endl;
  clout << "u_y_fluid_max     [m/s]           = " << u_fluid_max << std::endl;
  clout << "Re (D_h, u_fluid_avg)  [-]        = " << Re << std::endl;
  clout << "mu   [Pa.s]                       = " << mu << std::endl;
  clout << "mass_relative_error    [-]        = " << massRelErr << std::endl;
  clout << "B_yy [m^2]                        = " << Byy << std::endl;
  clout << "B_yy [nm^2]                       = " << Byy_nm2 << std::endl;
  clout << "==================================================" << std::endl;

  // ---- write the formal results file (single source of truth) ----
  if (singleton::mpi().isMainProcessor()) {
    std::ofstream res(singleton::directories().getLogOutDir() + "final_results_fine.txt");
    res << std::scientific << std::setprecision(15);
    res << "Qy_m3_per_s                = " << Qy          << "\n";
    res << "qy_cell_m_per_s            = " << qy          << "\n";
    res << "u_y_fluid_average_m_per_s  = " << u_fluid_avg << "\n";
    res << "u_y_fluid_max_m_per_s      = " << u_fluid_max << "\n";
    res << "Re                         = " << Re          << "\n";
    res << "mass_relative_error        = " << massRelErr   << "\n";
    res << "B_yy_m2                    = " << Byy         << "\n";
    res << "B_yy_nm2                   = " << Byy_nm2     << "\n";
    res.close();
    clout << "Wrote formal results to final_results_fine.txt" << std::endl;
  }
}

// --- transverse blocking check (B_xx): apply +x body force and verify that the
//     continuous solid walls block any net transverse flow ---------------------
// The straight grooves are separated along x by continuous (y-invariant) solid
// walls, so x-flow is blocked and the exact steady state is u = 0 everywhere
// (hydrostatic equilibrium: grad p = rho * a_x).  We drive with a_x and measure
// the residual Qx / qx, which should be ~0 to machine precision.  B_xx_num =
// mu*qx/(rho*a_x) is therefore a numerical-residual upper bound, NOT a physical
// transverse conductance (whose ideal value is B_xx = 0).
void simulateCheckBxx(MyCase& myCase) {
  using T = MyCase::value_t;
  using DESCRIPTOR = MyCase::descriptor_t_of<NavierStokes>;
  OstreamManager clout(std::cout, "simulateCheckBxx");

  auto& parameters = myCase.getParameters();
  auto& lattice    = myCase.getLattice(NavierStokes{});
  auto& converter  = lattice.getUnitConverter();

  // geometry cross-sections (identical to the B_yy run)
  const T wall   = parameters.get<parameters::WALL_WIDTH>();
  const T groove = parameters.get<parameters::GROOVE_WIDTH>();
  const T Hfluid = parameters.get<parameters::CHANNEL_HEIGHT>();
  const int nG   = parameters.get<parameters::NUM_GROOVES>();
  const T Lx     = (nG + 1) * wall + nG * groove;   // 600 nm
  const T Ly     = parameters.get<parameters::DOMAIN_LY>();
  const T A_cell = Lx * Hfluid;                     // full unit-cell cross-section [m^2]
  const T dx     = converter.getPhysDeltaX();

  // fluid properties + driving
  const T rho = converter.getPhysDensity();
  const T nu  = converter.getPhysViscosity();
  const T mu  = rho * nu;
  const T ax  = parameters.get<parameters::BODY_FORCE_ACCEL_X>();   // +x [m/s^2]

  // Fixed number of lattice steps.  A ValueTracer is deliberately NOT used here:
  // the measured signal (u_x) decays to machine zero, so stdDev/average -> 0/0
  // (NaN) and the tracer would spuriously throw "diverged".  The blocked flow
  // reaches hydrostatic equilibrium in a few thousand steps; 20000 is a safe margin.
  const std::size_t iTmax = 20000;

  std::ofstream flowFile;
  if (singleton::mpi().isMainProcessor()) {
    flowFile.open(singleton::directories().getLogOutDir() + "flowrate_bxx.dat");
    flowFile << std::scientific << std::setprecision(15);
    flowFile << "# iT  physTime_s  Qx_m3_per_s  qx_cell_m_per_s  max_abs_ux_m_per_s\n";
  }

  util::Timer<T> timer(iTmax, myCase.getGeometry().getStatistics().getNvoxel());
  clout << "starting CHECK_BXX (transverse blocking) simulation, iTmax="
        << iTmax << " ..." << std::endl;
  timer.start();

  // construct the measurement functors ONCE
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  SuperLatticePhysVelocity3D<T,DESCRIPTOR> velocity(lattice, converter);
  SuperIntegral3D<T> volIntegral(velocity, myCase.getGeometry(), 1);
  SuperMax3D<T> maxVel(velocity, myCase.getGeometry(), 1);
  SuperMin3D<T> minVel(velocity, myCase.getGeometry(), 1);

  for (std::size_t iT = 0; iT < iTmax; ++iT) {
    lattice.collideAndStream();

    lattice.setProcessingContext(ProcessingContext::Evaluation);
    T fluxVol[3] = {0.,0.,0.}; T maxU[3] = {0.,0.,0.}; T minU[3] = {0.,0.,0.};
    int dummy[1] = {0};
    volIntegral(fluxVol, dummy);
    maxVel(maxU, dummy);
    minVel(minU, dummy);

    // Qx = (volume integral of u_x) / (Ly + dx)   [m^3/s]  (see note in getResults)
    const T Qx  = fluxVol[0] / (Ly + dx);
    const T qx  = Qx / A_cell;                       // superficial velocity [m/s]
    const T max_abs_ux = std::max(std::abs(maxU[0]), std::abs(minU[0]));

    if (singleton::mpi().isMainProcessor()) {
      flowFile << iT << " " << converter.getPhysTime(iT) << " "
               << Qx << " " << qx << " " << max_abs_ux << "\n";
    }

    if (iT % 500 == 0) {
      clout << "iT=" << iT << " t=" << converter.getPhysTime(iT)
            << "  Qx=" << Qx << " m^3/s  qx=" << qx
            << " m/s  max|ux|=" << max_abs_ux << " m/s" << std::endl;
    }

    // VTK snapshots: initial + final
    if (iT == 0 || iT == iTmax - 1) {
      writeVtk(myCase, iT, "grooveDnsBxx");
    }
  }

  timer.stop();
  timer.printSummary();

  // ---- final measurement (from the last field) ----
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  T fluxVol[3] = {0.,0.,0.}; T maxU[3] = {0.,0.,0.}; T minU[3] = {0.,0.,0.};
  int dummy[1] = {0};
  volIntegral(fluxVol, dummy);
  maxVel(maxU, dummy);
  minVel(minU, dummy);

  const T Qx  = fluxVol[0] / (Ly + dx);
  const T qx  = Qx / A_cell;
  const T max_abs_ux = std::max(std::abs(maxU[0]), std::abs(minU[0]));

  // numerical residual upper bound for B_xx (NOT a physical conductance)
  const T Bxx_num = mu * qx / (rho * ax);

  // mass conservation / compressibility check (same definition as the B_yy run)
  SuperLatticeDensity3D<T,DESCRIPTOR> density(lattice);
  SuperMax3D<T> maxRho(density, myCase.getGeometry(), 1);
  SuperMin3D<T> minRho(density, myCase.getGeometry(), 1);
  T rhoMax[1] = {0.}, rhoMin[1] = {0.}; int dm[1] = {0};
  maxRho(rhoMax, dm);
  minRho(rhoMin, dm);
  const T massRelErr = std::max(std::abs(rhoMax[0] - 1.0),
                                std::abs(rhoMin[0] - 1.0));

  // conclusion: qx ~ machine precision relative to the ~1e-4 m/s unblocked scale
  const T qx_tol = 1e-13;   // [m/s]
  std::string conclusion;
  if (std::abs(qx) < qx_tol) {
    conclusion = "B_xx = 0 within numerical tolerance";
  } else {
    conclusion = "B_xx numerical residual is nonzero (above tolerance)";
  }

  clout << "\n===== CHECK_BXX RESULT (transverse blocking) =====" << std::endl;
  clout << "a_x (prescribed)     [m/s^2]     = " << ax << std::endl;
  clout << "Qx  [m^3/s]                       = " << Qx << std::endl;
  clout << "qx  [m/s]                         = " << qx << std::endl;
  clout << "max_abs_ux  [m/s]                 = " << max_abs_ux << std::endl;
  clout << "mass_relative_error   [-]         = " << massRelErr << std::endl;
  clout << "B_xx numerical residual [m^2]     = " << Bxx_num << std::endl;
  clout << "B_xx conclusion                   = " << conclusion << std::endl;
  clout << "==================================================" << std::endl;

  if (singleton::mpi().isMainProcessor()) {
    std::ofstream res(singleton::directories().getLogOutDir() + "bxx_blocking_results.txt");
    res << std::scientific << std::setprecision(15);
    res << "Qx_m3_per_s               = " << Qx          << "\n";
    res << "qx_cell_m_per_s           = " << qx          << "\n";
    res << "max_abs_ux_m_per_s        = " << max_abs_ux  << "\n";
    res << "mass_relative_error       = " << massRelErr  << "\n";
    res << "B_xx_numerical_residual_m2 = " << Bxx_num    << "\n";
    res << "B_xx_conclusion           = " << conclusion  << "\n";
    res.close();
    clout << "Wrote CHECK_BXX results to bxx_blocking_results.txt" << std::endl;
  }
}

void setDefaultParameters(MyCase::ParametersD& params) {
  using namespace olb::parameters;

  // geometry (nanometers -> SI): wall | groove | wall | groove | wall
  params.set<WALL_WIDTH    >(120e-9);
  params.set<GROOVE_WIDTH  >(120e-9);
  params.set<CHANNEL_HEIGHT>( 65e-9);   // Lz
  params.set<DOMAIN_LY     >(240e-9);   // Ly
  params.set<NUM_GROOVES   >(2);        // 2 grooves, 3 walls -> Lx = 600 nm

  // fluid (water-like)
  params.set<PHYS_CHAR_DENSITY  >(1000.0);   // kg/m^3
  params.set<PHYS_CHAR_VISCOSITY>(1.0e-6);   // m^2/s (kinematic)

  // driving (physical acceleration a_y; the lattice body force is derived from it)
  params.set<BODY_FORCE_ACCEL>(1.0e8);       // a_y [m/s^2] in +y (default = highest sweep value)
  params.set<BODY_FORCE_ACCEL_X>(1.0e6);     // a_x [m/s^2] in +x (used only by --CHECK_BXX)
  params.set<CHECK_BXX>(0);                  // 0 = default B_yy; 1 = transverse blocking check

  // numerics / discretization
  // dx = 5 nm divides 120 nm (->24 nodes) and 65 nm (->13 nodes) into integer
  // node counts, so the wall/groove/height geometry is exact (no snapping).
  params.set<RESOLUTION>(48);                 // voxels per char length -> dx = 5 nm
  params.set<PHYS_CHAR_LENGTH>(240e-9);       // reference length (wall + groove)
  params.set<PHYS_CHAR_VELOCITY>(1.0);        // reference only (does not set the driving)
  params.set<LATTICE_RELAXATION_TIME>(1.0);   // tau = 1.0
  params.set<OVERLAP>(3);

  // time control (physical seconds; dt ~ 4.2e-12 s)
  params.set<MAX_PHYS_T>(3.0e-7);             // ~72000 steps safety cap
  params.set<INTERVAL_CONVERGENCE_CHECK>(1.2e-8); // ~2900 steps
  params.set<CONVERGENCE_PRECISION>(1.0e-6);
  params.set<PHYS_VTK_ITER_T>(3.0e-8);

  params.set<PHYS_DELTA_X>([&]{
    return params.get<PHYS_CHAR_LENGTH>() / params.get<RESOLUTION>();
  });
}
