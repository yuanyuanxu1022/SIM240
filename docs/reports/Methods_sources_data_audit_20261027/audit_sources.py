#!/usr/bin/env python3
"""Read-only record/provenance and private-share coverage audit. Never runs project code."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SHARE=ROOT.parent/'SIM240_code_figures_data_review_20261026'
E=HERE/'evidence'
inputs={}
def read(p):
    p=Path(p);p=p if p.is_absolute() else ROOT/p
    data=p.read_bytes();inputs[str(p)]=hashlib.sha256(data).hexdigest();return data.decode('utf-8-sig')
def rows(p):return list(csv.DictReader(read(p).splitlines()))
def kv(p):return dict(x.split('=',1) for x in read(p).splitlines() if '=' in x)
def save(name,obj):(HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

tree=json.loads(read(E/'github_tree.json'));remote={x['path']:x for x in tree['tree'] if x['type']=='blob'}
meta=json.loads(read(E/'github_repository.json'));head=json.loads(read(E/'github_head.json'))
manifest=rows(SHARE/'文件清单.csv')
inventory=rows(ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv')
source_map={r['原项目路径']:r for r in manifest}
critical={r[k] for r in inventory for k in ['result_path','manifest_path','log_path']}
critical.update(str(Path(r['result_path']).with_name('exit_code.txt')) for r in inventory)
critical.update('CASE/D_series/D2_groove_error_map/results/'+n for n in ['summary.csv','d75_summary.csv','h25_summary.csv','d120_summary.csv'])
critical.update('figures/paper/'+n for n in ['make_fig1.py','make_fig4.py','make_fig7_fig8.py'])
critical.update('figures/paper/'+n+'.'+ext for n in ['Fig1_device_and_unitcell','Fig4_K_and_anisotropy','Fig7_error_vs_gap','Fig8_error_map'] for ext in ['png','pdf','svg'])
package_checks=[]
for row in manifest:
    relative=row['本文件夹路径'];p=SHARE/relative
    if relative not in remote:
        package_checks.append({'path':relative,'remote_path_present':False,'ok':False,'reason':'MISSING_REMOTE_PATH'});continue
    if not p.is_file():
        if row['原项目路径'] not in critical:
            package_checks.append({'path':relative,'remote_path_present':True,'byte_check':'NOT_PERFORMED_SPARSE_CHECKOUT','ok':None});continue
        current=Path(row['原项目路径'])
        current=current if current.is_absolute() else ROOT/current
        if current.is_file() and hashlib.sha256(current.read_bytes()).hexdigest()==row['SHA256']:
            data=current.read_bytes()
            method='CURRENT_SOURCE_IDENTICAL_TO_MANIFEST_AND_REMOTE_BLOB'
        else:
            data=subprocess.run(['git','-C',str(SHARE),'cat-file','blob',remote[relative]['sha']],capture_output=True,check=True,timeout=30).stdout
            method='LOCAL_GIT_OBJECT_COMPARED_WITH_REMOTE_TREE'
        size=len(data);sha256=hashlib.sha256(data).hexdigest();gitsha=hashlib.sha1(f'blob {size}\0'.encode()+data).hexdigest()
        package_checks.append({'path':relative,'remote_path_present':True,'byte_check':method,
          'bytes':size,'sha256':sha256,'git_blob_sha':gitsha,'ok':str(size)==row['字节数'] and sha256==row['SHA256'] and gitsha==remote[relative]['sha']})
        continue
    size=p.stat().st_size
    h=hashlib.sha256();g=hashlib.sha1();g.update(f'blob {size}\0'.encode())
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);g.update(chunk)
    sha256=h.hexdigest();gitsha=g.hexdigest()
    ok=(str(size)==row['字节数'] and sha256==row['SHA256'] and relative in remote and gitsha==remote[relative]['sha'])
    package_checks.append({'path':relative,'remote_path_present':True,'byte_check':'WORKTREE_BYTES_COMPARED_WITH_REMOTE_TREE','bytes':size,'sha256':sha256,'git_blob_sha':gitsha,'ok':ok})
save('package_file_checks.json',package_checks)

coverage=[]
def compare_source(path,kind):
    path=Path(path);rel=str(path.relative_to(ROOT)) if path.is_absolute() and path.is_relative_to(ROOT) else str(path)
    r=source_map.get(rel)
    local=ROOT/rel
    current_hash=hashlib.sha256(local.read_bytes()).hexdigest() if local.is_file() else None
    if local.is_file():inputs[str(local.resolve())]=current_hash
    coverage.append({'kind':kind,'source_path':rel,'in_share_manifest':r is not None,'package_path':r['本文件夹路径'] if r else None,
      'current_source_sha256':current_hash,'shared_snapshot_sha256':r['SHA256'] if r else None,'matches_current':bool(r and current_hash==r['SHA256'])})

missing_fields=collections.Counter();binaries=collections.Counter();run_records=[]
for row in inventory:
    result=kv(row['result_path']);man=kv(row['manifest_path'])
    ex=read(Path(row['result_path']).with_name('exit_code.txt')).strip()
    for key in ['source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags']:
        if key not in man:missing_fields[key]+=1
    binaries[man['binary_sha256']]+=1
    for key,kind in [('result_path','run_result'),('manifest_path','run_manifest'),('log_path','run_log')]:compare_source(row[key],kind)
    compare_source(Path(row['result_path']).with_name('exit_code.txt'),'run_exit')
    run_records.append({'run_id':row['run_id'],'recorded_PASS':result.get('PASS'),'independent_exit':ex,
                        'binary_sha256':man.get('binary_sha256'),'binary_path':man.get('binary')})
for name in ['summary.csv','d75_summary.csv','h25_summary.csv','d120_summary.csv']:
    compare_source('CASE/D_series/D2_groove_error_map/results/'+name,'main_plot_input')
for name in ['make_fig1.py','make_fig4.py','make_fig7_fig8.py']:
    compare_source('figures/paper/'+name,'main_plot_script')
for name in ['Fig1_device_and_unitcell','Fig4_K_and_anisotropy','Fig7_error_vs_gap','Fig8_error_map']:
    for ext in ['png','pdf','svg']:compare_source('figures/paper/'+name+'.'+ext,'main_plot_output')
for name in ['SIM240_中文稿_导师审阅版_20261022.md','SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md']:
    compare_source('docs/reports/'+name,'current_document')
save('share_coverage.json',coverage)
current_binaries=[]
for bp in sorted({r['binary_path'] for r in run_records if r['binary_path']}):
    p=Path(bp)
    if p.is_file():
        digest=hashlib.sha256(p.read_bytes()).hexdigest();inputs[str(p)]=digest
        current_binaries.append({'path':bp,'current_sha256':digest,'matches_recorded_runs':sum(r['binary_sha256']==digest for r in run_records)})
    else:current_binaries.append({'path':bp,'exists_now':False})
for p in [ROOT/'CASE/D_series/D2_groove_error_map/src/Makefile',ROOT/'CASE/D_series/D3_oblique_groove_tensor_check/src/Makefile',
          ROOT/'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',ROOT/'CASE/D_series/D3_oblique_groove_tensor_check/src/d3_oblique_groove_tensor_check.cpp',
          Path('/home/dell/openlb/src/dynamics/dynamics.h'),Path('/home/dell/openlb/src/dynamics/momenta/elements.h'),Path('/home/dell/openlb/CITATION.cff')]:read(p)
openlb_head=subprocess.run(['git','-C','/home/dell/openlb','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
save('provenance.json',{'run_count':len(inventory),'missing_manifest_fields':dict(missing_fields),'binary_hash_groups':dict(binaries),
 'current_binary_observations':current_binaries,'current_openlb_head':openlb_head,'historical_openlb_version_proved':False,
 'scope':'52 specified run manifests and current implementations; not an exhaustive search for all possible historical archives','runs':run_records})
groups={k:{'rows':len(sub),'in_snapshot':sum(x['in_share_manifest'] for x in sub),'matches_current':sum(x['matches_current'] for x in sub)}
 for k in sorted({x['kind'] for x in coverage}) for sub in [[x for x in coverage if x['kind']==k]]}
result={'checked_at_UTC':datetime.now(timezone.utc).isoformat(),'repository':meta,'head':head,'tree_truncated':tree.get('truncated'),
 'remote_blob_count':len(remote),'manifest_rows':len(manifest),'all_manifest_paths_present_in_remote':all(x['remote_path_present'] for x in package_checks),
 'selected_package_files_byte_checked':sum(x['ok'] is not None for x in package_checks),
 'all_selected_package_byte_checks_match_remote':all(x['ok'] is not False for x in package_checks),
 'full_archive_byte_recheck_performed':False,
 'failed_package_checks':[x for x in package_checks if x['ok'] is False], 'coverage_groups':groups,
 'different_current_plot_scripts_or_outputs':[x['source_path'] for x in coverage if x['kind'] in ['main_plot_script','main_plot_output'] and not x['matches_current']],
 'all_52_results_recorded_PASS_and_exit0':all(x['recorded_PASS']=='true' and x['independent_exit']=='0' for x in run_records),
 'repository_is_public':not meta['private'],'source_build_provenance_complete':False,'scientific_gate_reassessed':False,
 'new_solver_run_id':None,'submission_ready':False}
save('availability.json',result);save('read_inputs.json',{'sha256':inputs})
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['all_manifest_paths_present_in_remote'] and result['all_selected_package_byte_checks_match_remote'] and result['all_52_results_recorded_PASS_and_exit0'] else 1)
