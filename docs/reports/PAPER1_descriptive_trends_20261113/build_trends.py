from pathlib import Path
import csv
import json
import math
import hashlib

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = ROOT / 'docs/reports/PAPER1_descriptive_trends_20261113'
DOE = ROOT / 'docs/reports/PAPER1_V2_coefficient_choice_audit_20261110/fixed_V2_primary36_checked.csv'
FVM = ROOT / 'docs/reports/PAPER1_teacher_workorder_audit_20261112/current_fvm_v21_assessment.json'

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'axes.edgecolor': '#888780',
    'axes.linewidth': 0.7,
    'grid.color': '#D3D1C7',
    'grid.linewidth': 0.5,
    'grid.alpha': 0.55,
})

D_VALUES = [25, 50, 75, 100, 120]
H_VALUES = [25, 50, 75, 125]
D_COLORS = {25: '#185FA5', 50: '#0F6E56', 75: '#534AB7', 100: '#BA7517', 120: '#993C1D'}
D_MARKERS = {25: 'o', 50: 's', 75: '^', 100: 'D', 120: 'P'}
H_COLORS = {25: '#888780', 50: '#185FA5', 75: '#0F6E56', 125: '#993C1D'}
H_MARKERS = {25: 'D', 50: 'o', 75: '^', 125: 's'}
DIR_NAME = {'P': '沿槽 P', 'T': '横槽 T'}


def save(fig, stem):
    fig.savefig(OUT / f'{stem}.png', bbox_inches='tight', facecolor='white')
    fig.savefig(OUT / f'{stem}.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def write_csv(path, rows, fields):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def load_doe():
    rows = []
    with DOE.open() as f:
        for r in csv.DictReader(f):
            x = {
                'h_nm': int(float(r['h_nm'])),
                'd_nm': int(float(r['d_nm'])),
                'direction': r['direction'],
                'd_over_w': float(r['d_over_w']),
                'h_over_w': float(r['h_over_w']),
                'F_star_Kref_over_KLC': float(r['required_F_for_exact_discrete_K']),
                'F_V2_fixed': float(r['fixed_V2_F']),
                'V2_signed_residual_percent': float(r['V2_residual_percent']),
                'raw_result_path': r['raw_result_path'],
            }
            x['LC_signed_error_percent'] = (1 / x['F_star_Kref_over_KLC'] - 1) * 100
            check = (x['F_V2_fixed'] / x['F_star_Kref_over_KLC'] - 1) * 100
            if abs(check - x['V2_signed_residual_percent']) > 1e-9:
                raise ValueError(f"V2 identity mismatch: {x}")
            x['matrix_role'] = 'h25_thin_gap_listed_separately' if x['h_nm'] == 25 else 'regular_3x5_matrix'
            rows.append(x)
    if len(rows) != 36 or len({(r['h_nm'], r['d_nm']) for r in rows}) != 18:
        raise ValueError('expected 36 records and 18 geometries')
    return rows


def panel_vs_h(ax, rows, direction, value_key, title, ylab):
    ax.set_title(title)
    ax.set_xlabel('间隙 h (nm)')
    ax.set_ylabel(ylab)
    ax.grid(True)
    ax.axhline(0, color='#5F5E5A', lw=0.8)
    for d in D_VALUES:
        main = sorted((r for r in rows if r['direction'] == direction and r['d_nm'] == d and r['h_nm'] != 25), key=lambda r: r['h_nm'])
        ax.plot([r['h_nm'] for r in main], [r[value_key] for r in main], color=D_COLORS[d], marker=D_MARKERS[d], ms=4.5, lw=1.5, label=f'd={d} nm')
        thin = [r for r in rows if r['direction'] == direction and r['d_nm'] == d and r['h_nm'] == 25]
        for r in thin:
            ax.scatter([25], [r[value_key]], s=48, marker='D', facecolors='white', edgecolors=D_COLORS[d], linewidths=1.4, zorder=5)
    ax.set_xticks(H_VALUES)


def panel_vs_d(ax, rows, direction, value_key, title, ylab):
    ax.set_title(title)
    ax.set_xlabel('槽深 d (nm)')
    ax.set_ylabel(ylab)
    ax.grid(True)
    ax.axhline(0, color='#5F5E5A', lw=0.8)
    for h in H_VALUES:
        pts = sorted((r for r in rows if r['direction'] == direction and r['h_nm'] == h), key=lambda r: r['d_nm'])
        ax.plot([r['d_nm'] for r in pts], [r[value_key] for r in pts], color=H_COLORS[h], marker=H_MARKERS[h], ms=4.5, lw=1.4, ls=':' if h == 25 else '-', markerfacecolor='white' if h == 25 else H_COLORS[h], label=f'h={h} nm' + ('（薄隙单列）' if h == 25 else ''))
    ax.set_xticks(D_VALUES)


def doe_figures(rows):
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))
    for j, direction in enumerate(['P', 'T']):
        panel_vs_h(axes[0, j], rows, direction, 'LC_signed_error_percent', f'{DIR_NAME[direction]}：原公式偏差', '原公式相对 5 nm OpenLB 偏差 (%)')
        panel_vs_h(axes[1, j], rows, direction, 'V2_signed_residual_percent', f'{DIR_NAME[direction]}：V2 有符号残差', 'V2 相对 5 nm OpenLB 残差 (%)')
    handles = [Line2D([0], [0], color=D_COLORS[d], marker=D_MARKERS[d], lw=1.5, ms=4.5, label=f'd={d}') for d in D_VALUES]
    handles.append(Line2D([0], [0], color='#5F5E5A', marker='D', markerfacecolor='white', lw=0, ms=5, label='h=25 薄隙点'))
    fig.legend(handles=handles, loc='lower center', ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle('已有数据的描述性趋势：固定槽深看间隙（18 几何全部保留）', fontsize=13, y=0.995)
    fig.text(0.5, 0.955, '实线只连接 h=50/75/125 的已采样点；h=25 三点以空心菱形单列，不作精度域判定', ha='center', fontsize=9, color='#5F5E5A')
    fig.tight_layout(rect=[0, 0.055, 1, 0.90])
    save(fig, 'FIG1_DOE_trends_fixed_d')

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))
    for j, direction in enumerate(['P', 'T']):
        panel_vs_d(axes[0, j], rows, direction, 'LC_signed_error_percent', f'{DIR_NAME[direction]}：原公式偏差', '原公式相对 5 nm OpenLB 偏差 (%)')
        panel_vs_d(axes[1, j], rows, direction, 'V2_signed_residual_percent', f'{DIR_NAME[direction]}：V2 有符号残差', 'V2 相对 5 nm OpenLB 残差 (%)')
    handles = [Line2D([0], [0], color=H_COLORS[h], marker=H_MARKERS[h], lw=1.4, ls=':' if h == 25 else '-', markerfacecolor='white' if h == 25 else H_COLORS[h], ms=4.5, label=f'h={h}') for h in H_VALUES]
    fig.legend(handles=handles, loc='lower center', ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle('已有数据的描述性趋势：固定间隙看槽深（18 几何全部保留）', fontsize=13, y=0.995)
    fig.text(0.5, 0.955, 'h=25 仅有 d=25/50/100 三个已采样点，用虚线和空心菱形单列；未采样组合不插补', ha='center', fontsize=9, color='#5F5E5A')
    fig.tight_layout(rect=[0, 0.055, 1, 0.90])
    save(fig, 'FIG2_DOE_trends_fixed_h')

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.1))
    for j, direction in enumerate(['P', 'T']):
        ax = axes[j]
        ax.grid(True)
        ax.set_title(f'{DIR_NAME[direction]}：所需因子与固定 V2 因子')
        ax.set_xlabel('深宽比 d / w（w=120 nm）')
        ax.set_ylabel('F* = Kref / KLC；FV2')
        for h in H_VALUES:
            pts = sorted((r for r in rows if r['direction'] == direction and r['h_nm'] == h), key=lambda r: r['d_over_w'])
            ax.plot([r['d_over_w'] for r in pts], [r['F_star_Kref_over_KLC'] for r in pts], color=H_COLORS[h], marker=H_MARKERS[h], ms=4.5, lw=1.4, ls=':' if h == 25 else '-', markerfacecolor='white' if h == 25 else H_COLORS[h], label=f'h={h}')
        f_v2 = sorted({(r['d_over_w'], r['F_V2_fixed']) for r in rows if r['direction'] == direction})
        ax.plot([r[0] for r in f_v2], [r[1] for r in f_v2], color='#2C2C2A', lw=2, ls='--', label='固定 V2')
        ax.legend(frameon=False, ncol=2)
    fig.suptitle('所需修正因子仍随 h 变化；V2 乘性因子只保留 d/w', fontsize=13)
    fig.text(0.5, 0.91, '描述已采样离散参考，不证明连续模型的唯一成因或独立预测精度', ha='center', fontsize=9, color='#5F5E5A')
    fig.tight_layout(rect=[0, 0, 1, 0.86])
    save(fig, 'FIG3_DOE_required_factor')


def fvm_outputs():
    saved = json.loads(FVM.read_text())
    comparisons = saved['comparisons']
    order = ['h75_d100_P', 'h50_d120_P', 'h125_d120_P', 'h75_d100_T', 'h25_d100_T', 'h125_d120_T']
    fields = ['point', 'direction', 'reference_accepted', 'consistency_2percent', 'Kref_m3', 'delta_K_percent', 'grid_fine_mid_percent', 'algebraic_change_percent', 'LC_error_percent', 'V2_error_percent', 'V2_improved', 'claim_scope']
    out = []
    for point in order:
        r = next(x for x in comparisons if x['point'] == point)
        accepted = r.get('reference_accepted', False)
        out.append({
            'point': point,
            'direction': point.rsplit('_', 1)[-1],
            'reference_accepted': accepted,
            'consistency_2percent': r.get('status') if accepted else 'NA',
            'Kref_m3': r.get('Kref_m3', 'NA'),
            'delta_K_percent': r.get('delta_K_percent', 'NA'),
            'grid_fine_mid_percent': r.get('grid_fine_mid_percent', 'NA'),
            'algebraic_change_percent': r.get('algebraic_change_percent', 'NA'),
            'LC_error_percent': r.get('LC_error_percent', 'NA'),
            'V2_error_percent': r.get('V2_error_percent', 'NA'),
            'V2_improved': r.get('V2_improved', 'NA'),
            'claim_scope': 'qualified single-direction FVM comparison' if accepted else 'no qualified reference; no delta assigned',
        })
    write_csv(OUT / 'FVM_CLAIM_EVIDENCE.csv', out, fields)

    b = saved['baseline']
    kp = next(x for x in comparisons if x['point'] == 'h75_d100_P')
    kt = next(x for x in comparisons if x['point'] == 'h75_d100_T')
    a_v2 = b['Aref'] * (1 + kp['V2_error_percent'] / 100) / (1 + kt['V2_error_percent'] / 100)
    beta_v2 = math.degrees(math.atan(1 / a_v2))
    derived = {
        'geometry': 'h75_d100',
        'Aref': b['Aref'],
        'ALC': b['ALC'],
        'AV2_derived_from_same_pair': a_v2,
        'ALC_minus_Aref_percent': b['ALC_vs_reference_percent'],
        'beta_ref_deg': b['beta_ref_deg'],
        'betaLC_deg': b['betaLC_deg'],
        'betaV2_derived_deg': beta_v2,
        'betaLC_minus_reference_deg': b['betaLC_minus_reference_deg'],
        'betaV2_minus_reference_deg': beta_v2 - b['beta_ref_deg'],
        'A5_nm_OpenLB': b['A5'],
        'beta5_nm_OpenLB_deg': b['beta5_deg'],
        'independent_geometry_count': 1,
        'note': 'A and beta are derived from the same pair of K values; they do not add independent samples and do not replace the original 5nm statistics.',
    }
    (OUT / 'FVM_BASELINE_DERIVED.json').write_text(json.dumps(derived, ensure_ascii=False, indent=2) + '\n')

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.5))
    ax = axes[0, 0]
    qual = [next(x for x in comparisons if x['point'] == p) for p in order[:4]]
    labels = ['h75/d100 P', 'h50/d120 P', 'h125/d120 P', 'h75/d100 T']
    vals = [r['delta_K_percent'] for r in qual]
    colors = ['#185FA5' if r['status'] == 'PASS' else '#993C1D' for r in qual]
    bars = ax.bar(labels, vals, color=colors, width=0.65)
    ax.axhline(2, color='#993C1D', ls='--', lw=1.2, label='2% 一致性线')
    ax.set_ylabel('K5 / KFVM − 1 (%)')
    ax.set_title('四条合格参考：一致性判定与参考资格分开')
    ax.tick_params(axis='x', rotation=15)
    ax.grid(axis='y')
    ax.legend(frameon=False)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.07, f'{v:.3f}%', ha='center', fontsize=9)

    ax = axes[0, 1]
    x = [0, 1]
    width = 0.34
    lc = [kp['LC_error_percent'], kt['LC_error_percent']]
    v2 = [kp['V2_error_percent'], kt['V2_error_percent']]
    b1 = ax.bar([i-width/2 for i in x], lc, width, color='#888780', label='原公式')
    b2 = ax.bar([i+width/2 for i in x], v2, width, color='#185FA5', label='V2')
    ax.set_xticks(x, ['沿槽 P', '横槽 T'])
    ax.set_ylabel('相对合格 FVM 参考的偏差 (%)')
    ax.set_title('基准几何：换参考后 V2 改善仍存在')
    ax.grid(axis='y')
    ax.legend(frameon=False)
    for bars in [b1, b2]:
        for bar in bars:
            v = bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2, v+3, f'{v:.2f}%', ha='center', fontsize=9)

    ax = axes[1, 0]
    bars = ax.bar(['FVM 参考', '原公式', 'V2'], [b['Aref'], b['ALC'], a_v2], color=['#0F6E56', '#888780', '#185FA5'], width=0.6)
    ax.set_ylabel('各向异性比 A = Kyy / Kxx')
    ax.set_title('基准几何：原公式方向比仍高估 64.41%')
    ax.grid(axis='y')
    for bar in bars:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.08, f'{bar.get_height():.4f}', ha='center', fontsize=9)

    ax = axes[1, 1]
    bars = ax.bar(['FVM 参考', '原公式', 'V2'], [b['beta_ref_deg'], b['betaLC_deg'], beta_v2], color=['#0F6E56', '#888780', '#185FA5'], width=0.6)
    ax.set_ylabel('45° 驱动下重建平均流向角 (°)')
    ax.set_title('基准几何：原公式角差 −8.84°')
    ax.grid(axis='y')
    for bar in bars:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.35, f'{bar.get_height():.3f}°', ha='center', fontsize=9)

    fig.suptitle('FVM 独立方法对照：只支持所列代表方向，不替换原 36 条 5 nm 统计', fontsize=13, y=0.995)
    fig.text(0.5, 0.955, '（b–d）均来自 h75/d100 同一对主值；A 与流向角不增加独立几何数', ha='center', fontsize=9, color='#5F5E5A')
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    save(fig, 'FIG4_FVM_reference_and_baseline')
    return saved, out, derived


def representative_points():
    rows = [
        {
            'geometry': 'h75/d100', 'directions': 'P+T', 'current_status': 'paired qualified references; T consistency FAIL retained',
            'scientific_job': '基准成对对照：换方法后各向异性失真和V2改善是否仍存在',
            'if_selected_completion': '已完成现有对照；报告Aref、ALC、重建角差及原公式/V2偏差',
            'stop_rule': '不重跑追求2% PASS；T FAIL作为方法间差异结果保留', 'execution_authorized': False,
        },
        {
            'geometry': 'h50/d120', 'directions': 'T（P已有合格参考）', 'current_status': 'P qualified; T has no frozen case directory',
            'scientific_job': '若允许代表性缩减，优先补齐成对主值；检验原公式沿槽高偏差代表几何的各向异性',
            'scientific_job_note': '',
            'if_selected_completion': '新T方向按另行审定协议完成参考资格；分别报告2%一致性PASS/FAIL与公式偏差',
            'stop_rule': '取得合格参考并出比较结果，或按预定失败/未解决记录停止；不为通过2%反复续算', 'execution_authorized': False,
        },
        {
            'geometry': 'h100/d100', 'directions': 'P+T（若需加强固定d的间隙响应对照）', 'current_status': 'only existing 5nm OpenLB comparison; no qualified FVM pair',
            'scientific_job': '与h75/d100成对参考比较，在d=100固定时观察h=75到100的变化；不能只补T就声称独立各向异性',
            'if_selected_completion': 'P与T两方向都取得合格参考，再导出一对A和重建角；明确两个间隙不能定位精确过零点',
            'stop_rule': '两方向各自以合格/失败/未解决收口；若只完成一方向，不报告该几何独立各向异性', 'execution_authorized': False,
        },
        {
            'geometry': 'h125/d120', 'directions': 'T（P已有合格参考）', 'current_status': 'P qualified; original T fine exit124, no complete evidence',
            'scientific_job': '是否补此深槽点取决于老师选定的点集；它不能替代h50T或h100T',
            'if_selected_completion': '先审现有运行和停止证据；如需续算/改配置须另定协议，不把慢收敛称为残差地板',
            'stop_rule': '无新协议不续算；未合格方向标NA，不以P单独组成各向异性', 'execution_authorized': False,
        },
        {
            'geometry': 'h25/d100', 'directions': 'T', 'current_status': 'original fine REFERENCE_CHECK_FAIL; refined local result not qualified',
            'scientific_job': '薄隙边界的诊断记录，不用计算困难证明h25物理不重要',
            'if_selected_completion': '仅当老师保留该点时，审完整release/来源/同网格tight/接收链；功率单项不构成资格',
            'stop_rule': '原FAIL保留；不为消除FAIL自动逐级加密或改写门槛', 'execution_authorized': False,
        },
    ]
    for r in rows:
        r.pop('scientific_job_note', None)
    fields = ['geometry', 'directions', 'current_status', 'scientific_job', 'if_selected_completion', 'stop_rule', 'execution_authorized']
    write_csv(OUT / 'REPRESENTATIVE_POINT_RESPONSIBILITIES.csv', rows, fields)
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_doe()
    ordered = sorted(rows, key=lambda r: (r['direction'], r['h_nm'], r['d_nm']))
    fields = ['h_nm', 'd_nm', 'direction', 'd_over_w', 'h_over_w', 'matrix_role', 'F_star_Kref_over_KLC', 'F_V2_fixed', 'LC_signed_error_percent', 'V2_signed_residual_percent', 'raw_result_path']
    write_csv(OUT / 'DOE_TRENDS_36.csv', ordered, fields)
    doe_figures(rows)
    saved, fvm_rows, derived = fvm_outputs()
    rep = representative_points()
    verification = {
        'role': 'descriptive offline recomputation and plotting only',
        'doe_input': str(DOE.relative_to(ROOT)),
        'doe_input_sha256': hashlib.sha256(DOE.read_bytes()).hexdigest(),
        'fvm_input': str(FVM.relative_to(ROOT)),
        'fvm_input_sha256': hashlib.sha256(FVM.read_bytes()).hexdigest(),
        'doe_records': len(rows),
        'doe_geometries': len({(r['h_nm'], r['d_nm']) for r in rows}),
        'regular_matrix_geometries': len({(r['h_nm'], r['d_nm']) for r in rows if r['h_nm'] != 25}),
        'thin_gap_geometries_listed_separately': len({(r['h_nm'], r['d_nm']) for r in rows if r['h_nm'] == 25}),
        'v2_identity_max_abs_error_percent': max(abs((r['F_V2_fixed']/r['F_star_Kref_over_KLC']-1)*100-r['V2_signed_residual_percent']) for r in rows),
        'qualified_fvm_direction_records': sum(r['reference_accepted'] for r in fvm_rows),
        'paired_fvm_geometries': 1,
        'new_simulations': 0,
        'new_reference_qualification': False,
        'p_values_reported': False,
        'strict_error_lower_bound_claimed': False,
        'h125_residual_floor_claimed': False,
        'execution_authorized_for_proposed_points': False,
        'A_V2_derived': derived['AV2_derived_from_same_pair'],
        'beta_V2_derived_deg': derived['betaV2_derived_deg'],
        'outputs': sorted(p.name for p in OUT.iterdir() if p.suffix in {'.png', '.pdf', '.csv', '.json'}),
    }
    (OUT / 'VERIFICATION.json').write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
