# 配套方法补充材料

阅读入口：[补充材料S1—S11](SUPPLEMENTARY_METHODS.md)。

本目录为2026-10-24建立的作者审阅版补充材料编号稿，配套`SIM240_中文稿_导师审阅版_20261022.md`。它不构成投稿、发布、全部引文核验或物理验收；本轮不纳入并行D4新运行或变更冻结候选关联式。

- [旧索引—正式编号对应表](SUPPLEMENT_NUMBER_MAP.csv)：11行，一一对应原索引S1—S11与新稿锚点。
- [表S1](Table_S1_run_inventory.csv)：52项D2/D3地图及附加检查。
- [表S2](Table_S2_refinement.csv)：8行双网格方向比较。
- [表S3](Table_S3_periodic_checks.csv)：18项基准周期复制/多力记录。
- [表S4](Table_S4_grid_archive.csv)：9行历史三网格记录，保留失败状态。
- [表S5](Table_S5_conditional_gci.csv)：2026-10-27按作者采用范围增补的6项条件性Richardson/GCI估计；三项依赖历史细横槽失败点，限定说明见S9。
- `input_hashes.json`：编号前读取的支持资料及选定原始结果哈希。
- `REVISION_NOTE.md`与`verification.json`：本轮正文修改、编号和链接检查记录。

CSV方向：parallel/P为沿槽+y，perpendicular/T为跨槽+x，oblique为所标角度。K_m3/K5/K2_5单位m³；R单位Pa·s/m³；加速度单位m/s²；h/d/dx单位nm。K_change_percent和E5/E2_5单位为百分数，E_change_percentage_points单位为百分点。recorded_PASS是原文件记录值，不能替代本轮独立Gate结论。独立exit也不是整体通过结论。

原始路径按项目根目录`/home/dell/yuanyuanxu/SIM240`解析。外移或公开打包时需重新核对路径映射与附件覆盖；本轮未复制大型场文件、第三方论文全文或历史可执行文件。

2026-10-27的表S5/正文同步记录见[本次修订报告](../GCI_author_sync_20261027/REPORT.md)；既有verification.json是2026-10-24编号工作的历史记录，本次检查另存，不覆盖旧证书。
