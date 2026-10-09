from pathlib import Path
import csv
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]

summary = root / "results" / "summary"
fig_dir = summary / "figures"
fig_dir.mkdir(exist_ok=True)


# Resistance vs height

hP=[]
RP=[]

hT=[]
RT=[]

with open(summary/"F1_height_effect.csv") as f:
    reader=csv.DictReader(f)

    for row in reader:
        h=int(row["height_nm"])
        R=float(row["R_eff"])

        if row["direction"]=="parallel":
            hP.append(h)
            RP.append(R)
        else:
            hT.append(h)
            RT.append(R)


plt.figure(figsize=(6,4))

plt.plot(hP, RP, "o-", label="Parallel")
plt.plot(hT, RT, "s-", label="Perpendicular")

plt.xlabel("Film height (nm)")
plt.ylabel("Effective resistance")

plt.yscale("log")
plt.legend()
plt.tight_layout()

plt.savefig(
    fig_dir/"F1_resistance_vs_height.png",
    dpi=300
)

plt.close()


# anisotropy

h=[]
ratio=[]

with open(summary/"F1_anisotropy.csv") as f:
    reader=csv.DictReader(f)

    for row in reader:
        h.append(int(row["height_nm"]))
        ratio.append(float(row["R_ratio_RT_RP"]))


plt.figure(figsize=(6,4))

plt.plot(h, ratio, "o-")

plt.xlabel("Film height (nm)")
plt.ylabel("Resistance ratio $R_T/R_P$")

plt.tight_layout()

plt.savefig(
    fig_dir/"F1_anisotropy_ratio.png",
    dpi=300
)

plt.close()


print("F1 figures generated")
