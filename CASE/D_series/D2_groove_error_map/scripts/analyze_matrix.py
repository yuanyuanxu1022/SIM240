#!/usr/bin/env python3
"""D2 矩阵独立验收 + 误差表 + 12.1 敏感性 + 12.2 等体积效率 分析脚本"""
import csv, math, os

RES = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results"
OUT = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/analysis"
os.makedirs(OUT, exist_ok=True)

# ---- 读取 summary.csv：只取 dx=5 的主矩阵 9 几何 ----
rows = {}
with open(os.path.join(RES, "summary.csv")) as f:
    for r in csv.DictReader(f):
        if float(r["dx_nm"]) != 5.0:
            continue
        key = (int(float(r["h_nm"])), int(float(r["d_nm"])), r["direction"])
        rows[key] = float(r["Keff_m3"])

# ---- 模型（局部立方律 / Jain 等价），m³ 口径，每单位宽度 ----
def model_K(h, d):
    h3 = h**3
    hd3 = (h + d) ** 3
    Mpar = (h3 + hd3) / 24.0      # ⟨h³⟩/12, 占空比 0.5
    Mper = 1.0 / (6.0 * (1.0 / h3 + 1.0 / hd3))  # 1/(12⟨h⁻³⟩)
    return Mpar, Mper

HS, DS = [50, 75, 125], [25, 50, 100]
# nm³ → m³: ×1e-27
lines = [["h_nm", "d_nm", "dir", "K_dns_m3", "K_model_m3", "E_pct",
          "A_dns", "A_model", "H_ref_nm", "eta"]]
for h in HS:
    for d in DS:
        Mpar, Mper = model_K(h, d)
        for dirn, Km in (("P", Mpar), ("T", Mper)):
            Kd = rows[(h, d, dirn)]
            E = (Km * 1e-27 - Kd) / Kd * 100.0
            lines.append([h, d, dirn, f"{Kd:.6e}", f"{Km*1e-27:.6e}",
                          f"{E:.2f}", "", "", "", ""])
        Kp, Kt = rows[(h, d, "P")], rows[(h, d, "T")]
        A_dns = Kp / Kt
        A_mod = Mpar / Mper
        Href = h + 0.5 * d
        Kflat = Href**3 / 12.0 * 1e-27
        for i in (-2, -1):
            pass  # eta filled below
        # 把 A 与 eta 写进该几何的两行
        lines[-2][6] = f"{A_dns:.4f}"
        lines[-2][7] = f"{A_mod:.4f}"
        lines[-1][6] = f"{A_dns:.4f}"
        lines[-1][7] = f"{A_mod:.4f}"
        lines[-2][8] = Href
        lines[-1][8] = Href
        lines[-2][9] = f"{Kp / Kflat:.4f}"
        lines[-1][9] = f"{Kt / Kflat:.4f}"

with open(os.path.join(OUT, "error_table.csv"), "w", newline="") as f:
    csv.writer(f).writerows(lines)

# ---- 12.1 区间弹性 Ŝ = ln(K2/K1)/ln(x2/x1) ----
def elast(vals_a, vals_b, xa, xb):
    return math.log(vals_b / vals_a) / math.log(xb / xa)

el_lines = [["fixed", "swept", "step", "dir", "S_hat"]]
for d in DS:  # h 扫描：50→75, 75→125
    for (a, b) in ((50, 75), (75, 125)):
        for dirn in ("P", "T"):
            S = elast(rows[(a, d, dirn)], rows[(b, d, dirn)], a, b)
            el_lines.append([f"d={d}", "h", f"{a}->{b}", dirn, f"{S:.3f}"])
for h in HS:  # d 扫描：25→50, 50→100
    for (a, b) in ((25, 50), (50, 100)):
        for dirn in ("P", "T"):
            S = elast(rows[(h, a, dirn)], rows[(h, b, dirn)], a, b)
            el_lines.append([f"h={h}", "d", f"{a}->{b}", dirn, f"{S:.3f}"])

with open(os.path.join(OUT, "elasticity.csv"), "w", newline="") as f:
    csv.writer(f).writerows(el_lines)

# ---- 对账与网格敏感性 ----
recheck = {}
with open(os.path.join(RES, "summary.csv")) as f:
    for r in csv.DictReader(f):
        if float(r["dx_nm"]) == 2.5:
            key = (int(float(r["h_nm"])), int(float(r["d_nm"])), r["direction"])
            recheck[key] = float(r["Keff_m3"])

sens_lines = [["geometry", "dir", "K_dx5", "K_dx2p5", "rel_diff_pct"]]
for key in sorted(recheck):
    h, d, dirn = key
    k5 = rows[(h, d, dirn)]
    k25 = recheck[key]
    sens_lines.append([f"h{h}_d{d}", dirn, f"{k5:.6e}", f"{k25:.6e}",
                       f"{(k5 - k25) / k25 * 100:.3f}"])
with open(os.path.join(OUT, "grid_sensitivity.csv"), "w", newline="") as f:
    csv.writer(f).writerows(sens_lines)

print("analysis CSVs written to", OUT)
for ln in lines:
    print(ln)
print()
print("elasticity:")
for ln in el_lines:
    print(ln)
print()
print("grid sensitivity:")
for ln in sens_lines:
    print(ln)
