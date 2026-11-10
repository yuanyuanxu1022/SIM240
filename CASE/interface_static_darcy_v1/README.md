# SDI-v1：C01双程序运行包

2026-10-30。用途：验证同一平均Darcy模型的K→J与D→U→HU接口。两端独立装配压力系统；解析答案只由结果检查器使用。

- [原始协议](common/PROTOCOL.md)：SDI-v1原文副本，阈值保持原值。
- [二维程序](two_dimensional/darcy2d.cpp)：C++17、正交有限体积、CG/对角预条件、读K。
- [OpenFOAM程序](openfoam/application/depthAveragedDarcyFoam.C)：Foundation13、张量有限体积、PCG/DIC、读D、物理压力Pa；z一层empty，无第二份壁面阻力。
- [只读结果检查器](analysis/check_results.py)：从已完成的原始CSV、退出码、输入哈希重算压力/流量误差、恢复K、逐单元守恒、侧漏、能量及两端差异，不调用求解器。
- [启动脚本](scripts/run_c01.py)：默认仅检查，`--execute`才启动；只允许C01，不存在自动下例或重跑。
- `common/release_manifest.json`：源码、程序、网格、输入、运行库和检查工具的校验绑定。`reports/preparation.json`为编译与静态证据。

当前已编译并准备C01平均域网格；已经做输入读取、OpenFOAM矩阵装配审计，**没有压力迭代或流动结果**。检查器使用内存中的人造数据做功能测试，不能把其通过当成C01运行通过。首次编译审计输出的Info打印API错误及修正记录保存在reports/preparation_attempts，未删除失败记录。

此阶段的geometry_PASS只指512单元合成平均域；不是实际沟槽几何验收。NUMERICAL_GATE仍NOT_EVALUATED，RESULT_PASS=null，无新流动run_id。已有项目D4、参考资格、历史FAIL、投稿状态不受本包影响。

首例输入：24×48μm，H=125nm，μ=0.001Pa·s，槽沿y，V2，x两端过压24Pa/0Pa，y两边不穿流。其他SDI-v1算例只有设计，本包不批量生成或运行。

本包使用本机OpenFOAM13和当前动态库；不是跨机器直接可运行的容器镜像。换机器或升级库须重新编译/审计/封装，不能绕过校验。

用户启动位置：这台Linux机器的普通终端。只需下面一条命令，tmux会在后台顺序执行C01的两个程序。每端最多300秒、2GiB、单进程；任一失败就停止，无自动重试。运行目录若存在则拒绝覆盖。

```bash
tmux new-session -d -s sdi-c01-v1-20261030 'cd /home/dell/yuanyuanxu/SIM240/CASE/interface_static_darcy_v1 && exec python3 scripts/run_c01.py --execute --run-id SDI_C01_v1_20261030_01'
```

这条命令已准备不等于已经执行。运行输出将位于 `runs/SDI_C01_v1_20261030_01/`；其中execution.json分别记录两个退出码，logs/保存完整日志，run_manifest.json绑定该次输入/程序/源码副本。结束后由新一轮任务分析已有输出，启动脚本不会自动运行验收或改Gate。

后续结果读取器的参数为`--run-dir <已完成目录> --report <新报告路径>`。缺失/不完整证据返回NOT_EVALUATED，不把退出0当科学验证。新报告存在时拒绝覆盖。此处暂不交付第二条终端命令。

本任务按已读scientific-writing技能组织进度与证据；软件结构及算术由本轮实现，未进行独立人工验收。流程文献与科学适用边界见[协议入口](../../docs/reports/Static_Darcy_interface_protocol_20261030/README.md)。
