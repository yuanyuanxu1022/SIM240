#!/usr/bin/env python3
"""从各档 result.txt 全量重建 summary.csv（含正确的 steps 字段）。只读 result.txt，不依赖旧 summary。"""
import csv, glob, os, re

RES = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results"

def read_field(path, name):
    with open(path) as f:
        for line in f:
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return None

out_rows = []
pattern = re.compile(r"^h(\d+)_d(\d+)_dx([\d.]+)_([PT])$")
for d in sorted(os.listdir(RES)):
    if not os.path.isdir(os.path.join(RES, d)):
        continue
    m = pattern.match(d)
    if not m:
        continue
    h, dg, dx, dirn = m.groups()
    res = os.path.join(RES, d, "steady", "result.txt")
    if not os.path.exists(res):
        continue
    exit_code_path = os.path.join(RES, d, "steady", "exit_code.txt")
    exit_code = None
    if os.path.exists(exit_code_path):
        with open(exit_code_path) as f:
            exit_code = f.read().strip()
    out_rows.append({
        "h_nm": h, "d_nm": dg, "dx_nm": dx, "direction": dirn,
        "exit_code": exit_code or "NA",
        "J_main_m2_s": read_field(res, "J_main_m2_s") or "NA",
        "Keff_m3": read_field(res, "Keff_m3") or "NA",
        "R_eff_Pa_s_per_m3": read_field(res, "R_eff_Pa_s_per_m3") or "NA",
        "steps": read_field(res, "steps_completed") or "NA",
    })

cols = ["h_nm", "d_nm", "dx_nm", "direction", "exit_code",
        "J_main_m2_s", "Keff_m3", "R_eff_Pa_s_per_m3", "steps"]
with open(os.path.join(RES, "summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in out_rows:
        w.writerow(r)

print(f"重建完成：{len(out_rows)} 档")
na = sum(1 for r in out_rows if r["steps"] == "NA")
print(f"steps 仍为 NA 的档数：{na}（应为 0）")
for r in out_rows[:3]:
    print(r)
