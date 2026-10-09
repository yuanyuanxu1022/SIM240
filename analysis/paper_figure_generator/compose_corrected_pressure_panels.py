#!/usr/bin/env python3
"""Compose the two ParaView-rendered, direction-aligned pressure panels."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for root in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation2"):
        path = Path(root) / name
        if path.exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def compose(parallel: Path, perpendicular: Path, output: Path, pdf: Path | None = None) -> None:
    left = Image.open(parallel).convert("RGB")
    right = Image.open(perpendicular).convert("RGB")
    if left.size != right.size:
        raise ValueError(f"panel sizes differ: Parallel={left.size}, Perpendicular={right.size}")

    panel_width = left.width
    left_panel = left.copy()
    right_panel = right.copy()
    gap = 24
    top = 42
    canvas = Image.new(
        "RGB",
        (panel_width + gap + panel_width, left.height + top),
        "white",
    )
    canvas.paste(left_panel, (0, top))
    right_x = panel_width + gap
    canvas.paste(right_panel, (right_x, top))

    draw = ImageDraw.Draw(canvas)
    draw.text(
        (right_x + 28, top + 88),
        "(b) Perpendicular",
        fill="black",
        font=_font(46, bold=True),
        stroke_width=1,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, dpi=(300, 300))
    if pdf is not None:
        pdf.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(pdf, resolution=300.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parallel", type=Path, required=True)
    parser.add_argument("--perpendicular", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pdf", type=Path)
    args = parser.parse_args()
    compose(args.parallel, args.perpendicular, args.output, args.pdf)


if __name__ == "__main__":
    main()
