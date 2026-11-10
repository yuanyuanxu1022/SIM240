"""Offline volume and unit-mapping audit; does not implement or invoke OpenLB."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
design_path = HERE / "design.json"
design = json.loads(design_path.read_text())
g, n = design["geometry"], design["numerics"]
dx = n["candidate_dx_nm"]
lx = g["period_nm"] * g["periods_x"]
ly = g["period_nm"] * g["periods_y"]
h, depth = g["mesa_gap_nm"], g["groove_depth_nm"]
nx, ny, nz = [round(length / dx) for length in (lx, ly, h + depth)]
assert all(math.isclose(count * dx, length) for count, length in zip((nx, ny, nz), (lx, ly, h + depth)))
xs, ys, zs = [[(i + .5) * dx for i in range(count)] for count in (nx, ny, nz)]
left, right = g["groove_x_interval_within_period_nm"]
roof = [h + depth if left <= x % g["period_nm"] < right else h for x in xs]
fluid_x_count_by_z = [sum(z < wall for wall in roof) for z in zs]
fluid_cells = sum(fluid_x_count_by_z) * ny
volume_discrete = fluid_cells * dx**3
volume_analytic = lx * ly * (h + depth * g["groove_width_nm"] / g["period_nm"])
assert math.isclose(volume_discrete, volume_analytic, rel_tol=1e-12)
width = n["candidate_interface_width_nodes"] * dx


def gas_phi(signed_distance):
    return .5 * (1 + math.tanh(2 * signed_distance / width))


def bisect_value(function, low, high, target):
    f_low, f_high = function(low), function(high)
    assert min(f_low, f_high) <= target <= max(f_low, f_high)
    increasing = f_high > f_low
    for _ in range(80):
        mid = .5 * (low + high)
        if (function(mid) < target) == increasing:
            low = mid
        else:
            high = mid
    value = .5 * (low + high)
    assert abs(function(value) - target) < 1e-12
    return value


states = []
for state in design["initial_states"]:
    target_gas = 1 - state["liquid_fraction"]
    if state["id"] == "F":
        actual_gas, corrected = 0., None
    elif state["id"] == "G_roof":
        def amount(cut):
            return sum(count * gas_phi(z - cut) for z, count in zip(zs, fluid_x_count_by_z)) * ny / fluid_cells
        cut = bisect_value(amount, 0, h + depth, target_gas)
        actual_gas, corrected = amount(cut), {"z_cut_nm": cut}
    elif state["id"] == "G_band":
        center = state["band_center_y_nm"]
        distances = [abs((y - center + ly / 2) % ly - ly / 2) for y in ys]
        def amount(band_width):
            return sum(gas_phi(band_width / 2 - distance) for distance in distances) / ny
        band_width = bisect_value(amount, 0, ly, target_gas)
        actual_gas, corrected = amount(band_width), {"y_band_width_nm": band_width}
    else:
        raise ValueError(state["id"])
    states.append({"id": state["id"], "target_liquid_fraction": state["liquid_fraction"],
                   "discrete_liquid_fraction": 1 - actual_gas,
                   "liquid_volume_nm3": (1 - actual_gas) * volume_discrete,
                   "corrected_diffuse_profile": corrected})

material = design["material"]
rho = material["liquid_density_kg_m3"]["value"]
mu = material["liquid_dynamic_viscosity_Pa_s"]["value"]
rho_g = material["gas_density_kg_m3"]["value"]
mu_g = material["gas_dynamic_viscosity_Pa_s"]["value"]
sigma = material["liquid_gas_surface_tension_N_m"]["value"]
dx_m = dx * 1e-9
nu_lat = (n["candidate_tau_liquid"] - .5) / 3
dt = nu_lat * dx_m**2 / (mu / rho)
gradient = design["measurement"]["candidate_gradient_magnitudes"][0]
h_m = h * 1e-9
output = {
    "design_sha256": hashlib.sha256(design_path.read_bytes()).hexdigest(),
    "scope": "offline initialization quadrature and algebra; no lattice or physical validation",
    "domain_nm": [lx, ly, h + depth],
    "quadrature_cells_total": nx * ny * nz,
    "quadrature_pore_cells": fluid_cells,
    "pore_volume_nm3_analytic": volume_analytic,
    "pore_volume_nm3_discrete": volume_discrete,
    "initial_states": states,
    "diffuse_interface_width_nm": width,
    "candidate_BGK_mapping_not_stability_proof": {
        "dt_s": dt,
        "tau_gas": .5 + 3 * (mu_g / rho_g) * dt / dx_m**2,
        "surface_tension_lattice": sigma * dt**2 / (rho * dx_m**3),
    },
    "smooth_full_liquid_flat_slab_scale_only_not_groove_or_two_phase_prediction": {
        "gradient_Pa_per_m": gradient,
        "q_m2_per_s": gradient * h_m**3 / (12 * mu),
        "mean_velocity_m_per_s": gradient * h_m**2 / (12 * mu),
        "wall_shear_rate_per_s": gradient * h_m / (2 * mu),
    },
    "number_of_states": len(states),
    "directional_coefficients": 2 * len(states),
    "branches_at_one_nonzero_amplitude_including_zero_baseline": 5 * len(states),
    "branches_at_two_nonzero_amplitudes_including_zero_baseline": 9 * len(states),
    "solver_started": False,
    "geometry_PASS": "NOT_EVALUATED",
}
(HERE / "design_audit.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(output, indent=2, ensure_ascii=False))
