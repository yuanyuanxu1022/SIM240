# SIM240 科研助手使用说明书

版本：v1.0

适用对象：

* SIM240 项目使用者
* Linux 初学者
* OpenLB/LBM科研计算用户
* 使用 VS Code、Codex、MCP 辅助科研的用户

# 1. SIM240 项目简介

SIM240 是基于 OpenLB 的纳米尺度流动模拟项目。

主要研究：

* 纳米沟槽真实几何流动
* 不同方向液体输运阻力差异
* 压力损失
* 渗透率
* 纳米尺度输运机制

核心计算流程：

```
真实几何结构

↓

OpenLB lattice转换

↓

LBM流动模拟

↓

数据分析

↓

论文图表
```

---

# 2. 项目目录说明

## CASE

位置：

```
CASE/
```

作用：

存放所有模拟任务。

例如：

```
CASE/G2_EX240_grid_convergence
```

表示：

G2 网格收敛与流阻分析。

主要内容：

```
build/
    编译程序

results/
    模拟结果

scripts/
    自动运行脚本

src/
    源代码
```

---

## grooveDNS

位置：

```
grooveDNS/
```

作用：

OpenLB核心代码。

包含：

* 几何定义
* lattice设置
* 边界条件
* 求解器

修改前需要确认影响。

---

## analysis

位置：

```
analysis/
```

作用：

模拟结果后处理。

例如：

```
analysis/G2_resistance
```

用于：

* 流量计算
* 压降计算
* 水力阻力计算
* 渗透率计算

---

## figures

位置：

```
figures/
```

保存论文图片。

结构：

```
figures/

├── pressure
│
├── velocity
│
├── resistance
│
├── validation
│
└── presentation
```

---

## docs

位置：

```
docs/
```

保存：

* 项目状态
* 研究计划
* 汇报材料
* 使用说明

---

# 3. Linux基础操作

## 查看当前位置

```bash
pwd
```

---

## 查看文件

```bash
ls
```

详细：

```bash
ls -lh
```

---

## 进入目录

例如：

```bash
cd CASE
```

返回项目：

```bash
cd ~/yuanyuanxu/SIM240
```

---

## 查看目录结构

```bash
tree -L 2
```

---

# 4. Conda环境使用

## Conda是什么？

简单理解：

> 管理Python运行环境的软件。

不同项目可以使用不同Python版本。

---

## 查看环境

```bash
conda env list
```

---

## 激活环境

例如：

```bash
conda activate sim240-analysis
```

成功后：

```
(sim240-analysis)
```

---

## 退出环境

```bash
conda deactivate
```

---

# 5. tmux使用

## 为什么使用tmux？

服务器运行计算时：

普通方式：

```
SSH关闭
↓
程序停止
```

tmux：

```
SSH关闭
↓
程序继续运行
```

---

## 创建任务窗口

```bash
tmux
```

---

## 离开任务

按：

```
Ctrl+b
```

然后：

```
d
```

---

## 查看任务

```bash
tmux ls
```

---

## 回到任务

```bash
tmux attach
```

---

# 6. 运行SIM240计算

进入项目：

```bash
cd ~/yuanyuanxu/SIM240
```

进入案例：

```bash
cd CASE/G2_EX240_grid_convergence
```

查看脚本：

```bash
ls scripts
```

运行：

```bash
bash scripts/run_grid_matrix.sh
```

---

# 7. 查看计算结果

查看结果目录：

```bash
tree results -L 3
```

查看日志：

```bash
tail -50 run.log
```

查看结果：

例如：

```bash
cat result_summary.csv
```

---

# 8. G2流阻分析流程

数据来源：

```
CASE/G2_EX240_grid_convergence/results
```

分析流程：

```
OpenLB计算

↓

result_summary.csv

↓

analysis/G2_resistance

↓

流阻数据

↓

论文图片
```

---

# 9. 数据分析

进入：

```bash
cd analysis/G2_resistance
```

运行：

```bash
python scripts/extract_g2_summary.py
```

输出：

```
results/G2_resistance_summary.csv
```

包含：

* 网格尺寸
* 流量 J
* 渗透率 Keff
* 有效阻力 R_eff
* Mach数
* 质量误差

---

# 10. Jupyter Notebook

作用：

快速查看数据、画图。

启动：

```bash
jupyter notebook
```

适合：

* 数据检查
* 曲线绘制
* 参数分析

---

# 11. MCP使用说明

## MCP是什么？

MCP：

Model Context Protocol

作用：

让AI理解整个SIM240项目。

普通聊天：

```
只能看到发送的内容
```

MCP：

```
代码

↓

文件

↓

结果

↓

文档

↓

项目结构
```

---

# 12. MCP常用指令

## 查看项目状态

输入：

```
总结SIM240当前研究进展
```

---

## 分析代码

输入：

```
分析EX240边界条件设置位置
```

---

## 分析结果

输入：

```
分析最新G2网格收敛结果
```

---

## 写论文

输入：

```
根据G2结果生成论文Results章节
```

---

# 13. VS Code使用

打开项目：

```bash
code ~/yuanyuanxu/SIM240
```

常用：

查看Markdown：

```
Ctrl + Shift + V
```

打开终端：

```
Ctrl + `
```

---

# 14. Git版本管理

查看修改：

```bash
git status
```

保存：

```bash
git add .
```

提交：

```bash
git commit -m "update SIM240"
```

---

# 15. 推荐科研工作流程

每天：

## 第一步

运行模拟：

```
CASE
```

↓

## 第二步

检查结果：

```
results
```

↓

## 第三步

分析：

```
analysis
```

↓

## 第四步

生成图片：

```
figures
```

↓

## 第五步

整理：

```
docs
```

↓

## 第六步

保存：

```
git commit
```

---

# 16. 常见问题

## 程序停止怎么办？

查看：

```bash
tmux ls
```

恢复：

```bash
tmux attach
```

---

## Python错误？

检查：

```bash
which python
```

---

## 不知道项目状态？

查看：

```bash
cat docs/SIM240_status.md
```

---

# 17. SIM240最终科研流程

```
研究问题

↓

几何建模

↓

OpenLB模拟

↓

结果输出

↓

自动分析

↓

论文图片

↓

论文撰写
```

目标：

建立一个完整的科研计算自动化平台。

