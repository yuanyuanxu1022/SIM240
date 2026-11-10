#!/usr/bin/env python3
"""Curate an additive code/data snapshot; never invoke solvers or optimizers."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, shutil, argparse

ROOT=Path(__file__).resolve().parents[3]
REPORT=Path(__file__).resolve().parent
SHARE=ROOT.parent/'SIM240_code_figures_data_review_20261026'
RELEASE=Path('07_第一篇代码数据更新_20261107')
BLOCK={'build','results','runs','tmp','output','outputs','__pycache__','.git','audits','evidence','reports','provenance','references','reference','analysis_results','launch_attempts','performance_runs','lnInclude'}
SUFFIX={'.py','.cpp','.cc','.cxx','.c','.C','.h','.H','.hpp','.sh','.mk','.md','.json','.txt','.diff','.patch','.sha256'}
SPECIAL={'Makefile','Allwmake','Allclean','files','options','controlDict','fvSchemes','fvSolution','blockMeshDict','fvModels','fvModels.gapField','fvConstraints','transportProperties','physicalProperties','gdiProperties','SDIProperties','darcyProperties','p','U','owner','neighbour','boundary','points','faces','cellZones'}
FILES={}

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def add(p,role):
    p=Path(p)
    if not p.is_file():return
    rel=p.relative_to(ROOT)
    if p.is_symlink() and not p.resolve().is_relative_to(ROOT):
        raise RuntimeError('External symlink needs explicit source review: '+str(rel))
    if p.suffix in {'.o','.d','.dep','.so','.a','.pyc','.rho64','.vti','.vtm','.pvd'}:raise RuntimeError('Forbidden artifact '+str(rel))
    if p.stat().st_size>2_000_000:raise RuntimeError('Oversize input needs review '+str(rel))
    if p.read_bytes()[:4]==b'\x7fELF':raise RuntimeError('ELF '+str(rel))
    FILES[str(rel)]={'source':str(rel),'path':str(Path('project')/rel),'role':role,'bytes':p.stat().st_size,'sha256':sha(p),'was_symlink':p.is_symlink()}

def collect():
    roots=[ROOT/'CASE/D_series'/n for n in ['D2_groove_error_map','D3_oblique_groove_tensor_check','D3_squeeze_error_propagation']]
    roots += [ROOT/'CASE'/n for n in ['interface_static_darcy_v1','interface_static_darcy_v1_1','interface_static_darcy_v1_2','interface_static_darcy_v1_3','groove_porosity_model_v1','groove_darcy_static_v1']]
    roots += sorted((ROOT/'CASE').glob('unseen_v2_reference_*'))
    for base in roots:
        for p in sorted(base.rglob('*')):
            if not p.is_file():continue
            parts=p.relative_to(base).parts
            if any(x in BLOCK or x.startswith(('linux','darwin','platforms')) for x in parts[:-1]):continue
            if p.name.endswith(('.bak','.before','.orig')):continue
            if p.suffix in SUFFIX or p.name in SPECIAL or (p.suffix=='.csv' and any(x in {'tests','common'} for x in parts)):
                add(p,'code_protocol_or_small_input')
    with (ROOT/'docs/reports/PAPER1_claim_final_review_20261105/recomputed_44_records.csv').open() as f:
        old=list(csv.DictReader(f))
    runs={str(Path(x['source']).parent.parent) for x in old}
    runs.update('CASE/D_series/D2_groove_error_map/results/'+n for n in ['h100_d100_dx5_P','h100_d100_dx5_T','h75_d100_dx5_buildB_P','h75_d100_dx5_buildB_T'])
    for run in sorted(runs):
        for phase in ['precheck','steady']:
            for name in ['result.txt','run_manifest.txt','exit_code.txt','boundary_audit.txt','result_summary.csv','run.log']:
                add(ROOT/run/phase/name,'D2_saved_scalar_and_run_provenance')
    for name in ['h100_d100_dx5_P','h100_d100_dx5_T','h75_d100_dx5_buildB_P','h75_d100_dx5_buildB_T','h75_d100_dx5_P','h75_d100_dx5_T']:
        add(ROOT/'CASE/D_series/D2_groove_error_map/results'/name/'steady/diagnostics.csv','six_saved_diagnostic_trajectories')
    for name in ['closure_blindtest_20261106.csv','closure_blindtest_verdict.json']:
        add(ROOT/'CASE/D_series/D2_groove_error_map/results'/name,'historical_checker_output_reverse_A_convention')
    for base in [ROOT/'CASE'/n for n in ['interface_static_darcy_v1','interface_static_darcy_v1_1','interface_static_darcy_v1_2','interface_static_darcy_v1_3','groove_darcy_static_v1']]:
        for p in sorted((base/'runs').rglob('*')):
            if p.is_file() and 'provenance' not in p.parts and p.suffix in {'.json','.csv','.txt','.log'}:
                add(p,'static_interface_saved_data')
    # Validation summaries only: omit large raw trajectories and native fields.
    for base in sorted((ROOT/'CASE').glob('unseen_v2_reference_*')):
        for p in sorted((base/'analysis_results').rglob('*')):
            if p.is_file() and p.suffix in {'.json','.csv'} and p.stat().st_size<=500_000:add(p,'S0_S4_saved_analysis_not_new_acceptance')
        for p in sorted((base/'runs').rglob('*')):
            if p.is_file() and p.name in {'result.txt','run_manifest.txt','run_manifest.json','execution.json','exit_code.txt','completion.json'} and p.stat().st_size<=100_000:
                add(p,'S0_S4_saved_scalar_provenance')
    reportsets={
      'PAPER1_formula_comparison_20261105':['build_comparison.py','plot_comparison.py','comparison_36_points.csv','paired_18_geometries.csv','by_gap_summary.csv','direction_summary.csv','OpenFOAM_saved_cases.csv','OpenFOAM_outlet_Q.csv','summary.json','figure_metadata.json'],
      'PAPER1_claim_final_review_20261105':['recomputed_44_records.csv','recomputed_direction_stats.csv','recomputed_outlet9.csv'],
      'PAPER1_new_four_cases_acceptance_20261107':['audit_four.py','comparison.csv','ratios.csv','case_audits.json','build_diagnostic_differences.csv','build_file_comparison.csv','chronology.csv','collection_count.json','prediction_identity.json','summary.json','verification.json','final_verification.json'],
      'URV_S4_TGE_completion_check_20261104_234545':['independent_review.json','remote_hash_verification.json'],
      'PAPER1_bound_closure_review_20261105':['S4_grid_recomputed.csv'],
    }
    for folder,names in reportsets.items():
        for name in names:add(ROOT/'docs/reports'/folder/name,'derived_tables_or_archived_audit_code')
    for folder in ['SDI_C01_results_20261030','SDI_C02_results_20261030','SDI_C03_results_20261030','SDI_C04_results_20261030','GDI01_results_20261030']:
        for p in sorted((ROOT/'docs/reports'/folder).glob('*.json')):add(p,'saved_interface_acceptance')
    for p in sorted((ROOT/'figures/paper').iterdir()):
        if p.is_file() and p.suffix in {'.py','.md','.png','.pdf','.svg'} and not p.stem.startswith(('Fig_fRe','make_fig_fre')):
            add(p,'current_primary_figures_and_scripts')
    for ext in ['png','svg','pdf']:
        add(ROOT/'docs/reports/PAPER1_formula_comparison_20261105'/('formula_comparison.'+ext),'formula_comparison_figure')
    return sorted(FILES.values(),key=lambda r:r['path'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--copy',action='store_true');args=parser.parse_args()
    rows=collect();REPORT.mkdir(exist_ok=True)
    (REPORT/'candidate_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    summary={'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'roles':dict(Counter(r['role'] for r in rows)),'repo':'yuanyuanxu1022/SIM240_code_figures_data','release':str(RELEASE),'manuscripts_included':False,'native_fields_included':False,'new_simulations':0}
    (REPORT/'candidate_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    if args.copy:
        dest=SHARE/RELEASE
        if dest.exists():raise RuntimeError('Refuse overwrite '+str(dest))
        for r in rows:
            src=ROOT/r['source'];dst=dest/r['path'];dst.parent.mkdir(parents=True,exist_ok=True)
            if sha(src)!=r['sha256']:raise RuntimeError('Source changed '+r['source'])
            shutil.copy2(src,dst)
            if sha(dst)!=r['sha256']:raise RuntimeError('Copy mismatch '+r['source'])
        (dest/'source_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
        with (dest/'文件清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['source','path','role','bytes','sha256','was_symlink']);w.writeheader();w.writerows(rows)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
