#define main step4_boundary_fix_main
#include "explicit_piston_boundary_intersection_fix.cpp"
#undef main

#include <sstream>
#include <set>
#include <tuple>
#include <vector>

constexpr int scPostSteps = 500;
// Both the platform underside (z=72.5 nm) and groove ceiling
// (z=172.5 nm) cross cell centres in the same rigid-body step.
constexpr long long scExpectedConversions = 2304;
constexpr T cvResidualLimit=1e-3;
// Frozen before the candidate run. At alpha ~= 0.5, eight vertical receivers
// cap the ordinary-column density increment near 0.0625; the pressure-adjacent
// interior columns can receive two sources and are capped near 0.125.
constexpr int repairReceiverDepth=8;

int cvWrapX(int ix)
{
  const int wrapped=ix%48;
  return wrapped<0?wrapped+48:wrapped;
}

template<class L,class G>
std::array<int,4> cvUpdatePeriodicLinks(L& lattice,G& geometry,T h,T uWall)
{
  int active=0,invalid=0,recovered=0,falseSolid=0;
  auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  block.forCoreSpatialLocations([&](LatticeR<3> p) {
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i) {
      cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,-1);
      cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(i,0);
    }
    if(!isFluidMaterial(g.getMaterial(p))) return;
    const auto r=g.getPhysR(p);
    for(int i=1;i<D::q;++i) {
      const auto c=descriptors::c<D>(i);auto raw=p+c,mapped=raw;
      const bool crosses=raw[0]<0||raw[0]>=48;
      if(crosses) mapped[0]=cvWrapX(raw[0]);
      const int rawMaterial=g.getMaterial(raw);
      const int solidMaterial=crosses?g.getMaterial(mapped):rawMaterial;
      if(crosses&&(solidMaterial==2||solidMaterial==3)
         &&rawMaterial!=2&&rawMaterial!=3) ++recovered;
      if(crosses&&(rawMaterial==2||rawMaterial==3)
         &&solidMaterial!=2&&solidMaterial!=3) ++falseSolid;
      if(solidMaterial!=2&&solidMaterial!=3) continue;
      T q=.5,velocityCoefficient=0;
      if(solidMaterial==3) {
        T lo=0,hi=1;
        for(int k=0;k<50;++k) {
          const T a=(lo+hi)/2;
          T x=r[0]+a*dx*c[0];x=std::fmod(x,Lx);if(x<0)x+=Lx;
          if(punch(x,r[2]+a*dx*c[2],h)) hi=a;else lo=a;
        }
        q=(lo+hi)/2;velocityCoefficient=c[2]*uWall*dt/dx;
      }
      if(!(q>=0&&q<=1)) ++invalid;
      else {
        cell.template setFieldComponent<descriptors::BOUZIDI_DISTANCE>(i,q);
        cell.template setFieldComponent<descriptors::BOUZIDI_VELOCITY>(
          i,velocityCoefficient);
        ++active;
      }
    }
  });
  lattice.communicate();return {active,invalid,recovered,falseSolid};
}

template<class L,class G>
void cvSetAllZouHePressure(L& lattice,G& geometry,
                           SuperIndicatorFfromIndicatorF3D<T>& outside)
{
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(4),geometry.getMaterialIndicator(1),outside);
  boundary::set<T,D,boundary::ZouHePressure<T,D,BGKdynamics<T,D>>>(
    lattice,geometry.getMaterialIndicator(5),geometry.getMaterialIndicator(1),outside);
}

T cvSurfaceHeight(T x,T h)
{
  x=std::fmod(x,Lx);if(x<0)x+=Lx;
  return (x<60e-9||x>=180e-9) ? h : h+grooveDepth;
}

T cvAlpha(const Vector<T,3>& r,T h)
{
  const T zLow=r[2]-dx/T(2),zHigh=r[2]+dx/T(2);
  return std::clamp((std::min(zHigh,cvSurfaceHeight(r[0],h))
                    -std::max(zLow,T(0)))/dx,T(0),T(1));
}

struct CVStats {
  long long fluidCells=0;
  T fullMass=0,geomMass=0,rhoSum=0;
  T rhoMin=std::numeric_limits<T>::max(),rhoMax=-std::numeric_limits<T>::max();
  T maxU=0,macroInRate=0,macroOutRate=0;
  bool finite=true;
};

template<class L,class G>
CVStats cvStats(L& lattice,G& geometry,const UnitConverter<T,D>& converter,T h)
{
  CVStats s;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material=g.getMaterial(p);if(!isFluidMaterial(material)) return;
    auto cell=block.get(p);T u[3]{};cell.computeU(u);const T rho=cell.computeRho();
    const T speed=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
    ++s.fluidCells;s.rhoSum+=rho;s.fullMass+=rho*rhoPhys*dx*dx*dx;
    s.geomMass+=cvAlpha(g.getPhysR(p),h)*rho*rhoPhys*dx*dx*dx;
    s.rhoMin=std::min(s.rhoMin,rho);s.rhoMax=std::max(s.rhoMax,rho);
    s.maxU=std::max(s.maxU,speed);
    s.finite&=std::isfinite(rho)&&std::isfinite(speed);
    for(int i=0;i<D::q;++i)s.finite&=std::isfinite(cell[i]);
    if(material==4||material==5) {
      const T uy=converter.getPhysVelocity(u[1]);
      const T signedOut=(material==4?-1:1)*rho*rhoPhys*uy*dx*dx;
      if(signedOut>=0)s.macroOutRate+=signedOut;else s.macroInRate-=signedOut;
    }
  });
  return s;
}

struct CVPopulationFlux {T inMass=0,outMass=0;};
template<class L,class G>
CVPopulationFlux cvPopulationFlux(L& lattice,G& geometry)
{
  CVPopulationFlux flux;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int material=g.getMaterial(p);if(material!=4&&material!=5)return;
    auto cell=block.get(p);
    for(int i=0;i<D::q;++i) {
      const int cy=descriptors::c<D>(i,1);if(cy==0)continue;
      const T mass=(cell[i]+descriptors::t<T,D>(i))*rhoPhys*dx*dx*dx;
      const bool outgoing=material==4?cy<0:cy>0;
      if(outgoing)flux.outMass+=mass;else flux.inMass+=mass;
    }
  });
  return flux;
}

int scMaterialAt(const Vector<T,3>& r, T h)
{
  if (r[2] < 0) return 2;
  if (punch(r[0], r[2], h)) return 3;
  if (r[1] < dx) return 4;
  if (r[1] > Ly-dx) return 5;
  return 1;
}

struct SCCellSnapshot {
  LatticeR<3> p{};
  Vector<T,3> r{};
  int material = 0;
  T rho = 0;
  std::array<T,3> u{};
  std::array<T,D::q> f{};
  T alpha = 0;
  std::string oldLinks;
  int receivers = 0;
  std::string newLinks;
};

template<class CELL>
SCCellSnapshot scSnapshot(CELL cell, int material, LatticeR<3> p,
                          const Vector<T,3>& r, T h)
{
  SCCellSnapshot s;
  s.p=p; s.r=r; s.material=material; s.rho=cell.computeRho();
  cell.computeU(s.u.data());
  s.alpha=cvAlpha(r,h);
  std::ostringstream links;
  bool first=true;
  for (int i=0; i<D::q; ++i) {
    s.f[i]=cell[i];
    const T q=cell.template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
    if (q >= 0) {
      if (!first) links << '|';
      links << i << ':' << std::setprecision(17) << q;
      first=false;
    }
  }
  s.oldLinks=links.str();
  return s;
}

T scMomentum(const SCCellSnapshot& s, int iD)
{
  T value=0;
  for (int i=0; i<D::q; ++i) value += s.f[i]*descriptors::c<D>(i,iD);
  return value;
}

void scWritePopulationHeader(std::ofstream& out)
{
  out << "conversion_step,phase,ix,iy,iz,x_nm,y_nm,z_nm,material,h_nm,alpha,rho,"
         "ux,uy,uz,Mach,local_full_mass_kg,local_geom_mass_kg,"
         "momentum_x_lattice,momentum_y_lattice,momentum_z_lattice";
  for (int i=0; i<D::q; ++i) out << ",f" << i;
  out << '\n';
}

void scWritePopulation(std::ofstream& out, int conversionStep,
                       const std::string& phase, const SCCellSnapshot& s, T h)
{
  const T speed=std::sqrt(s.u[0]*s.u[0]+s.u[1]*s.u[1]+s.u[2]*s.u[2]);
  out << conversionStep << ',' << phase << ',' << s.p[0] << ',' << s.p[1] << ','
      << s.p[2] << ',' << s.r[0]*1e9 << ',' << s.r[1]*1e9 << ',' << s.r[2]*1e9
      << ',' << s.material << ',' << h*1e9 << ',' << s.alpha << ',' << s.rho
      << ',' << s.u[0] << ',' << s.u[1] << ',' << s.u[2] << ','
      << speed/std::sqrt(T(1)/3) << ',' << s.rho*rhoPhys*dx*dx*dx << ','
      << s.alpha*s.rho*rhoPhys*dx*dx*dx << ',' << scMomentum(s,0) << ','
      << scMomentum(s,1) << ',' << scMomentum(s,2);
  for (T f : s.f) out << ',' << f;
  out << '\n';
}

int scWrapYOrInvalid(int iy)
{
  return (iy>=0 && iy<48) ? iy : -1;
}

template<class L,class G>
std::vector<SCCellSnapshot> scConvertFirstLayer(
  L& lattice, G& geometry, T hPrevious, T hCurrent,
  T& transferredMassLattice, std::array<T,3>& transferredMomentum,
  T& transferError, std::vector<SCCellSnapshot>& receiverBefore,
  std::vector<SCCellSnapshot>& receiverAfter)
{
  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  std::vector<SCCellSnapshot> event;
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    const int oldMaterial=g.getMaterial(p);
    const auto r=g.getPhysR(p);
    if (isFluidMaterial(oldMaterial) && scMaterialAt(r,hCurrent)==3) {
      event.push_back(scSnapshot(block.get(p),oldMaterial,p,r,hPrevious));
    }
  });

  auto receiversFor=[&](const SCCellSnapshot& source) {
    std::vector<LatticeR<3>> receivers;
    receivers.reserve(repairReceiverDepth);
    int receiverY=source.p[1];
    // Zou/He cells prescribe rho and must not be used as storage receivers.
    // Boundary-source content is placed in the nearest interior fluid column.
    if (source.material==4) receiverY=1;
    if (source.material==5) receiverY=46;
    for (int layer=1; layer<=repairReceiverDepth; ++layer) {
      LatticeR<3> q{source.p[0],receiverY,source.p[2]-layer};
      q[0]=cvWrapX(q[0]);
      const auto qr=g.getPhysR(q);
      if (g.getMaterial(q)!=1 || scMaterialAt(qr,hCurrent)==3) {
        throw std::runtime_error("repair receiver column is not persistent material-1 fluid");
      }
      receivers.push_back(q);
    }
    if (receivers.empty()) throw std::runtime_error("conversion has no persistent fluid receiver");
    return receivers;
  };

  std::set<std::tuple<int,int,int>> receiverSet;
  for (const auto& source : event) {
    for (const auto& q : receiversFor(source)) receiverSet.emplace(q[0],q[1],q[2]);
  }
  for (const auto& key : receiverSet) {
    LatticeR<3> q{std::get<0>(key),std::get<1>(key),std::get<2>(key)};
    receiverBefore.push_back(scSnapshot(block.get(q),g.getMaterial(q),q,g.getPhysR(q),hCurrent));
  }

  transferredMassLattice=0;
  transferredMomentum={0,0,0};
  transferError=0;
  for (auto& source : event) {
    const auto receivers=receiversFor(source);
    source.receivers=static_cast<int>(receivers.size());
    const T alphaCurrent=cvAlpha(source.r,hCurrent);
    auto sourceCell=block.get(source.p);
    T directRho=1;
    for(int i=0;i<D::q;++i) directRho+=sourceCell[i];
    // For pressure source nodes, make the transferred F_i sum consistent with
    // their prescribed boundary rho while preserving the normalized shape and
    // velocity of the source populations.
    const T populationScale=source.rho/directRho;
    T beforeRhoSum=0;
    for (const auto& q : receivers) {
      auto cell=block.get(q);T rhoDirect=1;
      for(int i=0;i<D::q;++i)rhoDirect+=cell[i];
      beforeRhoSum+=rhoDirect;
    }
    for (const auto& q : receivers) {
      auto destination=block.get(q);
      for (int i=0; i<D::q; ++i) {
        const T fullPopulation=source.f[i]+descriptors::t<T,D>(i);
        destination[i] += alphaCurrent*populationScale*fullPopulation/receivers.size();
      }
    }
    T afterRhoSum=0;
    for (const auto& q : receivers) {
      auto cell=block.get(q);T rhoDirect=1;
      for(int i=0;i<D::q;++i)rhoDirect+=cell[i];
      afterRhoSum+=rhoDirect;
    }
    const T intended=alphaCurrent*source.rho;
    transferredMassLattice += intended;
    transferError += (afterRhoSum-beforeRhoSum)-intended;
    for (int iD=0; iD<3; ++iD) {
      transferredMomentum[iD] += alphaCurrent*populationScale*scMomentum(source,iD);
    }
  }

  for (const auto& source : event) {
    g.set(source.p,3);
    block.template defineDynamics<NoDynamics>(source.p);
  }
  geometry.communicate();
  lattice.communicate();
  for (const auto& key : receiverSet) {
    LatticeR<3> q{std::get<0>(key),std::get<1>(key),std::get<2>(key)};
    receiverAfter.push_back(scSnapshot(block.get(q),g.getMaterial(q),q,g.getPhysR(q),hCurrent));
  }
  return event;
}

struct SCExtrema {
  int maxIx=0,maxIy=0,maxIz=0,maxMaterial=0,maxPopulation=-1;
  T maxMach=0,maxPopulationMagnitude=0;
};

template<class L,class G>
SCExtrema scExtrema(L& lattice,G& geometry)
{
  SCExtrema e;auto& block=lattice.getBlock(0);auto& g=geometry.getBlockGeometry(0);
  g.forCoreSpatialLocations([&](LatticeR<3> p) {
    if(!isFluidMaterial(g.getMaterial(p)))return;
    auto cell=block.get(p);T u[3]{};cell.computeU(u);
    const T mach=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2])/std::sqrt(T(1)/3);
    if(mach>e.maxMach){e.maxMach=mach;e.maxIx=p[0];e.maxIy=p[1];e.maxIz=p[2];e.maxMaterial=g.getMaterial(p);}
    for(int i=0;i<D::q;++i){
      if(std::abs(cell[i])>e.maxPopulationMagnitude){
        e.maxPopulationMagnitude=std::abs(cell[i]);e.maxPopulation=i;
      }
    }
  });
  return e;
}

template<class L,class G>
void scFillNewLinks(std::vector<SCCellSnapshot>& event,L& lattice,G& geometry)
{
  auto& block=lattice.getBlock(0);
  auto& g=geometry.getBlockGeometry(0);
  for (auto& source : event) {
    std::ostringstream links;
    bool first=true;
    for (int i=1; i<D::q; ++i) {
      const auto c=descriptors::c<D>(i);
      LatticeR<3> donor=source.p-c;
      donor[0]=cvWrapX(donor[0]);
      if (donor[1]<0 || donor[1]>=48 || donor[2]<0) continue;
      if (!isFluidMaterial(g.getMaterial(donor))) continue;
      const T q=block.get(donor).template getFieldComponent<descriptors::BOUZIDI_DISTANCE>(i);
      if (q>=0) {
        if (!first) links << '|';
        links << donor[0] << '_' << donor[1] << '_' << donor[2]
              << ":d" << i << ":q" << std::setprecision(17) << q;
        first=false;
      }
    }
    source.newLinks=links.str();
  }
}

void scHistoryHeader(std::ofstream& out)
{
  out << "step,time_s,h_nm,steps_after_conversion,converted_this_step,"
         "converted_cumulative,fluid_cells,material1,material3,material4,material5,"
         "M_geom_kg,R_geom_macro_relative,R_geom_population_relative,"
         "macro_in_kg,macro_out_kg,population_in_kg,population_out_kg,"
         "rho_min,rho_max,max_velocity_m_s,max_Mach,max_ix,max_iy,max_iz,"
         "max_material,max_abs_population,max_abs_population_index,illegal_links,finite\n";
}

int scRun()
{
  const std::string runId="conversion_repair_A_column8_v1_20260908";
  const auto outDir=std::filesystem::path("output")/runId;
  if (std::filesystem::exists(outDir)) {
    std::cerr << "Refusing to overwrite " << outDir << '\n';
    return 2;
  }
  std::filesystem::create_directories(outDir);
  singleton::directories().setOutputDir((outDir.string()+"/").c_str());
  std::ofstream log(outDir/"run.log");
  log << std::setprecision(17) << std::boolalpha;
  try {
    IndicatorCuboid3D<T> domain({Lx-dx,Ly-dx,195e-9},{dx/2,dx/2,-dx/2});
    CuboidDecomposition<T,3> cuboids(domain,dx,1);
    cuboids.setPeriodicity({true,false,false});
    HeuristicLoadBalancer<T> loadBalancer(cuboids);
    SuperGeometry<T,3> geometry(cuboids,loadBalancer,overlap);
    auto& g=geometry.getBlockGeometry(0);
    g.forCoreSpatialLocations([&](LatticeR<3> p) { g.set(p,materialAt(g.getPhysR(p))); });
    geometry.communicate();
    const auto initialCounts=materialCounts(geometry);
    SuperIndicatorFfromIndicatorF3D<T> outside(new PeriodicXOutside,geometry);
    UnitConverter<T,D> converter(dx,dt,240e-9,1.,nuPhys,rhoPhys);
    SuperLattice<T,D> lattice(converter,cuboids,loadBalancer);
    dynamics::set<BGKdynamics>(lattice,geometry,1);
    cvSetAllZouHePressure(lattice,geometry,outside);
    dynamics::set<NoDynamics>(lattice,geometry,2);
    dynamics::set<NoDynamics>(lattice,geometry,3);
    AnalyticalConst3D<T,T> one(1),zero(0,0,0);
    lattice.defineRhoU(geometry.getMaterialIndicator({1,4,5}),one,zero);
    for (int material : {1,4,5}) lattice.iniEquilibrium(geometry,material,one,zero);
    lattice.addPostProcessor<stage::PostStream>(meta::id<BouzidiVelocityPostProcessor>{});
    lattice.initialize();
    lattice.defineRho(geometry,4,one);
    lattice.defineRho(geometry,5,one);
    lattice.communicate();

    std::ofstream history(outDir/"post_conversion_history.csv");
    history << std::setprecision(17) << std::boolalpha;
    scHistoryHeader(history);
    std::ofstream eventOut(outDir/"conversion_event.csv");
    eventOut << std::setprecision(17);
    eventOut << "conversion_step,ix,iy,iz,x_nm,y_nm,z_nm,old_material,new_material,"
                "h_previous_nm,h_current_nm,alpha_previous,alpha_current,rho_before,"
                "local_full_mass_before_kg,local_geom_mass_current_kg,"
                "momentum_x_lattice,momentum_y_lattice,momentum_z_lattice,"
                "receiver_count,old_bouzidi_links,new_bouzidi_links\n";
    std::ofstream populations(outDir/"conversion_population_before_after.csv");
    populations << std::setprecision(17);
    scWritePopulationHeader(populations);

    const auto initial=cvStats(lattice,geometry,converter,75e-9);
    auto previous=initial,current=initial;
    T macroIn=0,macroOut=0,popIn=0,popOut=0;
    T maxMach=0,minRho=std::numeric_limits<T>::max();
    T maxRho=-std::numeric_limits<T>::max(),maxAbsResidual=0;
    int conversionStep=-1,maxIllegal=0,completed=0;
    long long convertedTotal=0;
    T transferredMassLattice=0,transferError=0;
    std::array<T,3> transferredMomentum{};
    std::vector<SCCellSnapshot> event;
    std::vector<SCCellSnapshot> receiverBefore,receiverAfter;
    bool finite=true;

    for (int step=1; step<=trajectorySteps; ++step) {
      const T hPrevious=hAt(step-1,true),hCurrent=hAt(step,true);
      int convertedThisStep=0;
      if (conversionStep<0) {
        bool conversionDue=false;
        g.forCoreSpatialLocations([&](LatticeR<3> p) {
          if (isFluidMaterial(g.getMaterial(p))
              && scMaterialAt(g.getPhysR(p),hCurrent)==3) conversionDue=true;
        });
        if (conversionDue) {
          conversionStep=step;
          event=scConvertFirstLayer(lattice,geometry,hPrevious,hCurrent,
                                    transferredMassLattice,transferredMomentum,
                                    transferError,receiverBefore,receiverAfter);
          convertedThisStep=static_cast<int>(event.size());
          convertedTotal+=convertedThisStep;
          for (const auto& s : event) scWritePopulation(populations,step,"before",s,hPrevious);
          for (const auto& s : receiverBefore) scWritePopulation(populations,step,"receiver_before",s,hCurrent);
          for (const auto& s : receiverAfter) scWritePopulation(populations,step,"receiver_after_transfer",s,hCurrent);
        }
      } else {
        long long unexpected=0;
        g.forCoreSpatialLocations([&](LatticeR<3> p) {
          if (isFluidMaterial(g.getMaterial(p))
              && scMaterialAt(g.getPhysR(p),hCurrent)==3) ++unexpected;
        });
        if (unexpected) throw std::runtime_error("second conversion encountered before stop");
      }

      const auto links=cvUpdatePeriodicLinks(lattice,geometry,hCurrent,wallSpeed(step,true));
      const int illegal=links[1]+links[3];
      if (convertedThisStep) {
        scFillNewLinks(event,lattice,geometry);
        auto& block=lattice.getBlock(0);
        for (auto& s : event) {
          auto after=scSnapshot(block.get(s.p),g.getMaterial(s.p),s.p,s.r,hCurrent);
          scWritePopulation(populations,step,"after_conversion_before_collision",after,hCurrent);
        }
      }

      lattice.collide();
      const auto flux=cvPopulationFlux(lattice,geometry);
      lattice.AndStream();
      current=cvStats(lattice,geometry,converter,hCurrent);
      macroIn+=T(.5)*(previous.macroInRate+current.macroInRate)*dt;
      macroOut+=T(.5)*(previous.macroOutRate+current.macroOutRate)*dt;
      popIn+=flux.inMass; popOut+=flux.outMass;
      if (convertedThisStep) {
        auto& block=lattice.getBlock(0);
        for (auto& s : event) {
          auto after=scSnapshot(block.get(s.p),g.getMaterial(s.p),s.p,s.r,hCurrent);
          scWritePopulation(populations,step,"after_first_collide_stream",after,hCurrent);
        }
        for (const auto& s : receiverAfter) {
          auto after=scSnapshot(block.get(s.p),g.getMaterial(s.p),s.p,s.r,hCurrent);
          scWritePopulation(populations,step,"receiver_after_first_collide_stream",after,hCurrent);
        }
      }

      const T rMacro=current.geomMass-initial.geomMass-macroIn+macroOut;
      const T rPopulation=current.geomMass-initial.geomMass-popIn+popOut;
      const T mach=current.maxU/std::sqrt(T(1)/3);
      maxMach=std::max(maxMach,mach);
      minRho=std::min(minRho,current.rhoMin);
      maxRho=std::max(maxRho,current.rhoMax);
      maxAbsResidual=std::max(maxAbsResidual,std::abs(rMacro/initial.geomMass));
      maxIllegal=std::max(maxIllegal,illegal);
      finite &= current.finite;
      if (conversionStep>=0) {
        const auto counts=materialCounts(geometry);
        const auto extrema=scExtrema(lattice,geometry);
        history << step << ',' << step*dt << ',' << hCurrent*1e9 << ','
          << step-conversionStep << ',' << convertedThisStep << ',' << convertedTotal
          << ',' << current.fluidCells << ',' << counts[1] << ',' << counts[3] << ','
          << counts[4] << ',' << counts[5] << ',' << current.geomMass << ','
          << rMacro/initial.geomMass << ',' << rPopulation/initial.geomMass << ','
          << macroIn << ',' << macroOut << ',' << popIn << ',' << popOut << ','
          << current.rhoMin << ',' << current.rhoMax << ','
          << converter.getPhysVelocity(current.maxU) << ',' << mach << ','
          << extrema.maxIx << ',' << extrema.maxIy << ',' << extrema.maxIz << ','
          << extrema.maxMaterial << ',' << extrema.maxPopulationMagnitude << ','
          << extrema.maxPopulation << ',' << illegal << ',' << current.finite << '\n';
      }
      previous=current; completed=step;
      if (!finite || illegal) break;
      if (conversionStep>=0 && step>=conversionStep+scPostSteps) break;
    }

    if (conversionStep<0) throw std::runtime_error("no material conversion occurred");
    scFillNewLinks(event,lattice,geometry);
    for (const auto& s : event) {
      const T alphaCurrent=cvAlpha(s.r,hAt(conversionStep,true));
      eventOut << conversionStep << ',' << s.p[0] << ',' << s.p[1] << ',' << s.p[2]
        << ',' << s.r[0]*1e9 << ',' << s.r[1]*1e9 << ',' << s.r[2]*1e9 << ','
        << s.material << ",3," << hAt(conversionStep-1,true)*1e9 << ','
        << hAt(conversionStep,true)*1e9 << ',' << s.alpha << ',' << alphaCurrent
        << ',' << s.rho << ',' << s.rho*rhoPhys*dx*dx*dx << ','
        << alphaCurrent*s.rho*rhoPhys*dx*dx*dx << ',' << scMomentum(s,0) << ','
        << scMomentum(s,1) << ',' << scMomentum(s,2) << ',' << s.receivers << ','
        << s.oldLinks << ',' << s.newLinks << '\n';
    }

    const auto finalCounts=materialCounts(geometry);
    const T finalRMacro=current.geomMass-initial.geomMass-macroIn+macroOut;
    const T finalRPopulation=current.geomMass-initial.geomMass-popIn+popOut;
    const long long convertedM1=initialCounts[1]-finalCounts[1];
    const long long convertedM4=initialCounts[4]-finalCounts[4];
    const long long convertedM5=initialCounts[5]-finalCounts[5];
    const bool countPass=convertedTotal==scExpectedConversions
      && convertedM1==2208 && convertedM4==48 && convertedM5==48
      && finalCounts[3]-initialCounts[3]==scExpectedConversions;
    const bool transferPass=transferredMassLattice>0
      && std::abs(transferError)/transferredMassLattice<=1e-12;
    const bool pass=completed==conversionStep+scPostSteps && finite
      && maxMach<=machLimit && minRho>=rhoMinLimit && maxRho<=rhoMaxLimit
      && maxIllegal==0 && countPass && transferPass
      && maxAbsResidual<=cvResidualLimit;

    std::ofstream result(outDir/"result.txt");
    result << std::setprecision(17) << std::boolalpha
      << "run_id=" << runId << "\nPASS=" << pass
      << "\nrepair_choice=A_local_conservative_column_redistribution"
      << "\nrepair_receiver_depth=" << repairReceiverDepth
      << "\npressure_nodes_are_receivers=false"
      << "\npressure_source_population_rescaled_to_boundary_rho=true"
      << "\nconversion_step=" << conversionStep
      << "\nconversion_time_s=" << conversionStep*dt
      << "\nconversion_h_nm=" << hAt(conversionStep,true)*1e9
      << "\nsteps_completed=" << completed
      << "\npost_conversion_steps=" << completed-conversionStep
      << "\nconverted_nodes=" << convertedTotal
      << "\nconverted_material1=" << convertedM1
      << "\nconverted_material4=" << convertedM4
      << "\nconverted_material5=" << convertedM5
      << "\npredicted_converted_nodes=" << scExpectedConversions
      << "\ntransferred_geom_mass_kg=" << transferredMassLattice*rhoPhys*dx*dx*dx
      << "\ntransfer_relative_error=" << transferError/transferredMassLattice
      << "\ntransferred_momentum_lattice=" << transferredMomentum[0] << ','
      << transferredMomentum[1] << ',' << transferredMomentum[2]
      << "\nmax_Mach=" << maxMach << "\nrho_range=" << minRho << ',' << maxRho
      << "\nfinal_M_geom_kg=" << current.geomMass
      << "\nfinal_R_geom_macro_relative=" << finalRMacro/initial.geomMass
      << "\nfinal_R_geom_population_relative=" << finalRPopulation/initial.geomMass
      << "\nmax_abs_R_geom_macro_relative=" << maxAbsResidual
      << "\ncumulative_macro_in_mass_kg=" << macroIn
      << "\ncumulative_macro_out_mass_kg=" << macroOut
      << "\ncumulative_population_in_mass_kg=" << popIn
      << "\ncumulative_population_out_mass_kg=" << popOut
      << "\nmax_illegal_links=" << maxIllegal
      << "\nfinite=" << finite << "\ncount_pass=" << countPass
      << "\ntransfer_ledger_pass=" << transferPass
      << "\nmass_residual_pass=" << (maxAbsResidual<=cvResidualLimit)
      << "\nexit_code=" << (pass?0:3) << '\n';
    std::ofstream record(outDir/"run_record.txt");
    record << "run_id=" << runId
      << "\ncommand=mpirun -np 1 ./explicit_piston_conversion_repair_candidate"
      << "\nsource=explicit_piston_conversion_repair_candidate.cpp"
      << "\nfrozen_step5_source=explicit_piston_single_conversion_ledger.cpp"
      << "\nstep4_baseline=explicit_piston_zouhe_moving_control_volume_longrun.cpp"
      << "\nrepair_choice=A_local_conservative_column_redistribution"
      << "\nrepair_receiver_depth=" << repairReceiverDepth
      << "\npost_conversion_steps=" << scPostSteps
      << "\nmaterial_conversion_enabled=true"
      << "\nstop_after_first_event=true"
      << "\nexit_code=" << (pass?0:3) << '\n';
    log << "completed_steps=" << completed << "\nconversion_step=" << conversionStep
      << "\nconverted_nodes=" << convertedTotal << "\nPASS=" << pass
      << "\nexit_code=" << (pass?0:3) << '\n';
    return pass?0:3;
  } catch (const std::exception& e) {
    log << "exception=" << e.what() << "\nexit_code=4\n";
    std::ofstream(outDir/"failure.txt") << e.what() << '\n';
    return 4;
  }
}

int main(int argc,char** argv)
{
  initialize(&argc,&argv);
  if (singleton::mpi().getSize()!=1) return 2;
  return scRun();
}
