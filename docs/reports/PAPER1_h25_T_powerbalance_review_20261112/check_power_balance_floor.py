#!/usr/bin/env python3
"""Read-only audit: is the 0.1% power-balance failure at h25_d100_T_fine caused by
the early residual exit, or by the mesh?

Compares each point's fine and tight records, which share an identical mesh but
were stopped at 1e-10 and 1e-11 respectively. If power balance is unchanged while
the residual falls tenfold, the imbalance is a discretisation floor, not an
unconverged field. Never launches OpenFOAM, never writes into CASE.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2')
ASSESS = Path('/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_fvm_v21_batch_20261112/execution')
OUT = Path(__file__).resolve().parent


def mesh_sha(case):
    receipt = ROOT / 'prepared' / case / 'referenceEvidence/receipt.json'
    if not receipt.is_file():
        return None
    data = json.loads(receipt.read_text())
    blob = json.dumps(data.get('mesh_sha256', {}), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def stop(case):
    receipt = ROOT / 'prepared' / case / 'referenceEvidence/receipt.json'
    if not receipt.is_file():
        return {}
    return json.loads(receipt.read_text()).get('stopping', {})


def collect():
    seen = {}
    for path in sorted(ASSESS.glob('*.assessment.json')):
        for cid, record in json.loads(path.read_text()).get('cases', {}).items():
            m = record.get('metrics') or {}
            if 'power_balance_percent' in m:
                seen[cid] = dict(cid=cid, status=record['status'],
                                 pb=m['power_balance_percent'],
                                 K=m['K_m3'],
                                 spread=m['section_flux_spread_percent'])
    rows = []
    for cid, row in sorted(seen.items()):
        meta = json.loads((ROOT / 'prepared' / cid / 'case.json').read_text())
        st = stop(cid)
        row.update(level=meta['level'], dx=meta['dx_nm'], cells=meta['expected_cells'],
                   direction=meta['direction'], h=meta['h_nm'], d=meta['d_nm'],
                   reason=st.get('actual_stop_reason'), iters=st.get('outer_iterations'),
                   threshold=st.get('threshold'),
                   comps=st.get('components', {}), mesh=mesh_sha(cid))
        rows.append(row)
    return rows


def main():
    rows = collect()
    with (OUT / 'power_balance_rows.csv').open('w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['case_id', 'h_nm', 'd_nm', 'direction', 'level', 'dx_nm', 'cells',
                    'stop_reason', 'outer_iterations', 'residual_threshold',
                    'Ux', 'Uz', 'p', 'K_m3', 'power_balance_percent', 'status',
                    'mesh_group_sha256'])
        for r in rows:
            c = r['comps']
            w.writerow([r['cid'], r['h'], r['d'], r['direction'], r['level'], r['dx'],
                        r['cells'], r['reason'], r['iters'], r['threshold'],
                        c.get('Ux'), c.get('Uz'), c.get('p'), '%.12e' % r['K'],
                        '%.6f' % r['pb'], r['status'], (r['mesh'] or '')[:16]])

    verdicts = []
    for stem in ('h75_d100_P', 'h75_d100_T', 'h50_d120_P', 'h125_d120_P'):
        fine = next((r for r in rows if r['cid'] == stem + '_fine'), None)
        tight = next((r for r in rows if r['cid'] == stem + '_tight'), None)
        if not fine or not tight:
            continue
        same = fine['mesh'] == tight['mesh']
        verdicts.append(dict(point=stem, same_mesh=same,
                             dx_equal=fine['dx'] == tight['dx'],
                             residual_ratio=(tight['comps'].get('Uz') or 0) / (fine['comps'].get('Uz') or 1),
                             pb_fine=fine['pb'], pb_tight=tight['pb'],
                             pb_delta_pp=tight['pb'] - fine['pb'],
                             pb_relative_change_percent=(tight['pb'] / fine['pb'] - 1) * 100))
    (OUT / 'power_balance_pairs.json').write_text(
        json.dumps(dict(pairs=verdicts), ensure_ascii=False, indent=2) + '\n')

    print('%-24s %-6s %-7s %-9s %8s %12s %8s %s' %
          ('case', 'level', 'dx', 'stop', 'iters', 'Uz', 'pb%', 'status'))
    for r in rows:
        if r['direction'] != 'T' and r['level'] not in ('fine', 'coarse', 'mid'):
            continue
        print('%-24s %-6s %-7s %-9s %8s %12.3e %8.4f %s' %
              (r['cid'], r['level'], r['dx'], r['reason'], r['iters'],
               r['comps'].get('Uz') or float('nan'), r['pb'], r['status']))
    print()
    print('fine vs tight (identical mesh, residual 10x tighter):')
    for v in verdicts:
        print('  %-12s same_mesh=%-5s dUz=%.1e  pb %.5f -> %.5f (%+.6f pp, %+.2f%%)' %
              (v['point'], v['same_mesh'], v['residual_ratio'], v['pb_fine'],
               v['pb_tight'], v['pb_delta_pp'], v['pb_relative_change_percent']))

    h25 = [r for r in rows if r['h'] == 25 and r['direction'] == 'T']
    pts = sorted(((r['dx'], r['pb']) for r in h25), reverse=True)
    if len(pts) >= 2:
        import math
        slopes = [math.log(pts[i][1] / pts[i + 1][1]) / math.log(pts[i][0] / pts[i + 1][0])
                  for i in range(len(pts) - 1)]
        exponent = sum(slopes) / len(slopes)
        print()
        print('h25 T power-balance vs dx: ' + ', '.join('dx=%s pb=%.5f%%' % p for p in pts))
        print('  fitted order p = %.2f' % exponent)
        print('  predicted pb at dx=0.15625 nm: %.5f%%' %
              (pts[0][1] * (0.15625 / pts[0][0]) ** exponent))


if __name__ == '__main__':
    main()
