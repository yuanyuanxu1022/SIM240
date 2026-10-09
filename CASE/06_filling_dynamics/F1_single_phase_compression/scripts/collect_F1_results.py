from pathlib import Path
import csv

root = Path(__file__).resolve().parents[1]

result_files = sorted(
    root.glob("results/f1_single_phase_h*/result.txt")
)

summary_dir = root / "results" / "summary"
summary_dir.mkdir(parents=True, exist_ok=True)


def read_result(path):
    data = {}
    with open(path, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                data[key] = value
    return data


resistance_rows = []
validation_rows = []

for file in result_files:
    data = read_result(file)

    if data.get("PASS") != "true":
        continue

    case = data.get("case", "")
    direction = data.get("direction", "")

    height_nm = float(data["mesa_gap_m"]) * 1e9

    resistance_rows.append({
        "case": case,
        "height_nm": int(round(height_nm)),
        "direction": direction,
        "Q_m3_s": data.get("Q_m3_s", ""),
        "deltaP_Pa": data.get("deltaP_effective_Pa", ""),
        "Keff_m3": data.get("Keff_m3", ""),
        "R_eff_Pa_s_m3": data.get("R_eff_Pa_s_per_m3", ""),
        "dissipation_W": data.get("dissipation_W", ""),
        "Keff_over_K0": data.get("Keff_over_K0", ""),
    })

    validation_rows.append({
        "case": case,
        "height_nm": int(round(height_nm)),
        "direction": direction,
        "PASS": data.get("PASS", ""),
        "converged": data.get("converged", ""),
        "q_min": data.get("q_min", ""),
        "q_max": data.get("q_max", ""),
        "mass_error": data.get("max_mass_abs_relative", ""),
        "Mach": data.get("max_Mach", ""),
        "fallback_count": data.get("fallback_count", ""),
        "material_unchanged": data.get("material_unchanged", ""),
    })


with open(summary_dir/"F1_resistance_matrix.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=resistance_rows[0].keys())
    writer.writeheader()
    writer.writerows(resistance_rows)


with open(summary_dir/"F1_validation.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=validation_rows[0].keys())
    writer.writeheader()
    writer.writerows(validation_rows)


print(f"Collected {len(resistance_rows)} F1 cases")
print(summary_dir/"F1_resistance_matrix.csv")
print(summary_dir/"F1_validation.csv")
