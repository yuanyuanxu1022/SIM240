#!/usr/bin/env python3
import pathlib, sys
p=pathlib.Path(sys.argv[1])/'initialization_summary.txt'
print(p.read_text())
