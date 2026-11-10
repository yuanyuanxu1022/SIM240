#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""等效缝高自检：H 反算 K 必须回到原始 K；比值与偏差必须互洽。"""
import csv

R = "/home/dell/yuanyuanxu/SIM240"
TAB = f"{R}/docs/reports/PAPER1_equivalent_gap_20261109/equivalent_gap_table.csv"
MAIN = f"{R}/docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv"
ADD = f"{R}/docs/reports/PAPER1_闭环方案_20261105/bound_check_44_points.csv"

raw = {}
for r in csv.DictReader(open(MAIN, encoding="utf-8")):
    raw[(r["h_nm"].split(".")[0], r["d_nm"].split(".")[0],
         "沿槽" if r["direction"] == "P" else "横槽")] = (float(r["K_DNS_m3"]),
                                                          float(r["K_model_m3"]),
                                                          float(r["E_pct"]))
for r in csv.DictReader(open(ADD, encoding="utf-8")):
    if r["run_id"].startswith("h100_d100"):
        raw[("100", "100", "沿槽" if r["direction"] == "parallel" else "横槽")] = (
            float(r["K_reference_m3"]), float(r["K_bound_m3"]), float(r["bias_percent"]))

rows = list(csv.DictReader(open(TAB, encoding="utf-8")))
print(f"表中记录数：{len(rows)}（应为 38）")
bad = 0
for r in rows:
    key = (r["h_nm"], r["d_nm"], r["direction"])
    if key not in raw:
        print("!! 键缺失", key); bad += 1; continue
    Kd, Km, E = raw[key]
    Hd = float(r["H_dns_nm"]); Hm = float(r["H_model_nm"])
    h = float(r["h_nm"])
    # 1. H 反算 K
    kd_back = Hd**3 / 12.0 * 1e-27
    km_back = Hm**3 / 12.0 * 1e-27
    e1 = abs(kd_back / Kd - 1); e2 = abs(km_back / Km - 1)
    # 2. H_model/H_dns 的三次方 = 1+E
    e3 = abs((Hm / Hd)**3 / (1 + E/100) - 1)
    # 3. 流量倍数 = (H/h)^3
    e4 = abs(float(r["flux_x"]) / (Hd/h)**3 - 1)
    # 4. H/h
    e5 = abs(float(r["H_ratio"]) / (Hd/h) - 1)
    for nm, e in (("K_dns反算", e1), ("K_model反算", e2), ("(Hm/Hd)^3 vs 1+E", e3),
                  ("flux_x", e4), ("H_ratio", e5)):
        if e > 1e-6:
            print(f"!! {key} {nm} 相对误差 {e:.3e}"); bad += 1
print("全部通过" if bad == 0 else f"失败 {bad} 项")

# 汇总口径
for d in ("沿槽", "横槽"):
    sub = [r for r in rows if r["direction"] == d]
    hr = [float(r["H_ratio"]) for r in sub]
    fx = [float(r["flux_x"]) for r in sub]
    print(f"{d}: n={len(sub)}  H/h {min(hr):.3f}~{max(hr):.3f}  流量 {min(fx):.2f}~{max(fx):.2f}")
