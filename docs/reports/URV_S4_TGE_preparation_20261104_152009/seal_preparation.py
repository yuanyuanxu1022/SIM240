"""Single-use preparation A seal. No native, VTK, PERF or formal execution."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_tge_v1';CHECKER=ROOT/'CASE/unseen_v2_reference_checker_S4_tge_v1'
sys.path.insert(0,str(CHECKER/'analysis'))
import tge_stage as s
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
def save(p,v):
    with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
protected=load(OUT/'protected_old_files.json');assert all(sha(p)==h for p,h in protected.items())
tests=load(OUT/'software_tests.json');assert tests['exit_code']==0 and tests['test_methods']==15 and tests['native_calls']==tests['VTK_calls']==0
inputs=dict(protected)
for tree in [CASE/'scripts',CASE/'common',CASE/'evidence',CHECKER]:
    for p in tree.rglob('*'):
        if p.is_file():
            assert '__pycache__' not in p.parts and not p.is_symlink()
            inputs[str(p.resolve())]=sha(p)
for p in [CASE/'README.md',CASE/'PROTOCOL.md',OUT/'prepare_materials.py',OUT/'review_intake.json',
          OUT/'review_intake_validation.json',OUT/'materialization_audit.json',OUT/'software_tests.log',OUT/'software_tests.json']:
    inputs[str(p)]=sha(p)
candidate=load(OUT/'candidate_preparation.json')
for rec in candidate['prepared_runs']+candidate['zero_prepared_runs']:
    for p in Path(rec['output_directory']).iterdir():inputs[str(p)]=sha(p)
candidate['inputs_sha256']=inputs
s.unchanged(candidate);s.validate_plan(candidate);s.verify_history(candidate);s.require_pristine(candidate)
syntax=[]
for p in [*list((CASE/'scripts').glob('*.py')),*list((CHECKER/'analysis').glob('*.py')),*list((CHECKER/'tests').glob('*.py'))]:
    compile(p.read_text(),str(p),'exec');syntax.append(str(p))
inspect_ast=ast.parse((CASE/'scripts/inspect_preparation.py').read_text())
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and
    (getattr(n,'module','')=='subprocess' or any(a.name=='subprocess' for a in getattr(n,'names',[]))) for n in ast.walk(inspect_ast))
path=CASE/'evidence/preparation_A.json';save(path,candidate)
with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')
verified=s.verify_seal(path,sha(path));s.require_pristine(verified)
save(OUT/'seal_verification.json',dict(preparation_A_path=str(path),preparation_A_sha256=sha(path),
    inputs_bound=len(inputs),all_input_hashes_match=True,source_history_verified=True,
    all_execution_permissions_closed=all(verified[k] is False for k in s.FLAGS),
    syntax_checked_files=syntax,unexecuted_directories_pristine=True,software_tests_pass=15,
    compiler_invocations=0,native_calls=0,VTK_calls=0,performance_advances=0,formal_runs=0))
print(json.dumps(dict(seal=str(path),sha256=sha(path),inputs=len(inputs),native_calls=0,builds=0),indent=2))
