# v2.1 求解解锁：逐字节差异证明

日期：2026-11-11 14:55。授权人：作者（本轮会话）。方案：A —— 只改控制元数据，代码与全部绑定输入不动。

本文件是解锁动作的正式记录。它回答一个问题：**当前要跑的东西，和被 Astra 审过的东西，差在哪里？**

## 一、结论

| 项 | 值 |
|---|---|
| 受审 release SHA256（Astra 复核对象） | `f1531d4091a6279a5db2df5cff75875d279d4ffc981f52ae5502bedd98ffc292` |
| 当前 release SHA256（已解锁） | `97ae55ff9dbaad4c2aa58fbe3b3b5dac548f82400631ac5cd1e12c9ef96c13e5` |
| 文件字节数 | 27495 → 27601（+106） |
| **绑定指纹** | **212 + 23 = 235 项，两份清单逐项完全相同**，从磁盘重算 0 不一致 |
| 绑定文件本身 | 一字节未改 |
| 代码（`.py`） | 一字节未改 |

差异只有 3 行，且全部位于同一个 JSON 对象的末尾：2 个控制字段的取值，加 1 个新增的溯源键。**没有任何一个被绑定的字节发生变化。**

## 二、完整差异（`diff -u`，无省略）

对比对象：`docs/reports/PAPER1_fvm_v21_review_20261111/release_manifest_before_authorization.json`（= 受审原件副本，SHA256 已核为 `f1531d40…`）与当前 `CASE/paper1_fvm_stokes_reference_v2/release_manifest.json`。

```diff
@@ -241,6 +241,7 @@
     "/usr/lib/x86_64-linux-gnu/libz.so.1": "f61677c7bdb7c2aa2a243ea781bfd16afcb361cede7b4ef76127a9d8eb9a5242"
   },
   "revision": "v2.1_stopping_fix",
-  "formal_review_status": "PENDING_ASTRA_V21_RECHECK",
-  "numerical_execution_authorized": false
+  "formal_review_status": "ASTRA_FINAL_STATIC_RECHECK_COMPLETE",
+  "numerical_execution_authorized": true,
+  "reviewed_release_sha256": "f1531d4091a6279a5db2df5cff75875d279d4ffc981f52ae5502bedd98ffc292"
 }
```

- 第 241 行之前（含 212 项本地指纹与 23 项外部指纹）**完全未动**。
- `revision`、`status`、`openfoam` 三个字段未动。

## 三、为什么必须有第 3 个键

作者要求"回执里双 SHA 并存"，同时要求"不动代码"。这两条只有在清单自己携带被审 SHA 时才能同时满足：

`run_one.py` 在启动时做两件事（第 185–189 行，未作任何修改）：

```python
receipt = dict(..., source_manifest_sha256=source_hash, ...)   # = 97ae55ff…（当前）
(runtime/'release_snapshot.json').write_bytes(release.read_bytes())  # 整份清单拷贝
```

于是启动后的 `runtime/` 目录里同时存在：

| 位置 | 内容 | 含义 |
|---|---|---|
| `receipt.json` → `source_manifest_sha256` | `97ae55ff…` | 这次实际跑的清单 |
| `release_snapshot.json` → 文件自身字节 | `97ae55ff…` | 可离线复核的当次清单全文 |
| `release_snapshot.json` → `reviewed_release_sha256` | `f1531d40…` | 这份代码被谁审过 |

脚本结束前还会用 `receipt['release_unchanged'] = digest(release) == source_hash` 复核清单在运行期间未被改动，仍以 `97ae55ff…` 为基准，因此该检查照常工作。

如果没有 `reviewed_release_sha256` 这个键，双 SHA 并存只能靠改代码实现——那会改掉受审字节，代价比多一行 JSON 大得多。这是本方案的唯一"计划外"改动，特此明示。

## 四、235 项指纹逐项相同的证明

复算脚本（可原样重跑）：

```bash
cd /home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2
python3 - <<'PY'
import json, hashlib, pathlib
old = json.load(open('/home/dell/yuanyuanxu/SIM240/docs/reports/'
                     'PAPER1_fvm_v21_review_20261111/'
                     'release_manifest_before_authorization.json'))
new = json.load(open('release_manifest.json'))
print("sha256 equal         :", old['sha256'] == new['sha256'], len(old['sha256']))
print("external_sha256 equal:", old['external_sha256'] == new['external_sha256'],
      len(old['external_sha256']))
bad = 0
for table in ('sha256', 'external_sha256'):
    for path, expect in new[table].items():
        p = pathlib.Path(path)
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expect:
            bad += 1; print("  MISMATCH", path)
print("re-hashed from disk  :", len(new['sha256']) + len(new['external_sha256']),
      "mismatches:", bad)
PY
```

实际输出：

```text
sha256 equal         : True 212
external_sha256 equal: True 23
re-hashed from disk  : 235 mismatches: 0
```

另经脚本核对：`changed binding keys: NONE`（`sha256` 与 `external_sha256` 两个字典在前后两版中完全相等，不只是哈希值相等）。

## 五、解锁后仍然成立的四项检查

| 检查 | 结果 |
|---|---|
| `run_one.verify_release()`（重算 235 项后放行） | 通过 |
| 启动闸门条件 `formal_review_status == 'ASTRA_FINAL_STATIC_RECHECK_COMPLETE'` | 成立 |
| 合成边界测试 `python3 -m unittest discover -s tests` | 46/46 通过 |
| 离线读取器 `postprocess.py`（空树） | `INCOMPLETE` / 26 例 `NOT_EXECUTED`，不崩 |

## 六、有意**没有**改的东西

**`PROTOCOL.md` 第 3 行、`run_config.md` 第 3 行仍写着 `PENDING_ASTRA_V21_RECHECK`。** 这是刻意保留的：

- 这两份文件在 212 项绑定清单内。改一个字符，235 项证明立即失效，Astra 的"受审字节"也就不存在了。
- 它们描述的是**静态准备完成那一刻的协议状态**，属于受审快照的一部分。当前授权状态以 `release_manifest.json` 为准。
- 因此本目录会出现一处表面矛盾：文档说 PENDING，清单说 COMPLETE。**以清单为准**，因为只有清单是启动逻辑实际读取的对象（`run_one.py:161`），也只有清单能用 SHA 证明未被动过。

同理未改 `freeze_release.py`、`README.md`、`PROTOCOL.md`、`run_config.md`、任何 `.py`、任何 `prepared/` 下的输入。

## 七、`freeze_release.py` 重跑风险（重要）

该脚本是准备阶段的工具，现进入执行阶段后**不得再跑**：

```python
formal_review_status='PENDING_ASTRA_V21_RECHECK',
numerical_execution_authorized=False)
```

它不写 `reviewed_release_sha256`。重跑（尤其 `--refresh-preparation`）会造成三件事：执行锁退回、溯源键消失、产生第三个 SHA。保护措施是行为性的，不是代码性的：不要执行它。

首个算例产生 `runtime/` 或 `referenceEvidence/` 之后，该脚本自身的守卫（`Runtime evidence exists; cannot re-freeze this release`）也会拒绝。

## 八、不受影响的既有结论

- Astra 对新快照"剩余静态阻塞 0"的结论，针对 `f1531d40…`，与 `97ae55ff…` 的差异仅为上表 3 行控制元数据，不涉及任何被审代码或输入。
- 原 v1 T 平板 `−8.943434%` `REFERENCE_CHECK_FAIL`、S4/D4 历史 FAIL、三项资格 false 全部原样。
- 本轮 0 次求解、0 次编译、0 次网格工具、0 次 mapFields、`run_id=null`。
- 解锁不等于验收：P 平板、T 平板、六方向沟槽仍需各自独立通过完整判据。
