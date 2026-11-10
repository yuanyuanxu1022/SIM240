#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 pptx 渲染成 PNG 预览（Pillow 轻量渲染，仅用于预览排版）"""
import sys
from pptx import Presentation
from pptx.util import Emu
from PIL import Image, ImageDraw, ImageFont

PPTX = sys.argv[1]
OUT_PREFIX = sys.argv[2] if len(sys.argv) > 2 else "preview"

EMU_PER_INCH = 914400
SCALE = 1.5  # 输出放大倍数

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
BOLD_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
] + FONT_CANDIDATES


def find_font(cands):
    import os
    for c in cands:
        if os.path.exists(c):
            return c
    return None


REG_PATH = find_font(FONT_CANDIDATES)
BOLD_PATH = find_font(BOLD_CANDIDATES)
_cache = {}


def get_font(path, px):
    key = (path, px)
    if key not in _cache:
        try:
            _cache[key] = ImageFont.truetype(path, px)
        except Exception:
            _cache[key] = ImageFont.load_default()
    return _cache[key]


def rgb(c):
    if c is None:
        return None
    try:
        return tuple(c)
    except Exception:
        return None


def emu2px(v):
    return int(v / EMU_PER_INCH * 96 * SCALE)


def render(pptx_path, out_path):
    prs = Presentation(pptx_path)
    W = emu2px(prs.slide_width)
    H = emu2px(prs.slide_height)

    for idx, slide in enumerate(prs.slides, 1):
        img = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(img)

        for shp in slide.shapes:
            left, top = emu2px(shp.left), emu2px(shp.top)
            w, h = emu2px(shp.width), emu2px(shp.height)

            # 填充与描边
            fill = None
            line = None
            try:
                if shp.fill.type is not None and shp.fill.type == 1:
                    fill = rgb(shp.fill.fore_color.rgb)
            except Exception:
                pass
            try:
                if shp.line.color and shp.line.color.type is not None:
                    line = rgb(shp.line.color.rgb)
            except Exception:
                pass

            is_round = 'ROUNDED' in str(shp.shape_type)
            if fill or line:
                if is_round:
                    r = min(w, h) // 8
                    d.rounded_rectangle([left, top, left + w, top + h],
                                        radius=max(r, 3),
                                        fill=fill, outline=line, width=2 if line else 0)
                else:
                    d.rectangle([left, top, left + w, top + h],
                                fill=fill, outline=line, width=2 if line else 0)

            # 文本
            if not shp.has_text_frame:
                continue
            tf = shp.text_frame
            y = top
            for para in tf.paragraphs:
                if not para.runs:
                    continue
                segs = []
                max_size = 0
                for r in para.runs:
                    sz = r.font.size.pt if r.font.size else 18
                    max_size = max(max_size, sz)
                    col = rgb(r.font.color.rgb) if r.font.color and r.font.color.type is not None else (0x1A, 0x22, 0x30)
                    segs.append((r.text, sz, bool(r.font.bold), col))

                px_size = int(max_size * 96 / 72 * SCALE)
                is_bold = any(s[2] for s in segs)
                font = get_font(BOLD_PATH if is_bold else REG_PATH, px_size)

                align = str(para.alignment) if para.alignment else 'LEFT'
                line_h = int(px_size * 1.45)

                full = "".join(s[0] for s in segs)
                color = segs[0][3]

                # 逐字符自动换行（中文按字换行，兼容英文单词）
                for hard_chunk in full.split("\n"):
                    if not hard_chunk:
                        y += line_h
                        continue
                    cur = ""
                    for ch in hard_chunk:
                        trial = cur + ch
                        if d.textlength(trial, font=font) > w:
                            if cur:
                                tw = d.textlength(cur, font=font)
                                if "CENTER" in align:
                                    x = left + (w - tw) / 2
                                elif "RIGHT" in align:
                                    x = left + w - tw
                                else:
                                    x = left
                                d.text((x, y), cur, font=font, fill=color)
                                y += line_h
                            cur = ch
                        else:
                            cur = trial
                    if cur:
                        tw = d.textlength(cur, font=font)
                        if "CENTER" in align:
                            x = left + (w - tw) / 2
                        elif "RIGHT" in align:
                            x = left + w - tw
                        else:
                            x = left
                        d.text((x, y), cur, font=font, fill=color)
                        y += line_h

        img.save(out_path.replace("*", str(idx)))
        print(f"rendered page {idx} -> {out_path.replace('*', str(idx))}")


if __name__ == "__main__":
    render(PPTX, OUT_PREFIX)
