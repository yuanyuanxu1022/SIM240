#!/usr/bin/env python3
"""Seal a PREPARATION-ONLY build; cannot authorize or execute formal calculations."""
from pathlib import Path
import ast
import json
import re
import shutil
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from evidence import sha,save,need,kv,rows

CASE=Path(__file__).resolve().parents[1]
PROJECT=CASE.parents[1]
REPORT=PROJECT/'docs/reports/URV_v1_preparation_20261101'

def command(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True)
    return p.stdout.strip()

def main():
    need(not (CASE/'evidence/preparation_seal.json').exists(), 'preparation already sealed')
    base=PROJECT/'CASE/D_series/D4_variable_groove_transport_20261023/src/variable_groove_transport.cpp'
    port=CASE/'src/urv_reference.cpp'
    edits=json.loads((REPORT/'source_port_edits.json').read_text())
    source=port.read_text();restored=source
    for change in reversed(edits['edits']):
        need(restored.count(change['new'])==1,'unlisted source change')
        restored=restored.replace(change['new'],change['old'])
    need(restored==base.read_text(), 'source port no longer reverses exactly')
    zero=CASE/'audits/URV_ZERO_20261101_01'
    audit=json.loads((zero/'verification.json').read_text())
    need(audit['PREPARATION_PASS'] is True and audit['actual_time_steps']==0, 'zero audit incomplete')
    for path,digest in audit['bound_inputs_sha256'].items(): need(sha(path)==digest,'audited source changed '+path)
    for path,digest in json.loads((zero/'audit_files_sha256.json').read_text()).items(): need(sha(path)==digest,'zero evidence changed '+path)
    shutil.copy2(zero/'verification.json',REPORT/'zero_step_verification.json')
    geometries={};reader_count=0
    for record in audit['records']:
        initial=Path(record['modes']['initialize']['output'])
        cfg=kv(initial/'run_config.txt');r=kv(initial/'result.txt');boundary=kv(initial/'boundary_audit.txt')
        reader=json.loads((initial/'field_readback.json').read_text());need(reader['PASS'],'reader failure')
        reader_count+=len(reader['frames'])
        key=','.join(cfg[k] for k in ['h_nm','d_nm','dx_nm'])
        geometries[key]=dict(h_nm=float(cfg['h_nm']),d_nm=float(cfg['d_nm']),dx_nm=float(cfg['dx_nm']),
            fluid_nodes=int(r['fluid_nodes']),installed_links=int(boundary['installed_links']),
            q_min=float(boundary['q_min']),q_max=float(boundary['q_max']),
            initialization_steps=0,independent_geometry=True)
    save(REPORT/'zero_step_summary.json',dict(describe=24,precheck=24,initialize=24,
        actual_VTK_frames_read=reader_count,geometries=list(geometries.values()),
        actual_time_steps=0,steady_attempt_rejected_before_output=True,
        ZERO_STEP_GEOMETRY_PASS=True,formal_solver_started=False))
    # The dependency list comes from this compilation, not a historical build.
    dep=(CASE/'build/urv_reference.d').read_text().replace('\\\n',' ')
    deps=set()
    for token in dep.split(':',1)[1].split():
        if token.endswith(':'): break
        p=Path(token)
        if not p.is_absolute(): p=CASE/'src'/p
        if p.is_file(): deps.add(p.resolve())
    deps.update([Path('/home/dell/openlb/build/lib/libolbcore.a'),
        Path('/home/dell/openlb/external/lib/libz.a'),Path('/home/dell/openlb/external/lib/libtinyxml2.a')])
    dependencies={str(p):sha(p) for p in sorted(deps) if p.is_file()}
    ldd=command(['ldd',str(CASE/'build/urv_reference')]);(REPORT/'ldd.txt').write_text(ldd+'\n')
    dynamic={}
    for line in ldd.splitlines():
        match=re.search(r'(/[^\s]+)',line)
        if match:
            p=Path(match.group(1));dynamic[str(p.resolve())]=sha(p)
    environment=dict(compiler=command(['g++','--version']),mpi_wrapper=command(['mpic++','--showme']),
        openlb_commit=command(['git','-C','/home/dell/openlb','rev-parse','HEAD']),
        openlb_git_status=command(['git','-C','/home/dell/openlb','status','--porcelain']),
        compile_command=next(l for l in (REPORT/'compile_attempt1.log').read_text().splitlines() if ' -c ' in l and l.startswith('mpic++')),
        compiler_executable=str(Path(shutil.which('g++')).resolve()),
        compiler_sha256=sha(Path(shutil.which('g++')).resolve()),
        binary_sha256=sha(CASE/'build/urv_reference'),compile_exit_code=0,
        build_mode='URV_PREPARATION_ONLY=1; native steady rejected',
        dependency_sha256=dependencies,dynamic_library_sha256=dynamic,
        historical_environment_reconstruction_claimed=False)
    save(CASE/'evidence/build_environment.json',environment)
    # Record exact analytic/source sections kept unchanged.
    spans=[('geometry_and_wall', 'T wrapX(T x)', 'template <typename LATTICE, typename GEOMETRY>\nMeasurement measure'),
           ('profile_and_physical_field_export', 'template <typename LATTICE, typename GEOMETRY>\nvoid writeFinalProfiles', '} // namespace'),
           ('initialization_force_collision_parameters', '  AnalyticalConst3D<T, T> one(1.0);','  SuperVTMwriter3D<T> writer'),
           ('original_statistical_window', 'struct FluxWindow {','std::map<std::string,std::string> readConfig')]
    matches={}
    original=base.read_text()
    for name,start,end in spans:
        a=original[original.index(start):original.index(end)];b=source[source.index(start):source.index(end)]
        need(a==b,'physical section changed '+name)
        matches[name]=dict(byte_identical=True,characters=len(a))
    save(REPORT/'physical_port_audit.json',dict(reverse_19_edits_recovers_base=True,
        source_sections=matches,legacy_measurement_preserved=True,
        mass_header_exact_C_copy=sha(CASE/'src/mass_stats.h')==sha(PROJECT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/src/mass_stats.h'),
        solve_path_compiled_but_not_executed=True))
    for p in [*CASE.rglob('*.py')]:
        if 'audits' not in p.parts: ast.parse(p.read_text(),filename=str(p))
    need('Ran 35 tests' in (REPORT/'checker_tests_final.log').read_text() and '\nOK\n' in (REPORT/'checker_tests_final.log').read_text(), 'checker tests not passing')
    inputs={str(p):sha(p) for d in ['src','scripts','analysis','tests','common'] for p in (CASE/d).rglob('*') if p.is_file()}
    inputs.update(dependencies);inputs.update(dynamic)
    for p in [CASE/'build/urv_reference',CASE/'build/test_mass_stats',CASE/'build/test_mass_oracle',
              CASE/'evidence/build_environment.json',REPORT/'physical_port_audit.json']:
        inputs[str(p)]=sha(p)
    seal=dict(protocol_id='URV-v1',kind='PREPARATION_ONLY_NOT_EXECUTION_RELEASE',
        date='2026-11-01',simulation_authorized=False,preparation_only_build=True,
        author_external_data_history_confirmation='PENDING',approved_run_ids=[],
        actual_formal_run_ids=[],inputs_sha256=inputs,
        zero_audit_verification_sha256=sha(zero/'verification.json'),
        zero_audit_directory=str(zero),independent_checker_tests=35,
        compiled=True,zero_steps=True,reference_qualified=False,submission_ready=False)
    save(CASE/'evidence/preparation_seal.json',seal)
    (CASE/'evidence/preparation_seal.sha256').write_text(sha(CASE/'evidence/preparation_seal.json')+'\n')
    print(json.dumps(dict(preparation_sealed=True,input_bindings=len(inputs),
        compilation_dependencies=len(dependencies),dynamic_libraries=len(dynamic),solver_started=False)))

if __name__=='__main__': main()
