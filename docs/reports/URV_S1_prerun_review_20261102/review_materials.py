#!/usr/bin/env python3
"""S1 input/contract review only: pure arithmetic and source reads, no native calls."""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_mrp_v1_a1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_mrp_v1_a1'
ORIGINAL = ROOT / 'docs/reports/Unseen_V2_reference_protocol_20261101'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def rows(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def save(name, value):
    with (OUT / name).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def locator(path, text):
    lines = Path(path).read_text().splitlines()
    found = [index + 1 for index, line in enumerate(lines) if text in line]
    assert found, (path, text)
    return dict(path=str(path), sha256=sha(path), lines=found, exact_text=text)


def main():
    protected = load(ROOT / 'docs/reports/URV_A1_S0_results_review_20261102/protected_inputs_before.json')
    for path in (ROOT / 'docs/reports/URV_A1_S0_results_review_20261102').rglob('*'):
        if path.is_file():
            protected[str(path)] = sha(path)
    assert all(sha(path) == value for path, value in protected.items())
    sources = [CHECKER / 'common/case_matrix.csv', CHECKER / 'common/protocol.json',
        CHECKER / 'common/PROTOCOL.md', CHECKER / 'common/acceptance_spec.json',
        CHECKER / 'analysis/check_results.py', CHECKER / 'analysis/evidence.py',
        CHECKER / 'analysis/read_fields.py', CHECKER / 'analysis/revision.py',
        CHECKER / 'analysis/contracts.py', CHECKER / 'analysis/mass_capture.py',
        CHECKER / 'analysis/check_mass_repair.py', CASE / 'src/mrp_observer.h',
        CASE / 'src/urv_reference.cpp', CASE / 'src/capture_schedule.h',
        CASE / 'scripts/run_S0_A1.py', CASE / 'scripts/audit_A1_zero.py',
        ORIGINAL / 'PROTOCOL.md', ORIGINAL / 'case_matrix.csv']
    matrix = rows(CHECKER / 'common/case_matrix.csv')
    selected = [row for row in matrix if row['stage'] == 'S1_SMOOTH_THIN']
    assert len(selected) == 2
    assert selected == [row for row in rows(ORIGINAL / 'case_matrix.csv') if row['stage'] == 'S1_SMOOTH_THIN']
    sys.path.insert(0, str(CHECKER / 'analysis'))
    from evidence import exact_parameters, geometry, kv
    calculations = []
    inputs = []
    for row in selected:
        path = ORIGINAL / 'describe_only_templates' / (row['planned_case_id'] + '.txt')
        sources.append(path)
        cfg = kv(path)
        assert cfg['mode'] == 'describe' and cfg['output_directory'] == 'NOT_AN_EXECUTION_DIRECTORY'
        exact = exact_parameters(cfg)
        geo = geometry(cfg)  # pure NumPy classification; no OpenLB/native code
        assert exact['nodes'] == int(row['expected_fluid_nodes']) == 884736
        assert exact['window'] == int(row['window_steps']) == 2592
        assert exact['cap'] == int(row['maximum_steps']) == 27648
        assert geo['candidate_links'] == 10 * 192 * 192 == 368640
        assert geo['q_min'] == geo['q_max'] == .5
        h = Fraction(cfg['h_nm']) / 10**9; dx = Fraction(cfg['dx_nm']) / 10**9
        nu = Fraction(cfg['nu_m2_s']); acceleration = Fraction(cfg['acceleration_m_s2'])
        K = h**3 / 12; J = K * acceleration / nu; U = J / h
        vmax = acceleration * h**2 / (8 * nu)
        times = [Fraction(str(v)) for v in load(CHECKER / 'common/protocol.json')['time']['frame_tstar']]
        dt = dx**2 / (6 * nu)
        frames = [math.ceil(t * h**2 / (nu * dt)) for t in times]
        assert frames == [0,35,70,173,346,692,1728,3456,6912,13824,27648]
        item = dict(planned_case_id=row['planned_case_id'], direction=cfg['direction'],
            actual_run_id=None, simulation_authorized=False, parameters=exact,
            static_geometry_prediction=geo, frame_target_steps=frames,
            analytic_K_m3=float(K), analytic_J_m2_s=float(J), analytic_U_m_s=float(U),
            analytic_max_velocity_m_s=float(vmax), analytic_Re_H=float(vmax*h/nu),
            analytic_max_Mach=float(vmax*dt/dx)*math.sqrt(3),
            dt_exact_fraction=str(dt), physical_time_cap_s=float(8*h*h/nu),
            statistical_window_time_s=float(Fraction('0.75')*h*h/nu),
            volume_m3=float(Fraction(cfg['period_nm'])*Fraction(cfg['Ly_nm'])*Fraction(cfg['h_nm'])/10**27),
            single_distribution_bytes=884736*19*8,
            single_distribution_MiB=884736*19*8/1024**2,
            wall_cap_seconds=int(row['wall_cap_seconds']), memory_limit_GiB=int(row['memory_limit_GiB']),
            native_zero_step_executed=False, source_template=str(path), source_template_sha256=sha(path))
        assert item['single_distribution_bytes'] == int(row['single_distribution_bytes'])
        calculations.append(item)
        inputs.append(dict(planned_case_id=row['planned_case_id'],direction=cfg['direction'],
            drive_axis=row['drive_axis'],h_nm=row['h_nm'],d_nm=row['d_nm'],dx_nm=row['dx_nm'],
            Lx_nm=row['P_nm'],Ly_nm=row['Ly_nm'],rho_kg_m3=row['rho_kg_m3'],nu_m2_s=row['nu_m2_s'],
            acceleration_m_s2=row['acceleration_m_s2'],expected_fluid_nodes=exact['nodes'],
            window_steps=exact['window'],maximum_steps=exact['cap'],wall_cap_seconds=row['wall_cap_seconds'],
            analytic_K_m3=float(K),actual_run_id='',execution_authorized=False))
    save('static_geometry_and_analytics.json', dict(method='Exact rational arithmetic plus existing pure Python/NumPy geometry reader; no native execution',
        actual_S1_NUMERICAL_GATE='NOT_EVALUATED', actual_S1_geometry_PASS=None, cases=calculations))
    with (OUT / 'reviewed_inputs.csv').open('x', newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(inputs[0]));writer.writeheader();writer.writerows(inputs)
    findings = [
      dict(id='C01',status='INCOMPATIBLE_BY_DESIGN',issue='Existing native steady mode always instantiates h75-specific density capture.',
        consequence='884736 core values exceed the fixed 57600 buffer; append fails by source logic before steady iteration.',
        evidence=[locator(CASE/'src/mrp_observer.h','static constexpr std::size_t count = 57600;'),
                  locator(CASE/'src/mrp_observer.h','require(ordinal<count'),
                  locator(CASE/'src/urv_reference.cpp','mrp::DensityCapture capture(')]),
      dict(id='C02',status='INCOMPATIBLE_BY_DESIGN',issue='Current source revision acceptance explicitly limits A1 to S0.',
        consequence='Changing the release stage to S1 cannot authorize the existing A1 source.',
        evidence=[locator(CHECKER/'analysis/revision.py',"bound.get('stage')=='S0_REGRESSION'")]),
      dict(id='C03',status='INCOMPATIBLE_BY_DESIGN',issue='S0 controller pins stage, exact H75 run IDs and 3600 s cap.',
        consequence='It must not be renamed/reused as an S1 launcher; original S1 cap is 14400 s.',
        evidence=[locator(CASE/'scripts/run_S0_A1.py',"data['stage'] == 'S0_REGRESSION'"),
                  locator(CASE/'scripts/run_S0_A1.py','URV1_H75_P_dx5_a100000'),
                  locator(CASE/'scripts/run_S0_A1.py','solver_wall_cap_seconds_per_case=3600')]),
      dict(id='C04',status='NOT_APPLICABLE_TO_S1_AS_WRITTEN',issue='MRP replay schedule/geometry and history comparisons are h75-specific.',
        consequence='Do not impose S0 190-point history or fabricate same-geometry baselines for S1; use separately scoped S1 acceptance.',
        evidence=[locator(CHECKER/'analysis/mass_capture.py','len(rows)==len(expected)==57600'),
                  locator(CHECKER/'analysis/check_mass_repair.py',"h75_regression_references")]),
      dict(id='C05',status='MISSING_S1_PREPARATION_EVIDENCE',issue='Existing describe templates and h75 zero-step audit do not supply S1 native installation evidence or final bindings.',
        consequence='No adopted S1 implementation, new build/provenance, native two-direction zero-step audit, actual IDs or execution release yet.',
        evidence=[locator(CASE/'scripts/audit_A1_zero.py',"int(result['fluid_nodes'])==57600"),
                  locator(ORIGINAL/'describe_only_templates'/ (selected[0]['planned_case_id']+'.txt'),'output_directory=NOT_AN_EXECUTION_DIRECTORY')])]
    save('compatibility_findings.json',dict(scope='S1 against current S0/A1 artifacts; intentional stage boundaries are not evidence contradictions',
        overall='NOT_COMPATIBLE_FOR_DIRECT_LAUNCH',findings=findings,
        F04='OPEN: future cross-stage aggregation still needs per-run release/SHA; no blocker to standalone S1 per-run acceptance',
        new_instruction_or_evidence_contradiction=False,new_Astra_ruling_invoked=False))
    for path in sources:
        digest=sha(path)
        assert str(path) not in protected or protected[str(path)]==digest
        protected[str(path)]=digest
    save('protected_inputs_before.json',protected)
    for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
        with (OUT/('before_'+name)).open('xb') as stream:stream.write((ROOT/'docs/reports'/name).read_bytes())
    save('source_manifest.json',dict(verified_by='AI-assisted actual source reads and arithmetic only; no native run or human scientific signoff',
        sources={str(path):sha(path) for path in sources}))
    save('scope_review.json',dict(user_instruction_verbatim='另定范围后，审核 S1 光滑基准的运行前材料与合同兼容性。',
        interpretation='Current authorization is material/contract review only. Proposed future implementation remains separate; formal launch not authorized.',
        reviewed_stage='S1_SMOOTH_THIN',planned_case_ids=[row['planned_case_id'] for row in selected],
        actual_run_ids=[],simulation_authorized=False,build_authorized_this_task=False,
        native_zero_step_authorized_this_task=False,formal_run_authorized=False,
        new_solver_or_checker_implementation_authorized=False,
        scientific_threshold_changes_authorized=False,S0_accepted_pair_unchanged=True))
    print(json.dumps(dict(cases=2,nodes=884736,wall_links=368640,window=2592,cap=27648,
        K_m3=calculations[0]['analytic_K_m3'],single_distribution_MiB=calculations[0]['single_distribution_MiB'],
        native_calls=0,protected_files=len(protected),direct_launch_compatible=False)))


if __name__ == '__main__':
    main()
