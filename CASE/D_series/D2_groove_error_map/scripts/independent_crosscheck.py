#!/usr/bin/env python3
"""独立交叉验证：不与项目任何脚本共享代码，从底层数据重算论文全部数字并对比。"""
import csv, os, math

RES = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results"
OUT = os.path.join(RES, "analysis")

fails = 0
def check(label, got, expected, tol_rel=1e-6, tol_abs=0.0):
    global fails
    ok = abs(got - expected) <= tol_rel * abs(expected) + tol_abs
    if not ok:
        fails += 1
        print(f"  ✗ MISMATCH {label}: got={got!r} expected={expected!r}")
    return ok

# ---------- 1. 重建 summary 的 Keff vs error_table 的 K_dns（18 dx5 点） ----------
summ = {}
with open(os.path.join(RES, "summary.csv")) as f:
    for r in csv.DictReader(f):
        if float(r["dx_nm"]) == 5.0:
            summ[(int(r["h_nm"]), int(r["d_nm"]), r["direction"])] = float(r["Keff_m3"])

n1 = 0
with open(os.path.join(OUT, "error_table.csv")) as f:
    for r in csv.DictReader(f):
        key = (int(r["h_nm"]), int(r["d_nm"]), r["dir"])
        # 1a: K_dns 逐位一致
        check(f"K_dns {key}", summ[key], float(r["K_dns_m3"]), 1e-14)
        # 1b: 独立重算模型值（算术/调和平均，占空比 0.5，nm->m）
        h, d = key[0], key[1]
        H = h + d
        if r["dir"] == "P":
            M = (0.5 * h**3 + 0.5 * H**3) / 12.0 * 1e-27
        else:
            M = (1.0 / (0.5 / h**3 + 0.5 / H**3)) / 12.0 * 1e-27
        check(f"K_model {key}", M, float(r["K_model_m3"]), 1e-10)
        # 1c: 独立重算误差
        E = (M - summ[key]) / summ[key] * 100.0
        check(f"E_pct {key}", E, float(r["E_pct"]), 1e-6)
        n1 += 1
print(f"[1] error_table 18 行：K_dns / K_model / E_pct 全部重算比对完成")

# ---------- 2. 独立重算 A_dns / A_model / H_ref / eta ----------
n2 = 0
with open(os.path.join(OUT, "error_table.csv")) as f:
    seen = set()
    for r in csv.DictReader(f):
        h, d = int(r["h_nm"]), int(r["d_nm"])
        if (h, d) in seen:
            continue
        seen.add((h, d))
        A_dns = summ[(h, d, "P")] / summ[(h, d, "T")]
        check(f"A_dns h{h}d{d}", A_dns, float(r["A_dns"]), 1e-6)
        H = h + d
        Mpar = (0.5 * h**3 + 0.5 * H**3) / 12.0
        Mper = (1.0 / (0.5 / h**3 + 0.5 / H**3)) / 12.0
        check(f"A_model h{h}d{d}", Mpar / Mper, float(r["A_model"]), 1e-8)
        Href = h + 0.5 * d
        check(f"H_ref h{h}d{d}", Href, float(r["H_ref_nm"]), 1e-9)
        Kflat = Href**3 / 12.0 * 1e-27
        check(f"eta_P h{h}d{d}", summ[(h, d, "P")] / Kflat, float(r["eta"]), 1e-6)
        n2 += 1
print(f"[2] A / H_ref / eta：9 几何重算比对完成")

# ---------- 3. 弹性表独立重算 ----------
n3 = 0
with open(os.path.join(OUT, "elasticity.csv")) as f:
    for r in csv.DictReader(f):
        if r["swept"] == "h":
            a, b = map(int, r["step"].split("->"))
            d = int(r["fixed"].split("=")[1])
            S = math.log(summ[(b, d, r["dir"])] / summ[(a, d, r["dir"])]) / math.log(b / a)
        else:
            a, b = map(int, r["step"].split("->"))
            h = int(r["fixed"].split("=")[1])
            S = math.log(summ[(h, b, r["dir"])] / summ[(h, a, r["dir"])]) / math.log(b / a)
        check(f"S {r['fixed']} {r['step']} {r['dir']}", S, float(r["S_hat"]), 1e-6)
        n3 += 1
print(f"[3] 弹性表 {n3} 行重算比对完成")

# ---------- 4. d75 修正预测独立重算 ----------
print("[4] d75 修正预测独立重算（参数取拟合报告四舍五入值）")
aP, bP = 1.7207, 1.8046
aT, bT = 0.5276, 0.8259
w = 120.0
pred_d75 = {
    "P": {50: 3.7601e-23, 75: 8.6553e-23, 125: 2.9076e-22},
    "T": {50: 1.4420e-23, 75: 4.6028e-23, 125: 1.9269e-22},
}
for dirn in ("P", "T"):
    for h in (50, 75, 125):
        H = h + 75.0
        if dirn == "P":
            M = (0.5 * h**3 + 0.5 * H**3) / 12.0 * 1e-27
            Href = h + 0.5 * 75.0
            F = 1.0 / (1.0 + aP * (75.0 / Href) ** bP)
        else:
            M = (1.0 / (0.5 / h**3 + 0.5 / H**3)) / 12.0 * 1e-27
            F = 1.0 / (1.0 + aT * (75.0 / w) ** bT)
        got = M * F
        exp = pred_d75[dirn][h]
        rel = abs(got - exp) / exp
        status = "✓" if rel < 1e-3 else "✗"
        if rel >= 1e-3:
            fails += 1
        print(f"  {dirn} h{h}: {got:.4e} vs 报告 {exp:.4e} 相对差 {rel:.2e} {status}")

print()
print("=" * 60)
if fails == 0:
    print("独立交叉验证：全部通过（论文全部数字与底层数据一致）")
else:
    print(f"发现 {fails} 处不一致，需要逐一排查")
