#!/usr/bin/env python3
"""生成"上界检验"清单：原局部立方律 K0 作为非严格上界，逐个方向点核对。

数据来源（只读）：
  1) docs/reports/PAPER1_formula_comparison_20261105/comparison_36_points.csv
     —— dx=5 nm 主地图 36 个方向点
  2) CASE/D_series/D2_groove_error_map/results/*_dx2.5_*/steady/result.txt
     —— dx=2.5 nm 加密 8 个方向点
  3) CASE/D_series/D2_groove_error_map/results/h100_d100_dx5_{P,T}/steady/result.txt
     —— 2026-11-06 盲测批次 2 个方向点（h=100 nm，未参与 V2 系数确定）

输出：bound_check_44_points.csv（文件名沿用，行数为 46）
"""
import csv
import glob
import os
import re

SIM = "/home/dell/yuanyuanxu/SIM240"
OUT_DIR = os.path.join(SIM, "docs/reports/PAPER1_闭环方案_20261105")
OUT = os.path.join(OUT_DIR, "bound_check_44_points.csv")
RES = os.path.join(SIM, "CASE/D_series/D2_groove_error_map/results")
W_NM = 120.0


def K0(h, d, w=W_NM):
    kyy = ((h + d) ** 3 + h ** 3) / 24.0
    kxx = (h ** 3 * (h + d) ** 3) / (6.0 * (h ** 3 + (h + d) ** 3))
    return kxx * 1e-27, kyy * 1e-27


def parse_result(path):
    txt = open(path, encoding="utf-8", errors="replace").read()

    def g(key):
        m = re.search(key + r"=([-\d.eE+]+)", txt)
        return float(m.group(1)) if m else None

    direction = re.search(r"direction=(\w+)", txt).group(1)
    return {
        "h": g("mesa_gap_m") * 1e9,
        "d": g("groove_depth_m") * 1e9,
        "K": g("Keff_m3"),
        "component": "Kyy" if direction in ("parallel", "P") else "Kxx",
        "direction": direction,
    }


rows = []

# 1) dx=5 主地图 36 点
for r in csv.DictReader(open(os.path.join(
        SIM, "docs/reports/PAPER1_formula_comparison_20261105/comparison_36_points.csv"),
        encoding="utf-8")):
    kx, ky = K0(float(r["h_nm"]), float(r["d_nm"]))
    k0 = ky if r["component"] == "Kyy" else kx
    k = float(r["OpenLB_dx5_K_m3"])
    rows.append({
        "run_id": r["run_id"], "h_nm": r["h_nm"], "d_nm": r["d_nm"], "w_nm": r["w_nm"],
        "direction": r["direction"], "component": r["component"], "dx_nm": "5",
        "K_bound_m3": f"{k0:.9e}", "K_reference_m3": f"{k:.9e}",
        "bias_percent": f"{(k0 / k - 1) * 100:.6f}", "below_bound": k0 > k,
        "reference_source": "D2 5nm 主地图", "raw_path": r["raw_result_path"],
    })

# 2) dx=2.5 加密 8 点
for p in sorted(glob.glob(os.path.join(RES, "*_dx2.5_*/steady/result.txt"))):
    rec = parse_result(p)
    kx, ky = K0(rec["h"], rec["d"])
    k0 = ky if rec["component"] == "Kyy" else kx
    rows.append({
        "run_id": p.split("/")[-3], "h_nm": rec["h"], "d_nm": rec["d"], "w_nm": W_NM,
        "direction": rec["direction"], "component": rec["component"], "dx_nm": "2.5",
        "K_bound_m3": f"{k0:.9e}", "K_reference_m3": f"{rec['K']:.9e}",
        "bias_percent": f"{(k0 / rec['K'] - 1) * 100:.6f}", "below_bound": k0 > rec["K"],
        "reference_source": "D2 2.5nm 加密",
        "raw_path": os.path.relpath(p, SIM),
    })

# 3) 2026-11-06 盲测 2 点（h=100 nm）
for dirn in ("P", "T"):
    p = os.path.join(RES, f"h100_d100_dx5_{dirn}", "steady/result.txt")
    rec = parse_result(p)
    kx, ky = K0(rec["h"], rec["d"])
    k0 = ky if rec["component"] == "Kyy" else kx
    rows.append({
        "run_id": f"h100_d100_dx5_{dirn}", "h_nm": rec["h"], "d_nm": rec["d"],
        "w_nm": W_NM, "direction": rec["direction"], "component": rec["component"],
        "dx_nm": "5", "K_bound_m3": f"{k0:.9e}", "K_reference_m3": f"{rec['K']:.9e}",
        "bias_percent": f"{(k0 / rec['K'] - 1) * 100:.6f}", "below_bound": k0 > rec["K"],
        "reference_source": "2026-11-06 盲测新增（h=100，未参与 V2 拟合）",
        "raw_path": os.path.relpath(p, SIM),
    })

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

bad = [r for r in rows if not r["below_bound"]]
print(f"写入 {len(rows)} 行 -> {OUT}")
print(f"超出上界（反例）：{len(bad)}")
print(f"偏差范围：{min(float(r['bias_percent']) for r in rows):+.4f}% ~ "
      f"{max(float(r['bias_percent']) for r in rows):+.4f}%")
for c in ("Kxx", "Kyy"):
    print(f"  {c}: {sum(1 for r in rows if r['component'] == c)} 点")
