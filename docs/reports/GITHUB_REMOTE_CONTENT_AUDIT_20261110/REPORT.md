# GitHub SIM240当前内容与第二篇材料只读核查

核查日期：2026-11-10（Asia/Shanghai）。仓库为yuanyuanxu1022/SIM240，不是另一个SIM240_code_figures_data共享库。通过已登录gh的GitHub REST API直接读取元数据、main提交、完整递归树及5份代表文件；不以本地删除或本地跟踪分支代替远端证据。

## 结论

GitHub当前main仍包含第二篇核心研究材料。远端HEAD为ac4b15a2a9208685bf8ebf4918999c1263484720；完整树未截断，9517个文件。仓库API显示visibility=public。用户关心的第二篇不是已从GitHub消失：本地清理提交c5522fd尚未出现在远端main，它列出的941个删除路径现在仍全部存在于远端。

这些941项是此前拟清理范围的路径核对，不是本轮对每个文件科学归属的重新裁决。CASE/07下代表README实际上描述单相压缩复用；D1目录也包含单相沟槽绘图状态/剖面表，不能把清理范围内每项都称为第二篇独有成果。后续若继续执行删除，应核实混合/共享材料的范围；本轮不推送，不扩大删除。

## 当前仓库概况

| 顶层目录 | 远端文件数 | 内容概况 |
|---|---:|---|
| docs | 4547 | 论文、补充方法、审查/审计、改前快照、交接、打包脚本等 |
| CASE | 4252 | 第一篇单相/参考核验/静态接入及第二篇两相/历史材料混存 |
| grooveDNS | 547 | 历史沟槽程序与相场/自由表面等基础程序 |
| figures | 73 | 图件及相关文件 |
| analysis | 49 | 分析脚本等 |
| paper_database | 14 | 论文数据相关文件 |
| tools | 12 | 工具程序 |
| paper_figures | 10 | 论文作图相关文件 |
| transport_database | 3 | 输运数据表 |
| notebooks | 2 | 笔记本 |

其余8个根目录文件包括README替代入口SIM240_项目总览.md、AGENTS.md、CLAUDE.md、规则、Allrun、.gitignore，以及此前本地清理但仍在远端的test.txt与tmp_jain2017.txt。当前树也含部分历史png/pdf/vti/vtm/log，不能照本次新增入库排除规则推断整个远端没有这些类型；本轮未认证完整原始数据备份。

第一篇当前两母稿、两补充、结论及两投稿派生件共7个核心路径已直接在远端树确认，完整路径见verification.json。

## 第二篇已确认在远端的材料

- CASE/09_dynamic_liquid_gas/：771个文件。代表README明确题为“第二篇论文：液气动态条件下的Kxx、Kyy对比”。包括RESISTANCE_COMPARISON.md（系数/阻力比较草案）、PARAMETER_CARD.md、材料目录、成对输运与机理方案、target_prevalidation、Laplace2000、alpha_c_validation、ab_diffusion_validation、source3d_validation等。文件是研究设计、源码、参数、检查与分析记录，不据此认定第二篇完成或验证放行。
- CASE/08_droplet_inplane/：3个文件，含R2XY受限液区README、源码及短段报告。
- grooveDNS/stage3_ex240_local/下本地清理范围：freesurface_minimal_validation 22、phasefield_minimal_validation 17、right_angle_freesurface 20及step6G相场接触角报告1，共60项，均在远端。
- 此前清理范围其余路径也仍在：CASE/07_filling_dynamics 86、D1_nanoimprint_droplet_filling 9、CASE/plans所选10、D1_existing_run_check两份。它们包含旧路线、复用和支持材料，未将每项判作第二篇独占。
- CASE/06_filling_dynamics/34个文件亦存在；既有范围将G3-h高度扫描/单相压缩保留，不应仅凭filling名字认定两相。

本轮未找到并核实一份完整的第二篇投稿正文；“第二篇内容已在GitHub”指已直接确认的研究目录与文件。不能从按文件名搜索“第二篇/Paper2”无命中，反推没有第二篇内容，目录README正文已提供明确身份。

## 本地与远端差异

远端main：ac4b15a。当前本地HEAD：c5522fd；中间还有16a1cdd临时文件清理。因此本地移出版本控制不等于远端完成删除。旧状态里的941是删除清单条目数，当前完整本地HEAD树为8575；树总数还受提交中新文件等影响，不用简单相减替代逐路径核对。

本轮GitHub API读取成功；旧SSH公钥访问失败记录不等于无法通过现有gh API读取GitHub，也不据此断言推送权限状态。

下一动作若仅查看，可直接访问固定提交下的第二篇README与目录；如用户后续要求远端移除，先核混合/共享路径再执行已授权范围，并说明普通删除不会清除旧提交历史。本轮只读核查，不推送已有提交、不删除本地文件、不改可见性或历史。

## 证据与本轮改动

remote_tree.json保存完整远端路径及Git blob标识，inventory.json保存计数，second_paper_paths_still_remote.txt保存941条远端仍在的路径；remote_samples保存5份从固定blob获取的代表文件。verification.json记录来源、范围、未验证项和无远端改动。同步项目当前状态与便携交接，其余源码、稿件、数据与索引不改。

无新增计算或数值验证、run_id=null，无编译/求解/拟合/新Gate/提交推送/上传/删除/投稿，既有科学状态与FAIL保持。
