# -*- coding: utf-8 -*-
"""
Fig. 1 — Device and unit cell (publication version)
(a) J-FIL process: dispense -> press & fill -> cure & demold
(b) Unit-cell cross-section: rib / groove / substrate, dimensions P, w, d, h
(c) Unit-cell top view: coordinate convention and the two driving directions
Real geometry: P = 240 nm, w = 120 nm (groove 60-180 nm), h = 75 nm, d = 100 nm
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Polygon, Arc

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "mathtext.fontset": "dejavusans",
})

C_SUB   = "#CBCBCB"
C_MOLD  = "#6E6E6E"
C_MOLD2 = "#8A8A8A"
C_LIQ   = "#9CCBE0"
C_LIQ_D = "#5B9FBF"
C_EDGE  = "#2E2E2E"
INK     = "#1A1A1A"

fig = plt.figure(figsize=(7.16, 5.9), dpi=400)

# =====================================================================
# (a) process stages
# =====================================================================
axa = fig.add_axes([0.015, 0.635, 0.97, 0.335])
axa.set_xlim(0, 30.4)
axa.set_ylim(-1.35, 6.55)
axa.axis("off")

W, SUB_T = 8.0, 0.50
N_PIL, PITCH = 3, W / 3
PW = PITCH * 0.5
D_RIB, H_GAP, BODY = 1.15, 0.62, 0.85


def meniscus(ax, xl, xr, y0, sag, n=24, color=C_LIQ_D):
    """gently curved liquid surface sitting at y0, sagging by `sag`"""
    xs = np.linspace(xl, xr, n)
    ys = y0 - sag * np.sin(np.pi * (xs - xl) / (xr - xl))
    ax.plot(xs, ys, color=color, lw=0.9, zorder=4)


def stage(ax, x0, kind):
    ax.add_patch(Rectangle((x0, 0), W, SUB_T, facecolor=C_SUB,
                           edgecolor=C_EDGE, lw=0.8, zorder=1))
    top = SUB_T + H_GAP + D_RIB if kind == 1 else SUB_T + 3.05

    if kind == 0:                                  # dispense: three drops
        for k in range(N_PIL):
            cx = x0 + PITCH * (k + 0.5)
            ax.add_patch(Polygon([[cx - 0.52, SUB_T], [cx - 0.34, SUB_T + 0.60],
                                  [cx - 0.10, SUB_T + 0.66], [cx + 0.10, SUB_T + 0.66],
                                  [cx + 0.34, SUB_T + 0.60], [cx + 0.52, SUB_T]],
                                 closed=True, facecolor=C_LIQ, edgecolor=C_LIQ_D,
                                 lw=0.7, zorder=3))
    elif kind == 1:                                # press: thin film + partial groove
        for k in range(N_PIL):
            ax.add_patch(Rectangle((x0 + PITCH * k, SUB_T), PW, H_GAP,
                                   facecolor=C_LIQ, edgecolor="none", zorder=2))
        for k in range(N_PIL - 1):
            gx = x0 + PITCH * k + PW
            filly = H_GAP + D_RIB * 0.55
            ax.add_patch(Rectangle((gx, SUB_T), PITCH - PW, filly,
                                   facecolor=C_LIQ, edgecolor="none", zorder=2))
            meniscus(ax, gx, gx + PITCH - PW, SUB_T + filly, 0.10)
    else:                                          # cured: groove filled
        for k in range(N_PIL):
            ax.add_patch(Rectangle((x0 + PITCH * k, SUB_T), PW, H_GAP,
                                   facecolor=C_LIQ, edgecolor="none", zorder=2))
        for k in range(N_PIL - 1):
            gx = x0 + PITCH * k + PW
            ax.add_patch(Rectangle((gx, SUB_T), PITCH - PW, H_GAP + D_RIB,
                                   facecolor=C_LIQ, edgecolor="none", zorder=2))

    for k in range(N_PIL):
        ax.add_patch(Rectangle((x0 + PITCH * k, top - D_RIB), PW, D_RIB,
                               facecolor=C_MOLD, edgecolor=C_EDGE, lw=0.7, zorder=5))
    ax.add_patch(Rectangle((x0, top), W, BODY, facecolor=C_MOLD2,
                           edgecolor=C_EDGE, lw=0.8, zorder=5))

    if kind == 1:
        for xx in (x0 + W * 0.30, x0 + W * 0.70):
            ax.annotate("", xy=(xx, top + BODY + 0.02), xytext=(xx, top + BODY + 0.78),
                        arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#B03A2E",
                                        mutation_scale=11))
        ax.text(x0 + W * 0.5, top + BODY + 0.86, "press", ha="center", va="bottom",
                fontsize=8.2, color="#B03A2E")
    if kind == 2:
        for k in range(5):
            xx = x0 + 0.75 + k * 1.62
            ax.annotate("", xy=(xx, top + BODY + 0.10), xytext=(xx, top + BODY + 0.72),
                        arrowprops=dict(arrowstyle="-|>", lw=1.0, color="#6C3FA0",
                                        mutation_scale=8))
        ax.text(x0 + W * 0.5, top + BODY + 0.80, "UV  cure", ha="center",
                va="bottom", fontsize=8.4, color="#6C3FA0", fontweight="bold")

    labels = ["(a1) dispense", "(a2) press and fill", "(a3) cure and demold"]
    ax.text(x0 + W / 2, -1.05, labels[kind], ha="center", va="center", fontsize=8.6)

for i in range(3):
    stage(axa, 1.15 + i * 9.9, i)

axa.text(-0.35, 6.30, "(a)", fontsize=11, fontweight="bold")

# =====================================================================
# (b) unit-cell cross-section
# =====================================================================
axb = fig.add_axes([0.055, 0.055, 0.415, 0.50])
P, WW, HH, DD = 240.0, 120.0, 75.0, 100.0
X0, X1 = 60.0, 180.0
axb.set_xlim(-62, 316)
axb.set_ylim(-78, 236)
axb.axis("off")

# substrate (drawn slightly wider than the cell)
axb.add_patch(Rectangle((-34, -24), P + 68, 24, facecolor=C_SUB,
                        edgecolor=C_EDGE, lw=0.9, zorder=1))
# liquid: film under ribs + column in groove
axb.add_patch(Rectangle((0, 0), X0, HH, facecolor=C_LIQ, edgecolor="none", zorder=2))
axb.add_patch(Rectangle((X1, 0), P - X1, HH, facecolor=C_LIQ, edgecolor="none", zorder=2))
axb.add_patch(Rectangle((X0, 0), WW, HH + DD, facecolor=C_LIQ, edgecolor="none", zorder=2))
# ribs
axb.add_patch(Rectangle((0, HH), X0, DD, facecolor=C_MOLD,
                        edgecolor=C_EDGE, lw=0.9, zorder=3))
axb.add_patch(Rectangle((X1, HH), P - X1, DD, facecolor=C_MOLD,
                        edgecolor=C_EDGE, lw=0.9, zorder=3))
# mold body
axb.add_patch(Rectangle((0, HH + DD), P, 30, facecolor=C_MOLD2,
                        edgecolor=C_EDGE, lw=0.9, zorder=3))

# periodic cut lines
for xx in (0, P):
    axb.plot([xx, xx], [-24, HH + DD + 30], ls=(0, (4, 2.5)), lw=1.0,
             color="#8B3A2E", zorder=6)

# ---- dimension P (top) ----
yp = HH + DD + 30 + 20
axb.annotate("", xy=(0, yp), xytext=(P, yp),
             arrowprops=dict(arrowstyle="<|-|>", lw=0.9, color=C_EDGE,
                             mutation_scale=8, shrinkA=0, shrinkB=0))
for xx in (0, P):
    axb.plot([xx, xx], [HH + DD + 30, yp + 3], lw=0.6, color=C_EDGE, zorder=5)
axb.text(P / 2, yp + 7, r"$P = 240$ nm", ha="center", va="bottom", fontsize=8.4)

# ---- dimension w (inside groove, near the top of the groove) ----
yw = HH + DD * 0.62
axb.annotate("", xy=(X0, yw), xytext=(X1, yw),
             arrowprops=dict(arrowstyle="<|-|>", lw=0.9, color="#14507A",
                             mutation_scale=8, shrinkA=0, shrinkB=0))
axb.text(P / 2, yw + 9, r"$w = 120$ nm", ha="center", va="bottom",
         fontsize=8.2, color="#14507A")

# ---- dimension h (left, inside the liquid film under the left rib) ----
xh = 30.0
axb.annotate("", xy=(xh - 6, 0), xytext=(xh - 6, HH),
             arrowprops=dict(arrowstyle="<|-|>", lw=1.0, color="#0F3D5C",
                             mutation_scale=8, shrinkA=0, shrinkB=0))
axb.text(xh - 12, HH / 2, r"$h$", ha="right", va="center", fontsize=9.2,
         color="#0F3D5C", fontweight="bold")

# ---- dimension d (right rib height = groove depth), white on dark ----
xd2 = P - 30.0
axb.annotate("", xy=(xd2, HH), xytext=(xd2, HH + DD),
             arrowprops=dict(arrowstyle="<|-|>", lw=1.0, color="white",
                             mutation_scale=8, shrinkA=0, shrinkB=0))
axb.text(xd2 - 6, HH + DD / 2, r"$d$", ha="right", va="center", fontsize=9.2,
         color="white", fontweight="bold")

# ---- labels ----
axb.text(P / 2, -12, "substrate", ha="center", va="center", fontsize=7.8,
         color="#2E2E2E")
axb.text(P / 2, HH + DD + 15, "mold", ha="center", va="center", fontsize=7.8,
         color="#F2F2F2")
axb.text(P / 2, 34, "resist", ha="center", va="center", fontsize=8.0,
         color="#0F3D5C", style="italic")
axb.text(X0 - 30, HH + DD / 2, "rib", ha="center", va="center", fontsize=7.4,
         color="#F2F2F2", rotation=90)

# periodicity note (below substrate, clear of everything else)
axb.text(P / 2, -44, r"periodic in $x$", ha="center", va="center",
         fontsize=7.6, color="#8B3A2E")
axb.text(P / 2, -62, r"$y$ is out of the page", ha="center", va="center",
         fontsize=7.4, color="#5A5A5A")

axb.text(-56, 220, "(b)", fontsize=11, fontweight="bold")

# =====================================================================
# (c) unit-cell top view
# =====================================================================
axc = fig.add_axes([0.545, 0.055, 0.42, 0.50])
axc.set_xlim(-72, 330)
axc.set_ylim(-108, 268)
axc.set_aspect("equal")
axc.axis("off")

axc.add_patch(Rectangle((0, 0), P, P, facecolor="#E9E9E9",
                        edgecolor=C_EDGE, lw=0.9, zorder=1))
axc.add_patch(Rectangle((X0, 0), WW, P, facecolor=C_LIQ,
                        edgecolor=C_LIQ_D, lw=0.8, zorder=2))
for xx in (0, P):
    axc.plot([xx, xx], [0, P], ls=(0, (4, 2.5)), lw=1.0, color="#8B3A2E", zorder=4)
for yy in (0, P):
    axc.plot([0, P], [yy, yy], ls=(0, (4, 2.5)), lw=1.0, color="#8B3A2E", zorder=4)

# axes
axc.annotate("", xy=(P + 48, 0), xytext=(-4, 0),
             arrowprops=dict(arrowstyle="-|>", lw=1.1, color=C_EDGE,
                             mutation_scale=10, shrinkA=0, shrinkB=0))
axc.annotate("", xy=(0, P + 44), xytext=(0, -4),
             arrowprops=dict(arrowstyle="-|>", lw=1.1, color=C_EDGE,
                             mutation_scale=10, shrinkA=0, shrinkB=0))
axc.text(P + 52, -14, r"$x$", fontsize=10, color=INK)
axc.text(-16, P + 46, r"$y$", fontsize=10, color=INK)

# K_parallel : along groove (y)
axc.annotate("", xy=(P / 2, P * 0.74), xytext=(P / 2, P * 0.30),
             arrowprops=dict(arrowstyle="-|>", lw=2.0, color="#14507A",
                             mutation_scale=13, shrinkA=0, shrinkB=0))
axc.text(P / 2, P * 0.79, r"$K_\parallel$", ha="center", va="bottom",
         fontsize=10, color="#14507A")
axc.text(P / 2, P * 0.25, "along groove", ha="center", va="top",
         fontsize=7.6, color="#14507A")

# K_perp : across groove (x) — drawn inside the cell, lower part
yK = P * 0.17
axc.annotate("", xy=(X1, yK), xytext=(X0, yK),
             arrowprops=dict(arrowstyle="<|-|>", lw=1.8, color="#8A4B08",
                             mutation_scale=12, shrinkA=0, shrinkB=0))
axc.text(P + 16, yK, r"$K_\perp$", ha="left", va="center",
         fontsize=9.6, color="#8A4B08")
axc.text(P / 2, -72, r"$K_\parallel$: along groove     $K_\perp$: across groove",
         ha="center", va="center", fontsize=7.6, color="#4A4A4A")

axc.text(-60, 252, "(c)", fontsize=11, fontweight="bold")

# =====================================================================
out = "/home/dell/yuanyuanxu/SIM240/figures/paper/Fig1_device_and_unitcell.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.05)
fig.savefig(out.replace(".png", ".pdf"), facecolor="white",
            bbox_inches="tight", pad_inches=0.05)
fig.savefig(out.replace(".png", ".svg"), facecolor="white",
            bbox_inches="tight", pad_inches=0.05)
print("saved:", out)
