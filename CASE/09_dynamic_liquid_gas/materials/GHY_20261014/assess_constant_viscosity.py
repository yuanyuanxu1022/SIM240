"""Assess candidate error point by point; no extrapolation or rheology model fit."""
import json
from pathlib import Path

base = Path(__file__).resolve().parent
raw = json.loads((base / "user_transcribed_data.json").read_text())
mu = 0.012
points = []
for row in raw["rows"]:
    measured = row[4]
    points.append({
        "shear_rate_per_s": row[3],
        "measured_mu_Pa_s": measured,
        "candidate_mu_Pa_s": mu,
        "error_percent_of_measured": abs(mu - measured) / measured * 100,
        "deviation_percent_of_candidate": abs(mu - measured) / mu * 100,
    })
report = {
    "candidate_mu_Pa_s": mu,
    "observed_temperature_range_C": [min(r[1] for r in raw["rows"]), max(r[1] for r in raw["rows"])],
    "points": points,
    "max_error_percent_of_measured_all_five": max(p["error_percent_of_measured"] for p in points),
    "max_error_percent_of_measured_last_three": max(p["error_percent_of_measured"] for p in points[2:]),
    "diagnostic_tolerances_not_protocol_gates": {
        str(tol): [p["shear_rate_per_s"] for p in points if p["error_percent_of_measured"] <= tol]
        for tol in (5, 10)
    },
    "constitutive_model_validated": False,
    "extrapolation_below_10_or_above_50_per_s_supported": False,
    "scope": "individual observed points only; no continuous plateau, repeatability or confidence bound established",
}
(base / "constant_viscosity_assessment.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(report, indent=2, ensure_ascii=False))
