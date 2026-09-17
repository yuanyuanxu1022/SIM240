#ifndef STAGE3_MINIMAL_CASE_H
#define STAGE3_MINIMAL_CASE_H

#include <olb.h>
#include "dropletInitializer.h"

using namespace olb;
using namespace olb::names;
using namespace olb::descriptors;

using Stage3Case = Case<
  NavierStokes,
  Lattice<double, descriptors::D3Q27<descriptors::FORCE,
    FreeSurface::MASS,
    FreeSurface::EPSILON,
    FreeSurface::CELL_TYPE,
    FreeSurface::CELL_FLAGS,
    FreeSurface::TEMP_MASS_EXCHANGE,
    FreeSurface::PREVIOUS_VELOCITY,
    FreeSurface::HAS_INTERFACE_NBRS>>
>;

namespace olb::parameters {
struct DROPLET_RADIUS : public descriptors::FIELD_BASE<1> { };
}

inline Mesh<Stage3Case::value_t,Stage3Case::d>
createMinimalMesh(Stage3Case::ParametersD& params)
{
  using T = Stage3Case::value_t;
  const auto extent = params.get<parameters::DOMAIN_EXTENT>();
  const T dx = params.get<parameters::PHYS_CHAR_LENGTH>()
             / params.get<parameters::RESOLUTION>();
  IndicatorCuboid3D<T> domain(Vector<T,3>{extent[0],extent[1],extent[2]},
                              Vector<T,3>{0,0,0});
  Mesh<T,3> mesh(domain, dx, singleton::mpi().getSize());
  mesh.setOverlap(3);
  mesh.getCuboidDecomposition().setPeriodicity({false,true,false});
  return mesh;
}

inline void prepareMinimalGeometry(Stage3Case& c)
{
  using T = Stage3Case::value_t;
  auto& geometry = c.getGeometry();
  auto& params = c.getParameters();
  const auto e = params.get<parameters::DOMAIN_EXTENT>();
  const T dx = params.get<parameters::PHYS_DELTA_X>();

  geometry.rename(0,2);
  IndicatorCuboid3D<T> fluid(
    Vector<T,3>{e[0]-T(2)*dx, e[1], e[2]-T(2)*dx},
    Vector<T,3>{dx,0,dx});
  geometry.rename(2,1,fluid);
  geometry.innerClean();
  geometry.checkForErrors();
  geometry.print();
}

inline void prepareMinimalLattice(Stage3Case& c)
{
  using T = Stage3Case::value_t;
  using DESCRIPTOR = Stage3Case::descriptor_t_of<NavierStokes>;
  auto& lattice = c.getLattice(NavierStokes{});
  auto& geometry = c.getGeometry();
  auto& p = c.getParameters();

  lattice.setUnitConverter<UnitConverterFromResolutionAndRelaxationTime<T,DESCRIPTOR>>(
    int{p.get<parameters::RESOLUTION>()},
    T{p.get<parameters::LATTICE_RELAXATION_TIME>()},
    T{p.get<parameters::PHYS_CHAR_LENGTH>()},
    T{p.get<parameters::PHYS_CHAR_VELOCITY>()},
    T{p.get<parameters::PHYS_CHAR_VISCOSITY>()},
    T{p.get<parameters::PHYS_CHAR_DENSITY>()});

#ifdef STAGE3_USE_SMAGORINSKY
  dynamics::set<SmagorinskyForcedBGKdynamics>(lattice, geometry.getMaterialIndicator(1));
  lattice.setParameter<collision::LES::SMAGORINSKY>(T(0.2));
#else
  dynamics::set<ForcedBGKdynamics>(lattice, geometry.getMaterialIndicator(1));
#endif
  boundary::set<boundary::BounceBack>(lattice, geometry, 2);
  lattice.setParameter<descriptors::OMEGA>(
    lattice.getUnitConverter().getLatticeRelaxationFrequency());

  AnalyticalConst3D<T,T> zero(0);
  AnalyticalConst3D<T,T> zeros(0,0,0);
  AnalyticalConst3D<T,T> one(1);
  AnalyticalConst3D<T,T> four(4);
  for (int material : {0,1,2}) {
    lattice.defineField<FreeSurface::MASS>(geometry,material,zero);
    lattice.defineField<FreeSurface::EPSILON>(geometry,material,zero);
    lattice.defineField<FreeSurface::CELL_TYPE>(geometry,material,zero);
    lattice.defineField<FreeSurface::CELL_FLAGS>(geometry,material,zero);
    lattice.defineField<FreeSurface::PREVIOUS_VELOCITY>(geometry,material,zeros);
    lattice.defineField<descriptors::FORCE>(geometry,material,zeros);
    lattice.defineField<FreeSurface::HAS_INTERFACE_NBRS>(geometry,material,one);
  }

  const T dx = lattice.getUnitConverter().getPhysDeltaX();
  const auto e = p.get<parameters::DOMAIN_EXTENT>();
  const T radius = p.get<parameters::DROPLET_RADIUS>();
  const std::array<T,3> center{T(0.5)*e[0],T(0.5)*e[1],T(0.5)*dx};
  HemisphereField3D<T> typeField(center,radius,dx,{0,1,2});
  HemisphereField3D<T> fractionField(center,radius,dx,{0,0.5,1});
  lattice.defineField<FreeSurface::CELL_TYPE>(geometry,1,typeField);
  lattice.defineField<FreeSurface::EPSILON>(geometry,1,fractionField);
  lattice.defineField<FreeSurface::MASS>(geometry,1,fractionField);
  // Match the official examples: non-fluid/solid material carries a full
  // reference mass and epsilon, while CELL_TYPE=Solid (4).
  for (int material : {0,2}) {
    lattice.defineField<FreeSurface::MASS>(geometry,material,one);
    lattice.defineField<FreeSurface::EPSILON>(geometry,material,one);
    lattice.defineField<FreeSurface::CELL_TYPE>(geometry,material,four);
  }

  lattice.defineRhoU(geometry.getMaterialIndicator({0,1,2}),one,zeros);
  for (int material : {0,1,2}) {
    lattice.iniEquilibrium(geometry,material,one,zeros);
  }

  FreeSurface::initialize(lattice);
  lattice.initialize();
  static FreeSurface3DSetup<T,DESCRIPTOR> freeSurface(lattice);
  freeSurface.addPostProcessor();

  const T sigma = p.get<parameters::SURFACE_TENSION>();
  const T factor = std::pow(lattice.getUnitConverter().getConversionFactorTime(),2)
                 / (p.get<parameters::PHYS_CHAR_DENSITY>()*std::pow(dx,3));
  lattice.setParameter<FreeSurface::DROP_ISOLATED_CELLS>(true);
  lattice.setParameter<FreeSurface::TRANSITION>(T(1e-3));
  lattice.setParameter<FreeSurface::LONELY_THRESHOLD>(T(1));
  lattice.setParameter<FreeSurface::HAS_SURFACE_TENSION>(sigma > T(0));
  lattice.setParameter<FreeSurface::SURFACE_TENSION_PARAMETER>(factor*sigma);
  lattice.setParameter<FreeSurface::FORCE_DENSITY>({0,0,0});
}

#endif
