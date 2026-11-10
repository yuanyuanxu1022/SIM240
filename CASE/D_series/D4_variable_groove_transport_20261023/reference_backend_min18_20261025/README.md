# 18项矩形基准：隔离后端、静态接口与记录准备 v1

2026-10-25。用户授权实现本准备包，不启动求解。承接待审修订 `D4_REFERENCE_CONSTRAINT_BUDGET_MINIMUM_20261025_DRAFT_v2`。本准备版本 `D4_REFERENCE_MIN18_STATIC_PREPARATION_v1` 仅为软件准备，**不冻结或启用参考协议、容差、运行许可或新模型**。

已在本目录的 `.backend` 安装独立Conda环境：Python 3.12.15、DOLFINx/Basix/FFCx 0.11.0、dolfinx_mpc 0.11.0、PETSc/petsc4py 3.25.6、MPICH 5.0.1，共131个Conda包。环境及缓存默认不进入Git。导入与接口检查已执行，使用实数float64、单进程；不是求解器或周期边界的数值验收。base包元数据是否保持由最终evidence/verification.json核对，不凭安装命令推断。

## 入口和严格范围

- `prepare.py` 无参数默认只核18项输入，写JSON到标准输出，不导入有限元后端。
- `--mode describe` 输出完整参数；`--planned-id` 只接受18项白名单中的ID。`--config` 可读取该描述中的单项对象，必须与原计划完全一致，未知键、尺寸/容差/权限变化、重复JSON键和非对象输入均拒绝。
- `--mode stage --prep-id <唯一准备编号>` 仅在本目录 `prepared_records/` 的新子目录生成静态记录和18项输入/模板；可用白名单ID缩小到单项。已存在或链接目录、路径越界拒绝。每次前后绑定输入哈希，失败保留准备失败记录。
- **没有execute/solve/steady模式，没有运行命令或求解实现。** 即使给执行选项也只拒绝；描述、记录和准备退出码均不是求解退出码。
- 原18项CSV逐字节复制到 `protocol/benchmarks18.csv`，绑定SHA `fb784710590acdbdc1ac5abdc33cdc542d3643bd4df28d49a85cb12902e85aee`。原审查/方法/AGENTS来源绑定见 `protocol/review_input_hashes.json`，不改原文件。

## 已实现的接口与尚未实现的环节

|文件|已实现|未据此宣称|
|---|---|---|
|src/contract.py|白名单、几何/单位、周期/规范说明、源哈希、默认拒绝求解|实际网格、自由度或周期配对已创建|
|src/physics.py|平板解析量、独立显式制造解及源项、解析节点计数|有限元场、数值收敛或误差界|
|src/symbolic_forms.py|标量Poisson和物理压力Stokes的惰性UFL表达；MMS源项用符号求导|JIT编译、矩阵组装或求解|
|src/records.py / schemas/|输入、准备日志/退出码、全部为空的未来记录模板、模板JSON Schema|完成证书、真实残差、实际原始场或运行验收|
|environment/|实际环境、精确包URL/MD5与包SHA元数据、依赖锁、只导入的API探测|运行资源足够、压力零空间/周期约束已正确施加|

压力使用 `−Δu+∇π=f`，弱式两个压力/连续项取负；驱动只施加一次。后续周期约束须覆盖P2边中点，固壁交点速度优先固定，压力边界顶点配对；一个压力常数零空间、rhs兼容和面积积分去均值。当前仅记录这些约束及核实对应后端API存在，**实际MPC应用、压力零空间构造与测试尚未实现**。

平板内部用长度h、速度ah²/ν和运动学压力ah缩放；K=h³Ĵ（m³）、J=ah³Ĵ/ν（m²/s）、R=ρa/J（Pa·s/m³）。MMS采用非均匀人为源项，Ĵ=1/6仅检验泛函，不能当物理K。MMS能量输入须采用一次∫f·u或标量∫fv，不能沿用单位均匀驱动功率。

`future_record_template.json` 必须标记 `TEMPLATE_NOT_A_RESULT`，真实运行ID、求解退出码、输入前后哈希、真实残差、原始网格/场/周期映射/积分、守恒/能量/剖面、资源等均留空。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。未来实际求解记录及其完整性/数值验收器仍需另行实现，不能将模板填几个值就当合格结果。

## 核查、资源与停止点

`tests/test_static_preparation.py` 检查白名单与来源变动、异常配置、求解选项拒绝、输出越界/链接/覆盖、18项记录、单位与解析表达。`tests/check_symbolic_ufl.py` 只声明抽象符号域，不创建实际计算网格，检查表达形状及独立显式源项与UFL求导的对应；无JIT、组装或求解。这两类检查均不产生数值精度PASS。初次测试夹具和UFL求值API问题的修正记录保留在evidence，不改历史计算FAIL。

导入/API证据见 `evidence/backend_probe.json`，二进制摘要和动态链接见同目录记录。环境规格 `environment/environment.yml` 是需求；精确重建应按 `environment/conda-linux-64.explicit.txt` 与 `package_metadata.json`，并在新机器重新探测，不复用本机环境路径或验收结论。依赖快照只绑定软件版本，不是科学公式冻结。

动态链接核查采用仅对子进程设置的 `LD_LIBRARY_PATH=<本包>/.backend/lib`，并核对Python实际加载的核心共享库均来自隔离目录。未设置该路径时独立ldd工具曾报告找不到库，原始检查保留为first_attempt证据；不通过修改全局环境或放宽缺库条件解决。当前静态准备记录由 `evidence/current_preparation.json` 指向；较早准备快照保留但不代表当前来源绑定，更不是实际运行。

安装后本机 `du -sh` 显示环境约1.8G、独立缓存约638M（遍历与硬链接口径有重叠，不当精确相加总量）。这些是环境准备开销；原拟议4GiB可用内存/4GiB结果磁盘/2小时试验额度未实测、未生效，不能据此保证18项可完成。

本轮到静态准备为止。下一任务若继续，应先审查并准备真实网格、MPC消元、唯一压力规范、组装/提取与完整运行记录接口；仍可保持不求解。实际基准运行安排、草案门槛冻结与运行许可是后续独立工作。全部沟槽、NS、OpenLB停止控制、重新拟合及预测不在本包实施范围；旧窄槽网格FAIL和G4 v1保持。

## 软件来源与辅助方法

后端路径依据[DOLFINx官方Conda安装说明](https://github.com/FEniCS/dolfinx#conda)及[dolfinx_mpc作者安装说明](https://github.com/jorgensd/dolfinx_mpc#conda)，2026-10-25核对；实际版本以本包安装记录为准，不使用主分支文档推断固定版已验证。周期API取自本机已安装0.11.0接口。

使用scientific-critical-thinking技能界定方法证据与准备边界。辅助软件引用：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。2026-10-25核对当前v2及作者信息；该引用不是CFD精度依据。
