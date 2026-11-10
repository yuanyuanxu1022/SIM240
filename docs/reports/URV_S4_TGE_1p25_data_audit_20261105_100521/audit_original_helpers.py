"""Read-only original diagnostic/slice/grid functions; do not issue acceptance."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np

REPORT=Path(__file__).resolve().parent
REPO=REPORT.parents[2]
PACKAGE=REPO/'outputs/URV_S4_1p25_data_20261104_234955'
RAW=PACKAGE/'01_raw_server/steady'
CHECKER=REPO/'CASE/unseen_v2_reference_checker_S4_reuse_v1'
prepared=json.loads((REPO/'CASE/unseen_v2_reference_S4_tge_v1/evidence/preparation_A.json').read_text())
assert hashlib.sha256((REPO/'CASE/unseen_v2_reference_S4_tge_v1/evidence/preparation_A.json').read_bytes()).hexdigest()=='53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9'
inputs={}
for relative in ['analysis/check_results.py','analysis/evidence.py','analysis/contracts.py','common/acceptance_spec.json']:
    path=CHECKER/relative
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert prepared['inputs_sha256'][str(path)]==digest
    inputs[str(path)]=digest
sys.path.insert(0,str(CHECKER/'analysis'))
from check_results import diagnostics,check_slice
from evidence import kv,grid_estimate
cfg=kv(RAW/'run_config.txt');result=kv(RAW/'result.txt')
with (RAW/'diagnostics.csv').open() as f:
    rows=list(csv.DictReader(f))
data={key:np.array([float(r[key]) for r in rows]) for key in rows[0]}
scalar=diagnostics(cfg,result,data)
smooth=check_slice(RAW,cfg,scalar['K_m3'])
slice_data=np.genfromtxt(RAW/'field_slice.csv',delimiter=',',names=True)
K_slice=float(cfg['nu_m2_s'])*float(slice_data['ux'].sum())*(float(cfg['dx_nm'])*1e-9)**2/(float(cfg['period_nm'])*1e-9*float(cfg['acceleration_m_s2']))
grid=json.loads((PACKAGE/'04_local_reference/local_S4_grid_report.json').read_text())
transverse=next(d for d in grid['directions'] if d['direction']=='T')
k=transverse['K_m3']
estimate=grid_estimate(*k,scalar['final_span'])
assert estimate['REFERENCE_QUALIFIED_FOR_CASE'] is False
assert estimate['medium_fine_change']==transverse['grid_estimate']['medium_fine_change']
assert abs(estimate['GCI_fine_estimate']-transverse['grid_estimate']['GCI_fine_estimate'])<1e-15
out=dict(frozen_helper_input_hashes=inputs,diagnostic_helpers_PASS=True,diagnostic_scalars=scalar,
         slice_checks_PASS=True,slice_rows=len(slice_data),slice_K_m3=K_slice,
         slice_K_relative_to_volume=K_slice/scalar['K_m3']-1,
         smooth_analytic_check=smooth,smooth_analytic_check_applicability='NOT_APPLICABLE_GROOVED_GEOMETRY',
         original_transverse_grid_estimate=estimate,
         old_grid_FAIL_preserved=True,RESULT_PASS_not_modified=True,
         whole_acceptance_CLI_called=False,solver_calls=0)
(REPORT/'original_helper_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(diagnostic_helpers_PASS=True,slice_PASS=True,slice_K_m3=K_slice,
                     slice_relative_difference=out['slice_K_relative_to_volume'],
                     original_grid_PASS=False,grid_change=estimate['medium_fine_change']),indent=2))
