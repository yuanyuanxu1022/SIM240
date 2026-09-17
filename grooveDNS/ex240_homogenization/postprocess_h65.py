#!/usr/bin/env python3
from pathlib import Path
import csv
import re
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
RUNS={
 "X":ROOT/"output/ex240_h65_dx5_a1e5_x_20260907",
 "Y":ROOT/"output/ex240_h65_dx5_a1e5_y_20260907",
}

def result(path):
    d={}
    for line in (path/"result.txt").read_text().splitlines():
        if "=" in line:
            k,v=line.split("=",1); d[k]=v
    return d

def data(path):
    return np.genfromtxt(path/"diagnostics.csv",delimiter=",",names=True)

def vec(s): return [float(x) for x in s.split(",")]

R={k:result(v) for k,v in RUNS.items()}; D={k:data(v) for k,v in RUNS.items()}
rows=[]
for case in ("X","Y"):
    r=R[case]; J=vec(r["J_m2_s"]); K=vec(r["K_m3"]); B=vec(r["B_m2"]); Q=vec(r["Q_sections_m3_s"])
    rows.append({
      "case":case,"run_id":r["run_id"],"dx_nm":5,"h_nm":65,"acceleration_m_s2":1e5,
      "dt_s":float(r["dt_s"]),"tau":float(r["tau"]),"convergence_step":int(r["steps_completed"]),
      "physical_time_s":int(r["steps_completed"])*float(r["dt_s"]),"fluid_nodes":int(r["fluid_nodes"]),
      "fluid_volume_m3":float(r["fluid_volume_m3"]),"max_mass_abs_relative":float(r["max_mass_abs_relative"]),
      "max_density_deviation":float(r["max_density_deviation"]),"max_speed_m_s":float(r["max_speed_m_s"]),
      "Re_max_Href":float(r["Re_max_Href"]),"Mach_max":float(r["Mach_max"]),
      "mean_ux_m_s":vec(r["mean_u_m_s"])[0],"mean_uy_m_s":vec(r["mean_u_m_s"])[1],
      "Jx_m2_s":J[0],"Jy_m2_s":J[1],"Kx_m3":K[0],"Ky_m3":K[1],"Bx_m2":B[0],"By_m2":B[1],
      "Q_section1_m3_s":Q[0],"Q_section2_m3_s":Q[1],"section_relative_difference":float(r["section_relative_difference"]),
      "window_main_rel_std":float(r["window_main_rel_std"]),"window_main_rel_span":float(r["window_main_rel_span"]),
      "window_cross_abs_max_m2_s":float(r["window_cross_abs_max"]),"PASS":r["PASS"]})
with (ROOT/"homogenization_h65_summary.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

figdir=ROOT/"figures";figdir.mkdir(exist_ok=True)
plt.rcParams.update({"font.size":9,"figure.dpi":160})

fig,ax=plt.subplots(figsize=(6.4,4.2))
for c,color in (("X","#2468b4"),("Y","#d1495b")):
    d=D[c]; main=d["Jx_m2_s"] if c=="X" else d["Jy_m2_s"]
    ax.plot(d["time_s"]*1e9,main*1e12,label=f"{c} drive: J{c.lower()}",color=color,lw=1.5)
ax.set(xlabel="Physical time (ns)",ylabel=r"Main response $J$ ($10^{-12}$ m$^2$/s)")
ax.grid(alpha=.25);ax.legend();fig.tight_layout()
for ext in ("png","pdf"):fig.savefig(figdir/f"h65_J_convergence.{ext}")
plt.close(fig)

fig,axs=plt.subplots(2,1,figsize=(6.4,5.8),sharex=True)
for c,color in (("X","#2468b4"),("Y","#d1495b")):
    d=D[c];axs[0].plot(d["time_s"]*1e9,d["mass_signed_relative"],label=c,color=color,lw=1.2)
    axs[1].plot(d["time_s"]*1e9,d["max_density_deviation"],label=c,color=color,lw=1.2)
axs[0].set_ylabel("Fluid mass relative drift");axs[1].set_ylabel(r"max $|\rho/\rho_0-1|$");axs[1].set_xlabel("Physical time (ns)")
for ax in axs:ax.grid(alpha=.25);ax.legend()
fig.tight_layout()
for ext in ("png","pdf"):fig.savefig(figdir/f"h65_mass_density_history.{ext}")
plt.close(fig)

K=np.array([[rows[0]["Kx_m3"],rows[1]["Kx_m3"]],[rows[0]["Ky_m3"],rows[1]["Ky_m3"]]])*1e27
fig,ax=plt.subplots(figsize=(5.2,4.3));im=ax.imshow(K,cmap="coolwarm")
ax.set_xticks([0,1],["x drive","y drive"]);ax.set_yticks([0,1],[r"$J_x$",r"$J_y$"])
for i in range(2):
    for j in range(2):ax.text(j,i,f"{K[i,j]:.4g}",ha="center",va="center",color="white" if abs(K[i,j])>.5*np.max(abs(K)) else "black")
ax.set_title(r"$K_{ij}$ at h=65 nm, dx=5 nm (nm$^3$)");fig.colorbar(im,ax=ax,label=r"$K$ (nm$^3$)");fig.tight_layout()
for ext in ("png","pdf"):fig.savefig(figdir/f"h65_K_response_matrix.{ext}")
plt.close(fig)

print("wrote summary and figures")
