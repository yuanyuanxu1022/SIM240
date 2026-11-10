#include "mass_stats.h"

#include <cmath>
#include <iostream>

int main()
{
  fine_t_stat::NeumaierSum sum;
  sum.add(1.0e16);
  sum.add(1.0);
  sum.add(-1.0e16);
  if (sum.value() != 1.0) return 1;

  fine_t_stat::NeumaierSum reference;
  fine_t_stat::NeumaierSum disturbed;
  for (int i = 0; i < 100000; ++i) {
    reference.add(1.0);
    disturbed.add(1.0 + (i % 2 == 0 ? 1.0e-12 : -1.0e-12));
  }
  if (std::abs((disturbed.value() - reference.value()) / reference.value())
      > 1.0e-13) return 2;
  std::cout << "mass_stats_PASS=true\n";
  return 0;
}
