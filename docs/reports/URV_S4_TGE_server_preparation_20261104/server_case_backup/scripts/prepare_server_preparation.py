"""Build the server-lineage preparation seal.  Never runs the solver or the reader.

Usage (on the server):
    python3 -B CASE/unseen_v2_reference_S4_tge_server_v1/scripts/prepare_server_preparation.py
    python3 -B ... --check          # verify an existing seal, execute nothing

The seal is written LAST and does not bind itself; the sidecar binds it.
"""
from pathlib import Path
import argparse, json, os, re, shlex, subprocess, sys

CASE = Path(__file__).resolve().parents[1]
ROOT = CASE.parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S4_tge_server_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))

import server_stage as s  # noqa: E402
from evidence import need, sha  # noqa: E402

S1 = CASE.parent / 'unseen_v2_reference_S1_a1_v1'
BIN = S1 / 'build/urv_reference'
DEP = S1 / 'build/urv_reference.d'
OLB = Path.home() / 'openlb'
SYS_INCLUDE = Path('/usr/lib/x86_64-linux-gnu/openmpi/include')
EV = CASE / 'evidence'
SEAL = EV / 'preparation_S.json'
FRAME = '0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8'


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def sh(cmd):
    r = run(['bash', '-c', cmd])
    return (r.stdout + r.stderr).strip()


def write_new(path, text):
    path = Path(path)
    need(not path.exists(), 'refusing to overwrite ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def config_text(mode, run_id, out, dx_nm):
    need(mode in ('steady', 'describe', 'precheck', 'initialize'), 'bad mode')
    return '\n'.join(['mode=' + mode, 'run_id=' + run_id, 'output_directory=' + str(out),
                      'direction=T', 'dx_nm=' + dx_nm, 'h_nm=30.0', 'd_nm=80.0', 'w_nm=120',
                      'period_nm=240', 'Ly_nm=240', 'nu_m2_s=1e-06',
                      'acceleration_m_s2=100000', 'window_tstar=0.75',
                      'max_time_H_diffusion=8', 'frame_tstar=' + FRAME, ''])


def dependencies():
    """Resolve the compiler dependency file into concrete source/header paths."""
    text = DEP.read_text().replace('\\\n', ' ')
    body = text.split(':', 1)[1]
    out = set()
    for token in body.split():
        if token.startswith('/'):
            cand = [Path(token)]
        else:
            cand = [S1 / 'build' / token, S1 / 'src' / token]
        for p in cand:
            if p.is_file():
                out.add(str(p.resolve()))
                break
    return sorted(out)


def capture_build_environment():
    need(BIN.is_file(), 'native binary missing; build it first')
    ldd = run(['ldd', str(BIN)])
    need(ldd.returncode == 0 and 'not found' not in ldd.stdout,
         'native binary has missing shared libraries')
    status = run(['git', '-C', str(OLB), 'status', '--porcelain']).stdout.strip().splitlines()
    # Only the paths that can influence the build matter here.  examples/, doc/ and
    # tests/ were deliberately not transferred, so git reports them as deleted; that
    # is a transfer choice, not a source edit.
    build_paths = ('src/', 'config.mk', 'Makefile', 'rules.mk', 'external/')
    dirty = sorted(line for line in status
                   if any(f in line for f in build_paths)
                   and not re.search(r'(^|/)build/|(^|/)external/lib/|config\.mk\.bak', line))
    excluded = sorted({line.split()[-1].split('/')[0] for line in status
                       if line.strip().startswith(' D') or line.strip().startswith('D ')})
    sources = sorted(str(p) for p in (S1 / 'src').glob('*') if p.is_file())
    deps = dependencies()
    return dict(
        kind='SERVER_BUILD_CAPTURE', captured_at=s.now(),
        host=run(['hostname']).stdout.strip(),
        os_release={k: v.strip('"') for k, v in
                    (line.split('=', 1) for line in
                     Path('/etc/os-release').read_text().splitlines() if '=' in line)},
        kernel=os.uname().release,
        cpu_model=next((line.split(':', 1)[1].strip() for line in
                        Path('/proc/cpuinfo').read_text().splitlines()
                        if line.startswith('model name')), None),
        cpu_count=os.cpu_count(),
        compiler_gxx=run(['g++', '--version']).stdout.splitlines()[0],
        compiler_mpi=run(['mpic++', '--version']).stdout.splitlines()[0],
        mpi_showme=run(['mpic++', '--showme']).stdout.strip(),
        openlb_root=str(OLB),
        openlb_commit=run(['git', '-C', str(OLB), 'rev-parse', 'HEAD']).stdout.strip(),
        openlb_config_mk_sha256=sha(OLB / 'config.mk'),
        openlb_build_relevant_dirty=dirty,
        openlb_excluded_from_transfer=excluded,
        openlb_dirty_note='src/, config.mk, Makefile, rules.mk and external/ are unmodified relative to the '
                          'recorded commit; build/ and external/lib/ are untracked build outputs; the excluded '
                          'directories were never transferred, which is why git lists them as deleted',
        compile_working_directory=str(S1 / 'src'),
        compile_command=sh('cd %s/src && make -B -n OLB_ROOT=%s 2>/dev/null | grep -m1 "\\-c urv_reference.cpp" || true'
                           % (shlex.quote(str(S1)), shlex.quote(str(OLB)))),
        link_command=sh('cd %s/src && make -B -n OLB_ROOT=%s 2>/dev/null | grep -m1 "\\-o ../build/urv_reference " || true'
                        % (shlex.quote(str(S1)), shlex.quote(str(OLB)))),
        binary_path=str(BIN), binary_sha256=sha(BIN),
        native_sources={str(p): sha(p) for p in sources},
        build_recipe_path=str(S1 / 'src/Makefile'),
        build_recipe_sha256=sha(S1 / 'src/Makefile'),
        dependency_file=str(DEP), dependency_sha256=sha(DEP),
        dependency_headers={p: sha(p) for p in deps},
        dependency_header_count=len(deps),
        ldd=ldd.stdout,
        core_library_sha256=sha(OLB / 'build/lib/libolbcore.a'),
        embedded_libs={n: sha(OLB / 'external/lib' / n)
                       for n in ('libz.a', 'libtinyxml2.a')},
        preparation_only_build=False,
        solver_invoked_by_build_script=False,
        note='Captured on the server itself. The local build is a different ELF and is NOT reused.')


def build_inputs():
    """Every file the seal covers, keyed by path relative to the project root."""
    inputs = {}
    skip = {SEAL, EV / (SEAL.name + '.sha256')}
    for base in (CASE, CHECKER):
        for p in sorted(base.rglob('*')):
            if p.is_file() and p not in skip and '__pycache__' not in p.parts:
                inputs[s.key_for(p.resolve())] = sha(p)
    extra = sorted((S1 / 'src').glob('*')) + [BIN, DEP, S1 / 'src/Makefile',
                                              OLB / 'Makefile', OLB / 'rules.mk',
                                              OLB / 'config.mk', OLB / 'build/lib/libolbcore.a',
                                              OLB / 'external/lib/libz.a',
                                              OLB / 'external/lib/libtinyxml2.a']
    for p in extra:
        if p.is_file():
            inputs[s.key_for(p.resolve())] = sha(p)
    for p in dependencies():
        inputs[s.key_for(Path(p))] = sha(p)
    return inputs


def prepare():
    need(not SEAL.exists(), 'seal already exists; remove it before re-preparing')
    EV.mkdir(parents=True, exist_ok=True)

    env = capture_build_environment()
    write_new(EV / 'build_environment.json', json.dumps(env, indent=2, ensure_ascii=False) + '\n')
    write_new(EV / 'ldd_at_preparation.txt', env['ldd'])
    (EV / 'build_environment.json.sha256').write_text(sha(EV / 'build_environment.json') + '\n')

    formal = []
    for run_id, case_id, dx in ((s.RUN_1P25, s.CASE_1P25, '1.25'),
                                (s.RUN_0P625, s.CASE_0P625, '0.625')):
        out = CASE / 'runs' / run_id / 'steady'
        write_new(out / 'run_config.txt', config_text('steady', run_id, out, dx))
        write_new(out / 'run_manifest.txt', 'run_id=%s\nmode=steady\n' % run_id)
        formal.append(dict(run_id=run_id, planned_case_id=case_id, mode='steady',
                           output_directory=str(out),
                           run_config_path=str(out / 'run_config.txt')))

    zeros = []
    for mode in s.MODES:
        run_id = 'ZERO_' + s.AUDIT_ID + '_' + mode
        out = CASE / 'audits' / s.AUDIT_ID / s.CASE_0P625 / mode
        write_new(out / 'run_config.txt', config_text(mode, run_id, out, '0.625'))
        write_new(out / 'run_manifest.txt', 'run_id=%s\nmode=%s\n' % (run_id, mode))
        zeros.append(dict(run_id=run_id, planned_case_id=s.CASE_0P625, mode=mode,
                          output_directory=str(out),
                          run_config_path=str(out / 'run_config.txt')))

    write_new(CASE / 'common/server_zero_resources.json', json.dumps(dict(
        kind='PROPOSED_NOT_ADOPTED_SERVER_RESOURCE_PROPOSAL',
        user_explicitly_authorized=False, resource_decision_accepted=False,
        resources=s.SERVER_RESOURCES,
        rationale=['the local 8 GiB per-process cap failed with std::bad_alloc at 16,515,072 fluid nodes',
                   'this host has 188 GiB total, so the cap is set high enough that the audit measures '
                   'real usage instead of failing on the cap',
                   'no measured peak exists for this grid; these figures are not measurements']),
        indent=2, ensure_ascii=False) + '\n')

    inputs = build_inputs()
    prepared = dict(
        protocol_id='URV-v1', schema_version='S4-TGE-SERVER-1',
        stage=s.STAGE, revision=s.REVISION, root=str(ROOT),
        external_roots=[str(OLB), str(SYS_INCLUDE)],
        kind='S4_TGE_SERVER_PREPARATION_NOT_AUTHORIZATION',
        simulation_authorized=False, formal_simulation_authorized=False,
        native_zero_step_authorized=False, initial_field_readback_authorized=False,
        performance_time_stepping_authorized=False, automatic_retry_authorized=False,
        automatic_extension_authorized=False, S5_authorized=False,
        prepared_runs=[dict(r, run_config_sha256=inputs[s.key_for(Path(r['run_config_path']))])
                       for r in formal],
        zero_prepared_runs=[dict(r, run_config_sha256=inputs[s.key_for(Path(r['run_config_path']))])
                            for r in zeros],
        approved_run_ids=[], approved_runs=[], approved_audit_run_ids=[],
        actual_audit_run_ids=[], actual_formal_run_ids=[],
        original_S4_stage_accepted=False,
        proposed_grid_nm=[2.5, 1.25, 0.625], original_grid_nm=[5, 2.5, 1.25],
        baseline_reference=dict(
            local_run_id='URV_S4_T_dx1p25_reuse_v1_20261103_01',
            local_completion_sha256=s.LOCAL_1P25_COMPLETION,
            local_K_m3=s.LOCAL_1P25_K,
            server_run_id=s.RUN_1P25,
            requirement='the server rerun must reproduce the local K within the declared tolerance'),
        lineage=dict(
            kind='CROSS_BUILD_LINEAGE_REFERENCE',
            local_preparation_A_sha256=s.LOCAL_A_SHA,
            local_1p25_run_id='URV_S4_T_dx1p25_reuse_v1_20261103_01',
            local_1p25_completion_sha256=s.LOCAL_1P25_COMPLETION,
            local_1p25_K_m3=s.LOCAL_1P25_K,
            local_transverse_medium_fine_change=s.LOCAL_T_MEDIUM_FINE,
            local_transverse_grid_pass=False,
            build_equivalence_criterion=dict(
                source_run_id='URV_S4_T_dx1p25_reuse_v1_20261103_01',
                reference_K_m3=s.LOCAL_1P25_K,
                relative_tolerance=s.BUILD_EQUIVALENCE_RTOL,
                applies_to_run_id=s.RUN_1P25,
                declared_before_measurement=True,
                on_failure='STOP; the two builds are not interchangeable and the 0.625 supplement '
                           'cannot be paired with the original 5/2.5 nm points'),
            note='The local build produced the accepted 5/2.5/1.25 nm points. This server build is a '
                 'different ELF (-march=native, different CPU). Its 1.25 nm rerun must reproduce the '
                 'local K within the declared tolerance before its 0.625 nm result can be used.'),
        provenance=dict(native_binary=str(BIN), native_sources=sorted(env['native_sources']),
                        build_recipe=env['build_recipe_path'],
                        build_environment=str(EV / 'build_environment.json'),
                        dependency_file=str(DEP),
                        ldd_record=str(EV / 'ldd_at_preparation.txt')),
        reader_path=str(CHECKER / 'analysis/read_fields.py'),
        zero_resource_proposal=s.SERVER_RESOURCES,
        formal_solver_wall_cap_seconds=None, formal_checker_cap_seconds=None,
        NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=None,
        reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED', submission_ready=False,
        next_stage_started=False, zero_audit_status='NOT_EXECUTED',
        performance_status='NOT_IMPLEMENTED_NOT_AUTHORIZED',
        formal_interface_status='NOT_IMPLEMENTED_BUDGET_PENDING',
        AI_may_start_solver=False, user_manually_starts=True,
        external_history_independently_verified=False,
        author_confirmation_scope='author-declared nonuse for h60/d80 and h30/d80 only; '
                                  'no external independent audit',
        inputs_sha256=inputs)

    write_new(SEAL, json.dumps(prepared, indent=2, ensure_ascii=False) + '\n')
    digest = sha(SEAL)
    (EV / (SEAL.name + '.sha256')).write_text(digest + '\n')
    print(json.dumps(dict(seal=str(SEAL), sha256=digest, inputs=len(inputs),
                          native_elf=env['binary_sha256'],
                          dependency_headers=env['dependency_header_count'],
                          formal_runs=[r['run_id'] for r in formal],
                          zero_runs=[r['run_id'] for r in zeros]), indent=2))


def check():
    digest = (EV / (SEAL.name + '.sha256')).read_text().strip()
    bound = s.verify_seal(SEAL, digest)
    s.require_pristine(bound)
    print(json.dumps(s.static_summary(bound), indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    if args.check:
        check()
    else:
        prepare()
