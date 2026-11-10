#!/usr/bin/env python3
"""Read GitHub metadata/tree/blobs and verify the explicitly published snapshot."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,base64,hashlib

OUT=Path(__file__).resolve().parent
REPO='yuanyuanxu1022/SIM240_code_figures_data'
SHARE=OUT.parents[3]/'SIM240_code_figures_data_review_20261026'

def api(endpoint):
    p=subprocess.run(['gh','api',endpoint],text=True,capture_output=True)
    if p.returncode:raise RuntimeError('GitHub API failed: '+endpoint+' exit '+str(p.returncode))
    return json.loads(p.stdout)

def main():
    local=json.loads((OUT/'local_commit.json').read_text());commit=local['commit'];staged=json.loads((OUT/'staged_files.json').read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        meta,head,obj=list(pool.map(api,['repos/'+REPO,'repos/'+REPO+'/commits/main','repos/'+REPO+'/git/commits/'+commit]))
    assert meta['private'] and meta['permissions']['push']
    assert head['sha']==commit
    assert obj['parents'][0]['sha']==local['parent']
    tree=api('repos/'+REPO+'/git/trees/'+obj['tree']['sha']+'?recursive=1');assert not tree.get('truncated')
    remote={x['path']:x for x in tree['tree'] if x['type']=='blob'}
    missing=[];mismatches=[]
    for x in staged:
        r=remote.get(x['path'])
        if r is None:missing.append(x['path'])
        elif r['sha']!=x['git_blob'] or r['mode']!=x['mode']:mismatches.append(x['path'])
    assert not missing and not mismatches
    prefix='07_第一篇代码数据更新_20261107/'
    critical=['README.md','check_package.py','source_manifest.json','package_manifest.json',
      'project/CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',
      'project/CASE/D_series/D2_groove_error_map/results/h100_d100_dx5_P/steady/result.txt',
      'project/CASE/D_series/D2_groove_error_map/results/h100_d100_dx5_T/steady/result.txt',
      'project/docs/reports/PAPER1_new_four_cases_acceptance_20261107/ratios.csv',
      'project/CASE/groove_darcy_static_v1/application/grooveDarcyStaticFoam.C',
      'project/CASE/interface_static_darcy_v1/runs/SDI_C01_v1_20261030_01/openfoam/SDI_output/faces.csv',
      'project/CASE/interface_static_darcy_v1/openfoam/cases/C01/constant/darcyProperties',
      'project/CASE/interface_static_darcy_v1/openfoam/cases/C01/0/p',
      'project/CASE/groove_darcy_static_v1/cases/GDI01/0/U',
      'project/CASE/groove_darcy_static_v1/cases/GDI01/constant/polyMesh/points']
    byname={x['path']:x for x in staged}
    def blob_check(rel):
        path=prefix+rel;blob=api('repos/'+REPO+'/git/blobs/'+remote[path]['sha']);assert blob['encoding']=='base64'
        data=base64.b64decode(blob['content']);got=hashlib.sha256(data).hexdigest();assert got==byname[path]['sha256'],path
        return {'path':path,'git_blob':remote[path]['sha'],'bytes':len(data),'remote_bytes_sha256':got,'matches_committed_bytes':True}
    with ThreadPoolExecutor(max_workers=5) as pool:checked=list(pool.map(blob_check,critical))
    status=subprocess.check_output(['git','-C',str(SHARE),'status','--porcelain'],text=True);assert not status,status
    report={'repository':REPO,'private':True,'branch':'main','commit':commit,'parent':local['parent'],
      'initial_commit':local['initial_commit'],'comparison_base':local['comparison_base'],
      'remote_head_matches':True,'remote_tree_entries':len(tree['tree']),'remote_tree_truncated':False,
      'changed_paths_verified':len(staged),'source_files':local['source_files'],'package_files':local['package_files'],
      'missing_paths':missing,'blob_or_mode_mismatches':mismatches,'critical_remote_bytes_verified':checked,
      'share_worktree_clean':True,'entry_url':'https://github.com/'+REPO+'/tree/main/07_%E7%AC%AC%E4%B8%80%E7%AF%87%E4%BB%A3%E7%A0%81%E6%95%B0%E6%8D%AE%E6%9B%B4%E6%96%B0_20261107',
      'manuscript_refresh_uploaded':False,'new_simulations':0,'new_fits':0}
    (OUT/'remote_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='critical_remote_bytes_verified'},ensure_ascii=False,indent=2))
    print('Critical remote bytes verified:',len(checked))

if __name__=='__main__':main()
