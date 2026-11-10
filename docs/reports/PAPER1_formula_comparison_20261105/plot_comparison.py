"""Working research figure from saved scalar comparisons; no fits or solver calls."""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
with (OUT / 'comparison_36_points.csv').open() as f:
    rows = list(csv.DictReader(f))

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.labelsize': 11, 'axes.titlesize': 12,
                     'pdf.fonttype': 42, 'ps.fonttype': 42})
fig, axes = plt.subplots(1, 2, figsize=(10, 5.4))
for ax, component, label in zip(axes, ['Kxx', 'Kyy'],
                                [r'$K_{xx}$: across grooves', r'$K_{yy}$: along grooves']):
    group = [r for r in rows if r['component'] == component]
    x = np.array([float(r['OpenLB_dx5_K_m3']) for r in group])
    original = np.array([float(r['original_K_m3']) for r in group])
    corrected = np.array([float(r['V2_K_m3']) for r in group])
    lo = min(x.min(), original.min(), corrected.min()) / 1.35
    hi = max(x.max(), original.max(), corrected.max()) * 1.35
    ax.plot([lo, hi], [lo, hi], color='0.35', linestyle='--', linewidth=1,
            label='Equal values', zorder=1)
    ax.scatter(x, original, s=36, marker='s', color='#D55E00',
               facecolors='none', linewidths=1.2, label='Original formula', zorder=3)
    ax.scatter(x, corrected, s=31, marker='o', color='#0072B2',
               label='Existing V2', zorder=4)
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel(r'OpenLB, $\Delta x=5$ nm ($\mathrm{m^3}$)')
    ax.set_ylabel(r'Formula prediction ($\mathrm{m^3}$)')
    ax.set_title(label, loc='left')
    ax.grid(which='major', alpha=.18)
    ax.spines[['top', 'right']].set_visible(False)
    if component == 'Kxx':
        bad = next(r for r in group if r['run_id'] == 'h25_d100_dx5_T')
        bx, by = float(bad['OpenLB_dx5_K_m3']), float(bad['V2_K_m3'])
        ax.scatter([bx], [by], s=95, facecolors='none', edgecolors='#CC79A7',
                   linewidths=1.6, zorder=5)
        ax.annotate('h=25, d=100 nm\nV2: -18.71%', xy=(bx, by),
                    xytext=(.11, .34), textcoords='axes fraction', fontsize=9,
                    arrowprops={'arrowstyle': '->', 'color': '#CC79A7'},
                    bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .85})
    ax.legend(loc='lower right', fontsize=8, frameon=True)

fig.subplots_adjust(left=.08, right=.985, top=.91, bottom=.25, wspace=.32)
fig.text(.08, .12, '18 geometries / 36 direction points; P=240 nm, w=120 nm.', fontsize=10)
fig.text(.08, .075, 'Retrospective comparison; V2 coefficients unchanged. Reference uncertainty is not established.', fontsize=9)
fig.text(.08, .035, 'Each panel uses equal log scales on x and y; plotting limits differ between panels.', fontsize=9, color='0.3')
for ext in ('png', 'pdf', 'svg'):
    fig.savefig(OUT / ('formula_comparison.' + ext), dpi=300, facecolor='white')
plt.close(fig)
(OUT / 'figure_metadata.json').write_text(json.dumps({
    'matplotlib': matplotlib.__version__, 'numpy': np.__version__,
    'source': 'comparison_36_points.csv', 'points_per_panel_per_model': 18,
    'axes': 'log-log; equal aspect and limits within each panel',
    'reference_uncertainty': 'not established; no error bars supplied',
    'exclusions': [], 'coefficients_refit': False,
    'purpose': 'working research comparison, not independent validation',
    'exports': ['formula_comparison.png', 'formula_comparison.pdf', 'formula_comparison.svg']
}, indent=2) + '\n')
print('Wrote PNG/PDF/SVG and figure_metadata.json.')
