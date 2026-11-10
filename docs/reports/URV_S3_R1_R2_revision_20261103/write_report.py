from pathlib import Path
import json,hashlib,datetime
from zoneinfo import ZoneInfo
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent;CASE=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1_1';CHECK=ROOT/'CASE/unseen_v2_reference_checker_S3_reuse_v1_1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
v=json.loads((OUT/'verification.json').read_text());A=CASE/'evidence/preparation_A.json';data=json.loads(A.read_text());assert sha(A)==v['preparation_A_sha256']
ids='\n'.join(f"|{i+1}|{r['run_id']}|{r['planned_case_id']}|" for i,r in enumerate(data['prepared_runs']))
report=f'''# S3 v1.1：R1/R2 最小隔离修订与关闭权限的准备 A

日期：2026-11-03。用户采用最小修订范围，仅授权在新隔离候选补R1/R2、软件验证及重封A；原生审计和正式计算另行授权。本轮没有调用原生程序、VTK读取器或时间推进。AI辅助工程/证据报告，不代替人工科学终审。

## 1. 结论与封存

R1/R2软件修订在新候选中完成，正反检查通过。新版CASE/unseen_v2_reference_S3_reuse_v1_1及CASE/unseen_v2_reference_checker_S3_reuse_v1_1；准备A为前者evidence/preparation_A.json，SHA256 `{v['preparation_A_sha256']}`，2437项输入，侧文件preparation_A.sha256。

原v1准备A SHA5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d及其全部2339项输入逐项原样继承，同时绑定原A和旧审查报告；没有丢弃或修改原输入。原包、原HOLD及旧57+42测试记录保留。新包R1_R2_SOFTWARE_FIX_VERIFIED=true不等于真实零步审计通过，也不把旧包改成通过。

新版simulation_authorized/formal_simulation_authorized/native_zero_step_authorized/performance_time_stepping_authorized全部false，approved及actual列表全部空。正式四身份和零步十二身份只是预留，均仅配置/manifest。zero_audit_status=NOT_EXECUTED、正式未启动；B、audit_attempts、launch_attempts、analysis_results均不存在。未生成原生或正式授权合同、启动命令。

## 2. R1 输出参数交叉核对

新增analysis/zero_evidence.py的validate_zero_outputs，供audit_S3_zero执行入口及stage_s3总收据复核共用，替代重复但不完整的单点检查。

对describe/precheck/initialize逐项核对：配置与manifest身份/模式/输出、effective方向和formal_simulation=false、h/d/w/Lx/Ly/占比、dx/dt、面积/名义体积、a/nu、nx/ny、统计窗和最大步。格子力由已独立核对的a·dt²/dx计算，仍以原半步J响应核对初始化方向/强度；原格式没有格子力列，本轮不为此改C++。

每条都从实际文件重新检查独立进程receipt、exit_code、execution_audit，要求正常退出、无超时或资源停止、原300s零步预算字段、推进0次、非准备编译宏、日志存在，且没有steady诊断或密度捕获。初始化继续检查原几何/质量/体积/密度/单帧及半步J，并增加result身份和初始帧索引关联。原数值阈值不放宽。

## 3. R2 逐配置原始读回关联

新增validate_initial_readback与validate_audit_records：

- 总收据records按已授权零步计划逐条核对planned_case_id/run_id/mode/output，并确认原A指纹一致；不只看摘要计数。
- 重新解析各条实际输出，调用上述R1检查及真实退出/计数文件；不拿摘要native_exit=0代替原始证据。
- 四份初始化读回必须各自唯一、位于对应field_readback_<planned_case_id>.json，并有对应读取器进程receipt退出0/未超时及日志文件。
- 读回的step=0、唯一核心流体节点、单位、物理数组及零初始压强必须与该配置一致；diagnostic_J与自身result一致，导出J与原记录在其舍入界内一致，同时按原读取器的1e-6相对容差核对半步J。
- 从该初始化目录的唯一PVD、VTM到VTI重新解析完整引用闭包并核对指纹、单帧时间0；只能属于自身vtkData，payload必须同时在原始证据清单与绑定中。这里只用文本/XML和哈希，不导入VTK或运行新读取器。
- 总收据原始清单必须为固定审计目录下的audit_files_sha256.json，文件集合/内容完整一致；不接受额外、漏失或跨目录替代。

执行入口在每次真实初始化读回之后也会调用相同检查，错误时立即停止；未来B封存再从文件重验一次。当前未执行任何真实初始化或B封存。

## 4. 软件验证与格式兼容性

|检查组|结果|证据|
|---|---|---|
|R1/R2专项|31项通过，其中R1一项覆盖54个字段/模式反例子情形|R1_R2_software_tests.log|
|既有S3软件检查|57项通过|S3_software_tests.log|
|原检查器相关检查|42项通过|base_software_tests.log|
|Python语法|25份源码通过AST解析|verification.json|
|旧文件格式离线兼容|6份已有S2零步输出、2份已有读取报告及载荷闭包通过|legacy_format_compatibility.json|

合计130项软件测试（不把54个子情形再重复计入总数）。专项包括十二记录/四读回正常合成路径，以及effective字段矛盾、零通量、重复/错配读回、错run_id/output/A、非零退出/超时/资源停止/推进、缺读取器receipt、错帧/节点/单位/通量、非有限/负舍入界、跨配置载荷/载荷变化和额外原始文件等拒绝路径。旧反例在新软件中均被拒绝。

完整原生证据路径的合成测试明确模拟授权解析，文件完整性与内容检查真实执行；所有临时数据均标为SYNTHETIC_SOFTWARE_ZERO_FIXTURE_NO_NATIVE_NO_READER_NO_AUTHORITY，不作为真实授权、原生审计或场读回。本轮旧S2格式兼容性检查也只读已有文本/JSON/XML和哈希，不调用VTK读取器、不产生新S3审计证据。

封存后在拦截所有子进程创建的条件下：正式/零步默认入口退出0，准备A请求--execute时均退出2；缺真实审计不允许生成B。2437项输入与2371项旧保护文件前后一致。原common及check_results.py/evidence.py/read_fields.py共13份文件字节保持原值。

## 5. 保持的物理、身份、来源与门槛

同一S1原生ELF SHA5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b。真实构建/依赖/库来源及历史限定指令审计按原范围复用，无C++修改/拷贝、重编译或新反汇编；source_reuse_audit.json记录。

新预留身份：

|顺序|run_id（仅预留）|planned_case_id|
|---|---|---|
{ids}

零步审计预留编号URV_S3_ZERO_v1_1_20261103_01，四配置各describe/precheck/initialize，共12条零步，计划4次初态实际场读取。原h60/d80/w120/周期240/Ly240nm、dx2.5nm、P沿槽+y/T横槽+x、a50000/200000、原平均J/K定义、碰撞/体力/壁面/质量观察量/舍入路径/2592窗/150528最大步/帧计划均保持。新编号仅为隔离候选避免覆盖旧目录，不是新执行授权。

中力a100000仍引用S2两条2.5nm原合同结果，原release SHA d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd保持，不重新计算或改写。每方向三点K跨度/均值≤0.001及每条原数值/几何/低惯性守卫不变；单条4h、8GiB地址空间等原资源不变，低P→低T→高P→高T、P控制失败不启动T高、失败即停/无重试/不扩时不变。

## 6. 当前停点与下一步

本轮仅新增两个v1.1隔离目录、修订报告和共享状态。源码存在、语法/软件检查及封存通过均分别记录。真实native=0、VTK reader=0、推进=0、构建=0。NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行），参考资格false、MODEL_COMPARISON/physical_validation未评价、submission_ready=false。

原v1准备A保持HOLD历史结论；新版的软件缺口修订已通过，后续先只读复核新版与R1/R2范围。取得明确覆盖12次原生零步与4次初态场读取的授权后，才核对封存/届时资源、另存零步执行绑定并交付用户手动命令。正式四条还需真实零步通过后另行授权。当前没有原生或正式启动命令，不自动零步、性能推进、求解、重跑、扩时或进S4/S5。

S2六条及网格结论、旧PERF日志例外、历史FAIL、F04 OPEN和外部历史声明原范围保持；不运行24条全局聚合或评价V2。未提交/推送。入口verification.json、implementation_delta.patch、changed_code_files.json、input_set_delta.json、源复用记录与各测试日志；报告清单见report_manifest.json。
'''
(OUT/'REPORT.md').write_text(report)
body=f'''## S3 v1.1 R1/R2已修订并重封准备A；原包保留，执行权限关闭（2026-11-03）

用户已采用最小修订范围，仅授权新隔离候选代码/软件验证及重封A；原生审计和正式计算另行授权。新增CASE/unseen_v2_reference_S3_reuse_v1_1与CASE/unseen_v2_reference_checker_S3_reuse_v1_1。报告入口 docs/reports/URV_S3_R1_R2_revision_20261103/REPORT.md、verification.json、implementation_delta.patch。

新A evidence/preparation_A.json，SHA `{v['preparation_A_sha256']}`，2437项输入一致；原A SHA5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d及其全部2339项输入逐项保留，2371份旧保护文件不变。原v1 HOLD和旧报告保留，不回写。新revision=URV-S3-S1-ELF-REUSE-v1.1；同一原S1 ELF SHA5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b，13份科学common/核心检查文件字节保持，无C++改动或编译。

R1/R2通过共用zero_evidence.py补齐：逐模式effective全部相关物理/方向/零步标志、原生独立退出/计数/初态证据；逐配置run_id/output/A关联、四份唯一场读回、读取器退出、初态节点/帧/通量/单位及自身PVD/VTM/VTI引用闭包，绑定清单与文件集合复核。执行入口和总收据检查均使用同一逻辑；不靠摘要PASS。

验证31项R1/R2专项（含54个字段/模式反例子情形）+57项原S3+42项基础，合计130项软件测试全通过；25份Python语法通过。已有S2中格6份零步输出及2份读取报告/载荷指纹离线格式兼容通过，仅解析旧文本/JSON/XML，不执行VTK读取器，不计新审计。封存后两默认入口退出0，执行请求均拒绝2，无真实审计不能形成B。

四正式预留ID URV_S3_{{P,T}}_a{{50000,200000}}_reuse_v1_1_20261103_01；零步预留URV_S3_ZERO_v1_1_20261103_01共12条，计划4次真实初态读取。全部目录仅配置/manifest，approved及actual空，simulation/formal/native_zero/performance许可均false；无B/attempt/analysis目录，无执行合同/命令。本轮native=0、VTK reader=0、推进=0、构建=0。R1_R2_SOFTWARE_FIX_VERIFIED=true仅是新候选软件结论，非真实零步/几何/数值PASS。

原物理/平均/统计/0.1%线性门/资源/失败即停保持；两S2中档仍引用原合同d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd，不重跑。参考资格false、NUMERICAL_GATE未评价、geometry_PASS=null、RESULT_PASS=false，模型比较/物理验证未评价；历史FAIL、旧日志例外与F04 OPEN保持。

下一步：只读复核新v1.1准备A和修订范围；获得明确12次原生零步+4初态场读取授权后，再复核封存/届时资源并另存执行绑定，交付用户手动命令。当前不原生审计、性能推进或正式计算；正式四条须真实零步后另行授权。原v1包不再直接推进。

'''
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
 p=ROOT/'docs/reports'/name;before=(OUT/('before_'+name)).read_text();current=p.read_text();start=current.find('\n## ');oldstart=before.find('\n## ')
 if current!=before:
  (OUT/('concurrent_before_'+name)).write_text(current);assert current[start:]==before[oldstart:],'concurrent section changed'
 end=current.find('\n## ',start+1);assert p.read_text()==current;p.write_text(current[:start+1]+body+(current[end+1:] if end>=0 else ''))
protected=json.loads((OUT/'protected_inputs_before.json').read_text());assert all(sha(p)==h for p,h in protected.items())
assert all(sha(p)==h for p,h in data['inputs_sha256'].items())
(OUT/'report_manifest.json').write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='report_manifest.json'},ensure_ascii=False,indent=2)+'\n')
print('Report/state/handoff completed. New A closed; original package and all protected files unchanged.')
