"""Read the four archived VTK frames using XML/base64/zlib only.

Does not invoke/import a solver, pvpython, VTK, or a frozen checker.
This validates stored field consistency, not physical/reference qualification.
"""
from pathlib import Path
import base64
import csv
import hashlib
import json
import math
import struct
import xml.etree.ElementTree as ET
import zlib
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = ROOT/'CASE/D_series/D2_groove_error_map/results'


def kv(p):
    return dict(x.split('=', 1) for x in p.read_text().splitlines() if '=' in x)


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def decode(node, expected_points):
    assert node.attrib['type'] == 'Float32' and node.attrib['format'] == 'binary'
    ncomp = int(node.attrib['NumberOfComponents'])
    encoded = ''.join(node.text.split())
    nblocks = struct.unpack('<I', base64.b64decode(encoded[:8])[:4])[0]
    assert nblocks == 1, 'The observed archived writer uses one zlib block'
    hlen = 4*(3+nblocks)
    nchar = 4*math.ceil(hlen/3)
    header = struct.unpack('<'+'I'*(3+nblocks), base64.b64decode(encoded[:nchar]))
    compressed = base64.b64decode(encoded[nchar:])
    assert len(compressed) == sum(header[3:])
    payload = zlib.decompress(compressed)
    assert len(payload) == header[2] == expected_points*ncomp*4
    return np.frombuffer(payload, dtype='<f4').reshape(expected_points, ncomp)


frames = []
closure = {}
for tag in ['h25_d100_dx5_T','h25_d100_dx2.5_T']:
    run = BASE/tag/'steady'
    result = kv(run/'result.txt')
    dt, dx = float(result['dt_s']), float(result['dx_m'])
    h, d, w = (float(result[k]) for k in ['mesa_gap_m','groove_depth_m','groove_width_m'])
    lx, ly = float(result['Lx_m']), float(result['Ly_m'])
    nx, ny = round(lx/dx), round(ly/dx)
    nz = round((h+d)/dx)+5
    with (run/'diagnostics.csv').open() as f:
        diagnostics = {int(v['step']): v for v in csv.DictReader(f)}

    def safe(path):
        path = path.resolve()
        assert path.is_relative_to(run.resolve()) and path.is_file() and not path.is_symlink()
        closure[str(path)] = sha(path)
        return path

    masters = list((run/'vtkData').glob('*.pvd'))
    assert len(masters) == 1
    master = safe(masters[0])
    entries = list(ET.parse(master).getroot().iter('DataSet'))
    assert [int(v.attrib['timestep']) for v in entries] == [0, int(result['steps_completed'])]
    for entry in entries:
        step = int(entry.attrib['timestep'])
        vtm = safe(master.parent/entry.attrib['file'])
        children = list(ET.parse(vtm).getroot().iter('DataSet'))
        assert len(children) == 1
        vti = safe(vtm.parent/children[0].attrib['file'])
        tree = ET.parse(vti).getroot()
        assert tree.attrib['byte_order'] == 'LittleEndian'
        assert tree.attrib['compressor'] == 'vtkZLibDataCompressor'
        img = tree.find('ImageData')
        piece = img.find('Piece')
        ext = list(map(int, piece.attrib['Extent'].split()))
        origin = np.array(list(map(float, img.attrib['Origin'].split())))
        spacing = np.array(list(map(float, img.attrib['Spacing'].split())))
        assert np.allclose(spacing, dx, rtol=1e-12, atol=0.)
        dims = [ext[2*i+1]-ext[2*i]+1 for i in range(3)]
        count = math.prod(dims)
        data = {n.attrib['Name']: decode(n, count) for n in piece.find('PointData')}
        assert set(data) == {'material','velocity_m_s','pressure_Pa','dissipation_m2_s3'}
        mat = data['material'][:, 0].reshape(dims[::-1])
        coords = [origin[i]+np.arange(ext[2*i], ext[2*i+1]+1)*spacing[i] for i in range(3)]
        x, y, z = coords
        core = ((np.arange(ext[0], ext[1]+1)>=0)&(np.arange(ext[0], ext[1]+1)<nx))[None,None,:]
        core = core & ((np.arange(ext[2], ext[3]+1)>=0)&(np.arange(ext[2], ext[3]+1)<ny))[None,:,None]
        core = core & ((np.arange(ext[4], ext[5]+1)>=0)&(np.arange(ext[4], ext[5]+1)<nz))[:,None,None]
        groove = (x >= (lx-w)/2-1e-20) & (x < (lx+w)/2-1e-20)
        analytical = np.where(z[:,None,None] < 0., 2., np.where(z[:,None,None] < h+d*groove[None,None,:]-1e-20, 1., 3.))
        analytical = np.broadcast_to(analytical, mat.shape)
        geometry_matches = bool(np.array_equal(mat[core], analytical[core]))
        mask = core & (mat == 1)
        nodes = int(mask.sum())
        assert nodes == int(result['fluid_nodes']) and geometry_matches
        vel = data['velocity_m_s'][mask.ravel()]
        pressure = data['pressure_Pa'][mask.ravel()]
        dissipation = data['dissipation_m2_s3'][mask.ravel()]
        assert np.isfinite(vel).all() and np.isfinite(pressure).all() and np.isfinite(dissipation).all()
        assert np.all(dissipation >= 0.)
        v64 = vel.astype(np.float64)
        J = v64.sum(axis=0)*dx**3/(lx*ly)
        target = np.array([float(diagnostics[step]['J'+axis]) for axis in 'xyz'])
        gamma = nodes*np.finfo(float).eps/(1-nodes*np.finfo(float).eps)
        bound = ((np.abs(np.spacing(vel)).astype(float)*.5).sum(axis=0)+gamma*np.abs(v64).sum(axis=0))*dx**3/(lx*ly)
        bound += 2*np.finfo(float).eps*np.abs(target)
        consistent = bool(np.all(np.abs(J-target) <= bound))
        assert consistent
        half = float(result['acceleration_m_s2'])*dt/2*(h+w/lx*d)
        if step == 0:
            assert abs(J[0]-half) <= bound[0]+1e-24
            assert np.all(pressure == 0.)
        frames.append({'tag': tag, 'step': step, 'fluid_nodes_read': nodes,
                       'full_core_material_matches_analytic_geometry': geometry_matches,
                       'J_from_saved_float32_m2_s': J.tolist(), 'diagnostic_J_m2_s': target.tolist(),
                       'roundoff_bound_m2_s': bound.tolist(), 'field_flux_consistent_with_export_roundoff': consistent,
                       'pressure_range_Pa': [float(pressure.min()), float(pressure.max())],
                       'reader': 'independent pure Python XML/base64/zlib/NumPy; no native reader',
                       'physical_validation': 'NOT_EVALUATED'})

assert all(sha(Path(p)) == h for p,h in closure.items())
for name, value in [('saved_fields_review.json', frames), ('saved_fields_closure_sha256.json', closure)]:
    p = OUT/name
    assert not p.exists()
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
print(json.dumps({'frames_read': len(frames), 'payload_closure_files': len(closure),
                  'all_saved_material_and_flux_checks_pass': True, 'solver_executions': 0,
                  'native_field_reader_invocations': 0, 'formal_reference_qualified': False}, indent=2))
