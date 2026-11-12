# 配置与当前执行状态（v2）

状态：PREPARED_NOT_RUN。源码编译沿用 v1（源码与二进制哈希未变），不代表数值验证。

OpenFOAM Foundation 13；本地独立程序 paper1StokesReference。只用 CPU 单进程；不含惯性、时间推进、两相、滑移或动态壁面。nu=1e-6 m²/s，rho=1000 kg/m³，a=1e5 m/s²，真实 P=240 nm/w=120 nm；模型 Ly=1 nm，由严格沿槽不变性消去，Aplan=P*Ly。正式 K 单位 m³。

固定六方向：h75/d100 P/T；h25/d100 T；h50/d120 P；h125/d120 P/T。每方向 dx=1.25/0.625/0.3125 nm；最大单元 454656（h125_d120_T_fine）。另 6 份同最细网格 tight 输入和 h75 平板 P/T 两份，共 26 份。

v2 相对 v1 的三处改动（详见 PROTOCOL.md §3.1–3.3、§4.1）：

| 项 | v2 取值 |
|---|---|
| 稳态迭代上限 | coarse 6e4 / mid 1.2e5 / fine 2e5 / tight 2.5e5 / flat 6e4（上限，非计划量） |
| 墙钟上限 | 1 800 / 14 400 / 43 200 s；flat 3 600 s |
| 初场 | mid←coarse、fine←mid、tight←fine，mapFields 写入 `0.5/`；coarse 与 flat 用零场 |
| 残差控制（仅提前退出触发） | 普通 p 1e-10、U 1e-9、v 1e-10；tight 各收紧 10 倍 |
| 收敛判定 | 退出码 0 + 日志 End，且（日志 `solution converged` 或主导分量残差 ≤1e-9），由 postprocess 独立重算 |

另一固定约束：4 GiB 地址空间、单文件 256 MiB、blockMesh/checkMesh 各 120 s、mapFields 900 s。

接受目标未变：独立参考自身 0.1% 平板、1%/0.5% 网格变化、0.05% 求解收紧、0.1% 收支；接收后与 K5 差 ≤2%。基准输出采用方案 A：A 差 ≤2%、角差 ≤0.40 度。非连续误差界，不改 S4 及其他历史 FAIL。

当前没有 run_id，没有正式批准的启动批次。`release_manifest.json` 的 `formal_review_status` 为 `PENDING_ASTRA_V2_RECHECK`，`run_one.py` 会因此拒绝启动；须先完成指定模型复核并显式改写该位，才谈得上启动。实际启动时必须另有作者明确指令，并独立记录每份 run_id/退出码/源码字典/可执行文件与库/原场/资源/稳态证据。参考失败不自动重跑或换点。
