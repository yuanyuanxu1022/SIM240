"""Replot saved scalar records; never read fields or launch a solver."""
import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAIN = ROOT / 'docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv'
AUDIT = ROOT / 'docs/reports/PAPER1_闭环方案_20261105/bound_check_44_points.csv'


def read_csv(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bounds(h_nm, d_nm, direction):
    h, d = h_nm * 1e-9, d_nm * 1e-9
    lower = h ** 3 / 12
    upper = ((h ** 3 + (h + d) ** 3) / 24 if direction == 'P'
             else h ** 3 * (h + d) ** 3 / (6 * (h ** 3 + (h + d) ** 3)))
    return lower, upper


def write_csv(name, rows):
    with (HERE / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


main, audit = read_csv(MAIN), read_csv(AUDIT)
assert len(main) == 36 and len(audit) == 46
directions = {'parallel': 'P', 'perpendicular': 'T'}
main_by_path = {r['result_path']: r for r in main}
assert len(main_by_path) == 36
audit_by_path = {r['raw_path']: r for r in audit}
assert len(audit_by_path) == 46
extra = {r['raw_path'] for r in audit if float(r['h_nm']) == 100}
set38 = set(main_by_path) | extra
assert len(extra) == 2 and len(set38) == 38
assert set38 <= set(audit_by_path)
records, rounding_deltas = [], []
for path, row in audit_by_path.items():
    direction = directions[row['direction']]
    h, d, dx = (float(row[k]) for k in ['h_nm', 'd_nm', 'dx_nm'])
    assert float(row['w_nm']) == 120
    value = float(row['K_reference_m3'])
    if path in main_by_path:
        full = main_by_path[path]
        assert (float(full['h_nm']), float(full['d_nm']), full['direction']) == (h, d, direction)
        exact_value = float(full['K_DNS_m3'])
        rounding_deltas.append(abs(value / exact_value - 1))
        value = exact_value
        source = str(MAIN.relative_to(ROOT))
    else:
        source = str(AUDIT.relative_to(ROOT))
    lower, upper = bounds(h, d, direction)
    records.append(dict(run_id=row['run_id'], h_nm=h, d_nm=d, w_nm=120,
                        direction=direction, dx_nm=dx, K_m3=value,
                        lower_m3=lower, upper_m3=upper,
                        K_over_lower=value / lower, upper_over_lower=upper / lower,
                        in_primary36=path in main_by_path, in_main38=path in set38,
                        raw_path=path, scalar_source=source))
assert max(rounding_deltas) < 1e-8  # CSV serialization precision, not solver tolerance.
records.sort(key=lambda r: (r['h_nm'], r['d_nm'], r['direction'], -r['dx_nm']))
write_csv('normalized_records.csv', records)
write_csv('record_membership.csv', [dict(raw_path=r['raw_path'],
    in_primary36=r['in_primary36'], in_main38=r['in_main38'],
    in_audit46=True, counted_occurrences_in_38_plus_46=2 if r['in_main38'] else 1)
    for r in records])

geometries = sorted({(r['h_nm'], r['d_nm']) for r in records})
assert len(geometries) == 19
assert sum(r['dx_nm'] == 5 for r in records) == 38
assert sum(r['dx_nm'] == 2.5 for r in records) == 8
below = [r['run_id'] for r in records if r['K_m3'] < r['lower_m3']]
above = [r['run_id'] for r in records if r['K_m3'] > r['upper_m3']]
assert not below and not above
metrics = {}
for direction in ['P', 'T']:
    selected = [r for r in records if r['direction'] == direction and r['in_primary36']]
    metrics[direction] = dict(count=len(selected),
        mean_lower_underestimate_percent=sum(100 * (1 - r['lower_m3'] / r['K_m3']) for r in selected) / len(selected),
        mean_upper_overestimate_percent=sum(100 * (r['upper_m3'] / r['K_m3'] - 1) for r in selected) / len(selected),
        lower_closer_count=sum(abs(r['lower_m3'] / r['K_m3'] - 1) < abs(r['upper_m3'] / r['K_m3'] - 1) for r in selected),
        maximum_upper_over_lower=max(r['upper_over_lower'] for r in records if r['direction'] == direction))
    assert len(selected) == 18 and metrics[direction]['lower_closer_count'] == 11
previous = json.loads((ROOT / 'docs/reports/PAPER1_lower_baseline_comparison_20261109/summary.json').read_text())
for direction in ['P', 'T']:
    assert math.isclose(metrics[direction]['mean_lower_underestimate_percent'], previous[direction]['mean_absolute_relative_bias_percent']['lower'], abs_tol=1e-10)
    assert math.isclose(metrics[direction]['mean_upper_overestimate_percent'], previous[direction]['mean_absolute_relative_bias_percent']['LC'], abs_tol=1e-10)

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.linewidth': .7, 'pdf.fonttype': 42, 'ps.fonttype': 42,
    'savefig.facecolor': 'white'})
fig, axes = plt.subplots(1, 2, figsize=(12.2, 8.4))
fig.subplots_adjust(left=.105, right=.91, bottom=.15, top=.82, wspace=.52)
for ax, direction, label, color in zip(axes, ['P', 'T'],
        ['(a) Along grooves', '(b) Across grooves'], ['#0072B2', '#009E73']):
    subset = [r for r in records if r['direction'] == direction]
    for y, (h, d) in enumerate(geometries):
        same = [r for r in subset if (r['h_nm'], r['d_nm']) == (h, d)]
        main_row = [r for r in same if r['dx_nm'] == 5]
        assert len(main_row) == 1
        upper = main_row[0]['upper_over_lower']
        ax.plot([1, upper], [y, y], color='#9EA4AB', lw=2, zorder=1)
        ax.plot([1, upper], [y, y], '|', color='#646B73', ms=7, zorder=2)
        for row in same:
            refined = row['dx_nm'] == 2.5
            ax.plot(row['K_over_lower'], y, marker='D' if refined else 'o',
                    ms=6 if refined else 5.5, linestyle='none', color=color,
                    markerfacecolor='white' if refined else color, markeredgewidth=1.2,
                    zorder=4 if refined else 3)
        ax.text(1.035, y, f'{upper:.2f}', transform=ax.get_yaxis_transform(),
                va='center', ha='left', fontsize=9, clip_on=False)
    ax.text(1.035, 1.035, 'U / L', transform=ax.transAxes, ha='left', fontsize=10)
    ax.set_yticks(range(len(geometries)), [f'{h:g} / {d:g}' for h, d in geometries])
    ax.set_ylim(len(geometries) - .4, -.7)
    ax.set_xscale('log')
    ax.set_xlim(.93, 80)
    ticks = [1, 2, 5, 10, 20, 50]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in ticks]))
    ax.grid(axis='x', which='major', alpha=.2)
    ax.set_axisbelow(True)
    ax.axvline(1, color='#646B73', lw=.7, ls=':')
    ax.set_title(label, loc='left', pad=19, fontsize=12, weight='bold')
    ax.set_ylabel('h / d (nm)')
    ax.set_xlabel('Conductance divided by L = h³/12 (log scale)', labelpad=10)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='y', length=0, pad=6)
fig.suptitle('Continuous bounds and saved numerical conductances', y=.97, fontsize=15)
handles = [Line2D([0], [0], color='#9EA4AB', lw=2, label='Theoretical interval [L, U]'),
    Line2D([0], [0], marker='o', color='#555555', linestyle='none', label='5 nm grid (38 records)'),
    Line2D([0], [0], marker='D', color='#555555', markerfacecolor='white', linestyle='none', label='2.5 nm grid (8 records)')]
fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .93), ncol=3, frameon=False, fontsize=10)
fig.text(.5, .055, '19 geometries in each panel; w = 120 nm, period = 240 nm. No positional jitter.\n'
    'Both panels use the same horizontal scale. Intervals are bounds, not uncertainty bars.',
    ha='center', va='center', fontsize=10)
for extension in ['png', 'pdf']:
    fig.savefig(HERE / f'interval_positions_corrected.{extension}', dpi=250)
plt.close(fig)

protected = json.loads((HERE / 'protected_inputs.json').read_text())
assert all(sha(path) == digest for path, digest in protected.items())
verification = dict(scope='Saved scalar arithmetic and figure checks; no numerical/physical acceptance',
    concatenated_row_occurrences=84, main38_unique=38, audit46_unique=46,
    overlapping_records=38, union_unique=46, geometries=19,
    intervals_per_panel=19, total_intervals=38, plotted_points=46,
    main5nm=38, refinement2p5nm=8, h100_points_plotted=2,
    lower_violations=below, upper_violations=above,
    minimum_K_over_lower=min(records, key=lambda r: r['K_over_lower']),
    max_overlap_relative_serialization_difference=max(rounding_deltas),
    primary36_metrics=metrics, protected_inputs_unchanged=len(protected),
    formula_scope='Continuous Stokes, fully liquid, constant viscosity, no slip, fixed periodic rectangular geometry')
(HERE / 'verification.json').write_text(json.dumps(verification, indent=2, ensure_ascii=False) + '\n')
manifest = dict(python=platform.python_version(), matplotlib=matplotlib.__version__,
    source_sha256={str(p.relative_to(ROOT)): sha(p) for p in [MAIN, AUDIT]},
    script_sha256=sha(__file__), precision_policy='Use full map36 values for overlap; audit CSV for remaining 10 records',
    normalization='K / (h^3/12); h,d converted nm to m; no jitter or fit',
    output_sha256={name: sha(HERE / name) for name in ['normalized_records.csv', 'record_membership.csv',
        'interval_positions_corrected.png', 'interval_positions_corrected.pdf', 'verification.json']})
(HERE / 'figure_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k: verification[k] for k in ['union_unique', 'total_intervals', 'plotted_points',
    'h100_points_plotted', 'protected_inputs_unchanged']}, ensure_ascii=False))
