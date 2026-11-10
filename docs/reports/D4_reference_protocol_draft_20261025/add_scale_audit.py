#!/usr/bin/env python3
"""Add matched dimensionless mesh checks to the unfrozen review draft; no solve."""
import csv
import json
from fractions import Fraction
from pathlib import Path

OUT = Path(__file__).resolve().parent


def main():
    target = OUT / 'scale_audit_meshes2.csv'
    if target.exists():
        raise SystemExit('Refuse repeated scale-audit generation.')
    proposal = json.loads((OUT / 'proposal.json').read_text())
    assert not proposal['execution_authorized'] and not proposal['proposed_reference_contract_v2_activated']
    records = []
    for source, small, h, d, w in [('G05', 'G09', 50, 50, 80), ('G04', 'G10', 50, 80, 160)]:
        delta = Fraction(5, 6)
        nx, nh, nd, nw = [int(Fraction(v) / delta) for v in [2*w, h, d, w]]
        t = 2*(nx*nh + nw*nd)
        v = (nx+1)*(nh+1) + (nw+1)*nd
        records.append({'large_geometry': source, 'small_geometry': small,
                        'length_scale_fraction': '2/3', 'expected_K_scale_fraction': '8/27',
                        'large_mesh_nm_exact': '5/4', 'small_mesh_nm_exact': '5/6',
                        'triangles': t, 'scalar_P2_dofs_before_constraints': 2*v+t-1,
                        'stokes_P2P1_dofs_before_constraints': 5*v+2*t-2,
                        'extra_direction_solves': 2,
                        'status': 'DRAFT_NOT_EXECUTED'})
    with target.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)
    proposal['proposed_limits'].update({'MMS_pressure_L2_relative': .005,
                                        'MMS_minimum_observed_velocity_order': 2,
                                        'MMS_minimum_observed_pressure_order': 1,
                                        'MMS_near_roundoff_absolute_error_scale': 1e-8,
                                        'periodic_trace_relative_error': 1e-10})
    proposal['scale_audit_extra_meshes'] = 2
    proposal['scale_audit_extra_direction_solves'] = 4
    (OUT / 'proposal.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + '\n')
    resources = json.loads((OUT / 'resource_comparison.json').read_text())
    resources['matched_scale_audit_extra_direction_solves'] = 4
    resources['core_plus_matched_scale_linear_solves'] = 88
    resources['quadrature_algebraic_and_alternate_mesh_repeats_still_extra'] = True
    (OUT / 'resource_comparison.json').write_text(json.dumps(resources, ensure_ascii=False, indent=2) + '\n')
    print('Added two matched dimensionless scale meshes (four direction solves), draft only.')


if __name__ == '__main__':
    main()
