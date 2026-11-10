#!/usr/bin/env python3
"""拟合 Jain/局部立方律闭合的修正系数（D2 误差地图 9 点）。

物理背景：
- 沿槽(P)：模型 K = (0.5 h^3 + 0.5 H^3)/12（算术平均）高估来自忽略槽侧壁剪切。
- 跨槽(T)：模型 K = 1/(0.5/h^3 + 0.5/H^3)/12（调和平均）高估来自忽略台阶处额外耗散。
- H = h + d（槽内总高），w = 120 nm（槽宽）。

候选模型（全部写清楚自由度与物理含义），并给出 d=75 的留出验证预测。
"""
import numpy as np
import csv
from scipy.optimize import curve_fit

W = 120.0  # nm 槽宽

# ---------- 读数据 ----------
rows = []
with open("/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/analysis/error_table.csv") as f:
    for r in csv.DictReader(f):
        rows.append({k: float(v) if k not in ("dir",) else v for k, v in r.items()})

P = [(r["h_nm"], r["d_nm"], r["K_dns_m3"], r["K_model_m3"]) for r in rows if r["dir"] == "P"]
T = [(r["h_nm"], r["d_nm"], r["K_dns_m3"], r["K_model_m3"]) for r in rows if r["dir"] == "T"]

hP = np.array([p[0] for p in P]); dP = np.array([p[1] for p in P])
KdP = np.array([p[2] for p in P]); KmP = np.array([p[3] for p in P])
hT = np.array([t[0] for t in T]); dT = np.array([t[1] for t in T])
KdT = np.array([t[2] for t in T]); KmT = np.array([t[3] for t in T])

# ---------- 矩形通道流量归一系数（零参数解析） ----------
def beta_rect(H, W):
    # Q = G W H^3/(12 mu) * beta, beta = 1 - (192/pi^5)(H/W) sum_{n odd} tanh(n pi W/(2H))/n^5
    s = 0.0
    for n in range(1, 41, 2):
        s += np.tanh(n * np.pi * W / (2.0 * H)) / n**5
    return 1.0 - (192.0 / np.pi**5) * (H / W) * s

def report(name, h, d, K_dns, K_model, K_corr, k=None):
    E0 = (K_model - K_dns) / K_dns * 100
    E1 = (K_corr - K_dns) / K_dns * 100
    rms0 = np.sqrt(np.mean(E0**2)); rms1 = np.sqrt(np.mean(E1**2))
    print(f"[{name}] 修正前: 误差 {E0.min():+.1f}% ~ {E0.max():+.1f}%, RMS={rms0:.1f}%")
    print(f"         修正后: 误差 {E1.min():+.1f}% ~ {E1.max():+.1f}%, RMS={rms1:.1f}%", end="")
    if k is not None:
        print(f"  (参数: {k})")
    else:
        print()
    return E1

print("=" * 78)
print("沿槽方向 P（9 点）")
print("=" * 78)

# M1: F = 1/(1 + a (d/h)^b)  —— 纯经验幂律
def m1(X, a, b):
    h, d = X
    return 1.0 / (1.0 + a * (d / h) ** b)
p1, _ = curve_fit(m1, (hP, dP), KdP / KmP, p0=[0.5, 1.0])
Kc = KmP * m1((hP, dP), *p1)
report("M1 经验幂律 F=1/(1+a(d/h)^b)", hP, dP, KdP, KmP, Kc, np.round(p1, 4))

# M2: 槽内段用矩形通道解析解，beta_rect^alpha，alpha 单参数（注意 h³ 为 nm³，须乘 1e-27 转 m³）
def m2(X, alpha):
    h, d = X
    H = h + d
    beta = beta_rect(H, W)
    K = (0.5 * h**3 + 0.5 * H**3 * beta**alpha) / 12.0 * 1.0e-27
    return K
p2, _ = curve_fit(m2, (hP, dP), KdP, p0=[0.5], bounds=([0.0], [1.0]))
Kc = m2((hP, dP), *p2)
report("M2 矩形通道物理修正 beta_rect^alpha", hP, dP, KdP, KmP, Kc, np.round(p2, 4))

# M3: 槽内段 beta_rect * gamma（gamma 常数）
def m3(X, gamma):
    h, d = X
    H = h + d
    beta = beta_rect(H, W)
    K = (0.5 * h**3 + 0.5 * H**3 * (gamma * beta)) / 12.0 * 1.0e-27
    return K
p3, _ = curve_fit(m3, (hP, dP), KdP, p0=[1.5], bounds=([0.0], [10.0]))
Kc = m3((hP, dP), *p3)
report("M3 矩形通道 gamma*beta_rect", hP, dP, KdP, KmP, Kc, np.round(p3, 4))

# M5: 槽内等效系数 = beta_rect * (gamma + delta * h/H)（2 参数，考虑顶部耦合随 h/H 增强）
def m5(X, gamma, delta):
    h, d = X
    H = h + d
    beta = beta_rect(H, W)
    K = (0.5 * h**3 + 0.5 * H**3 * beta * (gamma + delta * h / H)) / 12.0 * 1.0e-27
    return K
p5, _ = curve_fit(m5, (hP, dP), KdP, p0=[1.0, 1.0], bounds=([0.0, -10.0], [10.0, 10.0]))
Kc = m5((hP, dP), *p5)
report("M5 beta_rect*(gamma+delta h/H)", hP, dP, KdP, KmP, Kc, np.round(p5, 4))

# M6: 槽内等效系数 = 1/(1 + a (H/w)^b)（2 参数，纯形状依赖）
def m6(X, a, b):
    h, d = X
    H = h + d
    beff = 1.0 / (1.0 + a * (H / W) ** b)
    K = (0.5 * h**3 + 0.5 * H**3 * beff) / 12.0 * 1.0e-27
    return K
p6, _ = curve_fit(m6, (hP, dP), KdP, p0=[0.6, 2.0])
Kc = m6((hP, dP), *p6)
report("M6 槽内系数=1/(1+a(H/w)^b)", hP, dP, KdP, KmP, Kc, np.round(p6, 4))

# M4: F = 1/(1 + a (d/H_ref)^b)，H_ref = h + 0.5 d
def m4(X, a, b):
    h, d = X
    Hr = h + 0.5 * d
    return 1.0 / (1.0 + a * (d / Hr) ** b)
p4, _ = curve_fit(m4, (hP, dP), KdP / KmP, p0=[0.5, 1.0])
Kc = KmP * m4((hP, dP), *p4)
report("M4 经验幂律 F=1/(1+a(d/H_ref)^b)", hP, dP, KdP, KmP, Kc, np.round(p4, 4))

print("=" * 78)
print("跨槽方向 T（9 点）")
print("=" * 78)

# T1: F = 1/(1 + a (d/H_ref)^b)
def t1(X, a, b):
    h, d = X
    Hr = h + 0.5 * d
    return 1.0 / (1.0 + a * (d / Hr) ** b)
q1, _ = curve_fit(t1, (hT, dT), KdT / KmT, p0=[0.2, 1.0])
Kc = KmT * t1((hT, dT), *q1)
report("T1 经验幂律 F=1/(1+a(d/H_ref)^b)", hT, dT, KdT, KmT, Kc, np.round(q1, 4))

# T2: F = 1/(1 + a (d/w)^b)
def t2(X, a, b):
    h, d = X
    return 1.0 / (1.0 + a * (d / W) ** b)
q2, _ = curve_fit(t2, (hT, dT), KdT / KmT, p0=[0.2, 1.0])
Kc = KmT * t2((hT, dT), *q2)
report("T2 经验幂律 F=1/(1+a(d/w)^b)", hT, dT, KdT, KmT, Kc, np.round(q2, 4))

# T3: 台阶耗散 = 一个附加阻力串联：K_corr = M / (1 + c*(d/H_ref))（1 参数，最简）
def t3(X, c):
    h, d = X
    Hr = h + 0.5 * d
    return 1.0 / (1.0 + c * (d / Hr))
q3, _ = curve_fit(t3, (hT, dT), KdT / KmT, p0=[0.5])
Kc = KmT * t3((hT, dT), *q3)
report("T3 单参数 F=1/(1+c(d/H_ref))", hT, dT, KdT, KmT, Kc, np.round(q3, 4))

# ---------- 留出验证预测：d = 75 nm ----------
print("=" * 78)
print("留出验证预测（d=75 nm，未参与任何拟合）——将来 DNS 对比用")
print("=" * 78)
print("沿槽 P（推荐 M4, a=%s b=%s）:" % (np.round(p4[0], 4), np.round(p4[1], 4)))
for h in (50.0, 75.0, 125.0):
    Km = (0.5 * h**3 + 0.5 * (h + 75.0) ** 3) / 12.0 * 1.0e-27
    Kc = Km * m4((h, 75.0), *p4)
    print(f"  h={h:g} d=75: 原模型 K={Km:.4e} m3 -> 修正 K={Kc:.4e} m3")
print("跨槽 T（推荐 T2, a=%s b=%s）:" % (np.round(q2[0], 4), np.round(q2[1], 4)))
for h in (50.0, 75.0, 125.0):
    Km = 1.0 / (0.5 / h**3 + 0.5 / (h + 75.0) ** 3) / 12.0 * 1.0e-27
    Kc = Km * t2((h, 75.0), *q2)
    print(f"  h={h:g} d=75: 原模型 K={Km:.4e} m3 -> 修正 K={Kc:.4e} m3")
