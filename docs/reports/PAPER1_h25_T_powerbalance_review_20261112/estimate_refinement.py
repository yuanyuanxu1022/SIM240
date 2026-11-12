#!/usr/bin/env python3
"""Read-only cost/benefit estimate for refining h25_d100_T from dx=0.3125 nm.

Uses only measured wall time, peak memory and iteration counts already recorded in
the frozen receipts. Extrapolates with an explicit fitted order so the guess can be
checked later. Never launches a solver and never writes into CASE.
"""
import json
import math
from pathlib import Path

ROOT = Path('/home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2')
ASSESS = Path('/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_fvm_v21_batch_20261112/execution')


def measured(cid):
    case = ROOT / 'prepared' / cid
    meta = json.loads((case / 'case.json').read_text())
    receipt = json.loads((case / 'referenceEvidence/receipt.json').read_text())
    stop = receipt.get('stopping', {})
    res = case / 'runtime/resource.txt'
    text = res.read_text() if res.is_file() else ''
    elapsed = next((float(l.split(': ')[-1].rstrip('\n').replace('m', '').split(':')[-1])
                    for l in text.splitlines() if 'Elapsed (wall clock)' in l and l.count(':') == 2), None)
    if elapsed is None:
        clock = next((l.split('): ')[-1].strip() for l in text.splitlines()
                      if 'Elapsed (wall clock)' in l), '')
        parts = clock.split(':')
        elapsed = float(parts[-1]) + (float(parts[-2]) * 60 if len(parts) > 1 else 0)
    peak_kb = next((float(l.split(':')[-1]) for l in text.splitlines()
                    if 'Maximum resident' in l), None)
    iters = stop.get('outer_iterations') or 0
    return dict(cid=cid, dx=meta['dx_nm'], cells=meta['expected_cells'], iters=iters,
                elapsed=elapsed, peak_mb=(peak_kb / 1024 if peak_kb else None),
                per_iter=(elapsed / iters if iters else None))


def power_balance(cid):
    for path in sorted(ASSESS.glob('*.assessment.json')):
        record = json.loads(path.read_text()).get('cases', {}).get(cid)
        if record and 'metrics' in record:
            return record['metrics']['power_balance_percent']
    return None


def main():
    ladder = [measured(c) for c in ('h25_d100_T_coarse', 'h25_d100_T_mid', 'h25_d100_T_fine')]
    for row in ladder:
        row['pb'] = power_balance(row['cid'])

    # Fit the observed decay order of power balance against dx (log-log, 3 points).
    xs = [math.log(r['dx']) for r in ladder]
    ys = [math.log(r['pb']) for r in ladder]
    n = len(xs)
    slope = (n * sum(x * y for x, y in zip(xs, ys)) - sum(xs) * sum(ys)) / \
            (n * sum(x * x for x in xs) - sum(xs) ** 2)
    segments = [(ys[i] - ys[i + 1]) / (xs[i] - xs[i + 1]) for i in range(n - 1)]

    target_dx = 0.15625
    pred = ladder[-1]['pb'] * (target_dx / ladder[-1]['dx']) ** slope
    pred_min = ladder[-1]['pb'] * (target_dx / ladder[-1]['dx']) ** min(segments)
    pred_max = ladder[-1]['pb'] * (target_dx / ladder[-1]['dx']) ** max(segments)

    cells_new = ladder[-1]['cells'] * 4
    per_iter_new = ladder[-1]['per_iter'] * 4 ** 1.2
    mem_new = ladder[-1]['peak_mb'] * 4 ** 1.05
    iter_growth = [ladder[i + 1]['iters'] / ladder[i]['iters'] for i in range(n - 1)]
    growth = sum(iter_growth) / len(iter_growth)

    out = dict(
        ladder=[{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in ladder],
        fitted_order=round(slope, 3),
        segment_orders=[round(s, 3) for s in segments],
        iteration_growth_per_level=[round(g, 3) for g in iter_growth],
        iteration_growth_mean=round(growth, 3),
        prediction=dict(
            dx_nm=target_dx, cells=cells_new,
            power_balance_percent=round(pred, 5),
            range_percent=[round(pred_min, 5), round(pred_max, 5)],
            threshold_percent=0.1,
            margin_factor=round(0.1 / pred, 2)),
        cost=dict(
            per_iteration_seconds=round(per_iter_new, 4),
            expected_iterations=round(ladder[-1]['iters'] * growth),
            fine_hours=round(ladder[-1]['iters'] * growth * per_iter_new / 3600, 2),
            tight_iterations_assumed=round(ladder[-1]['iters'] * growth * 0.40),
            tight_hours=round(ladder[-1]['iters'] * growth * 0.40 * per_iter_new / 3600, 2),
            peak_memory_gb=round(mem_new / 1024, 2),
            disk_gb=round(0.158 * 4, 2),
            wall_cap_hours=12),
    )
    out['cost']['total_hours_both_levels'] = round(
        out['cost']['fine_hours'] + out['cost']['tight_hours'], 2)
    out['cost']['wall_cap_margin_hours'] = round(
        out['cost']['wall_cap_hours'] - out['cost']['fine_hours'], 2)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    (Path(__file__).resolve().parent / 'refinement_estimate.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    print('\nseen order of power balance: %s (fitted %.2f)' %
          (out['segment_orders'], slope))
    print('predicted pb at dx=%.5f nm: %.4f%% (range %.4f-%.4f%%), threshold 0.1%%'
          % (target_dx, pred, pred_min, pred_max))
    print('cells %d, per-iteration %.3f s, new peak memory %.2f GB, disk %.2f GB'
          % (cells_new, per_iter_new, mem_new / 1024, 0.158 * 4))
    print('fine %.1f h + tight %.1f h = %.1f h; wall cap 12 h leaves %.1f h margin'
          % (out['cost']['fine_hours'], out['cost']['tight_hours'],
             out['cost']['total_hours_both_levels'], out['cost']['wall_cap_margin_hours']))


if __name__ == '__main__':
    main()
