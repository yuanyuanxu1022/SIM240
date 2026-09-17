#!/usr/bin/env python3
import csv, pathlib, sys
p=pathlib.Path(sys.argv[1]); rows=list(csv.DictReader((p/'statistics.csv').open()))
for r in rows: print(r['time_s'],r['epsilon_volume_rel_drift'],r['liquid_mass_rel_drift'])
