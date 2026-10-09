# F1_single_phase_compression

独立的单相 EX240 固定液膜高度 Case。该目录从现有 F1 框架派生，保留
D3Q19、ForcedBGK、tau=1、dx=2.5 nm、周期体力驱动和零速度 Bouzidi
边界；不包含空气、VOF 或动态移动边界，也不修改 G2/G3 原 Case。

## 高度与输出

支持 `h=50,75,125 nm`，每个高度分别生成 P（parallel）和 T
（perpendicular）可执行文件。最终 `result_summary.csv` 额外输出：

- `Q`：两截面流量的平均值（m3/s）；
- `deltaP`：周期体力等效压降 `rho*a*L_drive`（Pa），不是入口/出口压力差；
- `R_eff=deltaP/Q`（Pa s/m3）；
- `dissipation`：流体材料单元的耗散功率积分（W）；
- `fillRatio`：单相几何沟槽区域占据率，非两相界面填充率。

## 构建与运行

```bash
cd CASE/06_filling_dynamics/F1_single_phase_compression
bash scripts/build_height_matrix.sh
```

小规模几何预检：

```bash
bash scripts/run_precheck.sh 75 P
```

正式矩阵脚本会依次运行六个稳态点，可能需要较长时间；按项目协议应在
独立 `tmux` 会话中启动：

```bash
tmux new-session -d -s f1_single_phase \
  'cd CASE/06_filling_dynamics/F1_single_phase_compression && exec bash scripts/run_height_matrix.sh'
```

脚本不覆盖已有结果目录，每个运行保存 `run_manifest.txt`、`run.log` 和
`exit_code.txt`。程序退出码、`NUMERICAL_GATE`、几何审计和结果 PASS 必须
分开解释；本目录不改变任何 G2/G3 阈值或原始数据。
