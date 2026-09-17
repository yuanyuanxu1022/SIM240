#!/usr/bin/env python3
"""Post-process the four STEP 6-C formal runs without altering raw results."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
FIG = ROOT / "figures"
GAPS = (75, 65)
MODES = ("x", "y")


def value(text: str):
    if "," in text:
        return tuple(float(v) for v in text.split(","))
    if text in {"true", "false"}:
        return text == "true"
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def load(gap: int, mode: str) -> dict:
    run_id=f"sim_ec1xt240_right_angle_h{gap}_dx5_a1e5_{mode}_20260909"
    path=OUT/run_id/"result.txt"
    result={"result_path":str(path)}
    for line in path.read_text().splitlines():
        if "=" in line:
            key,item=line.split("=",1); result[key]=value(item)
    if result["run_id"]!=run_id or not result["PASS"]:
        raise RuntimeError(f"unexpected or failed run: {path}")
    return result


def history(result: dict) -> list[dict[str,float]]:
    path=Path(result["result_path"]).with_name("diagnostics.csv")
    with path.open(newline="") as handle:
        return [{k:float(v) for k,v in row.items()} for row in csv.DictReader(handle)]


def save(fig,stem: str):
    fig.savefig(FIG/f"{stem}.png",dpi=300,bbox_inches="tight")
    fig.savefig(FIG/f"{stem}.pdf",bbox_inches="tight")
    plt.close(fig)


def main():
    FIG.mkdir(exist_ok=True)
    runs={(gap,mode):load(gap,mode) for gap in GAPS for mode in MODES}
    plan=[[((60 <= (ix+0.5)*5 < 180) or (60 <= (iy+0.5)*5 < 180))
           for iy in range(48)] for ix in range(48)]
    x_seam_mismatch=sum(plan[0][iy] != plan[-1][iy] for iy in range(48))
    y_seam_mismatch=sum(plan[ix][0] != plan[ix][-1] for ix in range(48))
    groove_plan_nodes=sum(sum(row) for row in plan)
    (ROOT/"geometry_audit.txt").write_text(
        "geometry=orthogonal_cross_junction\n"
        f"core_plan_nodes={48*48}\n"
        f"groove_plan_nodes={groove_plan_nodes}\n"
        f"mesa_plan_nodes={48*48-groove_plan_nodes}\n"
        f"x_periodic_seam_mismatch={x_seam_mismatch}\n"
        f"y_periodic_seam_mismatch={y_seam_mismatch}\n"
        f"PASS={str(groove_plan_nodes==1728 and x_seam_mismatch==0 and y_seam_mismatch==0).lower()}\n"
    )
    columns=[
        "run_id","geometry","gap_nm","mode","steps_completed","dx_m","dt_s","tau",
        "applied_pressure_gradient_Pa_m","pressure_gradient_fit_Pa_m","pressure_min_Pa",
        "pressure_max_Pa","pressure_disturbance_Pa","fluid_nodes","groove_nodes",
        "fluid_volume_m3","nominal_volume_m3","max_mass_abs_relative",
        "max_density_deviation","max_speed_m_s","groove_max_speed_m_s","Mach_max",
        "mean_ux_m_s","mean_uy_m_s","groove_mean_ux_m_s","groove_mean_uy_m_s",
        "Jx_m2_s","Jy_m2_s","K_main_m3","flow_rate_mean_m3_s","R_J_Pa_s_per_m3",
        "Q_section1_m3_s","Q_section2_m3_s","section_relative_difference",
        "finite","material_unchanged","PASS",
    ]
    with (ROOT/"step6C_right_angle_summary.csv").open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=columns); writer.writeheader()
        for gap in GAPS:
            for mode in MODES:
                r=runs[(gap,mode)]
                writer.writerow({
                    "run_id":r["run_id"],"geometry":r["geometry"],"gap_nm":r["gap_nm"],
                    "mode":mode,"steps_completed":r["steps_completed"],"dx_m":r["dx_m"],
                    "dt_s":r["dt_s"],"tau":r["tau"],
                    "applied_pressure_gradient_Pa_m":r["applied_pressure_gradient_Pa_m"],
                    "pressure_gradient_fit_Pa_m":r["pressure_gradient_fit_Pa_m"],
                    "pressure_min_Pa":r["pressure_range_Pa"][0],
                    "pressure_max_Pa":r["pressure_range_Pa"][1],
                    "pressure_disturbance_Pa":r["pressure_disturbance_Pa"],
                    "fluid_nodes":r["fluid_nodes"],"groove_nodes":r["groove_nodes"],
                    "fluid_volume_m3":r["fluid_volume_m3"],"nominal_volume_m3":r["nominal_volume_m3"],
                    "max_mass_abs_relative":r["max_mass_abs_relative"],
                    "max_density_deviation":r["max_density_deviation"],
                    "max_speed_m_s":r["max_speed_m_s"],"groove_max_speed_m_s":r["groove_max_speed_m_s"],
                    "Mach_max":r["Mach_max"],"mean_ux_m_s":r["mean_u_m_s"][0],
                    "mean_uy_m_s":r["mean_u_m_s"][1],"groove_mean_ux_m_s":r["groove_mean_u_m_s"][0],
                    "groove_mean_uy_m_s":r["groove_mean_u_m_s"][1],"Jx_m2_s":r["J_m2_s"][0],
                    "Jy_m2_s":r["J_m2_s"][1],"K_main_m3":r["K_main_m3"],
                    "flow_rate_mean_m3_s":r["flow_rate_mean_m3_s"],"R_J_Pa_s_per_m3":r["R_J_Pa_s_per_m3"],
                    "Q_section1_m3_s":r["Q_sections_m3_s"][0],"Q_section2_m3_s":r["Q_sections_m3_s"][1],
                    "section_relative_difference":r["section_relative_difference"],
                    "finite":r["finite"],"material_unchanged":r["material_unchanged"],"PASS":r["PASS"],
                })

    plt.rcParams.update({"font.size":9,"axes.grid":True,"grid.alpha":0.25})
    fig,axes=plt.subplots(2,1,figsize=(6.5,6.2))
    for gap in GAPS:
        for mode,ls in (("x","-"),("y","--")):
            rows=history(runs[(gap,mode)]); main="Jx_m2_s" if mode=="x" else "Jy_m2_s"
            label=f"h={gap} nm, {mode.upper()}"
            axes[0].plot([r["time_s"]*1e9 for r in rows],[r[main]*1e12 for r in rows],ls=ls,label=label)
            axes[1].plot([r["time_s"]*1e9 for r in rows],[r["mass_abs_relative"] for r in rows],ls=ls,label=label)
    axes[0].set(ylabel=r"Main $J$ ($10^{-12}$ m$^2$/s)"); axes[0].legend(ncol=2)
    axes[1].set(xlabel="Physical time (ns)",ylabel="Absolute relative mass drift")
    save(fig,"convergence_and_mass")

    fig,axes=plt.subplots(1,3,figsize=(10.2,3.4))
    for mode,marker in (("x","o"),("y","s")):
        axes[0].plot(GAPS,[runs[(g,mode)]["flow_rate_mean_m3_s"]*1e18 for g in GAPS],marker=marker,label=mode.upper())
        axes[1].plot(GAPS,[runs[(g,mode)]["R_J_Pa_s_per_m3"]*1e-18 for g in GAPS],marker=marker,label=mode.upper())
        axes[2].plot(GAPS,[runs[(g,mode)]["pressure_disturbance_Pa"] for g in GAPS],marker=marker,label=mode.upper())
    axes[0].set(xlabel="Gap h (nm)",ylabel=r"Flow rate ($10^{-18}$ m$^3$/s)")
    axes[1].set(xlabel="Gap h (nm)",ylabel=r"Resistance ($10^{18}$ Pa s m$^{-3}$)")
    axes[2].set(xlabel="Gap h (nm)",ylabel="Pressure disturbance (Pa)")
    for ax in axes: ax.legend()
    save(fig,"flow_resistance_pressure")


if __name__=="__main__":
    main()
