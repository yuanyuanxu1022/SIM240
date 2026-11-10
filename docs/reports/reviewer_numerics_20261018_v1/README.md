# 复算入口

当前作者可读审查见`REPORT.md`；48次逐运行数值见`runs48.csv`/`runs.json`，36个模型误差及舍入V2评价见`map36.json`，历史原始网格/平板/C统计见`historical.json`，终检见`verification.json`。

用户后续强调黏度的补充见`VISCOSITY_AND_TEXT_ADDENDUM.md`；`viscosity_check.py`直接读取原始数据形成逐点`viscosity36.csv`与`viscosity_text_check.json`，并核对当前第1–5章。它指出不能虚构“正文36点都宣称mu15”，同时记录第4章仍存在的方向/单位/覆盖/归因错误。

本目录代码只做既有输出后处理，不启动求解器。默认解释器`/usr/bin/python3`具备VTK和NumPy。复现顺序：`recompute.py --vtk` → `historical_check.py` → `verify_artifacts.py`。输出只写本目录，不导入项目原有audit或拟合脚本，不变更原始结果或门槛。

证据ID：E-RUNS48=runs.json及其原始文件路径；E-SUMMARY=summary.json；E-MAP36=map36.json；E-HISTORICAL=historical.json；E-SOURCE-D2/D3=REPORT列出的求解器原始代码行；E-MANIFESTS=48原始run_manifest.txt；E-OPENLB=/home/dell/openlb/CITATION.cff与方案C原始manifest.json；E-POSTPROCESS=历史postprocess_grid.py对应原始行。代码/文字快照哈希见verification.json，不将这些ID本身当作证据。

已保留一次审查程序修正：初版VTI积分使用NumPy默认Float32累加，观察到最高0.0383%偏差；查明为审查器自身大量Float32累加误差，改为Float64累加后与高精度CSV最大相对差2.41e-9。它不是求解器错误，未据此形成审查问题。初版D3检查也在最终验收前按原源码改为交叉通量相对std；最终结果独立重跑后均通过。正式报告和JSON均为修正后的复算结果。

peer-review结构lint初次因缺作者/编辑栏目退出1；为避免把作者报告当外部审稿，随后补作者可见栏目及“不适用”的编辑栏目。无临床/统计清单适用于此确定性CFD任务；工具返回NO_BUNDLED_GUIDELINE_MATCH如实保留。流程schema通过不等于科学通过。人工作者仍须核对报告，不声称投稿已放行。
