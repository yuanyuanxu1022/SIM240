#!/usr/bin/env python3
"""Copy the reviewed development preparation to the explicitly selected sharing repo."""
from pathlib import Path
import csv,hashlib,json,re,shutil
P=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
W=P.parent/'SIM240_代码图片数据_20261022';C=P/'CASE/D_series/D4_variable_groove_transport_20261023'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=list(csv.DictReader((W/'文件清单.csv').open(encoding='utf-8-sig')));mapping={r['原项目路径']:r for r in old};items=[]
    for source in [C/'development_stage_20261023',HERE]:
        for f in source.rglob('*'):
            if not f.is_file() or '__pycache__' in f.parts or f.suffix in ['.pyc','.nul'] or f.name in ['publish.json','share_sync.json','share_paths.json','git_record.json']:continue
            group='01_代码/计算与分析' if f.suffix=='.py' else ('01_代码/00_技术说明' if f.suffix=='.md' else '03_数据')
            if source==HERE:dest=Path(group)/'D4_development_release_20261023'/f.relative_to(source)
            else:dest=Path(group)/'D4_variable_groove_transport_20261023/development_stage_20261023'/f.relative_to(source)
            items.append((f,dest))
    changed=[]
    for f,dest in items:
        target=W/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
        assert sha(f)==sha(target);assert target.read_bytes()[:4]!=b'\x7fELF'
        key=str(f.relative_to(P));mapping[key]={'原项目路径':key,'本文件夹路径':str(dest),'字节数':target.stat().st_size,'SHA256':sha(target)};changed.append(str(dest))
    with (W/'文件清单.csv').open('w',encoding='utf-8-sig',newline='') as fp:
        wr=csv.DictWriter(fp,fieldnames=['原项目路径','本文件夹路径','字节数','SHA256'],lineterminator='\r\n');wr.writeheader();wr.writerows(mapping.values())
    plan='01_代码/00_技术说明/D4_variable_groove_transport_20261023/development_stage_20261023/PLAN.md'
    table='03_数据/D4_variable_groove_transport_20261023/development_stage_20261023/stage_cases.csv'
    budget='03_数据/D4_variable_groove_transport_20261023/development_stage_20261023/case_budget.csv'
    status=f'**开发阶段准备完成：[方案与许可边界]({plan}) → [20项开发/线性逐算例表]({table}) → [含12项暂缓网格参考的32行预算]({budget})。当前技术启动许可仅6项：h75/d120/w240/P480/dx5，沿槽/横槽各3档驱动力；其余14项、网格参考与预测均待前置验收。尚未启动新仿真。**'
    f=W/'README.md';lines=f.read_text().splitlines();lines=[s for s in lines if not s.startswith('**开发阶段准备完成：')]
    ix=next(i for i,s in enumerate(lines) if s.startswith('**2026-10-23新进度：'))
    lines[ix+1:ix+1]=['',status]
    for i,s in enumerate(lines):
        if '加入D4准备及首批验收来源后现行为' in s:lines[i]=re.sub(r'加入D4准备及首批验收来源后现行为\d+项',f'加入D4准备、基础验收及开发许可资料后现行为{len(mapping)}项',s)
    for i,line in enumerate(lines):
        if line.startswith('**2026-10-23新进度：'):lines[i]=line.replace('后续执行许可未放行','开发阶段已单独准备首6项许可，见下方')
        if line.startswith('**最新供老师确认：'):lines[i]=line.replace('老师未批准，未运行','老师外部确认尚未独立核实，新槽宽流动计算尚未启动')
    f.write_text('\n'.join(lines)+'\n')
    f=W/'00_当前进度.md';s=f.read_text();start=s.index('**最新停点：');end=s.index('\n\n',start)
    s=s[:start]+f'**最新停点：首批8项基础验收PASS，开发阶段方案及首6项技术许可已准备并审查。** 全部20项开发/线性参数和另12项网格参考已逐行列明；当前只允许最大新几何两个方向各3档驱动力，共6项，由用户另行启动。其余14项、网格参考和预测组仍锁定。首批8项完整数据/74帧与独立验收已收集，当前无新增流动计算。详见[开发方案]({plan})和[基础验收](01_代码/00_技术说明/D4_foundation_acceptance_20261023/REPORT.md)。'+s[end:]
    s=s.replace('本轮新增比较保存在本地，尚未推送；远端最新内容未联网核对。','代码、数据与当前进度已按目录整理，最新版本可通过本仓库main提交记录核对。')
    start=s.index('## 下一步\n');s=s[:start]+'''## 下一步

由用户在原项目本机终端执行新development_stage_20261023/NEXT_COMMAND.txt的一条后台命令，仅启动首6项。该命令尚未执行；完成后独立核对数值/几何、实际全帧与同方向驱动力K差≤1%的新增预定判据，再决定后续14项和开发网格参考的许可。原foundation命令禁止重复运行。预测组及其参考继续要求先冻结公式/系数/逐点预测，再取得结果。历史FAIL、来源缺口与新槽宽精度未闭合状态保持。
''';f.write_text(s)
    f=W/'清单与核验入口.md';s=f.read_text();s=re.sub(r'现行为\d+项',f'现行为{len(mapping)}项',s);s=re.sub(r'\| \d+行，不含表头',f'| {len(mapping)}行，不含表头',s);s=re.sub(r'当前source_files=\d+',f'当前source_files={len(mapping)}',s);s=s.replace('对应上一轮报告source_files=8378','对应上一轮报告source_files=6542')
    if '开发阶段准备不增加正式计算结果' not in s:s+='\n本次追加开发阶段方案、运行许可和20项零推进配置说明；开发阶段准备不增加正式计算结果，当前只有首批8项已计算验收。\n'
    s=s.replace('加入首批8项原始结果与验收资料后现行为8378项','加入首批8项原始结果与验收资料后为8200项；本次追加开发准备178项，现行为8378项').replace('当前只有首批8项已计算验收','新D4当前只有首批8项已计算验收')
    f.write_text(s)
    changed+=['文件清单.csv','README.md','00_当前进度.md','清单与核验入口.md','检查记录/文件完整性.json']
    result={'source_files':len(mapping),'new_since_foundation_package':len(mapping)-8200,'source_bytes':sum(int(r['字节数']) for r in mapping.values()),'copied_files':len(items),'foundation_8200_source_rows_preserved':all(mapping[r['原项目路径']]==r for r in old[:8200]),'push_performed_by_sync':False}
    (HERE/'share_sync.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(HERE/'share_paths.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
