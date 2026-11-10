# -*- coding: utf-8 -*-
"""
简洁同款样张生成器（复刻《纳米管道初步结果.pptx》的版式类型）
模板：同款空白模板（Office 默认主题：白底、Calibri、标题 44pt、正文 28pt 圆点列表）
当前仅生成第 2 页样张；确认后再扩展为全量 10 页。
"""
from pptx import Presentation
from pptx.util import Pt
import copy, os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = "/home/dell/yuanyuanxu/SIM240/.workbuddy/tmp/SIM240_template.pptx"
OUT = os.path.join(HERE, "样张_简洁同款_第2页.pptx")


def add_bullet_slide(prs, title, bullets):
    """bullets: list of (bold_lead, normal_text)；bold_lead 为空则整行普通"""
    layout = prs.slide_layouts[1]  # Title and Content
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.clear()
    for i, (lead, rest) in enumerate(bullets):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if lead:
            r1 = para.add_run()
            r1.text = lead
            r1.font.bold = True
            r2 = para.add_run()
            r2.text = rest
        else:
            para.add_run().text = rest
    return slide


def build_sample():
    prs = Presentation(TEMPLATE)
    assert len(prs.slides) == 0

    add_bullet_slide(prs, "今天只说四个答案", [
        ("公式错多少：", "Jain 型闭合（行业在用）全面高估——沿槽最多 +154%、跨槽最多 +49%，槽越深错越多"),
        ("该控制什么：", "想让液体跨槽流快，唯一有效旋钮是减小间隙 h；加深沟槽几乎无效（深槽 82% 容积是死空间）"),
        ("怎么修：", "两个修正因子，在未参与拟合的 d=75 nm 考场 6/6 通过——沿槽 +66~99% → ±17%，跨槽 +34~41% → ±4%"),
        ("顺带两证：", "K 是合格张量（斜槽旋转律 6/6 命中）；K 与胶黏度无关（15 倍稠胶仅差 0.0006%）"),
    ])

    prs.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    build_sample()
