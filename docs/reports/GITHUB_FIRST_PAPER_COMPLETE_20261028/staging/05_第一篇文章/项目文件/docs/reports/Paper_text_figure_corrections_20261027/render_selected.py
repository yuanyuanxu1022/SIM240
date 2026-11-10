#!/usr/bin/env python3
"""Re-export only the two approved figures; compare old/new plotted values.

This runs local plotting code, never a simulation or a fit. The Fig7/Fig8
script is stopped before its Fig8 block. savefig is redirected into staging;
no production figure is replaced by this script.
"""
import ast
import contextlib
import hashlib
import io
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import PIL

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE = HERE / "staged"
STAGE.mkdir(exist_ok=True)
ALLOWED = {"Fig4_K_and_anisotropy", "Fig7_error_vs_gap"}
SAVEFIG = Figure.savefig


def figure_values(fig):
    return [dict(
        xlim=list(ax.get_xlim()), ylim=list(ax.get_ylim()),
        xscale=ax.get_xscale(), yscale=ax.get_yscale(),
        xticks=ax.get_xticks().tolist(), yticks=ax.get_yticks().tolist(),
        lines=[dict(x=np.asarray(line.get_xdata()).tolist(),
                    y=np.asarray(line.get_ydata()).tolist(),
                    color=line.get_color(), marker=line.get_marker(),
                    linestyle=line.get_linestyle()) for line in ax.lines],
    ) for ax in fig.axes]


def run_script(relative, old):
    source = ((HERE / "before" / relative) if old else (ROOT / relative)).read_text()
    tree = ast.parse(source, filename=relative)
    if relative.endswith("make_fig7_fig8.py"):
        # grid() begins the Fig8 block. Execute the complete preceding Fig7
        # block without rewriting the existing production plotting script.
        stop = next(node.lineno for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "grid")
        tree.body = [node for node in tree.body if node.lineno < stop]
    figures = {}

    def save_selected(fig, filename, *args, **kwargs):
        filename = Path(filename)
        if filename.stem not in ALLOWED or filename.suffix not in {".png", ".pdf", ".svg"}:
            raise RuntimeError(f"Unapproved export: {filename}")
        figures[filename.stem] = figure_values(fig)
        if not old:
            SAVEFIG(fig, STAGE / filename.name, *args, **kwargs)

    Figure.savefig = save_selected
    stream = io.StringIO()
    try:
        matplotlib.rcdefaults()
        with contextlib.redirect_stdout(stream):
            exec(compile(tree, relative, "exec"),
                 {"__name__": "__main__", "__file__": str(ROOT / relative)})
    finally:
        Figure.savefig = SAVEFIG
        plt.close("all")
    return figures, stream.getvalue()


def main():
    old, new, logs = {}, {}, []
    for relative in ("figures/paper/make_fig4.py", "figures/paper/make_fig7_fig8.py"):
        values, log = run_script(relative, True)
        old.update(values)
        logs.append(f"old-source, exports suppressed: {relative}\n{log}")
        values, log = run_script(relative, False)
        new.update(values)
        logs.append(f"new-source, exports redirected to staging: {relative}\n{log}")
    equal = old == new
    result = dict(
        scope="selected-figure data/style regression and local export only",
        plotted_values_axes_scales_and_line_styles_unchanged=equal,
        compared_figures=sorted(new),
        figure8_executed=False,
        environment=dict(python=platform.python_version(), matplotlib=matplotlib.__version__,
                         numpy=np.__version__, pillow=PIL.__version__),
        plotted_values_sha256=hashlib.sha256(
            json.dumps(new, sort_keys=True).encode()).hexdigest(),
        exports={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(STAGE.iterdir()) if p.suffix in {".png", ".pdf", ".svg"}},
    )
    (HERE / "render.log").write_text("\n".join(logs))
    (HERE / "render_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    if not equal or len(result["exports"]) != 6:
        raise RuntimeError("Figure data changed or expected six exports are missing")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
