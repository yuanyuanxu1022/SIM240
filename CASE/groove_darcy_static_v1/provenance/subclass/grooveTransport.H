// SPDX-License-Identifier: GPL-3.0-or-later
// Pure coefficient evaluation; no flow solution or reference qualification.
#ifndef sim240_grooveTransport_H
#define sim240_grooveTransport_H
#include <cmath>
#include <stdexcept>

namespace sim240
{
struct Transport
{
    double H, Kparallel, Kperpendicular, Dparallel, Dperpendicular;
};

inline Transport transport(double h, double depth, double width, double period, bool v2)
{
    if (!std::isfinite(h) || !std::isfinite(depth)
     || !std::isfinite(width) || !std::isfinite(period)
     || h <= 0 || depth < 0 || width <= 0 || period <= 0
     || std::abs(2*width/period-1) > 1e-12)
        throw std::invalid_argument("Require positive gap, nonnegative depth, and equal groove/land widths");
    // Published V2 belongs to the fixed 120/240 nm pattern, not arbitrary scaling.
    if (v2 && (std::abs(width/120e-9-1) > 1e-12
            || std::abs(period/240e-9-1) > 1e-12))
        throw std::invalid_argument("V2_published_rounded requires width=120nm, period=240nm");
    const double a = h*h*h, b = (h+depth)*(h+depth)*(h+depth);
    Transport r;
    r.H = h + (width/period)*depth;
    r.Kparallel = (a+b)/24;
    r.Kperpendicular = (a*b)/(6*(a+b));
    if (v2)
    {
        r.Kparallel /= 1 + 1.7685*std::pow(depth/width, 1.6331);
        r.Kperpendicular /= 1 + 0.4900*std::pow(depth/width, 0.6990);
    }
    r.Dparallel = r.H/r.Kparallel;
    r.Dperpendicular = r.H/r.Kperpendicular;
    for (double v : {r.H, r.Kparallel, r.Kperpendicular, r.Dparallel, r.Dperpendicular})
        if (!std::isfinite(v) || v <= 0)
            throw std::invalid_argument("Nonfinite or nonpositive transport coefficient");
    return r;
}
}
#endif
