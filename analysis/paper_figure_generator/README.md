# SIM240 论文图自动生成模块

该模块将最新或指定的 G2/G3 输运结果转换为论文级图件、图注和结果描述。

输出结构：

```text
paper_figures/
├── figures/*.png
├── figures/*.pdf
├── figure_captions.md
└── result_discussion.md
```

图片使用 matplotlib，PNG 输出 600 dpi；PDF 同步输出，坐标标签使用论文格式。

运行 G2：

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/paper_figure_generator/generate_paper_figures.py \
  --case G2
```

运行 G3：

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/paper_figure_generator/generate_paper_figures.py \
  --case G3
```

`auto` 模式优先使用已有 G3 数据库，否则使用 G2。模块只读 results/CSV 和数据库，不修改 OpenLB 或原始结果。
