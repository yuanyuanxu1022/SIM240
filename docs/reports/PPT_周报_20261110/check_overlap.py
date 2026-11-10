#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 pptx 中文本框之间的重叠，以及形状越界"""
import sys
from pptx import Presentation

EMU = 914400
SW, SH = 13.333, 7.5


def rect(sh):
    return (sh.left / EMU, sh.top / EMU,
            (sh.left + sh.width) / EMU, (sh.top + sh.height) / EMU)


def overlap(a, b, tol=0.02):
    ix = min(a[2], b[2]) - max(a[0], b[0])
    iy = min(a[3], b[3]) - max(a[1], b[1])
    if ix <= tol or iy <= tol:
        return 0.0
    return ix * iy


def main(path):
    prs = Presentation(path)
    bad = 0
    for si, slide in enumerate(prs.slides, 1):
        texts = [(sh, rect(sh)) for sh in slide.shapes
                 if sh.has_text_frame and sh.text_frame.text.strip()]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a_sh, a = texts[i]
                b_sh, b = texts[j]
                ov = overlap(a, b)
                if ov > 0.03:
                    ta = a_sh.text_frame.text[:16].replace("\n", " ")
                    tb = b_sh.text_frame.text[:16].replace("\n", " ")
                    # 判断是否包含关系（白名单：文字在卡片内属正常）
                    inside = (a[0] <= b[0] + 0.01 and a[1] <= b[1] + 0.01
                              and a[2] >= b[2] - 0.01 and a[3] >= b[3] - 0.01) or \
                             (b[0] <= a[0] + 0.01 and b[1] <= a[1] + 0.01
                              and b[2] >= a[2] - 0.01 and b[3] >= a[3] - 0.01)
                    if inside:
                        continue
                    print(f"  页{si} 重叠 {ov:.2f}in²: 「{ta}」×「{tb}」")
                    bad += 1
        for sh in slide.shapes:
            r = rect(sh)
            if r[2] > SW + 0.01 or r[3] > SH + 0.01 or r[0] < -0.01 or r[1] < -0.01:
                print(f"  页{si} 越界: {(round(r[0],2), round(r[1],2), round(r[2],2), round(r[3],2))}"
                      f" 「{sh.text_frame.text[:14] if sh.has_text_frame else sh.shape_type}」")
                bad += 1
    print("✓ 无重叠无越界" if bad == 0 else f"⚠ 共 {bad} 处问题")


if __name__ == "__main__":
    main(sys.argv[1])
