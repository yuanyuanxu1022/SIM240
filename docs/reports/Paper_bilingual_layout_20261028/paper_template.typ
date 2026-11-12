#set page(paper: "a4", margin: (top: 20mm, bottom: 20mm, left: 21mm, right: 21mm), numbering: "1", number-align: center,
 header: align(right)[#text(size: 8pt, fill: rgb("777777"))[SIM240 · Author review · 2026-10-28]])
#set text(font: ("Libertinus Serif", "Noto Serif CJK SC"), size: 10.5pt, lang: "$doc-lang$")
#set par(justify: true, leading: 0.6em, spacing: 0.75em)
#set heading(numbering: none)
#show heading.where(level: 1): it => block(sticky: true, above: 0pt, below: 15pt)[#text(size: 17pt, weight: "bold")[#it.body]]
#show heading.where(level: 2): it => block(sticky: true, above: 13pt, below: 7pt)[#text(size: 12pt, weight: "bold")[#it.body]]
#show heading.where(level: 3): it => block(sticky: true, above: 10pt, below: 5pt)[#text(size: 10.5pt, weight: "bold")[#it.body]]
#set table(inset: 4pt, stroke: (x: none, y: 0.4pt + rgb("b5bbc2")))
#show table: it => block(above: 5pt, below: 9pt)[#text(size: 8.8pt)[#it]]
#show raw: set text(font: ("DejaVu Sans Mono", "Noto Sans CJK SC"), size: 8.1pt)
#show link: it => text(fill: rgb("244c6e"), it)
#let horizontalrule = v(4pt)
#block(inset: (bottom: 8pt))[#text(size: 8.5pt, fill: rgb("555555"))[$review-note$]]
$body$
