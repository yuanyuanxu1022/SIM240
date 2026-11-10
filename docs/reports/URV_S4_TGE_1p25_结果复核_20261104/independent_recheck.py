"""1.25 nm 服务器重跑：独立复算（不采信 result.txt 的 K）

只读从服务器取回的证据，用原始诊断数据重算 K 与统计窗，
再逐项核对 result.txt / acceptance.json / completion.json 的一致性。
不写服务器、不改任何源证据、不启动任何计算。
"""
from pathlib import Path
import csv, json, math, re

HERE = Path(__file__).resolve().parent
EV = HERE / 'server_evidence'

# ---- 冻结的物理输入（来自 result.txt / run_config，非拟合） ----
MU = 0.001            # Pa s
RHO = 1000.0          # kg m^-3
ACC = 100000.0        # m s^-2
WINDOW = 2592
REF_K_LOCAL = 3.471791836744987e-24   # 本机 1.25nm 参照（测量前冻结）
RTOL = 1e-6


def kv(path):
    d = {}
    for line in path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            d[k.strip()] = v.strip()
    return d


def num(s):
    return float(s)


# ---- 1. 从 diagnostics.csv 独立读 J ----
# 检查器 evidence.py:125 用 w.std(axis=1, ddof=1)/|mean|，即「样本标准差」(n-1)，
# 且它核对原始诊断的容差是 rtol=1e-5。本复算与它对齐，避免口径不同造成假警报。
rows = []
diag_tail = {}
with (EV / 'diagnostics.csv').open() as f:
    for r in csv.DictReader(f):
        rows.append(float(r['J']))
        diag_tail = r          # 保留最后一行原始诊断，用于交叉核对

last_J = rows[-1]
win = rows[-WINDOW:]
win_mean = math.fsum(win) / len(win)
win_std = math.sqrt(math.fsum((x - win_mean) ** 2 for x in win) / (len(win) - 1))  # ddof=1
win_span = max(win) - min(win)
rel_std = win_std / win_mean
rel_span = win_span / win_mean

# K = J * mu / (rho * a)   [J 是 m^2/s 的体积通量, (rho*a) 是体力密度]
K_from_last = last_J * MU / (RHO * ACC)
K_from_window = win_mean * MU / (RHO * ACC)

# ---- 2. 读服务器原始结果 ----
res = kv(EV / 'result.txt')
K_server = num(res['Keff_m3'])
J_server = num(res['J_main_m2_s'])
steps = int(res['steps_completed'])

# ---- 3. 读验收回执 ----
acc = json.loads((EV / 'acceptance.json').read_text())
comp = json.loads((EV / 'completion.json').read_text())
ba = kv(EV / 'boundary_audit.txt')
formal = json.loads((EV / 'formal_run_record.json').read_text())

# ---- 4. 逐项核对 ----
checks = []

def chk(name, ok, detail):
    checks.append(dict(item=name, pass_=bool(ok), detail=detail))

chk('独立复算 K 与 result.txt 一致（相对差<1e-12）',
    abs(K_from_last - K_server) / K_server < 1e-12,
    f'recalc={K_from_last:.17e}  result={K_server:.17e}  rel={abs(K_from_last-K_server)/K_server:.3e}')
chk('独立复算 J 与 result.txt 一致',
    abs(last_J - J_server) / J_server < 1e-12,
    f'recalc={last_J:.17e}  result={J_server:.17e}')
chk('统计窗步数 = 2592', len(win) == WINDOW, f'len(win)={len(win)}')
chk('诊断行数 = 步数+1', len(rows) == steps + 1, f'rows={len(rows)}  steps={steps}')
chk('窗口相对标准差与 acceptance.json 一致（rtol=1e-5，与检查器自身容差相同）',
    abs(rel_std - acc['scalar']['final_window_std']) / acc['scalar']['final_window_std'] < 1e-5,
    f'recalc(ddof=1)={rel_std:.10e}  acceptance={acc["scalar"]["final_window_std"]:.10e}')
chk('窗口相对标准差与原始诊断末行一致（rtol=1e-5）',
    abs(rel_std - float(diag_tail['window_rel_std'])) / float(diag_tail['window_rel_std']) < 1e-5,
    f'recalc={rel_std:.10e}  diagnostics={diag_tail["window_rel_std"]}')
chk('窗口相对极差与 acceptance.json 一致',
    abs(rel_span - acc['scalar']['final_window_span']) / acc['scalar']['final_window_span'] < 1e-9,
    f'recalc={rel_span:.10e}  acceptance={acc["scalar"]["final_window_span"]:.10e}')
chk('几何 fluid_nodes = 2064384', ba['material_1'] == '2064384', ba['material_1'])
chk('边界 q 全部 = 0.5', ba['q_min'] == '0.5' and ba['installed_q_max'] == '0.5',
    f'q_min={ba["q_min"]}  installed_q_max={ba["installed_q_max"]}')
chk('无回退/无未解析链接',
    ba['geometric_fallback_count'] == '0' and ba['unresolved_link_count'] == '0',
    f'fallback={ba["geometric_fallback_count"]}  unresolved={ba["unresolved_link_count"]}')
chk('质量守恒 max < 1e-12', num(res['max_mass_abs_relative']) < 1e-12,
    res['max_mass_abs_relative'])
chk('Mach < 0.05', num(res['max_Mach']) < 0.05, res['max_Mach'])
chk('exit_code = 0 / 收敛 / 非超时 / 非资源停止',
    (EV / 'exit_code.txt').read_text().strip() == '0'
    and res['converged'] == 'true'
    and comp.get('timed_out') is False
    and comp.get('resource_stop_reason') is None,
    f'exit={(EV/"exit_code.txt").read_text().strip()} converged={res["converged"]} '
    f'timed_out={comp.get("timed_out")} resource_stop={comp.get("resource_stop_reason")}')
chk('输入闭包运行前后未变', comp.get('inputs_unchanged') is True,
    str(comp.get('inputs_unchanged')))
chk('构建等价 PASS（acceptance）', acc.get('BUILD_EQUIVALENCE_PASS') is True,
    str(acc.get('BUILD_EQUIVALENCE_PASS')))
rel_to_local = abs(K_from_last - REF_K_LOCAL) / REF_K_LOCAL
chk('独立复算 K 与本机参照相对差 <= 1e-6', rel_to_local <= RTOL,
    f'|recalc - local|/local = {rel_to_local:.6e}  (门槛 {RTOL:g})')
chk('正式回执 BUILD_EQUIVALENCE_PASS', formal.get('BUILD_EQUIVALENCE_PASS') is True,
    str(formal.get('BUILD_EQUIVALENCE_PASS')))

# 边界：不得把构建等价误当阶段接受
boundary_ok = (acc.get('S4_stage_accepted') if 'S4_stage_accepted' in acc
               else acc.get('original_S4_stage_accepted')) is False
chk('未把构建等价误写为 S4 阶段接受', boundary_ok,
    f'original_S4_stage_accepted={acc.get("original_S4_stage_accepted")}  '
    f'RESULT_PASS={acc.get("RESULT_PASS")}')

# ---- 5. 实测开销（run.log 的 /usr/bin/time -v） ----
log = (EV / 'run.log').read_text()
def grab(pat):
    m = re.search(pat, log)
    return m.group(1).strip() if m else None
peak_kb = grab(r'Maximum resident set size \(kbytes\): (\d+)')
elapsed = grab(r'Elapsed \(wall clock\).*: (.+)')
perf = acc.get('measured_performance', {})

out = dict(
    run_id=res['run_id'],
    independent_recalculation=dict(
        K_from_last_step_m3=K_from_last, K_from_window_mean_m3=K_from_window,
        J_last_m2_s=last_J, J_window_mean_m2_s=win_mean,
        window_steps=WINDOW, window_rel_std=rel_std, window_rel_span=rel_span,
        formula='K = J * mu / (rho * a)', mu=MU, rho=RHO, a=ACC),
    reported=dict(K_m3=K_server, J_m2_s=J_server, steps=steps,
                  window_rel_std=acc['scalar']['final_window_std'],
                  window_rel_span=acc['scalar']['final_window_span']),
    build_equivalence=dict(reference_local_K_m3=REF_K_LOCAL,
                           independent_relative_difference=rel_to_local,
                           tolerance=RTOL,
                           acceptance_relative_difference=acc['build_equivalence']['relative_difference']),
    measured_performance=dict(
        elapsed_hms=elapsed, peak_rss_bytes=int(peak_kb) * 1024 if peak_kb else None,
        peak_rss_GiB=round(int(peak_kb) * 1024 / 1024**3, 4) if peak_kb else None,
        acceptance_peak_rss_bytes=perf.get('peak_rss_bytes'),
        acceptance_elapsed_seconds=perf.get('elapsed_seconds'),
        steps_per_second=perf.get('steps_per_second'),
        wall_cap_seconds=perf.get('wall_cap_seconds')),
    checks=checks,
    all_checks_pass=all(c['pass_'] for c in checks))

(HERE / 'independent_recalculation.json').write_text(
    json.dumps(out, indent=2, ensure_ascii=False) + '\n')

print('=' * 68)
print('1.25 nm 服务器重跑：独立复算结果')
print('=' * 68)
print(f'独立复算 K (末步)   = {K_from_last:.17e} m^3')
print(f'独立复算 K (窗均值) = {K_from_window:.17e} m^3')
print(f'服务器报告 K        = {K_server:.17e} m^3')
print(f'本机参照 K          = {REF_K_LOCAL:.17e} m^3')
print(f'与本机参照相对差     = {rel_to_local:.6e}   (门槛 <= {RTOL:g})')
print(f'窗口 rel_std/rel_span= {rel_std:.6e} / {rel_span:.6e}')
print(f'峰值RSS              = {out["measured_performance"]["peak_rss_GiB"]} GiB  耗时 = {elapsed}')
print('-' * 68)
for c in checks:
    print(('  PASS  ' if c['pass_'] else '  FAIL  ') + c['item'])
    print(f'          {c["detail"]}')
print('-' * 68)
print('全部通过' if out['all_checks_pass'] else '存在未通过项')
