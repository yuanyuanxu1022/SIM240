# 跨机可复现性验证（PASS-1 / PENDING-T）

记录时间：2026-11-12 04:05–04:10 CST
性质：**诊断验证，不是正式计算**。未写入任何冻结目录，未产生正式 run_id，未改动冻结源码/协议/阈值/已有结果。

---

## 1. 为什么做这件事

要把剩余 T 算例或未来的批量算例放到实验室服务器上跑，前提是：**同一个算例在服务器上单核算出来的数字，必须和本机逐位一致**。如果不一致，服务器产出就不能当"参考答案"，只能当"参考解的近似"，参考资格链会断。

这是一个**此前从未验证过**的假设。本报告给出验证方法与第一份结果。

---

## 2. 机器与环境对照

| 项 | 本机（已接受结果的来源） | 10.103.102.55（jj-Rack-Server） |
|---|---|---|
| CPU | Intel i7-13700，AVX2 | AMD EPYC 9B14（Zen4，AVX-512），96 核 |
| 频率 | 5.1 GHz | 3.7 GHz |
| OS | Ubuntu 24.04.4 | Ubuntu 22.04.5 |
| glibc | 2.39 | 2.35 |
| libstdc++ 最高符号 | GLIBCXX_3.4.33 | GLIBCXX_3.4.30 |
| g++ | 13.3.0 | 11.4.0 |
| OpenFOAM | /opt/openfoam13，本地自编译 | /opt/openfoam13，服务器自编译（同为 `linux64GccDPInt32Opt`） |

### 2.1 一个必须先解决的阻塞

冻结的 `bin/paper1StokesReference`（sha256 `73b1f633…`）在服务器上**无法运行**：

```
libstdc++.so.6: version `GLIBCXX_3.4.32' not found
```

本机二进制要求 GLIBCXX_3.4.32，服务器系统库只到 3.4.30。尝试直接搬运本机 libstdc++.so.6 也不可行——它自身依赖 `GLIBC_2.38`，服务器只有 2.35。

⇒ **跨机执行必须在本机重新编译**（`wmake`，服务器 gcc 11.4.0、OpenFOAM 13 默认 `-std=c++14 -O3`）。服务器编译产物 sha256 为 `21a60334aa52c49971dae4766035dfb57d5eebeb2577f4cfc8dad65fd980c8d5`，与原 `73b1f633…` 不同——这是**预期内**的，不是源码改动。

源码一致性：服务器编译前先核对 5 个网格文件哈希，与本地回执逐项相同：

```
points    b16a073d57e18ab3e9ff64ca212900e2146cc30f27b8e63d7612a5890ff32dc5  ✓
faces     7ef013c2513ed35ececb5ce69d0884730e9ee7adee07616fabfbd295b12fd9d8  ✓
owner     0aea48aa7f9a24299a3b77f12692c0c417360d804c04b66df62cca5d9cb56c21  ✓
neighbour fbd508f022fbe01d0cf124e3de9c6460b631d7bafbe2121a551c382fc5d64b16  ✓
boundary  c5083ae3db14fec318bb1ee23df0b2fa612c37542d624225d520d928deeed6a6  ✓
```

运行环境：`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`，单进程，与冻结协议"单进程、线程 1"一致。

---

## 3. PASS-1：平板 P 方向 —— **逐字节一致**

算例：`h75_d0_P_flat`（d=0 平板，解析锚 K=h³/12，标量 Poisson，2 轮即收敛）。
本地基准 run_id：`h75_d0_P_flat_20261111T145810_b5a3ecc4`。

| 产物 | 本机（已接受） | 服务器（本次） | 判定 |
|---|---|---|---|
| 末场 `2/v` | `e94fa7a30f355946dad4740b971087914095ff8635beb071aaa0cc4443a0df08` | 同 | **一致** |
| 证据 `cells.csv` | `c69caf96f64c7c2cb9732e249ce7c38bf6f433e6f31034a506b6bc3afdd82267` | 同 | **一致** |
| `v` 末残差 | 4.523055253555043e-14 | 4.5230552535550432e-14 | **一致（同一浮点数）** |
| 外迭代数 | 2 | 2 | 一致 |
| 停止原因 | native_convergence | native_convergence | 一致 |

**结论**：即使编译器（gcc 13.3 vs 11.4）、CPU 指令集（AVX2 vs AVX-512）、glibc（2.39 vs 2.35）、OpenFOAM 自编译库都不同，P 方向的场与证据文件仍**逐字节相同**。

限定：P 是标量 Poisson，2 轮外迭代即收敛，线性求解路径短，**不足以代表 T 方向**（压速耦合、6 万轮外迭代、误差累积机会多得多）。

---

## 4. PENDING-T：平板 T 方向 —— 计算中，未出结论

算例：`h75_d0_T_flat`。本地基准 run_id `h75_d0_T_flat_20261111T154355_ab7f0638`：
- 60000 轮外迭代（**触及迭代上限**，非原生收敛）
- 末残差 Ux 3.43e-13 / Uz 2.93e-09 / p 1.60e-13，`flat_exception_used=true`
- 墙钟 988.7 s

本地基准哈希（待比对）：

```
60000/U    62b8717bd212ab14dea9d4f4466a4d853905beb9666b813a09ca6a2faa24cf3f
60000/p    bd10d35d589edf3e9bd611b401fe0bc111db674fd3adca729c9a929937a10028
60000/phi  6c29a90d82c66fcfa1d781ad88d7234aa4e78414e63f0dc2b9c32fa2ae9b8b9b
cells.csv  e1097ab60a104874254f63564ca0a4c2ca10b49e1482ff189eaab469de876d1b
x_faces.csv 31a2dc559af90fdb25a15fe4c7f6946c775aa8c0b8ecd1471ad899d265db904e
```

服务器侧：`/home/yuanyuan/SIM240_crosscheck_20261112/flatT`，PID 79458，启动 04:07。
预计墙钟约 20–25 min（服务器单核慢约 30%，且同机有他人 Fluent 负载）。

**未完成前不得把"服务器可用于参考解"写成结论。**

---

## 5. 判定规则（事前定，事后不改）

| 结果 | 含义 | 后续许可 |
|---|---|---|
| T 全部哈希一致 | 参考解跨机逐位可复现 | 服务器可用于参考解批量计算（每机自编译、记录各自二进制哈希） |
| T 哈希不一致但 K 相对差 < 1e-12 | 末位漂移，不影响物理 | 需明确"服务器 K 仅作交叉参考，不替代本机参考值" |
| T 哈希不一致且 K 差 > 1e-12 | 参考资格不跨机 | 服务器只用于 OpenLB 主算例与两相扫描，不承载参考解 |

---

## 6. 治理提示（必须与结果一起看）

如果 T 也一致，服务器仍**不能**直接沿用 `73b1f633…` 这个二进制身份：
- 冻结 release 绑定的是本机编译产物；
- 服务器必须用自己的 gcc 重编，产物哈希不同（本次 `21a60334…`）；
- 若将来在服务器上产出"正式参考值"，必须在回执里记录**该机自己的** `executable_sha256`，并附一份跨机一致性验证记录（即本报告），否则参考资格仍按"未跨机验证"处理。

本报告不改变任何已有 PASS/FAIL，不改变论文数字，未触碰 `CASE/paper1_fvm_stokes_reference_v2/prepared/**`。

---

## 7. 复现命令

服务器侧目录：`/home/yuanyuan/SIM240_crosscheck_20261112/`

```bash
source /opt/openfoam13/etc/bashrc
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /home/yuanyuan/SIM240_crosscheck_20261112/flatT
pgrep -af paper1StokesReference          # 是否仍在跑
tail -3 log.solver                        # 进度
ls 60000 2>/dev/null && sha256sum 60000/U 60000/p 60000/phi referenceEvidence/*.csv
```
