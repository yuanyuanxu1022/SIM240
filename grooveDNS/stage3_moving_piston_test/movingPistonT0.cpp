#include <olb.h>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <regex>
#include <stdexcept>
#include <string>
#include "movingPistonT0Case.h"
#include "dropletStatistics.h"

using T = Stage3Case::value_t;

struct Options {
  std::string runId;
  T sigma=0;
  T dtScale=1;
  T charLatticeVelocity=0.0008333333333333333;
  std::size_t maxSteps=100, statInterval=10, vtkInterval=50;
};

Options parseOptions(int argc,char** argv) {
  Options o;
  for (int i=1;i<argc;++i) {
    const std::string a=argv[i];
    auto value=[&]() -> std::string {
      if (++i>=argc) throw std::runtime_error("missing value after "+a);
      return argv[i];
    };
    if (a=="--run-id") o.runId=value();
    else if (a=="--sigma") o.sigma=std::stod(value());
    else if (a=="--dt-scale") o.dtScale=std::stod(value());
    else if (a=="--char-lattice-velocity") o.charLatticeVelocity=std::stod(value());
    else if (a=="--max-steps") o.maxSteps=std::stoull(value());
    else if (a=="--stat-interval") o.statInterval=std::stoull(value());
    else if (a=="--vtk-interval") o.vtkInterval=std::stoull(value());
  }
  if (!std::regex_match(o.runId,std::regex("[A-Za-z0-9][A-Za-z0-9_-]*")))
    throw std::runtime_error("--run-id is required and must match [A-Za-z0-9][A-Za-z0-9_-]*");
  if (o.statInterval==0 || o.vtkInterval==0) throw std::runtime_error("intervals must be positive");
  if (!(o.dtScale>0)) throw std::runtime_error("dt-scale must be positive");
  return o;
}

void writeVtk(Stage3Case& c,std::size_t iT) {
  using DESCRIPTOR=Stage3Case::descriptor_t_of<NavierStokes>;
  auto& lattice=c.getLattice(NavierStokes{});
  auto& conv=lattice.getUnitConverter();
  lattice.setProcessingContext(ProcessingContext::Evaluation);
  SuperVTMwriter3D<T> writer("stage3FreeSphere");
  SuperLatticePhysVelocity3D<T,DESCRIPTOR> velocity(lattice,conv);
  SuperLatticePhysPressure3D<T,DESCRIPTOR> pressure(lattice,conv);
  SuperLatticeExternalScalarField3D<T,DESCRIPTOR,FreeSurface::EPSILON> eps(lattice);
  SuperLatticeExternalScalarField3D<T,DESCRIPTOR,FreeSurface::CELL_TYPE> type(lattice);
  SuperLatticeExternalScalarField3D<T,DESCRIPTOR,FreeSurface::MASS> mass(lattice);
  writer.addFunctor(velocity,"Velocity"); writer.addFunctor(pressure,"Pressure");
  writer.addFunctor(eps,"Epsilon"); writer.addFunctor(type,"CellType");
  writer.addFunctor(mass,"Mass");
  if (iT==0) writer.createMasterFile();
  writer.write(iT);
}

int main(int argc,char** argv) {
  initialize(&argc,&argv);
  if (singleton::mpi().getSize()!=1) {
    std::cerr << "stage3FreeSphere currently requires one MPI rank\n"; return 2;
  }
  Options opt;
  try { opt=parseOptions(argc,argv); }
  catch (const std::exception& e) { std::cerr<<e.what()<<"\n"; return 2; }

  const std::filesystem::path out=std::filesystem::path("output")/opt.runId;
  if (std::filesystem::exists(out)) { std::cerr<<"output exists: "<<out<<"\n"; return 2; }
  std::filesystem::create_directories(out);
  singleton::directories().setOutputDir((out.string()+"/").c_str());

  Stage3Case::ParametersD p;
  p.set<parameters::DOMAIN_EXTENT>({240e-9,240e-9,200e-9});
  p.set<parameters::DROPLET_RADIUS>(60e-9);
  p.set<parameters::SURFACE_TENSION>(opt.sigma);
  p.set<parameters::DT_SCALE>(1.0);
  p.set<parameters::CHAR_LATTICE_VELOCITY>(opt.charLatticeVelocity);
  p.set<parameters::RESOLUTION>(
#ifdef FREE_SPHERE_RES96
    96
#else
    48
#endif
  );
  p.set<parameters::PHYS_CHAR_LENGTH>(240e-9);
  p.set<parameters::PHYS_CHAR_VELOCITY>(1.0);
  p.set<parameters::PHYS_CHAR_VISCOSITY>(1e-6);
  p.set<parameters::PHYS_CHAR_DENSITY>(1000.0);
  p.set<parameters::LATTICE_RELAXATION_TIME>(1.0);
  p.set<parameters::OVERLAP>(3);
  p.set<parameters::PHYS_DELTA_X>([&]{return p.get<parameters::PHYS_CHAR_LENGTH>()/p.get<parameters::RESOLUTION>();});

  Mesh mesh=createMinimalMesh(p);
  Stage3Case c(p,mesh);
  prepareMinimalGeometry(c);
  prepareMinimalLattice(c);
  auto& lattice=c.getLattice(NavierStokes{});
  const auto& conv=lattice.getUnitConverter();
  conv.print();

  const T radius=p.get<parameters::DROPLET_RADIUS>();
  const T analytic=T(4)/T(3)*std::acos(T(-1))*radius*radius*radius;
  const DropletStats initial=sampleDroplet(c);
  std::ofstream params(out/"parameters.txt");
  params<<std::scientific<<std::setprecision(15)
        <<"domain_m = 2.4e-7 2.4e-7 2.0e-7\n"
        <<"radius_m = "<<radius<<"\ndx_m = "<<conv.getPhysDeltaX()
        <<"\ndt_s = "<<conv.getPhysDeltaT()<<"\nsigma_N_per_m = "<<opt.sigma
        <<"\nchar_lattice_velocity = "<<opt.charLatticeVelocity
        <<"\ntau = "<<conv.getLatticeRelaxationTime()
        <<"\nmach = "<<opt.charLatticeVelocity/std::sqrt(1.0/3.0)
        <<"\nphysical_re = "<<(1.0*240e-9/1e-6)
        <<"\nlattice_re = "<<(opt.charLatticeVelocity*240e-9/conv.getPhysDeltaX()/((conv.getLatticeRelaxationTime()-0.5)/3.0))
        <<"\nsigma_lattice = "<<(std::pow(conv.getConversionFactorTime(),2)/(conv.getPhysDensity()*std::pow(conv.getPhysDeltaX(),3))*opt.sigma)
        <<"\nperiodicity = false true false\ncontact_angle_control = not_implemented\n";
  std::ofstream init(out/"initialization_summary.txt");
  init<<std::scientific<<std::setprecision(15)
      <<"analytic_full_sphere_volume_m3 = "<<analytic<<"\n"
      <<"discrete_epsilon_volume_m3 = "<<initial.volume<<"\n"
      <<"relative_discretization_error = "<<(initial.volume-analytic)/analytic<<"\n"
      <<"initial_mass_lattice = "<<initial.mass<<"\n";

  std::ofstream csv(out/"statistics.csv");
  csv<<"step,time_s,sigma_N_per_m,analytic_volume_m3,epsilon_volume_m3,epsilon_volume_rel_drift,liquid_mass_lattice,liquid_mass_rel_drift,max_abs_u_m_per_s,max_wall_adjacent_u_m_per_s,max_wall_normal_u_m_per_s,n_fluid,n_interface,n_gas,n_solid,center_x_m,center_y_m,center_z_m,bbox_xmin_m,bbox_xmax_m,bbox_ymin_m,bbox_ymax_m,bbox_zmin_m,bbox_zmax_m,nan_found,interface_fragment_count,largest_interface_component_cells,fragmented\n";
  csv<<std::scientific<<std::setprecision(15);
  bool failed=false;
  auto writeNan=[&](const DropletStats& s, std::size_t step) {
    std::ofstream f(out/"nan_diagnostic.txt", std::ios::app);
    f<<"first_or_detected_step = "<<step<<"\nfield = "<<s.nanField
     <<"\nrank = "<<s.nanRank<<"\ncuboid = "<<s.nanCuboid
     <<"\ncell_i = "<<s.nanCell[0]<<" "<<s.nanCell[1]<<" "<<s.nanCell[2]
     <<"\nvalue = "<<s.nanValue<<"\nfinite_range_seen = "<<s.fieldMin<<" "<<s.fieldMax
     <<"\nneighbor_material_context = inspect geometry around reported cell\n";
  };
  for (std::size_t iT=0;iT<=opt.maxSteps;++iT) {
    if (iT%opt.statInterval==0 || iT==opt.maxSteps) {
      const auto s=sampleDroplet(c);
      const double cx=s.weight?s.weightedX/s.weight:0, cy=s.weight?s.weightedY/s.weight:0, cz=s.weight?s.weightedZ/s.weight:0;
      const double vd=initial.volume?(s.volume-initial.volume)/initial.volume:0;
      const double md=initial.mass?(s.mass-initial.mass)/initial.mass:0;
      csv<<iT<<","<<conv.getPhysTime(iT)<<","<<opt.sigma<<","<<analytic<<","<<s.volume<<","<<vd<<","<<s.mass<<","<<md<<","<<s.maxU<<","<<s.maxWallAdjacentU<<","<<s.maxWallNormalU<<","<<s.nFluid<<","<<s.nInterface<<","<<s.nGas<<","<<s.nSolid<<","<<cx<<","<<cy<<","<<cz<<","<<s.xmin<<","<<s.xmax<<","<<s.ymin<<","<<s.ymax<<","<<s.zmin<<","<<s.zmax<<","<<s.nanFound<<","<<s.interfaceFragments<<","<<s.largestInterfaceFragment<<","<<s.fragmented<<"\n";
      failed = failed || s.nanFound || s.weight==0 || s.fragmented;
      if (s.nanFound && !std::filesystem::exists(out/"nan_diagnostic.txt")) writeNan(s,iT);
    }
    if (iT%opt.vtkInterval==0 || iT==opt.maxSteps) writeVtk(c,iT);
    if (failed || iT==opt.maxSteps) break;
    lattice.collideAndStream();
  }
  std::ofstream summary(out/"validation_summary.txt");
  summary<<"status = "<<(failed?"failed":"completed")<<"\ncontact_angle_control = not_implemented\n"
         <<"trapped_air = not_implemented\ninterface_fragmentation = 26_neighbor_with_y_periodic_wrap\n";
  return failed?1:0;
}
