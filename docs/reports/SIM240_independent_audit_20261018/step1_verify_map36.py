#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIM240 独立复核 Step 1（只读）：
1) 校验 map36_evidence.csv 里 36 条 result_path 是否真实存在、sha256 是否与记录一致
2) 用 K_DNS / K_model 独立复算 E_pct，与表中 E_pct 列比较
3) 用 V1 / V2 舍入系数独立复算残差，与表中两列比较
4) 检查是否所有 36 个工况都是正偏差
不修改任何原始文件。
"""
import csv, hashlib, os, sys, math

ROOT = "/home/dell/yuanyuanxu/SIM240"
CSV = os.path.join(ROOT, "docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# --- V1 / V2 舍入系数（取自 CORE_CLAIMS.md 公布值） ---
def F1_par(h, d):
    Href = h + d / 2.0
    return 1.0 / (1.0 + 1.7207 * (d / Href) ** 1.8046)

def F1_perp(d, w):
    return 1.0 / (1.0 + 0.5276 * (d / w) ** 0.8259)

def F2_par(d, w):
    return 1.0 / (1.0 + 1.7685 * (d / w) ** 1.6331)

def F2_perp(d, w):
    return 1.0 / (1.0 + 0.4900 * (d / w) ** 0.6990)

W = 120.0  # 槽宽 nm

rows = []
with open(CSV, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(r)

print("=" * 78)
print("Step 1-A  文件存在性与 SHA256 校验")
print("=" * 78)
missing, mismatch, ok = [], [], 0
for r in rows:
    p = os.path.join(ROOT, r["result_path"])
    if not os.path.exists(p):
        missing.append(r["result_path"])
        continue
    got = sha256(p)
    if got != r["result_sha256"]:
        mismatch.append((r["result_path"], r["result_sha256"][:12], got[:12]))
    else:
        ok += 1
print(f"总行数        : {len(rows)}")
print(f"文件存在且哈希一致: {ok}")
print(f"文件缺失      : {len(missing)}")
for m in missing:
    print("   [缺失]", m)
print(f"哈希不一致    : {len(mismatch)}")
for p, a, b in mismatch:
    print(f"   [不一致] {p}\n      记录={a} 实际={b}")

print()
print("=" * 78)
print("Step 1-B  独立复算 E_pct = (K_model/K_DNS - 1) * 100")
print("=" * 78)
maxdiff_E = 0.0
bad_E = []
for r in rows:
    kd = float(r["K_DNS_m3"]); km = float(r["K_model_m3"])
    E_calc = (km / kd - 1.0) * 100.0
    E_tab = float(r["E_pct"])
    diff = abs(E_calc - E_tab)
    maxdiff_E = max(maxdiff_E, diff)
    if diff > 1e-9:
        bad_E.append((r["h_nm"], r["d_nm"], r["direction"], E_tab, E_calc, diff))
print(f"最大绝对差 : {maxdiff_E:.3e} (%% 单位)")
print(f"超差行数   : {len(bad_E)}")
for b in bad_E[:10]:
    print("   ", b)

print()
print("=" * 78)
print("Step 1-C  独立复算 V1 / V2 残差 r = F*(1+E) - 1")
print("=" * 78)
maxd1 = maxd2 = 0.0
bad1, bad2 = [], []
for r in rows:
    h = float(r["h_nm"]); d = float(r["d_nm"]); dr = r["direction"]
    kd = float(r["K_DNS_m3"]); km = float(r["K_model_m3"])
    E = km / kd - 1.0
    if dr == "P":
        f1, f2 = F1_par(h, d), F2_par(d, W)
    else:
        f1, f2 = F1_perp(d, W), F2_perp(d, W)
    r1 = (f1 * (1 + E) - 1) * 100.0
    r2 = (f2 * (1 + E) - 1) * 100.0
    t1 = float(r["V1_rounded_residual_pct"]); t2 = float(r["V2_rounded_residual_pct"])
    d1 = abs(r1 - t1); d2 = abs(r2 - t2)
    maxd1 = max(maxd1, d1); maxd2 = max(maxd2, d2)
    if d1 > 1e-6: bad1.append((h, d, dr, t1, r1, d1))
    if d2 > 1e-6: bad2.append((h, d, dr, t2, r2, d2))
print(f"V1 最大绝对差 : {maxd1:.3e}    超差行数: {len(bad1)}")
for b in bad1[:6]: print("   ", b)
print(f"V2 最大绝对差 : {maxd2:.3e}    超差行数: {len(bad2)}")
for b in bad2[:6]: print("   ", b)

print()
print("=" * 78)
print("Step 1-D  '全部高估' 是否成立 / 偏差范围")
print("=" * 78)
for dr in ("P", "T"):
    sub = [r for r in rows if r["direction"] == dr]
    E = [(float(r["K_model_m3"]) / float(r["K_DNS_m3"]) - 1) * 100 for r in sub]
    neg = [e for e in E if e < 0]
    print(f"方向 {dr}: n={len(sub)}  E范围 = {min(E):.4f}% ~ {max(E):.4f}%  负偏差个数={len(neg)}")

print()
print("=" * 78)
print("Step 1-E  分组残差最大值复算（对照 correction_groups.csv）")
print("=" * 78)
g1, g2 = {}, {}
for r in rows:
    key = (r["group"], r["direction"])
    g1.setdefault(key, []).append(float(r["V1_rounded_residual_pct"]))
    g2.setdefault(key, []).append(float(r["V2_rounded_residual_pct"]))

print(f"{'group':12s} {'dir':3s} {'n':>3s}  {'V1 max|r|':>12s} {'V2 max|r|':>12s}")
for key in sorted(g1):
    g, dr = key
    print(f"{g:12s} {dr:3s} {len(g1[key]):3d}  "
          f"{max(abs(x) for x in g1[key]):11.6f}% "
          f"{max(abs(x) for x in g2[key]):11.6f}%")

print()
print("对照 correction_groups.csv 声称值：")
print("  calibration P 28.090820 / 9.914300 ; calibration T 5.669917 / 4.188569")
print("  d75        P 16.872586 / 9.334484 ; d75        T 3.469695 / 3.858046")
print("  d120       P 38.581788 /10.504978 ; d120       T 9.211759 / 6.920727")
print("  h25        P 43.911695 / 7.212757 ; h25        T 19.962054/18.705147")

print()
print("完成。以上均为只读复核，未修改任何文件。")
