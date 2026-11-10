"""Standard-library-only source/provenance and delivery checks; no field loading."""
import ast
import hashlib
import json
from pathlib import Path
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CODE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_preparation_20261026'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def read(p):return json.loads(p.read_text())

def main():
    manifest=read(OUT/'source_manifest.json')
    for group,files in manifest.items():
        for p,h in files.items():assert sha(ROOT/p)==h,p
    result=read(OUT/'fixture_results.json')
    assert result['status']=='SYNTHETIC_FIXTURES_PASS' and result['tests_run']==17
    assert result['failures']==result['errors']==result['skipped']==0
    for p,h in result['code_sha256'].items():assert sha(ROOT/p)==h,p
    for p in CODE.glob('*.py'):ast.parse(p.read_text())
    tree=ast.parse((CODE/'extractor.py').read_text())
    flag=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='REAL_RECORD_EXTRACTION_ENABLED' for x in n.targets)]
    assert len(flag)==1 and ast.literal_eval(flag[0].value) is False
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='extract_real_record')
    assert isinstance(fn.body[0],ast.If) and isinstance(fn.body[0].body[0],ast.Raise)
    for name in ('REPORT.md','EXTRACTOR_SPEC.md'):
        txt=(OUT/name).read_text();width=None
        for link in re.findall(r'\]\(([^)]+)\)',txt):
            if not link.startswith('http') and link!='verification.json':assert (OUT/link).is_file(),link
        for line in txt.splitlines():
            if line.startswith('|'):
                count=len(re.findall(r'(?<!\\)\|',line))
                if width is None:width=count
                assert count==width,(name,line)
            else:width=None
    freeze=ROOT/'docs/reports/Correlation_selection_freeze_20261024'
    g4=read(freeze/'candidate_lock.json')
    for p,h in g4['bound_files'].items():assert sha(freeze/p)==h,p
    data=dict(status='STATIC_PREPARATION_AUDIT_PASS',source_groups={k:len(v) for k,v in manifest.items()},
              G4_bound_files_unchanged=len(g4['bound_files']),all_old_sources_and_N8_records_unchanged=True,
              synthetic_tests=17,synthetic_validation_exit_code=0,real_entry_closed_before_io=True,
              actual_N8_arrays_loaded=False,actual_field_metrics_computed=False,
              actual_adapter_read_branch_executed=False,solver_started=False,backend_imported=False,
              theory_criteria_changed=False,strict_error_bound_established=False,
              NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
              reference_qualified=False,submission_ready=False,prediction_permission='HOLD',
              new_code_files=[str(p.relative_to(ROOT)) for p in sorted(CODE.iterdir()) if p.is_file()])
    (OUT/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
    assert (OUT/'verification.json').is_file()
    print(data['status'],data['source_groups'])

if __name__=='__main__':main()
