#!/usr/bin/env python3
"""Check approved mass errors against saved mass columns, without a solver."""
from pathlib import Path
import csv
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def main():
    p=ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800/diagnostics.csv'
    with p.open() as f:rows=list(csv.DictReader(f))
    m0=float(rows[0]['mass']);c0=float(rows[0]['corrected_mass'])
    corrected=[];legacy=[];agreement=[];err=0.
    for r in rows:
        old=(float(r['mass'])-m0)/m0;new=(float(r['corrected_mass'])-c0)/c0
        agree=abs(new-float(r['delta_mass_error']))
        err=max(err,abs(old-float(r['mass_error'])),abs(new-float(r['corrected_mass_error'])),abs(agree-float(r['mass_ledger_agreement'])))
        assert all(math.isfinite(v) for v in [old,new,agree])
        corrected.append(abs(new));legacy.append(abs(old));agreement.append(agree)
    assert err==0 and max(corrected)<1e-10 and max(agreement)<=1e-13 and max(legacy)>1e-10
    result=dict(rows=len(rows),max_corrected_error_recomputed=max(corrected),max_legacy_error_recomputed=max(legacy),
        max_ledger_agreement_recomputed=max(agreement),max_exported_derived_column_difference=err,
        corrected_mass_gate_PASS=True,legacy_mass_gate_PASS=False,
        source=str(p.relative_to(ROOT)),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),solver_started=False)
    (OUT/'mass_column_review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
