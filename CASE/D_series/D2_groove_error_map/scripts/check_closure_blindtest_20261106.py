#!/usr/bin/env python3
"""闭环盲测批次（2026-11-06）结果核对。

输入：
  results/h100_d100_dx5_{P,T}/steady/result.txt    A 组，盲测
  results/h75_d100_dx5_buildB_{P,T}/steady/result.txt  B 组，构建复跑
  results/h75_d100_dx5_{P,T}/steady/result.txt     历史构建 A 结果（只读）

输出：
  closure_blindtest_verdict.json  判定与逐项数值

判据在开跑前已冻结（见 REPORT.md §6.3 与运行脚本头注释），本脚本只做对照，
不改判据、不改任何历史结果。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "closure_blindtest_verdict.json")

W_NM = 120.0


def K0(h, d, w=W_NM):
    """原局部立方律，单位 m^3（长度按 nm 代入后乘 1e-27）。"""
    kyy = ((h + d) ** 3 + h ** 3) / 24.0
    kxx = (h ** 3 * (h + d) ** 3) / (6.0 * (h ** 3 + (h + d) ** 3))
    return kxx * 1e-27, kyy * 1e-27


def v2_factors(d, w=W_NM):
    r = d / w
    fxx = 1.0 / (1.0 + 0.4900 * r ** 0.6990)
    fyy = 1.0 / (1.0 + 1.7685 * r ** 1.6331)
    return fxx, fyy


def read_case(run_dir):
    """读 result.txt，返回 h/d/K/方向/退出码；缺失返回 None。"""
    path = os.path.join(RES, run_dir, "steady", "result.txt")
    if not os.path.exists(path):
        return None
    txt = open(path, encoding="utf-8", errors="replace").read()

    def g(key):
        m = re.search(key + r"=([-\d.eE+]+)", txt)
        return float(m.group(1)) if m else None

    direction = re.search(r"direction=(\w+)", txt)
    return {
        "dir": direction.group(1) if direction else "?",
        "h_nm": g("mesa_gap_m") * 1e9,
        "d_nm": g("groove_depth_m") * 1e9,
        "K_m3": g("Keff_m3"),
        "PASS": re.search(r"PASS=(\w+)", txt).group(1) if re.search(r"PASS=(\w+)", txt) else "?",
    }


def bias(formula_K, ref_K):
    return (formula_K / ref_K - 1.0) * 100.0


def main():
    report = {"criteria_frozen": True, "cases": {}, "verdict": {}}
    missing = []

    # ---------- A 组：h=100/d=100，盲测 ----------
    a = {}
    for dirn, comp in (("P", "Kyy"), ("T", "Kxx")):
        rec = read_case(f"h100_d100_dx5_{dirn}")
        if rec is None:
            missing.append(f"h100_d100_dx5_{dirn}")
            continue
        k0x, k0y = K0(rec["h_nm"], rec["d_nm"])
        fxx, fyy = v2_factors(rec["d_nm"])
        k0 = k0y if comp == "Kyy" else k0x
        f = fyy if comp == "Kyy" else fxx
        a[comp] = {
            "run_dir": f"h100_d100_dx5_{dirn}",
            "PASS": rec["PASS"],
            "K0_m3": k0,
            "K_V2_pred_m3": k0 * f,
            "K_measured_m3": rec["K_m3"],
            "V2_bias_percent": bias(k0 * f, rec["K_m3"]),
            "original_bias_percent": bias(k0, rec["K_m3"]),
        }
    if len(a) == 2:
        a["A_measured"] = a["Kyy"]["K_measured_m3"] / a["Kxx"]["K_measured_m3"]
        a["A_predicted"] = a["Kyy"]["K_V2_pred_m3"] / a["Kxx"]["K_V2_pred_m3"]
        a["A_bias_percent"] = (a["A_measured"] / a["A_predicted"] - 1.0) * 100.0
        a["below_bound_both"] = all(a[c]["K_measured_m3"] <= a[c]["K0_m3"] for c in ("Kxx", "Kyy"))

    # ---------- B 组：h=75/d=100，当前构建 vs 历史构建 A ----------
    b = {}
    for dirn, comp in (("P", "Kyy"), ("T", "Kxx")):
        old = read_case(f"h75_d100_dx5_{dirn}")
        new = read_case(f"h75_d100_dx5_buildB_{dirn}")
        if old is None or new is None:
            missing.append(f"h75_d100_dx5_buildB_{dirn}")
            continue
        b[comp] = {
            "K_buildA_m3": old["K_m3"],
            "K_buildB_m3": new["K_m3"],
            "build_difference_percent": (new["K_m3"] / old["K_m3"] - 1.0) * 100.0,
            "PASS_buildB": new["PASS"],
        }

    # ---------- 判定 ----------
    v = {}
    if len(a) >= 3:
        worst = max(abs(a["Kxx"]["V2_bias_percent"]), abs(a["Kyy"]["V2_bias_percent"]))
        v["A_primary_worst_abs_bias_percent"] = worst
        v["A_primary_pass_le_10pct"] = bool(worst <= 10.0)
        v["A_direction_ratio_pass_le_10pct"] = bool(abs(a["A_bias_percent"]) <= 10.0)
        v["A_below_theory_bound"] = bool(a["below_bound_both"])
    if b:
        v["build_effect_max_abs_percent"] = max(abs(x["build_difference_percent"]) for x in b.values())
        v["build_effect_within_1pct"] = bool(v["build_effect_max_abs_percent"] <= 1.0)
    if "h75_d100_dx5_P" in os.listdir(RES) and "Kxx" in a and "Kxx" in b:
        # 结构判据：A 组残差与 h75/d100 残差之差
        k0x, k0y = K0(75.0, 100.0)
        fxx, fyy = v2_factors(100.0)
        old_xx = read_case("h75_d100_dx5_T")
        old_yy = read_case("h75_d100_dx5_P")
        if old_xx and old_yy:
            r_xx = bias(k0x * fxx, old_xx["K_m3"])
            r_yy = bias(k0y * fyy, old_yy["K_m3"])
            d_xx = abs(a["Kxx"]["V2_bias_percent"] - r_xx)
            d_yy = abs(a["Kyy"]["V2_bias_percent"] - r_yy)
            v["structural_diff_points"] = {"Kxx": d_xx, "Kyy": d_yy}
            v["structural_pass_le_5points"] = bool(max(d_xx, d_yy) <= 5.0)

    report["cases"]["A_blind_h100_d100"] = a
    report["cases"]["B_buildcheck_h75_d100"] = b
    report["verdict"] = v
    report["missing"] = missing

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    # ---------- 屏幕输出 ----------
    print("=" * 74)
    print("A 组（h=100/d=100，盲测）")
    print("=" * 74)
    if len(a) >= 3:
        for comp in ("Kxx", "Kyy"):
            r = a[comp]
            print(f"  {comp}  K0={r['K0_m3']:.6e}  V2预测={r['K_V2_pred_m3']:.6e}  "
                  f"实测={r['K_measured_m3']:.6e}  V2偏差={r['V2_bias_percent']:+.2f}%  "
                  f"原公式偏差={r['original_bias_percent']:+.2f}%")
        print(f"  方向比 A：预测 {a['A_predicted']:.4f}  实测 {a['A_measured']:.4f}  偏差 {a['A_bias_percent']:+.2f}%")
        print(f"  两方向是否都在理论上界之下：{a['below_bound_both']}")
    else:
        print("  结果不完整，缺：", [m for m in missing if "h100" in m])

    print("=" * 74)
    print("B 组（h=75/d=100，当前构建复跑 vs 历史构建 A）")
    print("=" * 74)
    if b:
        for comp in ("Kxx", "Kyy"):
            if comp in b:
                r = b[comp]
                print(f"  {comp}  构建A={r['K_buildA_m3']:.6e}  构建B={r['K_buildB_m3']:.6e}  "
                      f"差={r['build_difference_percent']:+.4f}%")
    else:
        print("  结果不完整，缺：", [m for m in missing if "buildB" in m])

    print("=" * 74)
    print("判定")
    print("=" * 74)
    for k, val in v.items():
        print(f"  {k}: {val}")
    print(f"\n写入 {OUT}")


if __name__ == "__main__":
    sys.exit(main())
