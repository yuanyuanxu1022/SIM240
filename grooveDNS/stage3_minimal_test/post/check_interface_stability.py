#!/usr/bin/env python3
import csv, pathlib, sys
rows=list(csv.DictReader((pathlib.Path(sys.argv[1])/'statistics.csv').open()))
for k in ('max_abs_u_m_per_s','nan_found','n_interface','interface_fragment_count','fragmented'):
    print(k, rows[-1][k])
