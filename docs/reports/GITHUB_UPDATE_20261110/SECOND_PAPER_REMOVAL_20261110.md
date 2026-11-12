# 第二篇内容移出 GitHub 说明（2026-11-10）

## 一句话结论

第二篇（液滴／两相路线）的 **941 个文件** 已从版本控制里移除，`.gitignore` 已加规则防止再进来；
第一篇完全没动。**改动已在本地提交，还差在您自己的终端执行一条推送命令**（我这边没有推送权限）。

## 已经生效的部分

上一轮「9 月以来所有资料补齐」已经推送成功：远程文件从 1168 个变成 9517 个，五件母本都在。
（您当时贴的 `9bad48a..ac4b15a` 就是这次。）

## 本次做了什么（两笔本地提交，尚未推送）

| 提交 | 内容 |
|---|---|
| `16a1cdd` | 移除根目录两个不该上传的文件：`test.txt`（35 字节测试残留）、`tmp_jain2017.txt`（Jain 2017 论文全文 35 KB，有版权风险）。本地文件都还留着。 |
| `c5522fd` | 第二篇 941 个文件移出仓库（约 23.4 MB） |

### 移出的 941 个文件

| 目录 | 数量 | 内容 |
|---|---:|---|
| `CASE/09_dynamic_liquid_gas/` | 771 | 相场/两相主算例：alpha_c、ab_diffusion、source3d、target_prevalidation、laplace 扩展、actual_mobility 复核等 |
| `CASE/07_filling_dynamics/` | 86 | F2_dynamic_v1/v2/v3、F2_z_compression_fast、F3_z_compression_dynamic |
| `grooveDNS/stage3_ex240_local/` 下三处 | 59 | phasefield_minimal_validation、freesurface_minimal_validation、right_angle_freesurface、step6G 接触角验证报告 |
| `CASE/plans/` 液滴与润湿计划 | 10 | 液滴 R2-XY 协议、下压路线、润湿校准、模具接触角、固化胶选型等 |
| `CASE/D_series/D1_nanoimprint_droplet_filling/` | 9 | D1 纳米压印液滴填充 |
| `CASE/08_droplet_inplane/` | 3 | R2XY_confined_patch |
| `docs/reports/D1_existing_run_check_20261016.*` | 2 | 两相接触角 80°/104° 校准核对（明确属第二篇） |

### 特意保留的

- **`CASE/06_filling_dynamics/`（34 个文件）** —— 按您的选择保留。这里是 G3-h 高度扫描和单相压缩，属于第一篇。
  里面的 `generate_height_source.py` 和 `height_matrix.csv` 都在，所以被删掉的 `f1_single_phase_h50/h75/h125.cpp`
  （只是第二篇几个工作目录里的**生成副本**）随时能重新生成，第一篇复现一步不少。
- 第一篇的正文、补充材料、结论、投稿派生件、全部验证报告、图表与数值，一个都没碰。

## 核验结果

- 第二篇各路径在版本控制里的文件数：**全部 0**。
- 仓库受控文件：**9517 → 8575**（HEAD 树与索引一致，都是 8575）。
- `.gitignore` 实测：第二篇路径被忽略，`CASE/06` **没有**被误伤。
- 本地磁盘：`CASE/09_dynamic_liquid_gas` 5.2 G、`CASE/07_filling_dynamics` 426 M，原样都在。
- `docs/reports` 下 434 个目录用第二篇关键词（droplet／phasefield／freesurface／contact_angle／wetting／r2xy／液滴／润湿／接触角／相场／下压／移动边界／两相）扫过，**0 命中** —— 这棵树整体属于第一篇。
  之前看起来"494 个文件提到第二篇"，其实是 `AI_HANDOFF`、`SIM240_AI_CONTEXT` 这些状态文件的历史快照顺带提到目录名，不是第二篇的内容。
  `URV_*`、`SDI_*`、`GDI_*` 三个代号也查过了，都是第一篇的数值验证（URV1_SMOOTH_H30 光滑基准、GrooveDarcy 实现审计）。

## 需要您做的一件事

在您自己的终端（`dell@dell-OptiPlex-Tower-Plus-7010`）里执行：

```bash
cd /home/dell/yuanyuanxu/SIM240 && git push sim240 main
```

这一次会把两笔提交一起推上去（先删两个临时文件，再删第二篇）。

> 为什么我不能代推：这台会话的 SSH 目录属于 root，`git ls-remote` 直接报 `Permission denied (publickey)`，
> 密钥在您自己的账户下。所以推送必须您来执行。

## 另外两件事，请您定

1. **仓库目前是公开的（PUBLIC）** —— 匿名访问 GitHub 接口能拿到仓库信息。里面现在有内部 IP、未投稿草稿、以及 56 份论文全文提取文本（约 4.4 MB）。
   建议在 GitHub 网页 → Settings → 拉到最下面 Danger Zone → Change visibility 改成 **Private**。这一步只有您能操作。
2. **`CASE/reports/` 下有 35 个文件，本地已删但远程还在** —— 我没有提交这 35 个删除动作。
   因为它们在 `docs/reports/` 里没有同名的替代文件，提交删除就等于从 GitHub 上永久消失（历史里还能找回）。
   远程继续留着更安全，可以保住 G2/G3 那批审计记录。如果您确实要清干净，告诉我，我再单独处理。

## 附：本次没有做的事

没有新增任何计算或数值验证（`run_id = null`），没有编译、没有跑求解器、没有进下一个 Gate，
没有改动五件母本、补充材料、结论、MANIFEST、authority 和任何数值/编号。
