# -*- coding: utf-8 -*-
"""Crude raster preview of the generated deck (layout sanity check only).

Draws shapes/text/images with PIL at 96 dpi so the author can eyeball spacing,
overflow and overlap without PowerPoint. Not pixel-accurate: gradients, shadows
and exact line metrics are approximated.
"""
import io, os
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Emu

SRC = "PAPER1_导师汇报_20261105.pptx"
OUTDIR = "preview"
DPI = 96
W = int(13.333 * DPI); H = int(7.5 * DPI)
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

os.makedirs(OUTDIR, exist_ok=True)

def px(v): return int(round(v / 914400 * DPI))

def font_for(size_pt, bold):
    p = FONT_BOLD if bold else FONT_PATH
    # size in points -> pixels at DPI
    return ImageFont.truetype(p, max(6, int(round(size_pt * DPI / 72))), index=0)

def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        trial = cur + ch
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = ch
    lines.append(cur)
    return lines

def rgb(shape_fill):
    try:
        c = shape_fill.fore_color.rgb
        return "#" + str(c)
    except Exception:
        return None

prs = Presentation(SRC)
for idx, slide in enumerate(prs.slides, 1):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    for sh in slide.shapes:
        x, y = px(sh.left), px(sh.top)
        w, h = px(sh.width), px(sh.height)
        if sh.shape_type == 13:  # picture
            try:
                pic = Image.open(io.BytesIO(sh.image.blob)).convert("RGB")
                pic = pic.resize((max(1, w), max(1, h)))
                img.paste(pic, (x, y))
            except Exception:
                d.rectangle([x, y, x + w, y + h], outline="gray")
            continue
        if sh.has_table:
            tbl = sh.table
            cy = y
            for r, row in enumerate(tbl.rows):
                rh = px(row.height)
                cx = x
                for ci, cell in enumerate(row.cells):
                    cw = px(tbl.columns[ci].width)
                    fill = rgb(cell.fill) or "white"
                    d.rectangle([cx, cy, cx + cw, cy + rh], fill=fill,
                                outline="#E5E7EB")
                    txt = cell.text
                    if txt:
                        sizes = [run.font.size.pt for p in cell.text_frame.paragraphs
                                 for run in p.runs if run.font.size]
                        sp = max(sizes) if sizes else 11
                        bold = any(run.font.bold for p in cell.text_frame.paragraphs
                                   for run in p.runs)
                        col = "#1A2230"
                        for p in cell.text_frame.paragraphs:
                            for run in p.runs:
                                try: col = "#" + str(run.font.color.rgb)
                                except Exception: pass
                        fnt = font_for(sp, bold)
                        lines = wrap(d, txt, fnt, cw - 10)
                        th = len(lines) * sp * DPI / 72 * 1.15
                        ty = cy + max(2, (rh - th) / 2)
                        for ln in lines:
                            tw = d.textlength(ln, font=fnt)
                            d.text((cx + (cw - tw) / 2, ty), ln, font=fnt, fill=col)
                            ty += sp * DPI / 72 * 1.15
                    cx += cw
                cy += rh
            continue
        # autoshape / textbox
        if sh.shape_type == 1:
            fill = rgb(sh.fill) or None
            try:
                line = "#" + str(sh.line.color.rgb) if sh.line.width else None
            except Exception:
                line = None
            if fill or line:
                d.rectangle([x, y, x + w, y + h], fill=fill, outline=line)
        if not sh.has_text_frame:
            continue
        tf = sh.text_frame
        if not tf.text.strip():
            continue
        ml = px(tf.margin_left); mr = px(tf.margin_right)
        mt = px(tf.margin_top); mb = px(tf.margin_bottom)
        avail_w = max(10, w - ml - mr)
        blocks = []
        for p in tf.paragraphs:
            runs = [(r.text, (r.font.size.pt if r.font.size else 12),
                     bool(r.font.bold),
                     ("#" + str(r.font.color.rgb)) if r.font.color and r.font.color.rgb else "#1A2230")
                    for r in p.runs]
            if not runs:
                continue
            ls = p.line_spacing or 1.2
            sz = max(r[1] for r in runs)
            blocks.append((runs, sz, ls, p.alignment))
        total_h = sum(sz * ls * DPI / 72 * 1.02 for (_, sz, ls, _) in blocks)
        anchor = tf.vertical_anchor
        ty = y + mt
        if anchor is not None and int(anchor) == 3:  # middle
            ty = y + mt + max(0, (h - mt - mb - total_h) / 2)
        for (runs, sz, ls, al) in blocks:
            text = "".join(r[0] for r in runs)
            fnt = font_for(sz, any(r[2] for r in runs))
            col = runs[0][3]
            lines = wrap(d, text, fnt, avail_w)
            for ln in lines:
                tw = d.textlength(ln, font=fnt)
                tx = x + ml
                if al is not None and int(al) == 2:      # center
                    tx = x + ml + (avail_w - tw) / 2
                elif al is not None and int(al) == 3:    # right
                    tx = x + w - mr - tw
                d.text((tx, ty), ln, font=fnt, fill=col)
                ty += sz * ls * DPI / 72
    img.save(os.path.join(OUTDIR, "s%02d.png" % idx))

# contact sheets: 4 per sheet, 2x2
files = sorted(os.listdir(OUTDIR))
files = [f for f in files if f.startswith("s") and f.endswith(".png")]
tw, th = W // 2, H // 2
for k in range(0, len(files), 4):
    sheet = Image.new("RGB", (tw * 2 + 30, th * 2 + 30), "#888888")
    for j, f in enumerate(files[k:k + 4]):
        im = Image.open(os.path.join(OUTDIR, f)).resize((tw, th))
        cx = 10 + (j % 2) * (tw + 10)
        cy = 10 + (j // 2) * (th + 10)
        sheet.paste(im, (cx, cy))
    sheet.save(os.path.join(OUTDIR, "sheet_%d.png" % (k // 4 + 1)))
print("rendered", len(files), "slides")
