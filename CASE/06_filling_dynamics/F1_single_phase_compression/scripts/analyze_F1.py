from pathlib import Path
import csv


root = Path(__file__).resolve().parents[1]

summary = root / "results" / "summary"

input_file = summary / "F1_resistance_matrix.csv"


data = []

with open(input_file, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["height_nm"] = int(row["height_nm"])
        row["R_eff_Pa_s_m3"] = float(row["R_eff_Pa_s_m3"])
        row["Keff_m3"] = float(row["Keff_m3"])
        data.append(row)


# -----------------------------
# anisotropy
# -----------------------------

anisotropy = []

for h in sorted(set(r["height_nm"] for r in data)):

    P = [
        r for r in data
        if r["height_nm"] == h
        and r["direction"] == "parallel"
    ][0]

    T = [
        r for r in data
        if r["height_nm"] == h
        and r["direction"] == "perpendicular"
    ][0]

    anisotropy.append({
        "height_nm": h,
        "R_parallel": P["R_eff_Pa_s_m3"],
        "R_transverse": T["R_eff_Pa_s_m3"],
        "R_ratio_RT_RP":
            T["R_eff_Pa_s_m3"] /
            P["R_eff_Pa_s_m3"]
    })


with open(summary/"F1_anisotropy.csv","w",newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=anisotropy[0].keys()
    )
    writer.writeheader()
    writer.writerows(anisotropy)


# -----------------------------
# height effect
# -----------------------------

height_effect=[]

for r in sorted(data,key=lambda x:x["height_nm"]):
    height_effect.append({
        "height_nm":r["height_nm"],
        "direction":r["direction"],
        "R_eff":r["R_eff_Pa_s_m3"],
        "Keff":r["Keff_m3"]
    })


with open(summary/"F1_height_effect.csv","w",newline="") as f:
    writer=csv.DictWriter(
        f,
        fieldnames=height_effect[0].keys()
    )
    writer.writeheader()
    writer.writerows(height_effect)



