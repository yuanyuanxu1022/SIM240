#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 pptx 文本是否溢出其文本框（基于字符宽度估算，中文按字）"""
import sys
from pptx import Presentation
from pptx.util import Emu
from PIL import ImageFont

EMU_PER_INCH = 914400
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
_cache = {}

def font(px, bold=False):
    key = (px, bold)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(BOLD if bold else REG, max(px, 6))
    return _cache[key]

def wrap_lines(text, width_pt, px_size, bold=False):
    f = font(px_size, bold)
    lines, cur = 0, ""
    for ch in text:
        if ch == "\n":
            lines += 1; cur = ""; continue
        if f.getlength(cur + ch) > width_pt:
            lines += 1; cur = ch
        else:
            cur += ch
    if cur:
        lines += 1
    return max(lines, 1)

def check(path):
    prs = Presentation(path)
    problems = []
    for si, slide in enumerate(prs.slides, 1):
        for shp in slide.shapes:
            if not shp.has_text_frame or not shp.text_frame.text.strip():
                continue
            box_w_pt = shp.width / EMU_PER_INCH * 72
            box_h_pt = shp.height / EMU_PER_INCH * 72
            total = 0.0
            for p in shp.text_frame.paragraphs:
                if not p.runs:
                    continue
                txt = "".join(r.text for r in p.runs)
                if not txt.strip():
                    continue
                sizes = [r.font.size.pt for r in p.runs if r.font.size]
                sz = max(sizes) if sizes else 18
                bold = any(r.font.bold for r in p.runs)
                ls = p.line_spacing if p.line_spacing else 1.2
                n = wrap_lines(txt, box_w_pt, sz, bold)
                sb = p.space_before.pt if p.space_before else 0
                total += n * sz * ls + sb
            if total > box_h_pt + 1:
                problems.append((si, shp.name, round(total, 1), round(box_h_pt, 1),
                                 shp.text_frame.text[:38].replace("\n", " ")))
    if problems:
        print("⚠ 溢出：页 | 形状 | 需要pt | 可用pt | 文本")
        for p in problems:
            print("  ", p)
    else:
        print("✓ 未检测到文本溢出")
    return problems

if __name__ == "__main__":
    check(sys.argv[1])
