#!/usr/bin/env bash
set -euo pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$case_root/src/generated" "$case_root/build"
for h in 50 75 125; do
  python3 "$case_root/scripts/generate_height_source.py" \
    --height-nm "$h" \
    --output "$case_root/src/generated/f1_single_phase_h${h}.cpp"
  mpic++ -O3 -Wall -march=native -mtune=native -std=c++20 \
    -DOLB_VERSION=\"5953d8a-dirty\" -pthread -DPARALLEL_MODE_MPI \
    -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double \
    -I/home/dell/openlb/src -I/home/dell/openlb/external/zlib \
    -I/home/dell/openlb/external/tinyxml2 \
    -MMD -MP -MF "$case_root/build/f1_single_phase_h${h}.d" \
    -c "$case_root/src/generated/f1_single_phase_h${h}.cpp" \
    -o "$case_root/build/f1_single_phase_h${h}.o"
  mpic++ "$case_root/build/f1_single_phase_h${h}.o" \
    -o "$case_root/build/f1_single_phase_h${h}" \
    -L/home/dell/openlb/build/lib -lolbcore -L/home/dell/openlb/external/lib \
    -lz -ltinyxml2 -lpthread
done
echo "built heights: 50 75 125 nm"
