"""F01 output isolation and F03 mandatory provenance/identity checks.

Reads captured build records; never builds or executes a native program.
The caller-supplied release SHA remains the external trust anchor. Arithmetic
and physical acceptance limits are defined exclusively in the unchanged spec.
"""
from pathlib import Path
import json
import re
import shlex
from evidence import need,sha,kv,rows

CASE=Path(__file__).resolve().parents[1]
ORIGINAL=CASE.parent/'unseen_v2_reference_v1'

def release_inputs(release):
    """Collect protection declarations completely, or fail before any writes.

    This is structural path validation, not execution authorization. Incomplete
    declarations must never discard protection already known from other entries.
    """
    try:
        document=json.loads(Path(release).read_text())
        need(isinstance(document,dict), 'release declarations must be an object')
        inputs=document.get('inputs_sha256',{})
        records=document.get('approved_runs',[])
        references=document.get('h75_regression_references',{})
        need(isinstance(inputs,dict), 'input path declarations must be an object')
        need(isinstance(records,list), 'run path declarations must be a list')
        need(isinstance(references,dict), 'reference path declarations must be an object')
        paths=list(inputs)
        for record in records:
            need(isinstance(record,dict) and 'output_directory' in record,
                 'incomplete run output declaration')
            paths.append(record['output_directory'])
        for record in references.values():
            need(isinstance(record,dict) and 'directory' in record,
                 'incomplete reference directory declaration')
            paths.append(record['directory'])
        need(all(isinstance(p,str) and p.strip() and '\x00' not in p for p in paths),
             'invalid protected path declaration')
        return paths
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as error:
        need(False, 'cannot parse release protection declarations: '+str(error))

def time_stepping_defines(command):
    """Normalize joined/split -D and -U for the exact preparation macro."""
    flags=shlex.split(command);definitions=[];index=0
    while index<len(flags):
        flag=flags[index];index+=1
        if flag in ('-D','-U'):
            need(index<len(flags) and not flags[index].startswith('-'),
                 'macro option has no argument')
            option=flag;value=flags[index];index+=1
        elif flag.startswith(('-D','-U')):
            option=flag[:2];value=flag[2:]
        else:
            continue
        name=re.match(r'[A-Za-z_]\w*',value)
        if name and name.group(0)=='URV_PREPARATION_ONLY':
            definitions.append((option,value))
    return definitions

def output_location(output, runs, extra_inputs=(), require_new=True):
    output=Path(output).resolve()
    protected=[Path(p).resolve() for p in [*runs,ORIGINAL,CASE,*extra_inputs]]
    for p in protected:
        need(not (output==p or output.is_relative_to(p) or p.is_relative_to(output)),
             'analysis output overlaps protected input: '+str(p))
    if require_new:need(not output.exists(), 'analysis output already exists; refusing all writes')
    else:need(output.is_dir(), 'owned analysis output missing')
    return output

def absolute_file(value):
    p=Path(value)
    need(p.is_absolute() and p.is_file(), 'required provenance file missing or not absolute: '+str(p))
    need(str(p)==str(p.resolve()), 'provenance file must use canonical path: '+str(p))
    return p

def covered(path, inputs):
    p=absolute_file(path)
    need(str(p) in inputs, 'required provenance not bound: '+str(p))
    need(sha(p)==inputs[str(p)], 'required provenance hash mismatch: '+str(p))
    return p

def dependency_paths(path, directory):
    # Read the first compiler-generated Make rule; ignore subsequent -MP rules.
    line=path.read_text().replace('\\\n',' ').splitlines()[0]
    need(':' in line, 'invalid compiler dependency rule')
    files=[]
    for token in shlex.split(line.split(':',1)[1]):
        p=Path(token)
        if not p.is_absolute():p=directory/p
        files.append(str(p.resolve()))
    need(files, 'empty compiler dependency closure')
    return set(files)

def verify_provenance(bound, checker_case=CASE):
    inputs=bound['inputs_sha256']
    need(bound.get('schema_version')=='URV-EXEC-1.1', 'execution schema URV-EXEC-1.1 required')
    roles=bound.get('provenance')
    need(isinstance(roles,dict), 'required provenance roles missing')
    required={'native_binary','native_sources','build_recipe','build_environment','dependency_file','ldd_record'}
    need(required<=set(roles), 'required provenance roles incomplete')
    for key in required-{'native_sources'}:covered(roles[key],inputs)
    need(isinstance(roles['native_sources'],list) and roles['native_sources'], 'native source role empty')
    native={str(covered(p,inputs)) for p in roles['native_sources']}
    environment=json.loads(Path(roles['build_environment']).read_text())
    need(environment['compile_exit_code']==0 and environment['preparation_only_build'] is False,
         'formal build capture required; preparation build cannot pass')
    need(environment['binary_path']==roles['native_binary'] and environment['binary_sha256']==inputs[roles['native_binary']],
         'native binary/build capture mismatch')
    need(environment['build_recipe_path']==roles['build_recipe'] and environment['build_recipe_sha256']==inputs[roles['build_recipe']],
         'build recipe capture mismatch')
    defines=time_stepping_defines(environment['compile_command'])
    need(defines==[('-D','URV_PREPARATION_ONLY=0')], 'time-stepping build flag missing or ambiguous')
    sources=environment['native_sources_sha256']
    need(set(sources)==native and all(inputs.get(p)==s for p,s in sources.items()), 'native source coverage mismatch')
    # The v1.1 checker is limited to this physical kernel. Do not silently accept
    # physics edits while repairing provenance. Source copies may change paths.
    anchor=json.loads((checker_case/'common/source_preparation_anchor.json').read_text())
    need(sha(anchor['preparation_seal'])==anchor['preparation_seal_sha256'], 'original preparation seal changed')
    expected=anchor['native_source_sha256']
    observed={Path(p).name:s for p,s in sources.items()}
    if observed != expected:
        if bound.get('source_revision', {}).get('id') == 'URV-S3-S1-ELF-REUSE-v1':
            from revision_s3_reuse import verify_s3_reuse
            verify_s3_reuse(bound, observed, checker_case)
        elif bound.get('source_revision', {}).get('id') == 'URV-S2-S1-ELF-REUSE-v1':
            from revision_s2_reuse import verify_s2_reuse
            verify_s2_reuse(bound, observed, checker_case)
        elif bound.get('source_revision', {}).get('id') == 'URV-S1-A1-v1':
            from revision_s1 import verify_s1_revision
            verify_s1_revision(bound, observed, checker_case)
        else:
            need(bound.get('source_revision', {}).get('id')=='URV-MRP-v1',
                 'native physical source differs from preparation anchor')
            from revision import verify_revision
            verify_revision(bound, observed, checker_case)
            revision_anchor=json.loads((checker_case/'revision/revision_anchor.json').read_text())
            need(revision_anchor.get('instruction_audit_status')=='PASS',
                 'MRP source revision static instruction audit not passed; HOLD')
    need(environment['dependency_file_path']==roles['dependency_file'], 'dependency capture path mismatch')
    directory=Path(environment['compile_working_directory'])
    need(directory.is_absolute(), 'compile working directory must be absolute')
    actual=dependency_paths(Path(roles['dependency_file']),directory)
    deps=environment['dependency_sha256']
    need(actual<=set(deps) and native<=actual, 'compiler dependency closure incomplete')
    libraries=environment['link_library_sha256']
    need(isinstance(libraries,dict) and libraries, 'link library closure empty')
    need(any(Path(p).name=='libolbcore.a' for p in libraries), 'OpenLB core library not captured')
    runtime={}
    for line in Path(roles['ldd_record']).read_text().splitlines():
        need('not found' not in line, 'unresolved runtime library')
        hit=re.search(r'(/[^\s]+)',line)
        if hit:runtime[str(Path(hit.group(1)).resolve())]=None
    need(runtime and set(runtime)==set(environment['dynamic_library_sha256']), 'runtime library closure incomplete')
    all_libraries=[Path(p).name for p in [*libraries,*runtime]]
    for name in ['olbcore','z','tinyxml2']:
        need(any(p=='lib'+name+'.a' or p=='lib'+name+'.so' or p.startswith('lib'+name+'.so.') for p in all_libraries),
             'required linked library not captured: '+name)
    for mapping in [deps,libraries,environment['dynamic_library_sha256']]:
        for path,digest in mapping.items():
            covered(path,inputs)
            need(inputs[path]==digest, 'build/library capture hash mismatch: '+path)
    compiler=covered(environment['compiler_executable'],inputs)
    need(inputs[str(compiler)]==environment['compiler_sha256'], 'compiler capture mismatch')
    for folder in ['analysis','common']:
        for p in (checker_case/folder).glob('*'):
            if p.is_file():covered(str(p.resolve()),inputs)
    return roles

def approved_records(bound, checker_case=CASE):
    records=bound.get('approved_runs')
    need(isinstance(records,list) and records, 'explicit per-run identity bindings required')
    ids=bound['approved_run_ids']
    need(isinstance(ids,list) and len(ids)==len(set(ids)), 'duplicate approved run ID')
    need(len(records)==len(ids) and {r['run_id'] for r in records}==set(ids), 'approved run map incomplete or duplicate')
    configs=[];outputs=[];cases=[]
    matrix={r['planned_case_id']:r for r in rows(checker_case/'common/case_matrix.csv')}
    protocol=json.loads((checker_case/'common/protocol.json').read_text())
    stage=bound.get('stage')
    need(stage in protocol['stages'], 'single frozen stage required')
    for r in records:
        need(r['planned_case_id'] in matrix, 'approved case not in frozen matrix')
        row=matrix[r['planned_case_id']]
        need(row['stage']==stage, 'cross-stage authorization is not allowed')
        cfgpath=covered(r['run_config_path'],bound['inputs_sha256'])
        need(bound['inputs_sha256'][str(cfgpath)]==r['run_config_sha256'], 'approved config SHA mismatch')
        cfg=kv(cfgpath);output=Path(r['output_directory'])
        need(output.is_absolute() and str(output)==str(output.resolve()), 'run output path not canonical')
        need(cfg['mode']=='steady' and cfg['run_id']==r['run_id'] and cfg['output_directory']==str(output), 'approved config identity/directory mismatch')
        need(cfg['direction']==row['direction'], 'approved config direction mismatch')
        for key,mkey in [('h_nm','h_nm'),('d_nm','d_nm'),('w_nm','w_nm'),('period_nm','P_nm'),('Ly_nm','Ly_nm'),('dx_nm','dx_nm'),('nu_m2_s','nu_m2_s'),('acceleration_m_s2','acceleration_m_s2')]:
            need(float(cfg[key])==float(row[mkey]), 'approved physics mismatch: '+key)
        need(float(cfg['window_tstar'])==.75 and float(cfg['max_time_H_diffusion'])==8, 'approved observation time changed')
        need([float(v) for v in cfg['frame_tstar'].split(',')]==protocol['time']['frame_tstar'], 'approved frame plan changed')
        configs.append(str(cfgpath));outputs.append(str(output));cases.append(r['planned_case_id'])
    need(len(set(configs))==len(configs) and len(set(outputs))==len(outputs) and len(set(cases))==len(cases), 'per-run config/directory/case reused')
    for i,a in enumerate(outputs):
        for b in outputs[i+1:]:need(not(Path(a).is_relative_to(b) or Path(b).is_relative_to(a)), 'nested run output directories')
    # A completed run writes run_config.txt as the exact approved file, not a
    # copied and edited equivalent. The raw config path belongs in the release.
    need(all(Path(r['run_config_path'])==Path(r['output_directory'])/'run_config.txt' for r in records), 'approved config must be the raw run config')
    return {r['run_id']:r for r in records}

def check_run_identity(bound, run, config_path, run_id, case_id):
    record=next((r for r in bound['approved_runs'] if r['run_id']==run_id),None)
    need(record is not None, 'run not individually bound')
    need(record['planned_case_id']==case_id, 'run-to-case binding mismatch')
    need(str(run.resolve())==record['output_directory'], 'run output directory binding mismatch')
    need(str(config_path.resolve())==record['run_config_path'] and sha(config_path)==record['run_config_sha256'],
         'run config identity/hash binding mismatch')
