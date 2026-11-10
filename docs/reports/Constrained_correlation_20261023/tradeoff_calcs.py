# -*- coding: utf-8 -*-
"""DECISION_TRADEOFF_20261023.md 的新增计算复现脚本（WorkBuddy/GLM-5.3, 2026-10-23）。
计算：①各方案各向异性比 A=K_P/K_T 的留组误差；②混合方案C（P取G4、T取G6）误差；
③混合方案 K_T<=K_P 结构风险有限扫描。只读 predictions.csv / fits.json，不修改任何文件。"""
import csv, math, json
from collections import defaultdict

BASE = '/home/dell/yuanyuanxu/SIM240/docs/reports/Constrained_correlation_20261023/'
rows = list(csv.DictReader(open(BASE + 'predictions.csv')))
data = defaultdict(dict)
for r in rows:
    geo = r['key'].rsplit('_', 1)[0]
    data[(r['scheme'], r['model'], geo)][r['direction']] = (float(r['K_pred_m3']), float(r['K_raw_m3']))

# ① 各向异性比误差（同模型）
for scheme in ('leave_h', 'leave_d', 'training'):
    for model in ('G4', 'G6'):
        ea = []
        for (sc, m, geo), dd in data.items():
            if sc == scheme and m == model and 'P' in dd and 'T' in dd:
                Ap, Ar = dd['P'][0]/dd['T'][0], dd['P'][1]/dd['T'][1]
                ea.append(abs(Ap/Ar-1)*100)
        print(f"{scheme:8s} {model}: A比 MAE={sum(ea)/len(ea):.2f}% 最坏={max(ea):.2f}% n={len(ea)}")

# ② 混合方案C：A比误差
print("\n混合方案C（P取G4、T取G6）A比误差：")
for scheme in ('leave_h', 'leave_d', 'training'):
    ea = []
    for geo in set(g for (s, m, g) in data if s == scheme):
        try:
            p4, t6 = data[(scheme, 'G4', geo)]['P'], data[(scheme, 'G6', geo)]['T']
        except KeyError:
            continue
        ea.append(abs((p4[0]/t6[0])/(p4[1]/t6[1])-1)*100)
    print(f"  {scheme:8s}: A比 MAE={sum(ea)/len(ea):.2f}% 最坏={max(ea):.2f}% n={len(ea)}")

# ③ 结构风险：混合后 K_T(G6) <= K_P(G4) 有限扫描
fits = json.load(open(BASE + 'fits.json'))
def gains(s, t):
    r = t*(3+t*(3+t)); return r/2, r/(r+2)
def blend(x, y, m):
    lo, hi = min(x, y), max(x, y)
    return lo/(1+(lo/hi)**m)**(1/m)
def E(s, t, model):
    pt, pp = fits[model]['T'], fits[model]['P']
    mT = pt[2] if len(pt) == 3 else 1.0
    mP = pp[2] if len(pp) == 3 else 1.0
    LP, LT = gains(s, t)
    ET = blend(LT, math.exp(pt[0])*s**pt[1], mT)
    EP = ET + blend(LP-ET, math.exp(pp[0])*s**pp[1]+s*s*t/2, mP)
    return EP, ET

for label, grid in [
    ('目标矩形(0.8<=s<=3.2,1/3<=t<=1.6) 6561点',
     [(0.8*(3.2/0.8)**(i/80), (1/3)*(1.6/(1/3))**(j/80)) for i in range(81) for j in range(81)]),
    ('扩展域(s,t各4个量级) 10201点',
     [(10**(-3+6*i/100), 10**(-7+11*j/100)) for i in range(101) for j in range(101)])]:
    viol = sum(1 for s, t in grid if E(s, t, 'G6')[1] > E(s, t, 'G4')[0] + 1e-15)
    print(f"{label}: 违反 K_T(G6)>K_P(G4) 点数 = {viol}")
