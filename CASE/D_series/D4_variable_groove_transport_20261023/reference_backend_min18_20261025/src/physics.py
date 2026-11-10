"""Analytic definitions only. No mesh, assembly, field initialization or solve.

The scalar and mixed MMS use prescribed, nonuniform forcing; their J is NOT
a mobility under uniform acceleration. Pressure is the physical-sign
kinematic perturbation, not the negative-pressure demo convention.
"""
from math import cos, sin, pi


def scalar_mms(x, z):
    q = z * (1 - z)
    c = cos(pi * x)
    value = q * (1 + 0.1 * c)
    forcing = 2 * (1 + 0.1 * c) + 0.1 * pi**2 * q * c
    return {"value": value, "forcing": forcing, "J_exact": 1 / 6}


def mixed_mms(x, z):
    s, c = sin(pi * x), cos(pi * x)
    f = z**2 * (1 - z)**2
    fp = 2 * z - 6 * z**2 + 4 * z**3
    fpp = 2 - 12 * z + 12 * z**2
    fppp = -12 + 24 * z
    ux = z * (1 - z) + 0.1 * s * fp
    uz = -0.1 * pi * c * f
    pressure = 0.1 * c * cos(pi * z)
    fx = 2 + 0.1 * s * (pi**2 * fp - fppp) - 0.1 * pi * s * cos(pi * z)
    fz = 0.1 * pi * c * (fpp - pi**2 * f) - 0.1 * pi * c * sin(pi * z)
    return {"velocity": (ux, uz), "pressure": pressure,
            "forcing": (fx, fz), "J_exact": 1 / 6}


def flat_exact(h_m=75e-9, nu_m2_s=1e-6, acceleration_m_s2=1e5):
    k = h_m**3 / 12
    j = acceleration_m_s2 * k / nu_m2_s
    return {"J_hat_exact": 1 / 12, "K_m3": k, "J_m2_s": j,
            "R_Pa_s_m3": 1000 * acceleration_m_s2 / j,
            "velocity_scale_m_s": acceleration_m_s2 * h_m**2 / nu_m2_s,
            "kinematic_pressure_scale_m2_s2": acceleration_m_s2 * h_m}


def topology_counts(nx, nz, mixed):
    scalar = (2 * nx + 1) * (2 * nz + 1)
    pressure = (nx + 1) * (nz + 1) if mixed else 0
    return {"P2_trace_nodes_per_face": 2 * nz + 1,
            "free_P2_trace_pairs_per_component": 2 * nz - 1,
            "P1_pressure_pairs": nz + 1 if mixed else None,
            "raw_dofs": 2 * scalar + pressure if mixed else scalar,
            "is_actual_mesh_audit": False}
