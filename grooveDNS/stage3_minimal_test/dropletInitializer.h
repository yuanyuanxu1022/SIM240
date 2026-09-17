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

#endif
