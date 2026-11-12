# v2.1 静态准备：主代理独立复算记录

日期：2026-11-11。角色：主代理独立复算，不是新的方法审查。本文件只记录"报告里的数字能不能自己复现出来"，以及下一道闸的实际状态。没有启动任何求解、编译、网格工具或 mapFields。

## 一、结论

报告所述六项身份与测试结论，逐项复算成立。唯一需要作者决定的是**启动解锁方式**——见第三节，这不是缺陷，是设计上的硬闸。

## 二、逐项复算

| 项 | 我的做法 | 结果 |
|---|---|---|
| release 身份 | `sha256sum release_manifest.json` | `f1531d40…d98ffc292`，与报告一致 |
| 212 份本地文件 | 读清单逐份重算 sha256 | 212 份齐全，**0 缺失、0 漂移** |
| 23 份外部工具/依赖 | 逐份重算（含 `mapFields`、`libOpenFOAM.so` 等） | 23 份齐全，**0 缺失、0 漂移** |
| 合成边界测试 | 在正式目录 `python3 -m unittest discover -s tests` | **46 项全过**（0.7 s），含 0/0 一致、0/非0 不一致、缺 End、p/Uz 未达标、tight 未达标、原生优先级、cap 位次 |
| 规则与分支 | 读 `prepared_manifest.json` | `version=v2.1_stopping_fix`；normal `p/U/v=1e-10`、tight `=1e-11`；`groove.T=['Ux','Uz','p']`、`flat_P=['v']`、`flat_T` 带 `negligible_ratio=1e-9` 与两项 0.1% |
| 预算口径 | 同上 | `coarse=1800 s`、`flat=3600 s`、`mid=14400`、`fine/tight=43200` |
| 平板例外范围 | 逐份读 26 个 `case.json` | 仅 `h75_d0_T_flat` 为 `true`；`h75_d0_P_flat` 为 `false`；全部沟槽 `false` |
| 受审候选 = 正式目录 | 13 份绑定文件逐个比对 | 12 份同字节；`CURRENT_STATUS.md` 不同，但它不在 212 份绑定清单内（属正常的状态页更新） |
| 旧归档恢复 | 重算 `_archive/v2_68453dac/` 十份绑定文件 | `prepare.py=ce5e51ff…`、`freeze_release.py=c069653f…`、`postprocess.py=8bdd470e…`、`run_one.py=0b9bdce7…` 全部回到受审值；`MANIFEST.json` 已注明由 `714cf113…` 的 tar 逐字还原 |
| 离线读取器 | `postprocess.py` 跑正式树 | 不崩，输出 `INCOMPLETE` / `NOT_STARTED`，26 个算例全 `NOT_EXECUTED` |
| 运行记录 | `find prepared` | runtime 0、referenceEvidence 0、receipt/log 0 |
| 历史状态 | 读 v1 与主统计 | v1 T 平板 `-8.943434%` `REFERENCE_CHECK_FAIL` 原样；`map36_evidence.csv` = `9fe4324f…`，与 `scientific_inputs.json` 一致 |

## 三、下一道闸：启动锁是硬的，现在关着

`run_one.py:161-162`：

```python
if json.loads(release.read_text()).get('formal_review_status') != 'ASTRA_FINAL_STATIC_RECHECK_COMPLETE':
    raise RuntimeError('Specified Astra final static recheck is pending; this prepared release cannot launch')
```

冻结清单现在的值是 `PENDING_ASTRA_V21_RECHECK`，**两者不相等**。所以即便作者口头授权，现在执行 `--execute` 也只会在启动求解器之前抛异常退出——一个网格文件都不会生成。

这是有意的设计：代码自己不会因为"报告里写了审查完成"就放行。要把"审查已完成"这件事变成可执行状态，只能改清单里的字段。

### 要改的就是两个值

| 字段 | 现在 | 解锁后 |
|---|---|---|
| `formal_review_status` | `PENDING_ASTRA_V21_RECHECK` | `ASTRA_FINAL_STATIC_RECHECK_COMPLETE` |
| `numerical_execution_authorized` | `false` | `true` |

### 改完会发生什么

- `release_manifest.json` 的 SHA 从 `f1531d40…` 变成一个新值 X——文件变了，哈希必变。
- **212 份本地文件与 23 份外部工具的指纹一个都不受影响**：清单不把自己列进自己的 `sha256`，`verify_release()` 也不校验清单自身。所以 `verify_release()` 仍然全过。
- 启动时 `run_one.py:189` 会把当次的清单原样存成 `runtime/release_snapshot.json`，回执里写 `source_manifest_sha256=X`。也就是说**跑的是哪一版，事后可以从回执反查字节**：拿 X 与 `f1531d40…` 做 diff，只会看到这两行不同。
- 受审身份出现一处张力：Astra 的结论是对 `f1531d40…` 给的，解锁后启动的是 X。严格按 Astra 自己的条件（"同一 release 逐字节同步才能引用本结论"），X 并不等于受审版本。

## 四、三种解锁方式，请作者选

**方案 A：直接改这两个字段，出一份单字段差异说明**
新 SHA 记为 X。同时记录：X 与 `f1531d40…` 的差异仅这两行、212+23 指纹完全一致、受审代码与绑定输入零改动。启动回执同时记 X 与 `f1531d40…`。
优点：最省事、可审计、不动代码。缺点：启动的版本严格说不是受审字节。

**方案 B：清单不动，另加一份授权文件**
新建 `AUTHORIZATION_v21.json`（写明授权人、时间、案例、受审 SHA），并让 `run_one.py` 改读它而不是读清单字段。
优点：`f1531d40…` 一个字节都不动，受审身份完整保留。缺点：改 `run_one.py` 本身就是改代码，又产生新 SHA，等于绕了一圈还多改一个文件。

**方案 C：先解锁再复审一次**
把"解锁后的 release"当作一次被审变更，交由 Astra 再核一次（只核这两行差异），通过后才启动。
优点：链条最干净，任何时点都不存在"跑的版本没被审过"。缺点：多一轮审查。

我的建议是 **A**：差异是纯控制元数据，且可以做字节级证明，回执里双 SHA 并存已经足够追责。但这是发布控制决定，按约定由作者定，我不擅自改。

## 五、解锁后的启动顺序

必须先 P 平板、再 T 平板，两者都通过才能进沟槽——这一条已经硬编码在 `run_one.py:172-177`（任一沟槽算例启动前，会要求两份平板的 `read_case` 状态都是 `LOCAL_CHECKS_PASS`）。

单次一条命令（另一台机器/另一个终端，先 source 环境）：

```bash
tmux new -s v21flat 'source /opt/openfoam13/etc/bashrc && cd /home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2 && python3 run_one.py --case h75_d0_P_flat --execute 2>&1 | tee /tmp/v21_P_flat.out'
```

P 通过后，把 `--case h75_d0_P_flat` 换成 `--case h75_d0_T_flat`、会话名换成 `v21flatT`，同理再跑一次。

参考工时：46080 格 × 60000 步上限 × 5.886e-7 s/格/步 ≈ **1627 s（约 27 分钟）**，两例都在 3600 s 上限之内。这只是估算，不是工期承诺。

## 六、本轮我明确没有做的事

没有启动求解、没有编译、没有跑 blockMesh/checkMesh/mapFields、没有改任何 `CASE/` 下文件、没有改 release 状态位、没有改论文数字或历史 FAIL。本文只新增记录，不改受绑定文件。
