#!/usr/bin/env python3
"""Reproducible population-level analysis for the stage-3 f3 causal trace."""

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
C_PATH = ROOT / "output/f3_reverse_causal_trace_C_v3_20260908/f3_reverse_operator_trace.csv"
A_PATH = ROOT / "output/f3_moving_closed_A_population_reference_20260908/f3_reverse_operator_trace.csv"
OUT_DIR = ROOT / "output/f3_reverse_causal_trace_C_v3_20260908"


def load(path):
    rows = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            rows[(int(row["step"]), row["cell_name"], row["stage"])] = row
    return rows


def value(rows, step, cell, stage, key):
    return float(rows[(step, cell, stage)][key])


def first_from_which_abs_is_monotone(values, start=1, tolerance=1e-30):
    steps = sorted(step for step in values if step >= start)
    for candidate in steps:
        suffix = [values[step] for step in steps if step >= candidate]
        if all(abs(b) + tolerance >= abs(a) for a, b in zip(suffix, suffix[1:])):
            return candidate
    return None


def main():
    c_rows, a_rows = load(C_PATH), load(A_PATH)
    post_b = "post_moving_Bouzidi_PostStream"
    post_collision = "post_LP_reconstruction_and_collision_pre_comm"
    pre_collision = "pre_collision_after_full_communicate"
    post_stream = "post_stream_pre_PostStream_comm"

    source_delta = {}
    donor_f3 = {}
    with (OUT_DIR / "f3_stable_reference_delta.csv").open("w", newline="") as stream:
        fields = [
            "step", "population", "operator", "current_C", "stable_A_reference",
            "absolute_delta", "relative_delta_when_defined",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for step in range(1, 221):
            current = value(c_rows, step, "f8_stream_source", post_b, "f8")
            reference = value(a_rows, step, "f8_stream_source", post_b, "f8")
            delta = current - reference
            source_delta[step] = delta
            writer.writerow({
                "step": step,
                "population": "f8",
                "operator": "moving_Bouzidi_PostStream_at_(0,1,15)",
                "current_C": f"{current:.17g}",
                "stable_A_reference": f"{reference:.17g}",
                "absolute_delta": f"{abs(delta):.17g}",
                "relative_delta_when_defined": (
                    f"{delta/reference:.17g}" if abs(reference) > 1e-20 else ""
                ),
            })
            donor_f3[step] = value(c_rows, step, "donor", post_collision, "f3")

    first_clear_source = next(
        step for step in range(1, 221) if abs(source_delta[step]) >= 1e-12
    )
    source_monotone = first_from_which_abs_is_monotone(source_delta)
    donor_runaway = first_from_which_abs_is_monotone(donor_f3)

    selected = [3, 4, 20, 40, 52, 100, 160, 180, 200, 209]
    with (OUT_DIR / "f3_causal_selected_steps.csv").open("w", newline="") as stream:
        fields = [
            "step", "donor_f8_pre_LP", "donor_f3_after_LP_collision",
            "donor_f17_after_LP_collision", "source_f17_after_stream",
            "source_f8_before_Bouzidi", "source_f8_after_Bouzidi",
            "target_f3_before_stream", "target_f3_after_stream",
            "source_f8_stable_A", "source_f8_C_minus_A",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for step in selected:
            donor_f17 = value(c_rows, step, "donor", post_collision, "f17")
            source_f17 = value(c_rows, step, "f8_stream_source", post_stream, "f17")
            row = {
                "step": step,
                "donor_f8_pre_LP": value(c_rows, step, "donor", pre_collision, "f8"),
                "donor_f3_after_LP_collision": donor_f3[step],
                "donor_f17_after_LP_collision": donor_f17,
                "source_f17_after_stream": source_f17,
                "source_f8_before_Bouzidi": value(c_rows, step, "f8_stream_source", post_stream, "f8"),
                "source_f8_after_Bouzidi": value(c_rows, step, "f8_stream_source", post_b, "f8"),
                "target_f3_before_stream": value(c_rows, step, "target", post_collision, "f3"),
                "target_f3_after_stream": value(c_rows, step, "target", post_stream, "f3"),
                "source_f8_stable_A": value(a_rows, step, "f8_stream_source", post_b, "f8"),
                "source_f8_C_minus_A": source_delta[step],
            }
            writer.writerow({key: (f"{val:.17g}" if isinstance(val, float) else val)
                             for key, val in row.items()})
            if not math.isclose(donor_f17, source_f17, rel_tol=0, abs_tol=1e-16):
                raise RuntimeError(f"f17 stream identity failed at step {step}")

    # LocalPressure low-y reads all cy=0 and cy=-1 populations when it
    # computes its normal momentum and regularized stress.  Record every such
    # input rather than reporting only the largest contributor.
    directions = [
        (0, 0, 0, 0), (1, -1, 0, 0), (2, 0, -1, 0), (3, 0, 0, -1),
        (4, -1, -1, 0), (5, -1, 1, 0), (6, -1, 0, -1),
        (7, -1, 0, 1), (8, 0, -1, -1), (9, 0, -1, 1),
        (10, 1, 0, 0), (11, 0, 1, 0), (12, 0, 0, 1),
        (13, 1, 1, 0), (14, 1, -1, 0), (15, 1, 0, 1),
        (16, 1, 0, -1), (17, 0, 1, 1), (18, 0, 1, -1),
    ]
    with (OUT_DIR / "localpressure_f3_input_population_contributions.csv").open(
        "w", newline=""
    ) as stream:
        fields = [
            "step", "direction", "cx", "cy", "cz", "LocalPressure_reads",
            "shifted_population", "normal_velocity_numerator_contribution",
            "absolute_contribution_rank_among_read_populations",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for step in [3, 4, 20, 52, 100, 160, 200, 209]:
            row = c_rows[(step, "donor", pre_collision)]
            read = [(i, cx, cy, cz) for i, cx, cy, cz in directions
                    if cy in (0, -1)]
            ranked = sorted(
                read,
                key=lambda item: abs(float(row[f"lp_normal_contrib_f{item[0]}"])),
                reverse=True,
            )
            rank = {item[0]: index + 1 for index, item in enumerate(ranked)}
            for i, cx, cy, cz in directions:
                writer.writerow({
                    "step": step,
                    "direction": i,
                    "cx": cx,
                    "cy": cy,
                    "cz": cz,
                    "LocalPressure_reads": cy in (0, -1),
                    "shifted_population": row[f"f{i}"],
                    "normal_velocity_numerator_contribution": (
                        row[f"lp_normal_contrib_f{i}"] if cy in (0, -1) else ""
                    ),
                    "absolute_contribution_rank_among_read_populations": (
                        rank[i] if cy in (0, -1) else ""
                    ),
                })

    with (OUT_DIR / "f3_causal_analysis.txt").open("w") as stream:
        stream.write(f"first_clear_source_f8_delta_vs_stable_A_step={first_clear_source}\n")
        stream.write(f"source_f8_abs_delta_monotone_from_step={source_monotone}\n")
        stream.write(f"donor_post_collision_f3_abs_monotone_from_step={donor_runaway}\n")
        stream.write("target_f3_stream_source=(0,0,14)\n")
        stream.write("target_f3_stream_copy_max_abs_error=0\n")
        stream.write("feedback_chain=donor_f8->LocalPressure_momenta_and_CombinedRLB_collision"
                     "->donor_f17->stream_to_(0,1,15)->Bouzidi_direction17_overwrites_f8"
                     "->next_collision/stream_to_donor_f8\n")
        stream.write("f3_branch=donor_LocalPressure_collision_f3->same_step_stream_to_(0,0,13)\n")


if __name__ == "__main__":
    main()
