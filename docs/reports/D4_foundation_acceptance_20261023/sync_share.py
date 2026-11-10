#!/usr/bin/env python3
"""Copy reviewed first-study results and analysis into the existing local sharing repo."""
from pathlib import Path
import csv,hashlib,json,shutil
PROJECT=Path(__file__).resolve().parents[3]
W=PROJECT.parent/'SIM240_代码图片数据_20261022'
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=list(csv.DictReader((W/'文件清单.csv').open(encoding='utf-8-sig')));mapping={r['原项目路径']:r for r in old};changed=[]
    case=PROJECT/'CASE/D_series/D4_variable_groove_transport_20261023'
    items=[(p,Path('03_数据/D4_variable_groove_transport_20261023/results/foundation_20261023_v1')/p.relative_to(case/'results/foundation_20261023_v1')) for p in (case/'results/foundation_20261023_v1').rglob('*') if p.is_file()]
    items.append((case/'FOUNDATION_ACCEPTANCE.md',Path('01_代码/00_技术说明/D4_variable_groove_transport_20261023/FOUNDATION_ACCEPTANCE.md')))
    for p in ROOT.rglob('*'):
        if not p.is_file() or 'before' in p.relative_to(ROOT).parts or p.suffix=='.pyc' or p.name in ['share_sync.json','share_paths.json','share_review.json','stage_paths.nul','git_record.json']:continue
        if p.suffix=='.py':base=Path('01_代码/计算与分析/D4_foundation_acceptance_20261023')
        elif p.suffix=='.md':base=Path('01_代码/00_技术说明/D4_foundation_acceptance_20261023')
        else:base=Path('03_数据/D4_foundation_acceptance_20261023')
        items.append((p,base/p.relative_to(ROOT)))
    for src,dest in items:
        key=str(src.relative_to(PROJECT));dst=W/dest;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst);assert sha(src)==sha(dst)
        mapping[key]={'原项目路径':key,'本文件夹路径':str(dest),'字节数':dst.stat().st_size,'SHA256':sha(dst)}
        changed.append(str(dest))
    with (W/'文件清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=['原项目路径','本文件夹路径','字节数','SHA256'],lineterminator='\r\n');wr.writeheader();wr.writerows(mapping.values())
    count=len(mapping);total=sum(int(r['字节数']) for r in mapping.values())
    report_link='01_代码/00_技术说明/D4_foundation_acceptance_20261023/REPORT.md'
    p=W/'README.md';s=p.read_text();lines=s.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('**2026-10-23新进度：'):lines[i]=f'**2026-10-23新进度：[首批8项独立验收报告]({report_link})。新D4的2项旧几何回归与6项平板已完成，按冻结协议独立验收PASS；30,050条逐步记录及74帧真实流场齐备。可继续开发组准备/审批，后续执行许可未放行，不重复启动首批。完整原始数据、日志、流场和分析脚本已同步；新槽宽精度及候选范围网格独立性仍待验证。**'
        if line.startswith('**本地Git克隆后'):lines[i]='**本地Git克隆后的文件校验、恢复工作区、4图生成、主D2编译均已实际通过；见[克隆检查记录](检查记录/从Git克隆后的完整检查.json)。该次克隆复验未启动仿真，未在老师电脑上测试。**'
        if line.startswith('“6542项”旧清单'):lines[i]=line.replace('2026-10-23加入D4准备来源后现行为7871项',f'2026-10-23加入D4准备及首批验收来源后现行为{count}项')
    p.write_text('\n'.join(lines)+'\n')
    p=W/'00_当前进度.md';s=p.read_text();start=s.index('**最新停点：');end=s.index('\n\n',start)
    s=s[:start]+f'**最新停点：新D4首批8项已完成并独立验收PASS。** 2项旧几何回归＋6项平板；平板K最大误差约1.00%、剖面L2约0.4564%，低于2%；旧几何一致性通过。30,050条逐步记录和74帧实际流场已核查，数值/几何、全程质量、末态截面与帧计划均满足冻结协议。原始RESULT_PASS=false保留，独立FOUNDATION_RESULT_PASS=true只覆盖本批基础验收。详见[验收报告]({report_link})。后续开发组可进入准备/审批，当前尚无新阶段执行许可，禁止重复启动首批。'+s[end:]
    s=s.replace('尚无实际OpenLB几何预查或计算。','该表在形成时尚无实际预查/计算；现已完成独立新D4的42种实际网格零步预查与首批8项基础计算，尚无新槽宽稳态结果。')
    i=s.index('## 下一步\n');s=s[:i]+'''## 下一步

核对8种新开发几何及其数值参考、资源预算和逐项参数，单独准备并审查开发阶段许可；不自动启动。当前release白名单仍仅允许已完成的8项，原NEXT_COMMAND和准备文件保留为历史绑定快照，不能重复运行。预测组与对应参考必须先锁定公式、系数和预测文件哈希，再获得计算结果。首批通过不能替代新槽宽精度、候选范围网格独立性或最终公式预测验证；历史FAIL和来源缺口保持。
''';p.write_text(s)
    p=W/'清单与核验入口.md';s=p.read_text().replace('现行为7871项',f'准备阶段为7871项；加入首批8项原始结果与验收资料后现行为{count}项').replace('| 7871行，',f'| {count}行，').replace('source_files=7871',f'source_files={count}').replace('D4零步检查没有增加正式稳态结果数。','D4准备阶段的零步检查没有增加正式稳态结果数；本轮新增8项基础稳态结果，原52项历史索引保持。')
    p.write_text(s)
    changed+=['文件清单.csv','README.md','00_当前进度.md','清单与核验入口.md','检查记录/文件完整性.json']
    (ROOT/'share_sync.json').write_text(json.dumps({'source_files':count,'source_bytes':total,'new_source_files_since_preparation':len(mapping)-7871,'copied_files':len(items),'shared_root':str(W),'push_performed':False},ensure_ascii=False,indent=2))
    (ROOT/'share_paths.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2))
    print((ROOT/'share_sync.json').read_text())
if __name__=='__main__':main()
