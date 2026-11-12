#set document(title: "SIM240：目前得出的公式与结论", author: "")
#set page(paper: "a4", margin: (top: 20mm, bottom: 19mm, left: 22mm, right: 22mm), numbering: "1", number-align: center,
 header: align(right)[#text(size: 8pt, fill: rgb("6c7680"))[SIM240 · 公式与结论说明 · 2026-10-29]])
#set text(font: ("Libertinus Serif", "Noto Serif CJK SC"), size: 12pt, lang: "zh")
#set par(justify: true, leading: 0.6em, spacing: 0.72em)
#set heading(numbering: none)
#show heading.where(level: 1): it => block(sticky: true, above: 0pt, below: 12pt)[#text(size: 20pt, weight: "bold", fill: rgb("153e57"))[#it.body]]
#show heading.where(level: 2): it => block(sticky: true, above: 12pt, below: 7pt)[#text(size: 14pt, weight: "bold", fill: rgb("153e57"))[#it.body]]
#show heading.where(level: 3): it => block(sticky: true, above: 11pt, below: 6pt)[#text(size: 12pt, weight: "bold")[#it.body]]
#set table(inset: 6pt, stroke: (x: none, y: 0.4pt + rgb("bac5cb")))
#show table: it => block(above: 5pt, below: 8pt)[#text(size: 10.5pt)[#it]]
#show raw: set text(font: ("DejaVu Sans Mono", "Noto Sans CJK SC"), size: 8pt)
#show link: it => text(fill: rgb("244c6e"), it)
#let horizontalrule = v(4pt)
$body$
