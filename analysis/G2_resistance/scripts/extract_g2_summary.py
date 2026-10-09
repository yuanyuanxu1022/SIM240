import csv
from pathlib import Path


ROOT = Path(
    "CASE/G2_EX240_grid_convergence/results/"
    "g2_grid_20260917T165045+0800/runs"
)

OUTPUT = Path(
    "analysis/G2_resistance/results/"
    "G2_resistance_summary.csv"
)


fieldnames = [
    "grid",
    "Case",
    "direction",
    "dx",
    "tau",
    "force",
    "J",
    "Keff",
    "R_eff",
    "K_LBM",
    "K_theory",
    "relative_error",
    "Mach",
    "mass_error"
]


rows = []


for dx_dir in sorted(ROOT.glob("dx*")):

    for case in [
        "EX240_parallel",
        "EX240_perpendicular",
        "Smooth75"
    ]:

        file = (
            dx_dir /
            case /
            "steady" /
            "result_summary.csv"
        )

        if not file.exists():
            print("Missing:", file)
            continue


        with open(file, newline="") as f:

            reader = csv.DictReader(f)

            for r in reader:

                r["grid"] = dx_dir.name
                rows.append(r)



OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)


for r in rows:
    for k in fieldnames:
        if k not in r:
            r[k] = ""


with open(
    OUTPUT,
    "w",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


print("Saved:", OUTPUT)
print("Rows:", len(rows))
