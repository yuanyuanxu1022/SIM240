#!/usr/bin/env python3
"""Decode future diagnostic binary snapshots without invoking a solver."""
import math
import struct
from pathlib import Path


def read_mask(path):
    raw = Path(path).read_bytes()
    assert len(raw) >= 36 and raw[:8] == b'FTMMASK1'
    count, fingerprint, nx, ny, nz = struct.unpack_from('<QQiii', raw, 8)
    assert count > 0 and (nx,ny,nz) == (192,192,145)
    assert len(raw) == 36+8*count
    ids = struct.unpack_from(f'<{count}Q', raw, 36)
    assert all(0 <= i < nx*ny*nz for i in ids)
    assert all(a < b for a,b in zip(ids,ids[1:])), 'Duplicate or out-of-order mask IDs'
    return ids, fingerprint


def read_rho(path, mask_path):
    ids, fingerprint = read_mask(mask_path)
    raw = Path(path).read_bytes()
    assert len(raw) >= 28 and raw[:8] == b'FTMRHO1\0'
    step, count, actual_hash = struct.unpack_from('<iQQ', raw, 8)
    assert 0 <= step <= 4000 and count == len(ids) and actual_hash == fingerprint
    assert len(raw) == 28+8*count
    values = struct.unpack_from(f'<{count}d', raw, 28)
    assert all(math.isfinite(r) for r in values)
    return step, ids, values
