"""Read-only arithmetic study of existing artifacts; no solver or compiler.

The counterexample is constructed arithmetic, not a historical cell trace.
XZ extrusion uses a stated y-invariance assumption and cannot reconstruct the
190 differing historical timesteps, none of which has a saved field frame.
"""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json
import math
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_v1_2'
OLD = ROOT / 'CASE/D_series/D4_variable_groove_transport_20261023'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f))


def kv(path):
    return dict(line.split('=', 1) for line in Path(path).read_text().splitlines() if '=' in line)


def elf_double(path, address):
    data = Path(path).read_bytes()
    assert data[:6] == b'\x7fELF\x02\x01'
    header = struct.unpack_from('<16sHHIQQQIHHHHHH', data)
    for i in range(header[10]):
        ph = struct.unpack_from('<IIQQQQQQ', data, header[5] + i * header[9])
        p_type, _, offset, vaddr, _, size, _, _ = ph
        if p_type == 1 and vaddr <= address and address + 8 <= vaddr + size:
            raw = data[offset + address - vaddr:offset + address - vaddr + 8]
            return dict(address=hex(address), float_value=struct.unpack('<d', raw)[0], bytes_hex=raw.hex())
    raise ValueError('address not file-backed')


def bits(x):
    return struct.unpack('<Q', struct.pack('<d', x))[0]


def fold(rhos, dx):
    fused = separate = correction = 0.
    prefix_differences = 0; largest_prefix_difference = 0.; count = 0
    for rho in rhos:
        # Precisely the rounded partial products observed in both executables.
        partial = ((rho * 1000.) * dx) * dx
        term = partial * dx
        fused = math.fma(partial, dx, fused)
        nxt = separate + term
        correction += ((separate - nxt) + term if abs(separate) >= abs(term)
                       else (term - nxt) + separate)
        separate = nxt; count += 1
        if fused != separate:
            prefix_differences += 1
            largest_prefix_difference = max(largest_prefix_difference, abs(fused - separate))
    return dict(cells=count, old_fused_mass_kg=fused, new_separate_mass_kg=separate,
                compensated_mass_kg=separate + correction,
                unequal_cell_prefix_totals=prefix_differences,
                max_cell_prefix_absolute_difference_kg=largest_prefix_difference)


def main():
    b = json.loads((CASE / 'evidence/S0_launch_release_20261101_01.json').read_text())
    inspection = json.loads((OUT / 'binary_inspection.json').read_text())
    constants = dict(
        old_rhoPhys=elf_double(inspection['old']['binary'], 0xe2bd0),
        new_rhoPhys=elf_double(inspection['new']['binary'], 0xe3d50),
        old_initialized_dx=elf_double(inspection['old']['binary'], 0x111070),
        new_initialized_dx=elf_double(inspection['new']['binary'], 0x112070))
    assert constants['old_rhoPhys']['float_value'] == constants['new_rhoPhys']['float_value'] == 1000.
    replays = {}; densities = []
    for record in b['approved_runs']:
        run = Path(record['output_directory']); config = kv(run / 'run_config.txt')
        direction = config['direction']; dx = float(kv(run / 'effective_config.txt')['dx_m'])
        final = rows(run / 'field_slice.csv'); data = rows(run / 'diagnostics.csv')
        by_x = {}
        for row in final:
            by_x.setdefault(float(row['x']), []).append((float(row['z']), float(row['rho'])))
        assert len(by_x) == 48 and len(final) == 1200
        ordered_xz = [sorted(by_x[x]) for x in sorted(by_x)]
        # Source forCoreSpatialLocations is x outer / y middle / z inner.
        rho_values = [rho for column in ordered_xz for _y in range(48) for z, rho in column]
        densities += [rho for column in ordered_xz for z, rho in column]
        replay = fold(rho_values, dx)
        replay.update(input='existing final double precision XZ slice, extruded over 48 y planes',
            assumption='rho is identical along y; exact full-domain density was not saved',
            final_step=int(data[-1]['step']), actual_old_mass_kg=float(rows(
                Path(b['h75_regression_references'][direction]['directory']) / 'diagnostics.csv')[-1]['mass']),
            actual_new_mass_kg=float(data[-1]['mass']), actual_corrected_mass_kg=float(data[-1]['corrected_mass']),
            raw_slice_sha256=sha(run / 'field_slice.csv'))
        replay['old_final_total_matches_record'] = replay['old_fused_mass_kg'] == replay['actual_old_mass_kg']
        replay['new_final_total_matches_record'] = replay['new_separate_mass_kg'] == replay['actual_new_mass_kg']
        replay['compensated_final_total_matches_record'] = replay['compensated_mass_kg'] == replay['actual_corrected_mass_kg']
        replays[direction] = replay
    dx = constants['new_initialized_dx']['float_value']; witness = None
    for rho in densities:
        partial = ((rho * 1000.) * dx) * dx
        for k in range(1, 512):
            accumulator = (dx * dx * dx * 1000.) * k
            fused = math.fma(partial, dx, accumulator)
            separate = (partial * dx) + accumulator
            if fused != separate:
                exact = float(Fraction(partial) * Fraction(dx) + Fraction(accumulator))
                assert exact == fused
                witness = dict(label='CONSTRUCTED_ARITHMETIC_COUNTEREXAMPLE_NOT_HISTORICAL_PREFIX',
                    density_from_saved_slice=rho, prefix_cell_count_label=k,
                    accumulator_kg=accumulator, partial_before_last_dx=partial, dx=dx,
                    fused_result_kg=fused, separate_result_kg=separate,
                    fused_hex=fused.hex(), separate_hex=separate.hex(),
                    ULP_distance=abs(bits(fused) - bits(separate)),
                    absolute_difference_kg=abs(fused - separate),
                    exact_rational_single_round_matches_fma=True,
                    accumulator_was_constructed_not_observed=True)
                break
        if witness:
            break
    assert witness is not None
    diff = rows(ROOT / 'docs/reports/URV_S0_results_review_20261101/legacy_differences_T.csv')
    changed_steps = sorted({int(row['step']) for row in diff})
    frame_steps = [int(row['step']) for row in rows(CASE / 'runs/URV_S0_T_v1_2_20261101_01/steady/frame_index.csv')]
    covered = sorted(set(changed_steps) & set(frame_steps))
    evidence = dict(python_version=sys.version, arithmetic_only_not_solver_execution=True,
        compiler_invocations=0, solver_invocations=0, constants_read_from_bound_ELFs=constants,
        old_mass_model='partial=RN(RN(RN(rho*1000)*dx)*dx); M=RN(partial*dx+M) with one final FMA round',
        new_mass_model='same partial; term=RN(partial*dx); M=RN(term+M)',
        final_slice_extrusion_replays=replays, same_input_counterexample=witness,
        total_differing_T_timesteps=len(changed_steps), saved_T_timesteps=frame_steps,
        differing_timesteps_with_saved_field=covered,
        exact_full_density_at_differing_timesteps_available_in_bound_artifacts=False,
        whole_190_point_causal_replay_completed=False,
        limit='A static instruction-path difference and its arithmetic effect are established; full historical trajectory attribution is not.')
    (OUT / 'arithmetic_probe.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(dict(counterexample_found=True, final_slice_replays=replays,
                         differing_timesteps_with_saved_field=covered), indent=2))


if __name__ == '__main__':
    main()
