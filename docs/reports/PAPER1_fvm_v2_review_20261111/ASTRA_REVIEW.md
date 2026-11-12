# v2 停止判据与层间延拓：指定模型静态审查工作稿

日期：2026-11-11。审查角色：作者明确请求的 GPT-6 Astra High 方法/实现自审；不是期刊指派审稿、人工独立验收、数值参考接收或启动许可。作者负责最终科学声明。使用 peer-review 的范围、证据定位、影响和最小修复框架；本任务没有期刊评审委托，按作者已授权的项目自审处理，不捏造期刊许可或工具 intake PASS。审查限于当前 v2 配置、代码、两个 manifest、测试和旧判据/旧审查；未运行测试、编译、网格工具、mapFields 或求解器，未读取保留预测场。主代理另行负责指纹全检、合成测试和项目状态同步。本子任务唯一写入文件为本报告。

## 裁定

**当前 v2 不能获得“静态复核无剩余阻塞”的结论，不能据本报告解除执行闸门。** 分层预算与初场延拓方向可保留，但“平板 Uz 已接近零，因此所有横槽沟槽都可以只看 Ux”不成立；当前实现还会绕过 tight 更严格的停止条件，并存在来源绑定和接收器健壮性缺口。以下要求只涉及原固定四几何六方向的实施，不要求新增几何、第四档网格、物理实验或重拟合。

这是对新 v2 拟议判据的审查，不追溯把 v1 的 T 平板 FAIL、S4/D4 历史 FAIL 改成 PASS。v2 仍为 PREPARED_NOT_RUN，发布标记为 PENDING_ASTRA_V2_RECHECK，numerical_execution_authorized=false；本次目录快照 prepared 下 runtime/referenceEvidence 数均为 0。

## B1：平板零分量例外被不加条件地用于真实沟槽；“收紧”说法不成立

位置：PROTOCOL.md §3.3、§4.1；prepare.py:254–263；run_one.py:202–230；postprocess.py:112–127、225–237；tests/test_stopping.py:47–51。

观察：fallback 只要求最后一条 Ux 初始归一化残差≤1e-9，完全不检查 p 和 Uz，缺少 p/Uz 日志也能令 numeric_ok=true。测试还把忽略 Uz 作为预期成功行为。P 同样一律用1e-9，低于其原生普通 v 1e-10、tight v 1e-11 的严格程度。

物理原因：平板横槽解允许 Uz=0；真实台阶沟槽的流线在槽口/侧壁附近上下弯曲，Uz 是需解的物理分量。源码的 z 动量预测包含 −∂p/∂z，虽然体力 z 分量为零，不能说该方程总源项恒为零。离散 p、Ux、Uz 与面通量是耦合问题：Ux 单个方程的归一化初始残差小，不证明另外两项或整个耦合解已稳态。

本机 Foundation 13 原生实现核对：singleRegionConvergenceControl.C:167–180 对所列字段逐项检查；convergenceControlTemplates.C:82–83 对向量使用 cmptMax(initialResidual)。旧字符串因此代表原冻结 p/U 控制，不能表述成没有数值含义的字符串检查。v2 改普通 U 1e-10→1e-9，又加主分量 OR 分支，实质改变了接受的运行集合。重新解析同一日志并核回执是记录一致性改进，不等于科学门槛变严。

最小修复方向：为真实沟槽保留完整耦合停止证据；最省争议的准备修复是沟槽恢复原冻结 p/U/v 控制以及 tight 的十倍收紧，平板机器零分量问题单独形成明确限定的例外。若确需替换原生判据，必须先写成新的操作性接收条件，说明所有物理活跃分量和压力如何检查，明确例外适用条件，再审其实现。不能把固定1e-9主分量分支叫“阈值未变/收紧”。本报告不凭空给一个能保证精度的新残差数值。

PROTOCOL.md 的“U残差1e-9对应K误差约1e-4%”也缺乏成立依据。两条平板轨迹点不足以建立跨几何/网格/初场的残差到K误差界；后一个点还含空间离散误差。应改为平板诊断观察，不作真实沟槽误差保证。“初场只改变迭代路径”在充分求解同一唯一离散解时成立，不能先假定当前停止判据已保证该前提。

## B2：tight 可使用与 fine 相同的 fallback，削弱原定代数误差检查

位置：prepare.py:186–204；run_one.py:218–230；postprocess.py:112–127、282–287；PROTOCOL.md §3.3。

观察：字典确实收紧了线性容差和原生停止触发，但 numeric_ok 不读取 level 或该例 exit_trigger，fine/tight 一律只用1e-9。所以 tight 跑到上限、未满足自己的更严原生条件时，仍可按与 fine 相同的宽条件被接收。tight 又由 fine 原场初始化，K差≤0.05%可能只是两次共享未消除的外迭代误差；“K几乎不变”不能替代 tight 自己达标。

最小修复：tight 必须独立满足其预先冻结、确实更严格的停止条件，不能走普通层同一 fallback。保持 abs(Ktight/Kfine−1)≤0.05% 的原检查，不额外加新算例，也不禁止从 fine 起步。延拓本身合理；错误是把同一停止精度的两次近似不变误当作已经完成更严格求解。

## B3：结束/上限/字符串的实际逻辑与协议不一致

位置：run_one.py:204、218–230；postprocess.py:125–127、225–237；PROTOCOL.md §3.1、§4.1。

观察：C1 宣称日志末尾必须 End，但 runner 与后处理都未检查它；控制器只看退出码0。日志中的任意“solution converged”子串构成充分分支，没有与末轮、指定算法和对应数值检查绑定。该 OR 分支也直接反驳了协议“还要求主导分量达到1e-9”的 AND 式说明。对可信原生日志，字符串通常由同一残差检查产生，因此不是在断言已有真实日志曾被假通过；这里是静态接收语义与书面承诺不一致。

此外，协议§3.1和prepare.py注释说“跑到上限记未收敛”，而 fallback 正是可以在到达上限后据最后残差判通过；运行回执 stopped_by='numeric' 会把事后判定写成求解停止原因。源码没有实时主分量退出逻辑，实际可能由endTime停止。

最小修复：统一一份规范和两处实现。记录实际停止原因（原生收敛/迭代上限/墙钟/异常）与事后稳态判定两个字段；明确到底禁止上限运行通过，还是在新版本中允许其经完整判据接收。检查最终 End；字符串只能与正确末轮和冻结控制对应，不能绕过必需数值条件。不得在旧v1结果上倒推应用新规则。

## B4：种子来源没有完整绑定；mapFields 不在外部工具指纹里

位置：run_one.py:111–146；postprocess.py:171–237；freeze_release.py:44–46；release_manifest.json external_sha256。

观察：seed_fields 仅检查源 receipt 的 solver_converged 布尔，然后用last_time挑源目录中最新可读v或U/p。它不核该源receipt的case_id/run_id/release、独立退出/末轮收敛、源原生场与mesh哈希，也不要求所选时刻就是源receipt绑定的最终时刻。回执保存映射后目标场哈希，但没有保存/验证源receipt哈希、源run_id与实际读入源场哈希。后处理不验证seed字段和mapFields日志。外部工具清单只绑定blockMesh/checkMesh，没有新增加的mapFields。

影响：源场在生成receipt后被替换，或者新增一个未绑定的更晚目录，当前控制器仍可能使用它。目标充分收敛时种子通常不应改变解，但这不能替代协议要求的完整运行来源；也不能用本次更弱的停止条件预先保证初场误差已消除。

最小修复：启动前验证源记录的身份、实际绑定最终原场和mesh及收敛依据；从该绑定时刻取场，禁止“任意最新目录”。在目标receipt记录source run_id、source receipt/release及实际输入field哈希、源/目标时刻、mapFields身份与日志/退出；后处理对所需seed链作一致性验证。coarse/mid无需新增0.1%功率或截面硬门槛；源所需证据是既有来源、有限性、几何、完成和正确停止条件。

## B5：零残差会使接收器崩溃

位置：postprocess.py:231–234、271–274。

观察：若日志 measured=0，且回执 reported=0，则abs(reported/measured−1)引发ZeroDivisionError。零残差可能出现在已解好的延拓初场，属于合法输入边界；当前assess只捕获ValueError/KeyError/OSError，整个评估会中断。此为逐行静态确认，本子任务未执行复现代码。

最小修复：对0与有限非负残差显式处理，使用适当的绝对/相对一致性判断；不以零作分母。必要的合成检查应包括0/0一致、0/非0不一致、缺末尾End、p/Uz未达标、tight未达严格条件和种子绑定损坏；这些是代码边界检查，不是新增物理算例。

## N1：冻结文件内粗网格预算冲突

prepare.py:31及prepared_manifest/case.json实际coarse墙钟为3600秒；PROTOCOL.md§3.1、run_config.md与CURRENT_STATUS.md写1800秒。独立确认prepare.py当前SHA与release一致，所以是受冻结文件间口径不一致，不是未绑定的临时源码漂移。两者均只是上限，不能据此预测实际工期。请依据作者已授权预算统一文档和配置；本报告不自行将1800扩大为3600，也不更改任何值。

## 保持正确的范围与边界

- coarse/mid不强加最细层0.1%能量/截面门槛，是旧事前协议和首次Astra修复结论，必须保留。不能用新增全层硬门槛掩盖本次停止逻辑缺口。
- 既有fine/tight/flat功率、截面及面通量/体积通量自检有用，但它们只是有限全局约束，不单独证明完整耦合残差或连续K误差。三档K变化也须建立在每层达到各自停止条件的前提下。
- 初场延拓写0.5而保留冻结0目录，作为避免输入漂移的设计是合理的；本子任务未实际运行mapFields，不将CURRENT_STATUS的历史自报机制测试升级成独立实测。
- 分层预算只控制资源，不是收敛保证。达不到门槛时保留失败并停止，不自动增配或改阈值。
- 无新增数值结果、run_id、参考资格或科学Gate通过。本报告没有修改release审查位；修复后需对实际新快照重新复核，才可讨论是否完成静态准备。

## 审查快照

| 文件 | SHA256 |
|---|---|
| PROTOCOL.md | 7c216ffbe82f813996b3783a674413e05d41845af87e57b0ca8adee45a419457 |
| run_one.py | 0b9bdce70fd8a862c70c1119a95a74be227e8849e1f388a8e1ebc32f057066b2 |
| postprocess.py | 8bdd470e5da280d3e35879c92ed2a81915be4cdcc18e7ed574d4fbcd5145ca4b |
| prepare.py | ce5e51ff7184342813cb87d2338d299fc53b7f7b14c79954d80145218e404cb4 |
| freeze_release.py | c069653f6631fa37dfc1cc9bd48e8c53256220b4ec6d99c31dfd4b92d4b54190 |
| prepared_manifest.json | 511a07692a54058d8fd15109f67f0d607ce61bd79978bcf2703304443ee91a40 |
| release_manifest.json | 68453dac9777b701b2f044ad168e4631694b7c553c7553fbef0c0b041beb53e1 |
| tests/test_stopping.py | 4249006a54e2ced6b0bf5bef35460dbe1bfb5f1d4152ae9bd5e5db54ec21dd0b |

其他依据：docs/reports/PAPER1_claim_acceptance_contract_20261110/DECISION_RULES_V1.md；docs/reports/PAPER1_fvm_preparation_review_20261110/ASTRA_REVIEW.md；当前solver/paper1StokesReference.C；本机/opt/openfoam13原生solutionControl源码。未外传未公开项目内容进行搜索。本子任务只逐项比对上述四份主要源码/协议的release SHA，未声称已重算211本地+22外部全表；全表检查由主代理独立记录。
