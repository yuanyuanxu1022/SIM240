#!/usr/bin/env python3
"""由 36 条主结果 + 2 条 h=100 新增，导出每个几何的等效缝高。

等效缝高定义：H = (12 K)^(1/3)，即"多厚的平板缝能给出同一导度"。
  - K 为深度积分导度（m^3），换 nm^3 乘 1e27
  - 平板校验：h=75 nm 平板 K=75^3/12 -> H=75.000 nm
不做任何拟合、不改任何已有数字，只是把既有 K 重标定为长度。
"""
import csv, math, os, sys

ROOT = "/home/dell/yuanyuanxu/SIM240"
MAIN = f"{ROOT}/docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv"
ADD  = f"{ROOT}/docs/reports/PAPER1_闭环方案_20261105/bound_check_44_points.csv"
OUT  = f"{ROOT}/docs/reports/PAPER1_equivalent_gap_20261109/equivalent_gap_table.csv"

def H_from_K_nm3(K_m3):
    """K(m^3) -> 等效缝高(nm)"""
    K_nm3 = K_m3 * 1e27
    return (12.0 * K_nm3) ** (1.0/3.0)

# 平板校验
H_plate = H_from_K_nm3((75e-9)**3/12.0)
print(f"[校验] 75 nm 平板 -> H = {H_plate:.4f} nm (应为 75.0000)")

rows = []
with open(MAIN, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(dict(h=float(r["h_nm"]), d=float(r["d_nm"]),
                         dirn=r["direction"], grp=r["group"],
                         Kd=float(r["K_DNS_m3"]), Km=float(r["K_model_m3"]),
                         E=float(r["E_pct"]), V2=float(r["V2_rounded_residual_pct"]),
                         src=os.path.basename(r["result_path"])))
with open(ADD, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["run_id"].startswith("h100_d100"):
            dirn = "P" if r["direction"] == "parallel" else "T"
            rows.append(dict(h=float(r["h_nm"]), d=float(r["d_nm"]), dirn=dirn,
                             grp="h100", Kd=float(r["K_reference_m3"]),
                             Km=float(r["K_bound_m3"]),
                             E=float(r["bias_percent"]), V2=float("nan"),
                             src=r["run_id"]))

rows.sort(key=lambda r: (r["h"], r["d"], r["dirn"]))

out = []
for r in rows:
    Hd = H_from_K_nm3(r["Kd"]); Hm = H_from_K_nm3(r["Km"])
    out.append(dict(
        h_nm=r["h"], d_nm=r["d"], d_over_w=r["d"]/120.0,
        direction="沿槽" if r["dirn"]=="P" else "横槽",
        group=r["grp"],
        H_dns_nm=Hd, H_model_nm=Hm,
        H_ratio=Hd/r["h"],            # 等效缝高 / 名义最小间隙
        flux_x=(Hd/r["h"])**3,        # 同压差流量倍数（相对平板名义间隙）
        E_pct=r["E"],
    ))

with open(OUT, "w", newline="\n", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["h_nm","d_nm","d_over_w","direction","group",
                                      "H_dns_nm","H_model_nm","H_ratio","flux_x","E_pct"])
    w.writeheader()
    for r in out:
        w.writerow({k: (f"{v:.0f}" if k in ("h_nm","d_nm") else
                        (f"{v:.8g}" if isinstance(v,float) else v))
                    for k,v in r.items()})

print(f"[写出] {len(out)} 条方向记录 -> {OUT}")
print()
print(f"{'h':>4} {'d':>4} {'方向':<4} {'H_dns':>7} {'H_model':>7} {'H/h':>6} {'流量x':>6} {'E%':>8}")
for r in out:
    print(f"{r['h_nm']:>4.0f} {r['d_nm']:>4.0f} {r['direction']:<4} "
          f"{r['H_dns_nm']:>7.2f} {r['H_model_nm']:>7.2f} {r['H_ratio']:>6.3f} "
          f"{r['flux_x']:>6.2f} {r['E_pct']:>8.2f}")

# ---------- 可选：打印 Markdown 表（供 EQUIVALENT_GAP_GUIDE.md 第 2 节使用） ----------
if "--md" in sys.argv:
    cur = None
    for r in out:
        if cur != r["h_nm"]:
            cur = r["h_nm"]
            print(f"\n**h = {r['h_nm']:.0f} nm**\n")
            print("| d (nm) | d/w | 方向 | 等效缝高 H_dns (nm) | 公式给的 H (nm) | H/h | 同压差流量倍数 | 原式偏差 E |")
            print("|---|---|---|---|---|---|---|---|")
        print(f"| {r['d_nm']:.0f} | {r['d_over_w']:.4f} | {r['direction']} | "
              f"**{r['H_dns_nm']:.2f}** | {r['H_model_nm']:.2f} | {r['H_ratio']:.3f} | "
              f"{r['flux_x']:.2f}× | {r['E_pct']:+.2f}% |")
