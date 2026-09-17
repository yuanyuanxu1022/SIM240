#!/usr/bin/env python3
import csv, pathlib, sys
rows=list(csv.DictReader((pathlib.Path(sys.argv[1])/'statistics.csv').open()))
for key in ('max_wall_adjacent_u_m_per_s','max_wall_normal_u_m_per_s'):
    print(key, rows[-1][key])
print('BounceBack is implemented; contact-angle control is not implemented.')
