#ifndef STAGE3_DROPLET_STATISTICS_H
#define STAGE3_DROPLET_STATISTICS_H

#include <olb.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <queue>
#include <set>
#include <string>

struct DropletStats {
  double volume=0, mass=0, maxU=0;
  double weightedX=0, weightedY=0, weightedZ=0, weight=0;
  double xmin=std::numeric_limits<double>::max();
  double ymin=std::numeric_limits<double>::max();
  double zmin=std::numeric_limits<double>::max();
  double xmax=std::numeric_limits<double>::lowest();
  double ymax=std::numeric_limits<double>::lowest();
  double zmax=std::numeric_limits<double>::lowest();
  std::size_t nFluid=0,nInterface=0,nGas=0,nSolid=0;
  std::size_t interfaceFragments=0,largestInterfaceFragment=0;
  double maxWallAdjacentU=0,maxWallNormalU=0;
  bool nanFound=false;
  bool fragmented=false;
  std::string nanField=""; int nanRank=-1; int nanCuboid=-1; std::array<int,3> nanCell{0,0,0};
  double nanValue=0, fieldMin=std::numeric_limits<double>::max(), fieldMax=std::numeric_limits<double>::lowest();
};

inline DropletStats sampleDroplet(Stage3Case& c)
{
  using T = Stage3Case::value_t;
  auto& lattice = c.getLattice(NavierStokes{});
  auto& geometry = c.getGeometry();
  const auto& converter = lattice.getUnitConverter();
  const T dx = converter.getPhysDeltaX();
  const T dx3 = std::pow(converter.getPhysDeltaX(),3);
  const auto extent = c.getParameters().get<parameters::DOMAIN_EXTENT>();
  const int nyPeriod = int(std::llround(extent[1]/dx));
  DropletStats s;
  std::set<std::array<int,3>> interfaceNodes;

  for (int iC=0; iC<lattice.getLoadBalancer().size(); ++iC) {
    auto& block = lattice.getBlock(iC);
    auto& blockGeometry = geometry.getBlockGeometry(iC);
    block.forCoreSpatialLocations([&](auto iX, auto iY, auto iZ) {
      auto cell = block.get({iX,iY,iZ});
      const int material = blockGeometry.getMaterial(iX,iY,iZ);
      if (material == 2) { ++s.nSolid; return; }
      if (material != 1) { return; }

      const auto r = blockGeometry.getPhysR({iX,iY,iZ});
      const int qy = int(std::llround(r[1]/dx));
      // y=Ly duplicates y=0 on the periodic lattice; count physical cells once.
      if (qy == nyPeriod) { return; }

      const T eps = cell.template getField<FreeSurface::EPSILON>();
      const T mass = cell.template getField<FreeSurface::MASS>();
      T u[3] = {0,0,0};
      cell.computeU(u);
      const T rho = cell.computeRho();
      const T speed = std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
      auto check=[&](const std::string& name, double value) {
        if (std::isfinite(value)) { s.fieldMin=std::min(s.fieldMin,value); s.fieldMax=std::max(s.fieldMax,value); }
        else if (!s.nanFound) { s.nanFound=true; s.nanField=name; s.nanRank=singleton::mpi().getRank(); s.nanCuboid=iC; s.nanCell={iX,iY,iZ}; s.nanValue=value; }
      };
      check("rho",rho); check("ux",u[0]); check("uy",u[1]); check("uz",u[2]);
      check("MASS",mass); check("EPSILON",eps);
      const double cellType=static_cast<double>(static_cast<int>(cell.template getField<FreeSurface::CELL_TYPE>())); check("CELL_TYPE",cellType);
      for (unsigned iPop=0; iPop<Stage3Case::descriptor_t_of<NavierStokes>::q; ++iPop) check("f["+std::to_string(iPop)+"]",cell[iPop]);
      if (eps < T(-1e-8) || eps > T(1+1e-8)) { if (!s.nanFound) { s.nanFound=true; s.nanField="EPSILON(range)"; s.nanRank=singleton::mpi().getRank(); s.nanCuboid=iC; s.nanCell={iX,iY,iZ}; s.nanValue=eps; } }
      if (isCellType(cell,FreeSurface::Type::Fluid)) ++s.nFluid;
      else if (isCellType(cell,FreeSurface::Type::Interface)) {
        ++s.nInterface;
        interfaceNodes.insert({int(std::llround(r[0]/dx)),qy,int(std::llround(r[2]/dx))});
      }
      else if (isCellType(cell,FreeSurface::Type::Gas)) ++s.nGas;

      s.volume += eps*dx3;
      s.mass += mass;
      if (eps > T(1e-8)) {
        s.maxU = std::max(s.maxU,double(converter.getPhysVelocity(speed)));
        s.weightedX += eps*r[0]; s.weightedY += eps*r[1]; s.weightedZ += eps*r[2];
        s.weight += eps;
        s.xmin=std::min(s.xmin,double(r[0])); s.xmax=std::max(s.xmax,double(r[0]));
        s.ymin=std::min(s.ymin,double(r[1])); s.ymax=std::max(s.ymax,double(r[1]));
        s.zmin=std::min(s.zmin,double(r[2])); s.zmax=std::max(s.zmax,double(r[2]));

        const bool xm=blockGeometry.getMaterial(iX-1,iY,iZ)==2;
        const bool xp=blockGeometry.getMaterial(iX+1,iY,iZ)==2;
        const bool zm=blockGeometry.getMaterial(iX,iY,iZ-1)==2;
        const bool zp=blockGeometry.getMaterial(iX,iY,iZ+1)==2;
        if (xm||xp||zm||zp) {
          s.maxWallAdjacentU=std::max(s.maxWallAdjacentU,double(converter.getPhysVelocity(speed)));
          T normal=T(0);
          if (xm||xp) normal=std::max(normal,std::abs(u[0]));
          if (zm||zp) normal=std::max(normal,std::abs(u[2]));
          s.maxWallNormalU=std::max(s.maxWallNormalU,double(converter.getPhysVelocity(normal)));
        }
      }
    });
  }

  while (!interfaceNodes.empty()) {
    ++s.interfaceFragments;
    std::queue<std::array<int,3>> todo;
    todo.push(*interfaceNodes.begin());
    interfaceNodes.erase(interfaceNodes.begin());
    std::size_t component=0;
    while (!todo.empty()) {
      const auto p=todo.front(); todo.pop(); ++component;
      for (int dxq=-1;dxq<=1;++dxq) for (int dyq=-1;dyq<=1;++dyq)
        for (int dzq=-1;dzq<=1;++dzq) {
          if (dxq==0&&dyq==0&&dzq==0) continue;
          std::array<int,3> n{p[0]+dxq,(p[1]+dyq+nyPeriod)%nyPeriod,p[2]+dzq};
          auto it=interfaceNodes.find(n);
          if (it!=interfaceNodes.end()) { todo.push(n); interfaceNodes.erase(it); }
        }
    }
    s.largestInterfaceFragment=std::max(s.largestInterfaceFragment,component);
  }
  s.fragmented=s.interfaceFragments>1;
  return s;
}

#endif
