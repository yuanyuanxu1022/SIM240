#!/usr/bin/env python3
"""Offline STEP 5-C wall-motion ledger; never writes lattice state."""

import csv
from collections import defaultdict
from pathlib import Path

DX = 5.0e-9
RHO_PHYS = 1000.0
GROOVE_DEPTH = 100.0e-9
LX = 240.0e-9

ROOT = Path(__file__).resolve().parent
AUDIT_RUN = ROOT / "output/mass_audit_consistency_0to3nm_v1_20260909"
V3_RUN = ROOT / "output/first_material_conversion_0to3nm_v3_20260909"
HISTORY_IN = AUDIT_RUN / "first_conversion_history.csv"
EVENTS_IN = V3_RUN / "topology_events.csv"
CELLS_OUT = AUDIT_RUN / "wall_motion_conversion_event_cells.csv"
HISTORY_OUT = AUDIT_RUN / "wall_motion_corrected_history.csv"
SUMMARY_OUT = AUDIT_RUN / "wall_motion_mass_audit_summary.txt"


def fluid_fraction(x, z, h):
    surface = h if x < 60.0e-9 or x >= 180.0e-9 else h + GROOVE_DEPTH
    low = max(z - DX / 2.0, 0.0)
    high = min(z + DX / 2.0, surface)
    return max(0.0, min(1.0, (high - low) / DX))


def main():
    with HISTORY_IN.open(newline="") as stream:
        history = list(csv.DictReader(stream))
    by_step = {int(row["step"]): row for row in history}
    initial_pop_mass = (
        float(history[0]["M_pop_kg"])
        + float(history[0]["cumulative_outward_mass_kg"])
    ) / (1.0 + float(history[0]["R_pop_relative"]))

    with EVENTS_IN.open(newline="") as stream:
        events = list(csv.DictReader(stream))
    grouped = defaultdict(list)
    for event in events:
        grouped[int(event["step"])].append(event)

    event_wall_mass = {}
    event_wall_volume = {}
    with CELLS_OUT.open("w", newline="") as stream:
        fields = [
            "step", "ix", "iy", "iz", "x_nm", "y_nm", "z_nm",
            "old_material", "new_material", "alpha_before", "alpha_after",
            "delta_fluid_volume_m3", "occupied_volume_m3", "rho_pop_lattice",
            "delta_M_wall_signed_kg", "occupied_mass_kg",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for step in sorted(grouped):
            h_before = float(by_step[step - 1]["h_nm"]) * 1.0e-9
            h_after = float(by_step[step]["h_nm"]) * 1.0e-9
            total_mass = 0.0
            total_volume = 0.0
            for event in grouped[step]:
                x = float(event["x_nm"]) * 1.0e-9
                z = float(event["z_nm"]) * 1.0e-9
                alpha_before = fluid_fraction(x, z, h_before)
                alpha_after = fluid_fraction(x, z, h_after)
                delta_volume = (alpha_after - alpha_before) * DX**3
                rho_pop = 1.0 + sum(float(event[f"f{i}"]) for i in range(19))
                delta_mass = rho_pop * RHO_PHYS * delta_volume
                total_volume += delta_volume
                total_mass += delta_mass
                writer.writerow({
                    "step": step,
                    "ix": event["ix"], "iy": event["iy"], "iz": event["iz"],
                    "x_nm": event["x_nm"], "y_nm": event["y_nm"],
                    "z_nm": event["z_nm"], "old_material": event["old_material"],
                    "new_material": event["new_material"],
                    "alpha_before": f"{alpha_before:.17g}",
                    "alpha_after": f"{alpha_after:.17g}",
                    "delta_fluid_volume_m3": f"{delta_volume:.17g}",
                    "occupied_volume_m3": f"{-delta_volume:.17g}",
                    "rho_pop_lattice": f"{rho_pop:.17g}",
                    "delta_M_wall_signed_kg": f"{delta_mass:.17g}",
                    "occupied_mass_kg": f"{-delta_mass:.17g}",
                })
            event_wall_mass[step] = total_mass
            event_wall_volume[step] = total_volume

    cumulative_wall_mass = 0.0
    max_abs_corrected = 0.0
    max_abs_corrected_step = -1
    selected = {}
    with HISTORY_OUT.open("w", newline="") as stream:
        fields = [
            "step", "time_s", "h_nm", "displacement_nm", "M_pop_kg",
            "cumulative_outward_mass_kg", "cumulative_delta_M_wall_signed_kg",
            "R_pop_relative", "R_corrected_relative",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in history:
            step = int(row["step"])
            cumulative_wall_mass += event_wall_mass.get(step, 0.0)
            m_pop = float(row["M_pop_kg"])
            m_out = float(row["cumulative_outward_mass_kg"])
            # Existing convention: outward mass is positive, hence +m_out.
            # delta_M_wall is signed fluid-volume change (negative when occupied).
            corrected = (
                m_pop - initial_pop_mass + m_out - cumulative_wall_mass
            ) / initial_pop_mass
            value = abs(corrected)
            if value > max_abs_corrected:
                max_abs_corrected = value
                max_abs_corrected_step = step
            output = {
                "step": step, "time_s": row["time_s"], "h_nm": row["h_nm"],
                "displacement_nm": row["displacement_nm"], "M_pop_kg": row["M_pop_kg"],
                "cumulative_outward_mass_kg": row["cumulative_outward_mass_kg"],
                "cumulative_delta_M_wall_signed_kg": f"{cumulative_wall_mass:.17g}",
                "R_pop_relative": row["R_pop_relative"],
                "R_corrected_relative": f"{corrected:.17g}",
            }
            writer.writerow(output)
            if step in {3594, 3595, 3596, 3898}:
                selected[step] = output

    conversion_step = min(event_wall_mass)
    with SUMMARY_OUT.open("w") as stream:
        stream.write(f"initial_M_pop_kg={initial_pop_mass:.17g}\n")
        stream.write(f"conversion_step={conversion_step}\n")
        stream.write(f"converted_cells={len(grouped[conversion_step])}\n")
        stream.write(f"delta_V_wall_signed_m3={event_wall_volume[conversion_step]:.17g}\n")
        stream.write(f"occupied_volume_m3={-event_wall_volume[conversion_step]:.17g}\n")
        stream.write(f"delta_M_wall_signed_kg={event_wall_mass[conversion_step]:.17g}\n")
        stream.write(f"occupied_mass_kg={-event_wall_mass[conversion_step]:.17g}\n")
        stream.write(f"max_abs_R_corrected={max_abs_corrected:.17g}\n")
        stream.write(f"max_abs_R_corrected_step={max_abs_corrected_step}\n")
        for step in sorted(selected):
            stream.write(f"step_{step}_R_pop={selected[step]['R_pop_relative']}\n")
            stream.write(f"step_{step}_R_corrected={selected[step]['R_corrected_relative']}\n")
        stream.write(f"PASS={str(max_abs_corrected < 1.0e-3).lower()}\n")


if __name__ == "__main__":
    main()
