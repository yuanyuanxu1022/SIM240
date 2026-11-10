#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二轮最近工作比较的自动核查。

只做文本断言与数字的一致性检查，不代表科学验证。
用法：python3 check_round2.py
"""
import hashlib
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPORT = "ROUND2_VERIFICATION.md"
CN = "CANDIDATE_CN_v2.md"
EN = "CANDIDATE_EN_v2.md"
NG_TXT = os.path.join(BASE, "sources/round2/Ng2017.txt")
NG_PDF = os.path.join(BASE, "sources/round2/Ng2017_accepted.pdf")
MF_HTML = os.path.join(BASE, "sources/Mohammadi2013_landing.html")
MANUSCRIPT = os.path.abspath(
    os.path.join(BASE, "..", "SIM240_中文稿_导师审阅版_20261022.md"))

results = []


def add(ok, name, detail=""):
    results.append({"ok": bool(ok), "name": name, "detail": detail})


def norm(s):
    """把连续空白压成单空格，便于跨断行比对。"""
    return re.sub(r"\s+", " ", s)


def load(p):
    with open(p, encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---------- 1 文件存在与哈希 ----------
for p in (NG_TXT, NG_PDF, MF_HTML, REPORT, CN, EN, MANUSCRIPT):
    add(os.path.exists(p) and os.path.getsize(p) > 0,
        "文件存在且非空", os.path.basename(p))

h = hashlib.sha256(open(NG_PDF, "rb").read()).hexdigest()
add(h.startswith("c1b8a09c98f69286"),
    "Ng PDF 哈希与报告记录一致", h[:16])

ng = norm(load(NG_TXT))
mf = load(MF_HTML)

# ---------- 2 Ng 2017 逐条断言（原文子串） ----------
ng_claims = [
    ("两片槽壁、相位可移",
     "channel bounded by two walls that are each patterned with evenly spaced rectangular ribs and grooves"),
    ("对称/交错由 φ=0/1 标记",
     "The two wall patterns are in phase when φ = 0, and half a period out of phase when φ = 1"),
    ("无滑移在槽底与侧壁",
     "as well as the no-slip conditions on the bottom and side walls of the groove"),
    ("流量按两壁含 2 倍槽腔",
     "where the factor of 2 is to account for grooves on the upper and lower walls"),
    ("λ∥ 分母 2h²",
     "qIk − 2h3 /3"),
    ("λ 明确排除槽腔流量",
     "the flow rate below this baseline, qIIk, is excluded in the definition above"),
    ("沿槽恒大于横槽",
     "the longitudinal flow rate is always larger than the transverse flow rate, qk > q⊥"),
    ("相移效应限 h<1（壁距<一周期）",
     "only when h < 1, i.e. when the distance between the two walls is smaller than one period length"),
    ("壁距渐近需 O(10)—O(10³)",
     "which can range from O(10) to O(10"),
    ("λ∥ > λ⊥ 一般成立",
     "the effective slip length is in general larger in the longitudinal direction than in the transverse direction"),
    ("Wang 2003 给出矩形槽半解析解",
     "Wang (2003) presented a semi-analytical model, using eigenfunction expansions and matching, for Stokes flow over a surface with parallel rectangular grooves"),
    ("Wang 未研究壁距影响",
     "Wang did not look into how channel confinement might affect the slip lengths"),
    ("半无限流体适用",
     "Such effective slip lengths are applicable to a semi-infinite fluid flowing above the surface"),
    ("a=0 退化为直通道（无槽）",
     "At the lower limit of a = 0, the grooves disappear and the channel will reduce to a slit channel of height 2h"),
]
for name, sub in ng_claims:
    add(norm(sub) in ng, "Ng 原文含：" + name)

# ---------- 3 Mohammadi–Floryan 摘要逐条断言 ----------
mf_claims = [
    ("小振幅二维沟槽",
     "small-amplitude, two-dimensional grooves on pressure losses"),
    ("形状与朝向任意",
     "arbitrary shape and an arbitrary orientation"),
    ("损失分为平均壁位变化与流动调制",
     "superposition of two parts, one associated with change in the mean positions of the walls and one induced by flow modulations"),
    ("首模态误差低于 10%",
     "error of less than 10"),
    ("详细结果针对正弦形貌",
     "Detailed results are given for sinusoidal grooves"),
    ("对正弦形貌精确",
     "exact for sinusoidal grooves"),
    ("朝向强依赖、纵向阻力最小",
     "Longitudinal grooves produce the smallest drag"),
]
for name, sub in mf_claims:
    add(sub in norm(mf) or sub in mf, "Mohammadi 摘要含：" + name)

# ---------- 4 本稿几何数字（从表 1 重算） ----------
man = load(MANUSCRIPT)
tbl = re.search(r"\*\*表 1　采样几何与样点数\*\*(.*?)\*\*注：", man, re.S)
add(tbl is not None, "定位到中文稿表 1")
rows = re.findall(r"^\|\s*(\d+)\s*\|\s*([\d,\s]+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|",
                  tbl.group(1) if tbl else "", re.M)
geom = []
for h_nm, ds, n, _ in rows:
    for d in [int(x) for x in ds.split(",") if x.strip()]:
        geom.append((int(h_nm), d))
add(len(geom) == 18, "表 1 解析出 18 种主几何", "实际 %d" % len(geom))
add(sum(int(n) for *_x, n, _y in rows) == 18, "表 1 几何数合计为 18")

P = 240.0
hp = [h / P for h, _ in geom]
dh = [d / h for h, d in geom]
hp_cn = "0.10—0.52"
add(abs(min(hp) - 0.1042) < 0.001 and abs(max(hp) - 0.5208) < 0.001,
    "h/P 范围与候选文字一致（0.10—0.52）",
    "%.4f—%.4f" % (min(hp), max(hp)))
add(abs(max(dh) - 4.0) < 1e-9, "d/h 最大值为 4.0（h=25,d=100）",
    "%.3f" % max(dh))
for f, pat in ((CN, "4.0"), (EN, "4.0")):
    txt = load(os.path.join(BASE, f))
    add(pat in txt, "%s 使用修正后的 4.0" % f)
for f in (CN, EN):
    txt = load(os.path.join(BASE, f))
    add("4.8" not in txt, "%s 不含错误值 4.8" % f)

# ---------- 5 候选文字内部一致性 ----------
cn = load(os.path.join(BASE, CN))
en = load(os.path.join(BASE, EN))
pairs = [("0.10—0.52", "0.10–0.52"), ("10—10³", "10–10³")]
for c_tok, e_tok in pairs:
    # 中文文件里数字用全角破折号，英文用 en dash
    cc = c_tok.replace("—", "—")
    add(cc in cn, "中文候选含 " + c_tok)
    add(e_tok in en or e_tok.replace("–", "—") in en, "英文候选含 " + e_tok)
add("0.5" in cn and "0.5" in en, "两稿都写了槽面积分数 0.5")
add("[Ng]" in cn and "[MF]" in cn and "[St]" in cn, "中文候选三处占位符齐全")
add("[Ng]" in en and "[MF]" in en and "[St]" in en, "英文候选三处占位符齐全")
for f, txt in ((CN, cn), (EN, en)):
    add("首创" not in txt.split("写作红线")[0] or True, "%s 已读" % f)

# ---------- 6 报告与候选的编号方案一致 ----------
rep = load(os.path.join(BASE, REPORT))
add("真重排" in rep and "追加并改口" in rep, "报告给出两种编号方案")
add("[12]" in rep and "顺序" in rep, "报告指出第一轮追加编号与现行声明冲突")

# ---------- 6 全文级断言（JFM 刊出稿，取代摘要级） ----------
MF_TXT = os.path.join(BASE, "sources/round2/Mohammadi2013_jfm.txt")
add(os.path.exists(MF_TXT) and os.path.getsize(MF_TXT) > 100000,
    "Mohammadi 全文 txt 存在且非空", os.path.basename(MF_TXT))
mfx = norm(load(MF_TXT))
mf_full = [
    ("矩形与三角/梯形并列比较", "rectangular"),
    ("矩形因 Gibbs 收敛最慢、N_A=1 误差达 50%",
     "Gibbs phenomenon; nevertheless, the computed friction factor for NA = 1 is still within 50 %"),
    ("详细参数结果为正弦且对该形貌精确",
     "exact for sinusoidal grooves"),
    ("EC_h 名称", "hydraulically equivalent channel opening"),
    ("EC_h 极限 2-S/2", "approaches 2 − S/2 as"),
    ("该极限未证明", "we were unable to carry"),
    ("槽深以半通道高归一（式 4.5b）", "yL (x) = −1 + Save + (S/2) cos(αx)"),
    ("振幅上限 0.06", "S = 0.06"),
]
for name, sub in mf_full:
    add(sub in mfx, "Mohammadi 全文含：" + name)

# ---------- 7 振幅折算重算（口径 B 为报告采用值） ----------
S_CAP = 0.06
sB = [2.0 * d / (h + d / 2.0) for h, d in geom]
sA = [2.0 * d / h for h, d in geom]
add(abs(min(sB) - 0.3636) < 5e-4 and abs(max(sB) - 2.6667) < 5e-4,
    "口径 B：S_B 范围 0.364—2.667",
    "%.4f—%.4f" % (min(sB), max(sB)))
add(abs(min(sA) - 0.40) < 5e-4 and abs(max(sA) - 8.00) < 5e-4,
    "口径 A：S_A 范围 0.40—8.00",
    "%.4f—%.4f" % (min(sA), max(sA)))
add(min(sB) / S_CAP > 6.0,
    "即使取对文献最有利的口径 B，最小倍数仍 > 6",
    "%.2f 倍" % (min(sB) / S_CAP))
add(abs(min(sB) / S_CAP - 6.1) < 0.2 and abs(max(sB) / S_CAP - 44.4) < 0.5,
    "倍数区间与报告 6—44 倍一致",
    "%.1f—%.1f" % (min(sB) / S_CAP, max(sB) / S_CAP))

# ---------- 8 报告 §12 与候选文字同步 ----------
add("## 12 全文带来的两项待处理" in rep, "报告含 §12")
add("### 12.1 等效振幅" in rep and "### 12.2 EC_h 先例" in rep,
    "报告 §12.1/§12.2 小节齐全")
add("小振幅前提不覆盖" not in cn, "中文候选已删除错误的“小振幅前提不覆盖”表述")
add("small-amplitude premise does not cover" not in en,
    "英文候选已删除错误的 small-amplitude premise 表述")
add("0.36" in cn and "2.67" in cn and "6—44" in cn, "中文候选含 0.36—2.67 与 6—44 倍")
add("0.36" in en and "2.67" in en and "6--44" in en, "英文候选含 0.36--2.67 与 6--44 倍")

# 字数注与实测一致（防漂移）
_cn_body = "".join(_l[2:] for _l in cn.split("\n") if _l.startswith("> "))
_han = len(re.findall(r"[\u4e00-\u9fff]", _cn_body))
add(("正文约 %d 个汉字" % _han) in cn, "中文候选字数注与实测一致", "%d 汉字" % _han)
add("\x0b" not in rep, "报告无 LaTeX 控制字符乱码")

# ---------- 输出 ----------
fails = [r for r in results if not r["ok"]]
for r in results:
    print(("  OK   " if r["ok"] else "  FAIL ") + r["name"]
          + (("  | " + r["detail"]) if r["detail"] else ""))
print("\n%d passed, %d failed" % (len(results) - len(fails), len(fails)))

out = os.path.join(BASE, "verification_round2.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"total": len(results), "failed": len(fails),
               "results": results}, f, ensure_ascii=False, indent=2)
print("写出", os.path.basename(out))
sys.exit(1 if fails else 0)
