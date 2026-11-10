# 窄槽四项1.25nm最细网格准备与审查报告

2026-10-24。用户授权准备执行入口、资源和三格比较接续。本机技术准备 **PASS，可以交付用户手动启动本批4项的唯一命令**；正式批次尚未创建，未执行steady，未得到新最细格数值或流场。该结论不等于科学/网格PASS或老师外部审批。

## 逐算例范围与不变合同

新目录 `CASE/D_series/D4_variable_groove_transport_20261023/development_grid_narrow_fine4_20261024/`；batch_id=`development_grid_narrow_fine4_20261024_v1`。

|h/d/w（nm）|P=Ly（nm）|dx（nm）|方向|流体节点/方向|窗口步数|最大步数|
|---|---:|---:|---|---:|---:|---:|
|75/25/60|120|1.25|P、T|645120|16200|307200|
|75/120/60|120|1.25|P、T|995328|16200|1168128|

逐项ID、配对中格、步数和预算在case_budget4.csv。a1e5、ρ1000、ν1e−6、μ.001、τ1与原碰撞/边界/充分充液固定单相保持；dt=2.604166666666667e−13s。原质量/密度/Mach/窗口/截面/几何/有限值门槛和帧计划不改。首个原合格窗即停；未达到未来帧不补造或延算。源RESULT_PASS=false保留，完成后独立验收另存结论。

4项白名单只允许两窄槽1.25nm P/T；其余86canonical行拒绝，包含宽细2项、预测、已完成粗格/中格。run_narrow4.py默认仅检查；唯一batch和实际配置/输出路径固定，已存在batch或同case正式result拒绝覆盖、续跑或改tag重跑。单进程单rank、逐项串行，非零exit/绑定变化/资源不足立即停；不自动验收/拟合/启动下一批。

## 上游来源与新增实现

上游中格6项已独立验收PASS，原240文件、certificate与全部分析证据的哈希重新核对，原中格release/源码/程序不改。默认来源导出器合并真实粗6与已验收中6，生成12行bound upstream bundle；已有完整canonical参数/物性/周期/方法/K/run_id/独立exit/原始与分析来源均保持。新阶段改动是白名单、规模/资源、已知batch注册、上游certificate接入和新finish_grid_review入口；window_metrics.py、compare_grid.py、grid_policy.json三文件与冻结中格版逐字节一致。

未改C++、binary或原数值协议；make --question exit0、source/binary与原已验收哈希一致，复用已编译程序，无新编译。4 describe+4 precheck全部exit0、collideAndStream=0；2个不同形状/4方向均实际核几何与独立18方向壁面连接/q=.5，fallback/unresolved=0；实测最大零步RSS 730832KiB，约0.697GiB。零步只证明安装和参数，不证明新流动物理精度。

## 分块验收与比较接续核查

- 新阶段拒绝/回归检查通过：4允许、86禁止；RAM/磁盘不足、错MPI/OpenLB、绑定变化/缺失、错批次/重复完成case、参数变更、伪造周期/K/重复run_id等拒绝；相对路径从其他目录定位仍正确。
- 20个已有5nm算例共64675完整窗口与未分块算法逐值差0，停止点一致；4050/16200长窗及低物理通量和长双精度两遍算术对照通过；工作预算16MiB，ddof1和原阈值不变。系统Python测试峰值119.02MiB。旧阶段同一helper验证来源保持，不将测试当新最细格验收。
- 新数值适配器在已完成中格6项/91200行上完整回归exit0，实测峰值78984KiB。流场适配reader在已完成窄槽中格4项/40帧、84引用文件上实际读取exit0，峰值297640KiB；节点/字段/时间/通量与CSV保持，主通量最大相对差2.52670131e−9且在Float32界内。
- 未来fine4动态帧和完整证书还未产生，尚不能作真实fine4端到端验收。accept_batch.py只接受完成且正确batch的四项；当前给它中格batch或给finish_grid_review中格证书均拒绝，不创建伪验收目录。
- 真实上游12行经比较CLI输出缺最细格，未报全局或窄槽PASS。人造数据证明：窄槽六量可以局部PASS而宽细缺失时全局仍INCOMPLETE；窄槽某量失败时明确保留geometry FAIL及局部NOT_PASS，不能被全局缺项掩盖。阈值等号/内外、非单调/不收缩、近乎平坦、重复数据分支保持。

真实接续顺序冻结为：

1. 用户运行本批4项，结束后另行要求独立验收。
2. accept_batch.py按原合同完成数值/几何/输入/全部保存场核验，通过才生成四项certificate。
3. 显式调用finish_grid_review.py；它接完整四项证书，默认加已验收粗6/中6，形成16行有来源的参考并执行三格比较。
4. 每个窄几何的KP/KT/A分别判E(5→1.25)≤1%、E(2.5→1.25)≤0.5%以及原趋势分支，两个几何六量全过才给narrow_six_quantity_gate=PASS。原Decimal精度60/η=.0001/条件GCI均保持。
5. 任一FAIL或INCONCLUSIVE先停下复核；即便局部PASS，也只触发之后单独审查宽细22GiB/长期预算，不自动生成许可或运行。缺宽细2项时全局九量目标仍未完成。

中格已见窄槽横槽5→2.5nm差约1.59–1.61%，是保留的5nm参考敏感性风险。新最细格结果可能证明预设容差不满足；不得改门槛、丢点/方向、换最细参考，或用细格替换原5nm主模型评价以使公式变准。两窄几何三格只支持规定扩散缩放路径的联合离散敏感性，不等于全域网格独立/误差上界。G4 v1锁及原3%/5%预测合同不动，未新拟合。

## 资源与工作量

原分批方案要求可用RAM≥4GiB、磁盘≥11GiB，本轮不降低。末次只检查北京时间2026-10-24T18:49:56.300717+08:00：可用RAM约16.85GiB、磁盘约339.84GiB，满足；未来启动及每项前重查。swap不作可用RAM，不关闭用户程序或删除旧结果来满足门槛。

最坏原始诊断数值矩阵约178.25MiB，另有线性窗口输出及临时工作区；reader最大995328核心节点，按2KiB/节点+1GiB预算约2.90GiB，验收前同样要求4GiB空闲。此预算与零步RSS/旧帧回归分别报告，新细格真实峰值仍待计算/验收后测定，不能将零步当正式峰值保证。

用对应已验收中格四项的实测秒数按节点8倍、同物理时间步数4倍即32倍缩放，场景合计6.43小时；沿用旧慢样本的最大步数工作量外推138.58小时。均不是预计完成时间或严格上界；新格缓存、输出、负载和停止步数可能变化。不能为缩短时长改统计窗、周期、物性或收敛规则。

## 冻结与最终运行前核查

release SHA256 `680c2af160ad85e0af32184e3eafe56964c9a859e9f26e2ac67e1ace92bbb02c`，绑定3803本机输入路径；旧保护集合3682路径保持（包含旧输入、旧中格原始/验收，合并重叠，不相加）。上游证据、源码/binary/依赖/头文件、四项协议/配置/入口/验收比较程序、零步/测试和资源预算均绑定。已存在release拒绝原地重绑；启动日志和运行锁属于可变记录，科学输入和wrapper绑定。

从项目根、D4和/tmp运行默认只检查均exit0、will_run=false；隔离tmux按交付的直接参数形式--check、明确窗格check:0.0读取exit0。没有启动steady或创建正式batch，没有影响用户现有tmux会话。源码、原协议/数值门槛、中格冻结文件/原始记录、历史FAIL及G4锁保持；无Git提交/推送。

当前停点为“本机技术准备完成、命令可交付，用户未启动”。唯一NEXT_COMMAND.txt只启动这4项，结束即停。项目状态与交接已同步后再交付；命令已交不等于计算完成。宽细2项、预测16+4继续关闭；重拟合另立模型v2并在保留预测结果前重新冻结。

证据：preparation_verdict.json、final_preflight.json、resource_budget.json、case_budget4.csv、implementation_provenance.json、final_integrity.json；新阶段evidence/preparation、prebinding_review、cli_prebinding、upstream12_bundle、scalar_adapter_regression与flow_reader_regression及各独立exit/resource；新阶段PROTOCOL/release/NEXT_COMMAND和原中格独立验收入口。流场数据语义沿用前轮paraview-publication实际reader/有效液体/单位/来源核查原则，不以画面代替数值门槛。
