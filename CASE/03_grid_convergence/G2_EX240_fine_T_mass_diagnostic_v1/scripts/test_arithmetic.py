#!/usr/bin/env python3
"""Python arithmetic/schema reference tests; no C++ build, no LBM stepping."""
import csv
import json
import math
import struct
import tempfile
from pathlib import Path

import numpy as np
from snapshot_format import read_mask, read_rho
from check_static import check, CASE, ROOT


class Neumaier:
    def __init__(self):
        self.s = self.c = 0.

    def add(self, value):
        nxt = self.s+value
        self.c += (self.s-nxt)+value if abs(self.s)>=abs(value) else (value-nxt)+self.s
        self.s = nxt

    def value(self):
        return self.s+self.c


def totals(values):
    acc = Neumaier()
    for value in values:
        acc.add(value)
    return acc.value()


def main():
    result = check()
    n, dx = 3686400, 1.25e-9
    term = 1.*1000.*dx*dx*dx
    seq = comp = None
    acc = Neumaier()
    seq = 0.
    for _ in range(n):
        seq += term
        acc.add(term)
    comp = acc.value()
    assert seq == 7.1999999993792838e-18
    assert comp == math.fsum([term]*n)
    assert abs(comp/(n*term)-1) <= 2e-16
    extended = np.cumsum(np.full(n, np.longdouble(1000.)*np.longdouble(dx)**3,
                                 dtype=np.longdouble), dtype=np.longdouble)[-1]
    wide_bits = np.finfo(np.longdouble).nmant+1
    assert wide_bits > 53
    assert abs(float(extended/(np.longdouble(n)*1000*np.longdouble(dx)**3)-1)) < 1e-13
    cancellation = [1e16,1.,-1e16]*1000
    assert totals(cancellation) == math.fsum(cancellation) == 1000.
    balanced = [1.+2**-30,1.-2**-30]*4000
    assert totals(r-1. for r in balanced) == 0
    assert totals(reversed(balanced)) == math.fsum(balanced)
    # Independently stored double final slice; do not claim transient rho exists.
    field = ROOT/'CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800/runs/dx1p25/EX240_perpendicular/steady/field_slice.csv'
    with field.open(newline='') as fh:
        rho = [float(row['rho']) for row in csv.DictReader(fh)]
    assert len(rho)==19200
    stable_mean = math.fsum(r-1 for r in rho)/len(rho)
    assert abs(stable_mean-9.372583727647783e-15)<1e-28
    delta_comp = totals(r-1 for r in rho)
    assert delta_comp == math.fsum(r-1 for r in rho)
    # Schema round-trip in a temporary directory, including failure injection.
    with tempfile.TemporaryDirectory(prefix='fine_t_schema_') as tmp:
        mask, snap = Path(tmp)/'mask.bin', Path(tmp)/'rho.bin'
        ids, fingerprint = [0,1,145], 12345
        mask.write_bytes(b'FTMMASK1'+struct.pack('<QQiii',3,fingerprint,192,192,145)+struct.pack('<3Q',*ids))
        snap.write_bytes(b'FTMRHO1\0'+struct.pack('<iQQ',625,3,fingerprint)+struct.pack('<3d',1.,1.+2**-30,1.-2**-30))
        step, got_ids, values=read_rho(snap,mask)
        assert step==625 and list(got_ids)==ids and math.fsum(r-1 for r in values)==0
        invalid=0
        bad_masks=[[],[0,0,145],[0,145,1]]
        for bad_ids in bad_masks:
            mask.write_bytes(b'FTMMASK1'+struct.pack('<QQiii',len(bad_ids),fingerprint,192,192,145)+struct.pack(f'<{len(bad_ids)}Q',*bad_ids))
            try: read_mask(mask)
            except AssertionError: invalid+=1
        mask.write_bytes(b'FTMMASK1'+struct.pack('<QQiii',3,fingerprint,192,192,145)+struct.pack('<3Q',*ids))
        for raw in [snap.read_bytes()[:-1],b'FTMRHO1\0'+struct.pack('<iQQ',625,3,fingerprint+1)+struct.pack('<3d',1.,1.,1.),
                    b'FTMRHO1\0'+struct.pack('<iQQ',625,3,fingerprint)+struct.pack('<3d',1.,float('nan'),1.)]:
            snap.write_bytes(raw)
            try: read_rho(snap,mask)
            except AssertionError: invalid+=1
        assert invalid==6
    result.update({'arithmetic_reference_PASS':True,'binary_schema_reference_PASS':True,
                   'legacy_initial_mass_exact_replay':seq,'compensated_initial_mass':comp,
                   'initial_relative_bias':seq/(n*term)-1,'numpy_long_double_mantissa_bits':wide_bits,
                   'long_double_constant_relative_bias':float(extended/(np.longdouble(n)*1000*np.longdouble(dx)**3)-1),
                   'final_slice_stable_mean_delta_rho':stable_mean,'invalid_schema_cases_rejected':invalid,
                   'scope':'Python reference arithmetic and static source checks; actual C++ implementation uncompiled'})
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
