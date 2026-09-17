#ifndef STAGE3_DROPLET_INITIALIZER_H
#define STAGE3_DROPLET_INITIALIZER_H

#include <olb.h>
#include <algorithm>
#include <array>
#include <cmath>

template <typename T>
class HemisphereField3D final : public olb::AnalyticalF3D<T,T> {
private:
  std::array<T,3> _center;
  T _radius;
  T _dx;
  std::array<T,3> _values; // gas, interface, fluid
public:
  HemisphereField3D(std::array<T,3> center, T radius, T dx,
                    std::array<T,3> values)
    : olb::AnalyticalF3D<T,T>(1), _center(center), _radius(radius),
      _dx(dx), _values(values) { }

  bool operator()(T output[], const T x[]) override {
    const T rx = x[0] - _center[0];
    const T ry = x[1] - _center[1];
    const T rz = x[2] - _center[2];
    const T signedDistance = _radius - std::sqrt(rx*rx + ry*ry + rz*rz);
    if (x[2] < _center[2]) {
      output[0] = _values[0];
    } else if (signedDistance >= T(0.5)*_dx) {
      output[0] = _values[2];
    } else if (signedDistance <= -T(0.5)*_dx) {
      output[0] = _values[0];
    } else {
      if (_values[0] == T(0) && _values[1] == T(1) && _values[2] == T(2)) {
        output[0] = _values[1];
      } else {
        const T fraction = std::clamp(T(0.5) + signedDistance/_dx, T(0), T(1));
        output[0] = fraction;
      }
    }
    return true;
  }
};

// Official fallingDrop3d-style indicator: classify interface cells by a
// one-lattice-shell neighborhood around the spherical indicator.
template <typename T>
class OfficialSphereField3D final : public olb::AnalyticalF3D<T,T> {
  std::array<T,3> _center; T _radius, _dx; std::array<T,3> _values;
public:
  OfficialSphereField3D(std::array<T,3> center, T radius, T dx,
                        std::array<T,3> values)
    : olb::AnalyticalF3D<T,T>(1), _center(center), _radius(radius),
      _dx(dx), _values(values) { }
  bool operator()(T output[], const T x[]) override {
    const T dx2 = _dx*T(1.1);
    const auto inside = [&](T sx,T sy,T sz) {
      const T a=sx-_center[0], b=sy-_center[1], c=sz-_center[2];
      return a*a+b*b+c*c <= _radius*_radius;
    };
    output[0]=_values[0];
    if (inside(x[0],x[1],x[2])) { output[0]=_values[2]; return true; }
    for (int i=-1;i<=1;++i) for (int j=-1;j<=1;++j) for (int k=-1;k<=1;++k)
      if (inside(x[0]+i*dx2,x[1]+j*dx2,x[2]+k*dx2)) { output[0]=_values[1]; return true; }
    return true;
  }
};

template <typename T>
class ExactSphereVolumeField3D final : public olb::AnalyticalF3D<T,T> {
  std::array<T,3> c; T r,dx; std::array<T,3> values;
public:
  ExactSphereVolumeField3D(std::array<T,3> center,T radius,T spacing,std::array<T,3> v)
    : olb::AnalyticalF3D<T,T>(1),c(center),r(radius),dx(spacing),values(v) {}
  bool operator()(T out[], const T x[]) override {
    constexpr int N=8; int inside=0;
    for(int i=0;i<N;++i) for(int j=0;j<N;++j) for(int k=0;k<N;++k) {
      T sx=x[0]+((T(i)+T(0.5))/T(N)-T(0.5))*dx;
      T sy=x[1]+((T(j)+T(0.5))/T(N)-T(0.5))*dx;
      T sz=x[2]+((T(k)+T(0.5))/T(N)-T(0.5))*dx;
      T a=sx-c[0],b=sy-c[1],d=sz-c[2];
      inside += (a*a+b*b+d*d <= r*r);
    }
    T f=T(inside)/T(N*N*N); out[0]=values[0];
    if (values[0]==T(0) && values[1]==T(1) && values[2]==T(2))
      out[0]=(f<=T(0)?values[0]:(f>=T(1)?values[2]:values[1]));
    else out[0]=f;
    return true;
  }
};

#endif
