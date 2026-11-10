#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决定性算例分析：dx=5nm vs dx=2.5nm 的四点对比（修正版）
K_model 只依赖几何，直接从 map36_evidence.csv 读取项目自己的值，不自行重造公式。
只读，不改任何原始结果。
"""
import os, csv

RES = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results"
CSV = "/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv"
W = 120.0

def field(case, name, mode="steady"):
    p = os.path.join(RES, case, mode, "result.txt")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        for line in f:
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return None

def F2_par(d, w=W):
    return 1.0 / (1.0 + 1.7685 * (d / w) ** 1.6331)

def F2_perp(d, w=W):
    return 1.0 / (1.0 + 0.4900 * (d / w) ** 0.6990)

# 读项目自己的 K_model（几何决定，与网格无关）
kmod = {}
rows = list(csv.DictReader(open(CSV)))
for r in rows:
    kmod[(int(r["h_nm"]), int(r["d_nm"]), r["direction"])] = float(r["K_model_m3"])

# 旧 dx=5 工况的目录名（注意 d120 那批是 dX_hY 顺序）
OLD5 = {
    (25, 100, "P"): "h25_d100_dx5_P",
    (25, 100, "T"): "h25_d100_dx5_T",
    (125, 120, "P"): "d120_h125_dx5_P",
    (125, 120, "T"): "d120_h125_dx5_T",
}

POINTS = [(25, 100, "跨槽残差最差点（原 −18.7%）"),
          (125, 120, "沿槽负残差最大点（原 −10.5%）")]

print("=" * 90)
print("决定性算例：网格加密后 V2 残差是否收缩")
print("=" * 90)
print()

summary = []
for h, d, note in POINTS:
    print(f"### h={h} nm, d={d} nm  — {note}")
    print()
    for dr in ("P", "T"):
        c5 = OLD5[(h, d, dr)]
        c25 = f"h{h}_d{d}_dx2.5_{dr}"
        k5 = field(c5, "Keff_m3")
        k25 = field(c25, "Keff_m3")
        if not (k5 and k25):
            print(f"  [缺数据] {dr}: dx5({c5})={k5}  dx2.5({c25})={k25}")
            continue
        k5, k25 = float(k5), float(k25)
        Kmod = kmod[(h, d, dr)]
        change = (k25 / k5 - 1.0) * 100.0
        E5 = (Kmod / k5 - 1.0) * 100.0
        E25 = (Kmod / k25 - 1.0) * 100.0
        F = F2_par(d) if dr == "P" else F2_perp(d)
        r5 = (F * Kmod / k5 - 1.0) * 100.0
        r25 = (F * Kmod / k25 - 1.0) * 100.0
        shift = r25 - r5
        summary.append(dict(h=h, d=d, dr=dr, k5=k5, k25=k25, change=change,
                            E5=E5, E25=E25, F=F, r5=r5, r25=r25, shift=shift))
        label = "沿槽" if dr == "P" else "跨槽"
        print(f"  【{label}】")
        print(f"    K(dx=5.0nm) = {k5:.10e} m³     K(dx=2.5nm) = {k25:.10e} m³")
        print(f"    网格变化     = {change:+.4f}%")
        print(f"    K_model     = {Kmod:.10e} m³")
        print(f"    原闭合误差 E: {E5:+8.3f}%  ->  {E25:+8.3f}%      (变化 {E25-E5:+.3f} 个百分点)")
        print(f"    V2 因子 F   = {F:.6f}")
        print(f"    V2 残差 r   : {r5:+8.3f}%  ->  {r25:+8.3f}%      (变化 {shift:+.3f} 个百分点)")
        print()

print("=" * 90)
print("汇总表")
print("=" * 90)
print(f"{'h':>5} {'d':>5} {'方向':>4} | {'r(dx5)':>10} {'r(dx2.5)':>10} {'移动(pp)':>10} | {'网格变化':>10} {'外推dx5误差':>12}")
for s in summary:
    ext = abs((s['k5'] - s['k25']) / 3.0 / s['k25'] * 100)
    print(f"{s['h']:>5} {s['d']:>5} {s['dr']:>4} | {s['r5']:>9.3f}% {s['r25']:>9.3f}% {s['shift']:>+9.3f} "
          f"| {s['change']:>+9.3f}% {ext:>11.4f}%")
print()
print("说明：'外推dx5误差' 按两级网格假定二阶，取 |K5-K25|/3 相对 K25。")
