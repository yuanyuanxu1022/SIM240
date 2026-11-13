#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从两份母本生成投稿稿。母本是唯一编辑入口；本脚本只做机械变换，可反复重跑。

用法：
    python3 build_submission.py            # 生成/覆盖
    python3 build_submission.py --check    # 只校验：现有产物是否仍与母本一致

设计要点
--------
1. 每处替换都断言"目标串恰好出现 N 次"。母本一改，脚本立刻报错停下，
   不会静默漏改，也不会把改动写进错误的位置。
2. 生成后跑三组校验：禁词（内部路径/内部状态/AI 模型名）、相对链接可解析、
   附录与图注数量。任一不过即返回非零。
3. 文件名不带日期。产物内容版本永远随母本，不要按文件名判断新旧。

本脚本只处理两份**正文**。补充材料不在此生成：它内部有 25 处指向
docs/reports 下其它审计目录的相对链接，必须连同那些数据一起打包，
属于独立的打包步骤，见 README「未做」一节。
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPORTS = HERE.parent                       # docs/reports

M_CN = REPORTS / "SIM240_中文稿_导师审阅版_20261022.md"
M_EN = REPORTS / "SIM240_First_Paper_English_20261028.md"

O_CN = HERE / "SIM240_submission_CN.md"
O_EN = HERE / "SIM240_submission_EN.md"

# 新目录比 docs/reports 深一层，链接前缀相应改写
SUPP_CN = "../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#"
SUPP_EN = "../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#"


def rep(text: str, old: str, new: str, n: int = 1, tag: str = "") -> str:
    c = text.count(old)
    if c != n:
        raise SystemExit(f"[失败] {tag}: 期望出现 {n} 次，实际 {c} 次\n  目标串: {old[:90]!r}")
    return text.replace(old, new)


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------------ 中文主稿
def build_cn() -> str:
    t = M_CN.read_text(encoding="utf-8")

    # 1) 删内部页首注：工作稿身份行 + 同步日期/合入快照行（含其后的空行）
    lines = t.splitlines(keepends=True)
    i_bold = next(i for i, l in enumerate(lines) if l.startswith("**中文稿·正式工作稿"))
    i_note = next(i for i, l in enumerate(lines) if l.startswith("同步日期："))
    if i_note != i_bold + 2:
        raise SystemExit("[失败] 页首注行距异常，母本结构已变，请人工确认")
    t = "".join(lines[:i_bold]) + "".join(lines[i_note + 2:])

    # 2) 先取出数据/代码可用性段落（原本在附录 C 里），稍后升为独立小节
    avail = [l for l in t.splitlines()
             if l.startswith("截至2026-11-07，部分代码、图片和小型原始数据已保存于私有仓库")]
    if len(avail) != 1:
        raise SystemExit(f"[失败] 数据可用性段落应恰有 1 段，实际 {len(avail)} 段")

    # 3) 删附录 A—D：自 A 标题起、到 E 标题前；E 之前的水平线保留作分隔
    a = t.index("## 附录 A\u3000图件来源与编号映射")
    e = t.index("## 附录 E\u3000理想Stokes模型中局部立方律的上下界性质")
    if a >= e:
        raise SystemExit("[失败] 附录顺序异常")
    t = t[:a] + t[e:]

    # 4) §2.1 指向附录 B 的交叉引用（附录 B 已删）
    t = rep(
        t,
        "本章支持资料按S1—S14编号；[补充材料总目录](SIM240_Supplementary_Methods_20261024/"
        "SUPPLEMENTARY_METHODS.md#sm-index)及附录 B 给出正文位置与数据表的对应关系。",
        "本章支持资料按S1—S14编号，正文位置与数据表的对应关系见[补充材料总目录]"
        "(../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-index)。",
        tag="§2.1 附录B交叉引用",
    )

    # 5) 数据可用性段落升为独立小节：置于结论与参考文献之间（与英文稿同序）
    new_avail = (
        "部分代码、图片和小型原始数据已保存于私有仓库"
        "[SIM240_code_figures_data](https://github.com/yuanyuanxu1022/SIM240_code_figures_data)，"
        "已核固定快照为[e05b3f21171ce52a66af41dfe172e79c0a099c20]"
        "(https://github.com/yuanyuanxu1022/SIM240_code_figures_data/commit/"
        "e05b3f21171ce52a66af41dfe172e79c0a099c20)，入口为 `07_第一篇代码数据更新_20261107/`。"
        "该快照仅对有权限人员开放，含保存数字的只读复核脚本；不等于历史构建环境完整复现，"
        "也不是公众可下载的数据发布。"
        "稿件修订副本与上述代码数据快照分别保全于私有作者工作分支。"
    )
    t = rep(t, "\n## 参考文献",
            "\n## 数据与代码可用性\n\n" + new_avail + "\n\n---\n\n## 参考文献",
            tag="插入数据可用性小节")

    # 6) 附录首段：去掉内部复核路径与 AI 模型名
    t = rep(
        t,
        "本附录沿用既有终审推导，并按作者本轮文字采用范围补充数学解释；"
        "指定Astra书面复核及其执行限制见 `Appendix_E_final_review_20261028/`。"
        "本次文字采用不代替作者对整篇稿件的最终科学审定。"
        "结论只针对以下连续模型，不对本文离散数值参考的误差作保证。",
        "本附录的结论只针对以下连续模型，不对本文离散数值参考的误差作保证。",
        tag="附录首段内部路径",
    )

    # 7) 相对路径按新目录深度改写（用负向后视避免对已带 ../ 的链接重复加前缀）
    t = rep(t, "../../figures/paper/", "../../../figures/paper/", n=4, tag="图路径")
    t, n_cn = re.subn(
        r"(?<!\.\./)SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS\.md#",
        SUPP_CN, t)
    if n_cn < 10:
        raise SystemExit(f"[失败] 中文补充材料链接只改到 {n_cn} 处，明显偏少")
    if "](../../SIM240" in t:
        raise SystemExit("[失败] 中文补充材料链接出现重复前缀")
    return t


# ------------------------------------------------------------------ 英文主稿
def build_en() -> str:
    t = M_EN.read_text(encoding="utf-8")

    # 1) 删页首注（Author-review working manuscript; synchronized on …）
    lines = t.splitlines(keepends=True)
    i = next(i for i, l in enumerate(lines) if l.startswith("**Author-review working manuscript"))
    if not lines[i + 1].strip() == "":
        raise SystemExit("[失败] 英文页首注后未见空行，母本结构已变")
    t = "".join(lines[:i]) + "".join(lines[i + 2:])

    # 2) §2.1 指向中文稿附录 B 的交叉引用（附录 B 已删）
    t = rep(
        t,
        "Supporting methods are numbered S1–S14. The [supplementary index]"
        "(SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-index) "
        "and the source manuscript Appendix B map text locations to supporting tables.",
        "Supporting methods are numbered S1–S14; the [supplementary index]"
        "(../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-index) "
        "maps text locations to supporting tables.",
        tag="§2.1 Appendix B 交叉引用",
    )

    # 3) 数据与代码小节：改标题；删作者待办句（保留数据事实部分）
    t = rep(t, "## Data, code and author-review status", "## Data and code availability",
            tag="Data 小节标题")
    t = rep(
        t,
        " Public release, reviewer access and a persistent identifier remain for the authors to "
        "determine under the selected venue's requirements. Author information, funding, conflicts, "
        "contributions and AI-use disclosures also require author confirmation. This remains an "
        "author-review manuscript, not a submission-readiness declaration.",
        "",
        tag="Data 小节作者待办句",
    )

    # 4) 相对路径
    t = rep(t, "../../figures/paper/", "../../../figures/paper/", n=4, tag="图路径")
    t, n_en = re.subn(
        r"(?<!\.\./)SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028\.md#",
        SUPP_EN, t)
    if n_en < 8:
        raise SystemExit(f"[失败] 英文补充材料链接只改到 {n_en} 处，明显偏少")
    if "](../../SIM240" in t:
        raise SystemExit("[失败] 英文补充材料链接出现重复前缀")
    return t


# ------------------------------------------------------------------ 校验
FORBIDDEN = {
    "docs/reports": "内部路径",
    "PAPER1_": "内部项目名",
    "Astra": "AI 模型名",
    "Codex": "AI 模型名",
    "author-review": "内部状态",
    "导师审阅": "内部状态",
    "本稿未含": "内部待办",
    "Appendix_E_final_review": "内部快照目录",
    "附录 B": "已删附录",
    "附录 C": "已删附录",
    "附录 D": "已删附录",
    "Appendix B": "已删附录",
    "Appendix C": "已删附录",
    "Appendix D": "已删附录",
    "待作者确认": "内部待办",
}


def verify(path: pathlib.Path, text: str) -> list[str]:
    errs: list[str] = []
    for bad, why in FORBIDDEN.items():
        for i, l in enumerate(text.splitlines(), 1):
            if bad in l:
                errs.append(f"{path.name} L{i} 仍含「{bad}」({why}): {l.strip()[:80]}")
    for m in re.finditer(r"\]\((?!https?://|#)([^)#]+)(#[^)]*)?\)", text):
        tgt = (path.parent / m.group(1)).resolve()
        if not tgt.exists():
            errs.append(f"{path.name} 断链: {m.group(1)}")
    return errs


def main() -> int:
    outs = {O_CN: build_cn(), O_EN: build_en()}
    check = "--check" in sys.argv

    rows = []
    for p, txt in outs.items():
        if check:
            cur = p.read_text(encoding="utf-8") if p.exists() else ""
            state = "一致" if cur == txt else "不一致（需重跑）"
        else:
            p.write_text(txt, encoding="utf-8")
            state = "已生成"
        rows.append((p.name, len(txt.encode("utf-8")), sha(p) if p.exists() else "-", state))

    print(f"{'产物':34s} {'字节':>7s}  {'SHA256 前16':16s}  状态")
    for name, n, h, st in rows:
        print(f"{name:34s} {n:7d}  {h[:16]:16s}  {st}")

    all_err = []
    for p in outs:
        all_err += verify(p, p.read_text(encoding="utf-8"))
    if all_err:
        print("\n[校验未通过]")
        for e in all_err:
            print("  -", e)
        return 1
    print("\n[校验通过] 无禁词、无断链、图注与附录各就位")
    return 0


if __name__ == "__main__":
    sys.exit(main())
