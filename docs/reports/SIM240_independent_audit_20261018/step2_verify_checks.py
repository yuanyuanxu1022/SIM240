#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIM240 独立复核 Step 2（只读）：黏度对照 + 网格加密的实际数值"""
import os, re

RES = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results"

def field(case, name):
    p = os.path.join(RES, case, "steady", "result.txt")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        for line in f:
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return None

print("=" * 74)
print("Step 2-A  黏度对照：μ=1mPa·s vs μ=15mPa·s（K 应与黏度无关）")
print("=" * 74)
for d in ("P", "T"):
    a = field(f"h75_d100_dx5_{d}", "Keff_m3")
    b = field(f"mu15_h75_d100_dx5_{d}", "Keff_m3")
    if a and b:
        a, b = float(a), float(b)
        print(f"  方向 {d}: K(μ=1) = {a:.10e}")
        print(f"           K(μ=15)= {b:.10e}")
        print(f"           相对差 = {(b/a-1)*100:+.6f}%")
    else:
        print(f"  方向 {d}: 缺文件 a={a} b={b}")
    ma = field(f"h75_d100_dx5_{d}", "max_Mach")
    mb = field(f"mu15_h75_d100_dx5_{d}", "max_Mach")
    print(f"           Mach(μ=1)={ma}  Mach(μ=15)={mb}")
    print()

print("=" * 74)
print("Step 2-B  网格加密：dx=5nm vs dx=2.5nm")
print("=" * 74)
pairs = [("h50_d100", 50, 100), ("h125_d25", 125, 25)]
for name, h, d in pairs:
    print(f"  --- 几何 h={h}nm, d={d}nm ---")
    for dr in ("P", "T"):
        k5 = field(f"{name}_dx5_{dr}", "Keff_m3")
        k25 = field(f"{name}_dx2.5_{dr}", "Keff_m3")
        if k5 and k25:
            k5, k25 = float(k5), float(k25)
            diff = (k25 / k5 - 1) * 100
            print(f"    {dr}: K(dx5)   = {k5:.10e}")
            print(f"        K(dx2.5) = {k25:.10e}")
            print(f"        变化     = {diff:+.6f}%")
            # 若二阶收敛，Richardson 估计细网格误差
            if abs(diff) > 1e-12:
                ratio = 4.0  # dx 减半，二阶 -> 4倍
                gci = abs(diff) / (ratio - 1) * 100 / 100
                print(f"        Richardson 相对修正估计 = {abs(diff)/(ratio-1):.6f}%")
        else:
            print(f"    {dr}: 缺文件 k5={k5} k25={k25}")
    print()

print("=" * 74)
print("Step 2-C  全部 36 个地图工况的收敛与诊断摘要")
print("=" * 74)
cases = sorted([c for c in os.listdir(RES)
                if re.match(r"^h\d+_d\d+_dx5_[PT]$", c)])
print(f"{'case':22s} {'steps':>6s} {'exit':>4s} {'Mach':>11s} {'relStd':>11s} "
      f"{'relSpan':>11s} {'massErr':>9s} {'densDev':>9s}")
worst = []
for c in cases:
    steps = field(c, "steps_completed"); ex = field(c, "exit_code")
    mach = field(c, "max_Mach"); rs = field(c, "window_main_rel_std")
    rp = field(c, "window_main_rel_span"); me = field(c, "max_mass_abs_relative")
    dd = field(c, "max_density_deviation")
    print(f"{c:22s} {steps:>6s} {ex:>4s} {float(mach):11.3e} {float(rs):11.3e} "
          f"{float(rp):11.3e} {float(me):9.2e} {float(dd):9.2e}")
    worst.append((float(mach), float(rs), float(rp), float(me), float(dd), c))

print()
mx = max(w[0] for w in worst); mrs = max(w[1] for w in worst)
mrp = max(w[2] for w in worst); mme = max(w[3] for w in worst)
mdd = max(w[4] for w in worst)
print(f"最大 Mach          = {mx:.3e}   (门槛 0.05)  -> {'PASS' if mx < 0.05 else 'FAIL'}")
print(f"最大 window relStd = {mrs:.3e}   (门槛 1e-6)  -> {'PASS' if mrs <= 1e-6 else 'FAIL'}")
print(f"最大 window relSpan= {mrp:.3e}   (门槛 5e-6)  -> {'PASS' if mrp <= 5e-6 else 'FAIL'}")
print(f"最大 mass 相对变化 = {mme:.3e}   (门槛 1e-10) -> {'PASS' if mme <= 1e-10 else 'FAIL'}")
print(f"最大密度偏差       = {mdd:.3e}   (门槛 1e-6)  -> {'PASS' if mdd <= 1e-6 else 'FAIL'}")
