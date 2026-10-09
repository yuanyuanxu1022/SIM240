import csv
from pathlib import Path

import numpy as np
import pytest

from generate_pressure_perturbation_figure import (
    center_pressure,
    load_field_slice,
    validate_common_grid,
)


def write_slice(path: Path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["x", "z", "ux", "uy", "uz", "speed", "rho", "pressure", "Phi", "material"]
        )
        writer.writerows(rows)


def test_center_pressure_uses_only_fluid_slice_mean(tmp_path):
    source = tmp_path / "field_slice.csv"
    write_slice(
        source,
        [
            [1.0, 1.0, 0, 0, 0, 0, 1, 2.0, 0, 1],
            [2.0, 1.0, 0, 0, 0, 0, 1, 6.0, 0, 1],
            [3.0, 1.0, 0, 0, 0, 0, 1, 100.0, 0, 0],
        ],
    )

    data = load_field_slice(source)
    mean, perturbation = center_pressure(data)

    assert mean == pytest.approx(4.0)
    np.testing.assert_allclose(perturbation, [-2.0, 2.0])


def test_common_grid_rejects_mismatched_sections(tmp_path):
    parallel = tmp_path / "parallel.csv"
    perpendicular = tmp_path / "perpendicular.csv"
    rows = [[1.0, 1.0, 0, 0, 0, 0, 1, 2.0, 0, 1]]
    write_slice(parallel, rows)
    write_slice(perpendicular, [[1.1, 1.0, 0, 0, 0, 0, 1, 2.0, 0, 1]])

    with pytest.raises(ValueError, match="common x-z grid"):
        validate_common_grid(load_field_slice(parallel), load_field_slice(perpendicular))
