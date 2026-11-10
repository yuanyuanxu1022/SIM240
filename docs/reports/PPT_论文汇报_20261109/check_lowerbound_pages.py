#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 论文汇报.pptx 的页数、页脚连续性、第 4/7 页内容与新口径一致性。

只读检查，不修改 pptx。数字口径以 docs/reports/PAPER1_conclusions_current_20261109.md
与论文附录 E.1 为准。
"""
import hashlib
import os
import re
import subprocess
import sys

from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
PPTX = os.path.join(HERE, "论文汇报.pptx")
EXPECT_PAGES = 14

checks = []


def add(name, ok, detail=None):
    checks.append((name, bool(ok), detail))


def slide_text(s):
    out = []
    for sh in s.shapes:
        if sh.has_text_frame:
            out.append(sh.text_frame.text)
    return "\n".join(out)


prs = Presentation(PPTX)
slides = list(prs.slides)
add("总页数为 14", len(slides) == EXPECT_PAGES, len(slides))

# 页脚连续性：每页（封面除外）应有一个 "N / 14"
foot = re.compile(r"^(\d+)\s*/\s*14$")
nums = []
for i, s in enumerate(slides):
    hits = [m.group(1) for t in slide_text(s).splitlines() for m in [foot.match(t.strip())] if m]
    if hits:
        nums.append((i + 1, int(hits[0])))
add("除封面外每页都有页脚", len(nums) == EXPECT_PAGES - 1, len(nums))
add("页脚编号与该页序号一致",
    all(page == num for page, num in nums),
    [f"slide{page}!=footer{num}" for page, num in nums if page != num])
add("页脚编号从 2 连续到 14",
    [n for _, n in nums] == list(range(2, EXPECT_PAGES + 1)),
    [n for _, n in nums])

# 第 4 页（定理）：必须同时出现上下界
t4 = slide_text(slides[3])
add("第 4 页含下界 h³/12", "h³/12" in t4)
add("第 4 页含上界符号", "≤" in t4 and "LCL" in t4)
add("第 4 页标题点明上下界", "上界与下界" in t4)
add("第 4 页旧说法已消失", "局部立方律给出的是上界，只有无槽平板" not in t4)

# 第 7 页（可行区间）
t7 = slide_text(slides[6])
add("第 7 页标题存在", "地板在哪里" in t7)
add("第 7 页含闭式 (1 + r³)/2", "(1 + r³)/2" in t7)
add("第 7 页含闭式 2r³/(1 + r³)", "2r³/(1 + r³)" in t7)
add("第 7 页含 63.00 与 1.984", "63.00" in t7 and "1.984" in t7)
add("第 7 页含 11/18", "11/18" in t7)
add("第 7 页含两位小数偏差", all(k in t7 for k in ("58.17", "23.84", "88.85", "30.63")))
add("第 7 页含宽度依赖免责", "不含槽宽" in t7 or "槽宽 w" in t7)
add("第 7 页插入区间图", any(sh.shape_type == 13 for sh in slides[6].shapes))
add("第 7 页未越界",
    all(sh.left + sh.width <= prs.slide_width and sh.top + sh.height <= prs.slide_height
        for sh in slides[6].shapes))

# 第 6 页的过渡句已指向第 7 页
t6 = slide_text(slides[5])
add("第 6 页过渡句指向新页", "下一页把“地板”补上" in t6)
add("第 6 页不再把等效缝高说成下一页", "下一页先把“偏这么多”换成能感知的数" not in t6)

# 图存在且非空
png = os.path.join(HERE, "interval_cn.png")
add("interval_cn.png 存在", os.path.exists(png) and os.path.getsize(png) > 10000,
    os.path.getsize(png) if os.path.exists(png) else None)

# 溢出与重叠脚本
env_py = sys.executable
for script, expect in (("check_overflow.py", "未检测到文本溢出"), ("check_overlap.py", "无重叠无越界")):
    r = subprocess.run([env_py, os.path.join(HERE, script), PPTX],
                       capture_output=True, text=True)
    ok = expect in r.stdout
    add(f"{script} 通过", ok, (r.stdout + r.stderr).strip().splitlines()[-3:])

# 输出哈希
h = hashlib.sha256(open(PPTX, "rb").read()).hexdigest()
add("pptx 非空", os.path.getsize(PPTX) > 50000, os.path.getsize(PPTX))

failed = [c for c in checks if not c[1]]
for name, ok, detail in checks:
    print(("  OK  " if ok else "  FAIL") + f"  {name}" + ("" if ok else f"   -> {detail}"))
print(f"\n{len(checks) - len(failed)} passed, {len(failed)} failed")
print(f"pptx sha256 = {h}")
sys.exit(0 if not failed else 1)
