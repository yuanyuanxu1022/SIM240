"""Synchronize current handoff only; verify reviewed inputs without executing PDE."""
import difflib
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')

e=json.loads((OUT/'audit_evidence.json').read_text())
assert (OUT/'audit.exit_code').read_text().strip()=='0'
verdict=dict(status='HOLD_NO_RUN_PERMISSION',review_date='2026-10-26',
    reviewed_version=e['contract']['version'],single_case=e['contract']['planned_id'],
    technical_ready=False,authorized_to_execute=False,actual_run_id=None,
    blockers=['R1_INDEPENDENT_RECONSTRUCTION_AND_REQUIRED_RECORD_CHECKS',
              'R2_DURABLE_ARCHIVE_AND_FAILURE_STATUS',
              'ACTUAL_WORK_AND_RECORD_VOLUMES_NOT_PREPARED',
              'DIAGNOSTIC_CONTRACT_DRAFT_NO_RUN_AUTHORIZATION'],
    old_preparation_tests='16 methods passed in prior record; not rerun',
    new_counterexample='synthetic reconstruction mismatch 6 accepted by check(work)',
    real_solver_called=False,backend_loaded=False,volume_provisioned=False,
    NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
    prediction_permission='HOLD',source_and_old_evidence_unchanged=True)
write(OUT/'verdict.json',verdict)
section='''## 第一篇：单项诊断v2复核为HOLD，需补读回关联及持久归档（2026-10-26，当前入口/停点）

- 本轮用户授权核新版本、单项诊断合同和工作卷前提，明确不启动。结论HOLD_NO_RUN_PERMISSION：技术条件尚未齐全，且无运行授权。入口`docs/reports/D4_pilot_v2_release_review_20261026/REPORT.md`、`verdict.json`、`audit_evidence.json`；旧`pilot_record_v2_20261026/`源码/合同/测试原样保留。
- 已核：新旧合同并列门禁结构有效；原模板DRAFT_NOT_AUTHORIZED/false/approval=null在纯执行校验中拒绝。新来源354路径、旧保护4233路径、前次终审138输入、旧包358产物哈希全部相符（集合重叠不相加），13模块语法通过；既有16个无求解测试通过记录保持，本轮未重复跑16项。没有真实run_id、网格组装、KSP或物理结果。
- R1独立读回缺口已复现：复制旧人工夹具，A/b/代数向量不变，仅把重建向量及对应速度的一个非从属值1改7并更新数组哈希，check(work)仍PASS，差6。仅为人工反例，不冒充真实capture。需独立核r由x按已绑定周期关系回填，并强制真实成功必需记录、求解原因/配置/资源等一致；记录阶段错误须与子退出码分开。
- R2持久保存缺口：当前矩阵/场/日志/失败向量只在tmpfs工作卷，记录盘仅留清单等；没有终止后完整复制、哈希读回与完成发布。需另版补成功/失败/超时/OOM已落盘文件归档；复制失败标未完成、保留源，不掩盖首错。读回需支持显式绑定的持久副本。
- 工作卷前提未满足：模板work/record父目录均不存在。08:56北京时间只读快照MemAvailable约16.49GiB、仓库所在盘约337.00GiB；指定cgroup父路径memory/pids及可写检查通过，未创建组。现有/dev/shm容量约15.52GiB，非专用≤512MiB空卷。总体余量不等于目标卷已准备；未挂载/安装/改系统。见audit_evidence.json。
- 下一最小动作：另版补R1/R2及无求解拒绝/归档测试，再明确实际工作卷和持久记录路径、核卷测试与冻结单项配置。范围仍仅B0MIN_MMS_mixed_N8；协议审定并获用户明确单项授权前不能运行；本轮不交启动命令、不自动推进后项。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、预测HOLD，G4 v1及旧网格FAIL不变。无OpenLB编译、PDE求解、拟合、原协议/阈值修改或Git提交/推送。

'''
changes={}
for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
    p=REPO/'docs/reports'/name
    old=p.read_text()
    begin=old.index('## 第一篇：三项缺口v2已实现')
    end=old.index('\n## ',begin+1)+1
    backup=OUT/'before_state_sync'/name
    with backup.open('x') as f:f.write(old)
    new=old[:begin]+section+old[end:]
    p.write_text(new)
    tail=new.index('\n## ',new.index('## 第一篇：单项诊断v2')+1)+1
    assert new[tail:]==old[end:]
    diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+name,tofile='after/'+name))
    (OUT/(name+'.diff')).write_text(diff)
    changes[str(p.relative_to(REPO))]={'before_sha256':sha(backup),'after_sha256':sha(p),'historical_sections_unchanged':True}
write(OUT/'state_sync.json',changes)
inputs=json.loads((OUT/'review_inputs_sha256.json').read_text())
bad=[p for p,h in inputs.items() if sha(REPO/p)!=h]
assert not bad,bad
write(OUT/'final_verification.json',{'status':'REVIEW_COMPLETE_HOLD',
    'reviewed_package_files_unchanged':len(inputs),'mismatches':bad,
    'state_sync_verified':True,'historical_sections_unchanged':True,
    'actual_run_id':None,'real_solver_called':False,
    'review_artifacts_sha256':{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}})
print(json.dumps({'status':'REVIEW_COMPLETE_HOLD','unchanged_package_files':len(inputs),'state_files_updated':list(changes)},ensure_ascii=False))
