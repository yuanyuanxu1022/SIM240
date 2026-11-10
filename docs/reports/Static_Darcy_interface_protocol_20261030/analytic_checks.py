#!/usr/bin/env python3
"""Preparation arithmetic only: no flow solver, subprocess, build, or mesh calls."""
import hashlib
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / 'Shared_transport_interface_20261030/coefficient_examples.json'


def simpson(fn, a, b, n=2000):
    step = (b - a) / n
    return step / 3 * (fn(a) + fn(b) + sum(
        (4 if i % 2 else 2) * fn(a + i * step) for i in range(1, n)))


def main():
    cfg = json.loads((BASE / 'protocol.json').read_text())
    data = json.loads(SOURCE.read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == cfg['coefficient_source_sha256']
    mu, H = cfg['mu_Pa_s'], cfg['H_m']
    L = cfg['L_m'][:2]
    mapping = {(r['input_id'], r['orientation_id']): r for r in data['rows']}
    checks = []

    def check(name, residual, tolerance):
        passed = math.isfinite(residual) and residual <= tolerance
        checks.append(dict(check=name, residual=residual, tolerance=tolerance, satisfied=passed))
        assert passed, (name, residual, tolerance)

    # Separate formula recomputation; no import/execution of the previous generator.
    h, depth, width = 75e-9, 100e-9, 120e-9
    cube1, cube2 = (h + depth)**3, h**3
    original = [cube1 * cube2 / (6 * (cube1 + cube2)), (cube1 + cube2) / 24]
    factors = [1/(1 + 0.4900*(depth/width)**0.6990),
               1/(1 + 1.7685*(depth/width)**1.6331)]
    wall = []
    for input_id in ['original_local_cubic', 'V2_published_rounded']:
        row = mapping[input_id, 'groove_along_long_y']
        for axis in range(2):
            K = row['K_global_m3'][axis][axis]
            expected = original[axis] * (factors[axis] if input_id.startswith('V2') else 1)
            check(f'{input_id}_{axis}_formula', abs(K/expected - 1), 2e-12)
            D = row['D_global_m_minus2_conditional_total_drag'][axis][axis]
            check(f'{input_id}_{axis}_inverse', abs(D*K/H - 1), 2e-12)
            # Slab counterexample only; analytic solution independently integrated.
            q = math.sqrt(D)
            a = q*H/2
            G = 1e6
            scale = G/(mu*D)
            u = lambda z: scale*(1-math.cosh(q*z)/math.cosh(a))
            du = lambda z: -scale*q*math.sinh(q*z)/math.cosh(a)
            ratio = 1-math.tanh(a)/a
            exact_J = G/mu * H/D * ratio
            int_J = simpson(u, -H/2, H/2)
            dissipation = simpson(lambda z: mu*(du(z)**2 + D*u(z)**2), -H/2, H/2)
            check(f'{input_id}_{axis}_slab_integral', abs(int_J/exact_J-1), 1e-9)
            check(f'{input_id}_{axis}_slab_energy', abs(dissipation/(G*int_J)-1), 1e-9)
            wall.append(dict(input_id=input_id, direction=['perpendicular', 'parallel'][axis],
                             target_K_m3=K, D_m_minus2=D,
                             no_slip_plus_total_drag_K_m3=H/D*ratio,
                             ratio_to_target=ratio, interpretation='analytic_slab_counterexample_only'))

    forecasts = []
    for case in cfg['planned_cases']:
        row = mapping[case['input_id'], case['orientation_id']]
        axis = case['drive_axis']
        G = case['G_Pa_per_m']
        K = row['K_global_m3'][axis][axis]
        D = row['D_global_m_minus2_conditional_total_drag'][axis][axis]
        J = K/mu*G
        U = G/(mu*D)
        Q = J*L[1-axis]
        dp = G*L[axis]
        power = dp*Q
        energy = mu*D*U**2 * (L[0]*L[1]*H)
        if G:
            check(case['case_id']+'_flux_average', abs(H*U/J-1), 2e-12)
            check(case['case_id']+'_power', abs(energy/power-1), 2e-12)
        else:
            check(case['case_id']+'_zero', abs(J)+abs(U)+abs(Q)+abs(power), 0)
        forecasts.append(dict(case_id=case['case_id'], K_main_m3=K, D_main_m_minus2=D,
                              pressure_drop_Pa=dp, J_main_m2_per_s=J, U_main_m_per_s=U,
                              Q_high_signed_m3_per_s=Q, pressure_power_W=power,
                              Re_H_estimate=cfg['rho_kg_m3']*abs(U)*H/mu,
                              result_kind='ANALYTIC_EXPECTATION_NOT_SOLVER_RESULT'))
    by_id = {r['case_id']: r for r in forecasts}
    check('y_drive_width_ratio', abs(by_id['C05']['Q_high_signed_m3_per_s']/
          by_id['C02']['Q_high_signed_m3_per_s']-0.5), 2e-12)
    check('reverse_signed_flux', abs(by_id['C06']['J_main_m2_per_s']/
          by_id['C01']['J_main_m2_per_s']+1), 2e-12)
    check('double_drive', abs(by_id['C08']['J_main_m2_per_s']/
          by_id['C01']['J_main_m2_per_s']-2), 2e-12)
    check('geometry_volume', abs((24e-6*48e-6*125e-9)/(L[0]*L[1]*H)-1), 2e-12)
    for c in cfg['planned_cases']:
        row=mapping[c['input_id'],c['orientation_id']]
        K=row['K_global_m3']; D=row['D_global_m_minus2_conditional_total_drag']
        assert K[0][0]>0 and K[1][1]>0 and K[0][1]==K[1][0]==0
        assert D[0][0]>0 and D[1][1]>0 and D[0][1]==D[1][0]==0
    report = dict(protocol_id=cfg['protocol_id'], kind='ANALYTIC_AND_INPUT_CHECKS_ONLY',
                  source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  coefficient_records_used=4, checks=checks, all_checks_satisfied=all(x['satisfied'] for x in checks),
                  smooth_slab_125nm_K_m3=H**3/12, wall_counterexamples=wall,
                  forecasts=forecasts, flow_solver_run=False, independent_human_acceptance=False,
                  NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=None, geometry_PASS=None)
    (BASE/'analytic_checks.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    lines=['# 解析预期值（不是流动计算结果）', '',
           'SDI-v1，2026-10-30。以下由输入和解析表达式计算，用于未来独立读取求解输出时作比较。', '',
           '|ID|Δp (Pa)|U主向 (m/s)|J主向 (m²/s)|高坐标端有符号Q (m³/s)|',
           '|---|---:|---:|---:|---:|']
    for r in forecasts:
        lines.append(f"|{r['case_id']}|{r['pressure_drop_Pa']:.8g}|{r['U_main_m_per_s']:.10e}|{r['J_main_m2_per_s']:.10e}|{r['Q_high_signed_m3_per_s']:.10e}|")
    lines += ['', 'C01—C04为两系数×两槽向；C05为y驱动；C06反向；C07零驱动；C08倍增；C01-R只换网格。',
              '压力为p(s)=G(L_s−s)，其他速度分量为零。C07不能用相对误差或恢复K。', '',
              '解析平板反例（125 nm无滑移壁面再次叠加总D）：', '',
              '|系数|方向|算得导度/目标导度|', '|---|---|---:|']
    for r in wall:
        lines.append(f"|{r['input_id']}|{r['direction']}|{r['ratio_to_target']:.10f}|")
    lines += ['', '该表不是nanrPrint或真实沟槽的实际误差。解析积分与耗散核对记录见analytic_checks.json；无新仿真run_id。']
    (BASE/'EXPECTED_VALUES.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(analytic_checks=len(checks), satisfied=True, planned_cases=len(forecasts), flow_solver_run=False)))


if __name__ == '__main__':
    main()
