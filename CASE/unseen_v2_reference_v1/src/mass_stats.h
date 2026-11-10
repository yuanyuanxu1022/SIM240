#pragma once

#include <cmath>

// Measurement-only compensated summation. No OpenLB state is accessed here.
namespace fine_t_stat {

struct NeumaierSum {
  double sum = 0.0;
  double correction = 0.0;

  void add(double term)
  {
    const double next = sum + term;
    if (std::abs(sum) >= std::abs(term)) {
      correction += (sum - next) + term;
    }
    else {
      correction += (term - next) + sum;
    }
    sum = next;
  }

  double value() const { return sum + correction; }
};

} // namespace fine_t_stat
