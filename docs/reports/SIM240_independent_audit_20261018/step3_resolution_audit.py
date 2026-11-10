#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIM240 独立复核 Step 3（只读）：分辨率审计
用项目自己 G1 基准（平板 Poiseuille）验证过的误差标度，推算每个几何的最小间隙
被多少格点解析，以及在 dx=5nm 下等效的离散误差。
G1 两个已验收数据点：
  dx=2.5nm, H=75nm (30 格) -> 迁移率误差 +1.168883%
  dx=5.0nm, H=75nm (15 格) -> 迁移率误差 +4.675555%   (历史 FAIL，原样保留)
比值 4.0000，即误差 ∝ dx^2（二阶）。
"""
import csv, itertools

# 由 G1 两个点定标：err = C / N^2, N = h/dx
err30 = 1.168883   # %
err15 = 4.675555   # %
C1 = err30 * 30**2
C2 = err15 * 15**2
print("=" * 74)
print("Step 3-A  用 G1 两点定标误差律")
print("=" * 74)
print(f"  由 30 格点: C = {C1:.3f}  (%%·cells^2)")
print(f"  由 15 格点: C = {C2:.3f}  (%%·cells^2)")
print(f"  两值一致 -> 误差 = C / (h/dx)^2 成立, C ≈ {C1:.2f}")
print(f"  同时说明：dx=5nm 的历史 FAIL(+4.68%) 与 dx=2.5nm 的 PASS(+1.17%)")
print(f"  是同一误差律的两个点，两者不矛盾。")
C = (C1 + C2) / 2

print()
print("=" * 74)
print("Step 3-B  18 种几何在 dx=5 nm 下的间隙分辨率")
print("=" * 74)
hs = [25, 50, 75, 125]
ds = [25, 50, 100, 120]
print(f"{'h(nm)':>6} {'h/dx':>6} {'等效离散误差':>14}  {'评价'}")
for h in hs:
    n = h / 5.0
    e = C / n**2
    if n < 8:
        verdict = "严重欠解析"
    elif n < 12:
        verdict = "偏粗"
    elif n < 20:
        verdict = "可接受"
    else:
        verdict = "较好"
    print(f"{h:>6} {n:>6.1f} {e:>13.2f}%  {verdict}")

print()
print(f"{'d(nm)':>6} {'d/dx':>6}  说明")
for d in ds:
    print(f"{d:>6} {d/5.0:>6.1f}  台阶高度占 {d/5.0:.0f} 格")

print()
print("=" * 74)
print("Step 3-C  跨槽方向为何对最小间隙特别敏感（串联电阻分解）")
print("=" * 74)
W, P = 120.0, 240.0
print(f"{'h':>5} {'d':>5} {'薄区阻力占比':>12} {'薄区K占比(沿槽)':>16}")
for h, d in itertools.product(hs, ds):
    hh, hd = float(h), float(d)
    # 跨槽串联：阻力 ∝ w/h^3 + (P-w)/(h+d)^3
    r_thin = W / hh**3
    r_thick = (P - W) / (hh + hd) ** 3
    frac_T = r_thin / (r_thin + r_thick) * 100
    # 沿槽并联：K ∝ (h^3 + (h+d)^3)
    frac_P = hh**3 / (hh**3 + (hh + hd) ** 3) * 100
    print(f"{h:>5} {d:>5} {frac_T:>11.2f}% {frac_P:>15.2f}%")

print()
print("结论：跨槽方向 K 主要由厚度 h 的薄区决定（阻力占比常 >95%），")
print("      因此该方向对 h 的分辨率最敏感；而 h=25nm 在 dx=5nm 下只有 5 格。")
