"""Descriptive arithmetic on user-transcribed data, not a rheology validation."""
import json
import statistics
from pathlib import Path

base = Path(__file__).resolve().parent
data = json.loads((base / "user_transcribed_data.json").read_text())
rows = data["rows"]

def summary(subset):
    values = [r[4] for r in subset]
    mean = statistics.mean(values)
    return {
        "number_of_sweep_points_not_replicates": len(values),
        "mean_Pa_s": mean,
        "min_Pa_s": min(values),
        "max_Pa_s": max(values),
        "range_over_mean_percent": (max(values) - min(values)) / mean * 100,
        "max_over_min_minus_one_percent": (max(values) / min(values) - 1) * 100,
        "largest_deviation_from_candidate_0p012_Pa_s_percent": max(
            abs(v / 0.012 - 1) * 100 for v in values
        ),
    }

output = {
    "scope": "single ascending flow sweep, no replicate uncertainty or constitutive fit",
    "all_five_points": summary(rows),
    "last_three_points_descriptive_subset_not_validated_plateau": summary(rows[2:]),
    "temperature_range_C": [min(r[1] for r in rows), max(r[1] for r in rows)],
    "inferred_torque_uNm": [r[2] / data["stress_constant_Pa_per_Nm"] * 1e6 for r in rows],
    "torque_inference": "Calculated from reported stress constant; not raw measured torque channel",
    "max_relative_eta_vs_stress_over_rate_difference": max(
        abs((r[2] / r[3] - r[4]) / r[4]) for r in rows
    ),
    "candidate_mu_Pa_s": 0.012,
    "candidate_status": "discussion only; neither user-selected nor protocol-frozen",
}
(base / "analysis.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(output, indent=2, ensure_ascii=False))
