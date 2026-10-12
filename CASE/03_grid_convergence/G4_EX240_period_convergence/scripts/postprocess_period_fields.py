#!/usr/bin/env python3
"""New batches only: field completeness first, unchanged numerical gates next."""
import json
import sys
from pathlib import Path

from check_field_slice import check_field_slice
import postprocess_period as numerical


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_period_fields.py NEW_BATCH_DIR")
    batch = Path(sys.argv[1]).resolve()
    nx = int(batch.name.split("_")[2].removeprefix("nx"))
    checks = []
    errors = []
    for tag in numerical.TAGS:
        for direction in numerical.DIRECTIONS:
            path = batch / "runs" / f"nx{nx}_{direction}_{tag}" / "steady/field_slice.csv"
            try:
                checks.append(check_field_slice(path, nx))
            except (ValueError, OSError) as error:
                errors.append(str(error))
    # Fail before creating numerical success reports. Never rewrite old evidence.
    if errors:
        raise SystemExit("FIELD_OUTPUT_FAIL:\n" + "\n".join(errors))
    numerical.main()
    (batch / "FIELD_OUTPUT_AUDIT.json").write_text(
        json.dumps({"field_outputs_PASS": True, "checks": checks}, indent=2) + "\n")
    report = batch / "G4_LEVEL_REPORT.md"
    with report.open("a") as fh:
        fh.write("\n- field_outputs_PASS: true (rows, unique coordinates, "
                 "full fluid coverage, finite values; see FIELD_OUTPUT_AUDIT.json)\n")


if __name__ == "__main__":
    main()
