# 相关文献完整书目信息（逐项核对版）

**核对日期**：2026-10-17
**核对方式**：Crossref REST API 实时查询（`https://api.crossref.org/works/{DOI}`），非记忆、非二手页面
**原始返回**：见本文件末尾 §5

---

## 1 Ban & Bonnecaze 2021（您问的这篇）

### 1.1 核心字段（Crossref 实测，逐项确认）

| 字段 | 值 | 来源确认 |
|---|---|---|
| 题名 | Minimizing filling time for ultraviolet nanoimprint lithography with templates with multiple structures | Crossref `title` |
| 作者 | Yang H. Ban; Roger T. Bonnecaze（**两位，无第三人**） | Crossref `author` |
| 期刊 | Journal of Vacuum Science & Technology B, Nanotechnology and Microelectronics: Materials, Processing, Measurement, and Phenomena | Crossref `container-title` |
| 卷 | **39** | Crossref `volume` |
| 期 | **1** | Crossref `issue` |
| 文章号 | **012601**（**无起止页码**，AIP 采用文章号制） | Crossref `article-number` |
| 印刷出版 | 2021-01-01 | Crossref `published-print` |
| 在线出版 | **2020-12-16** | Crossref `published-online` |
| 出版社 | American Vacuum Society（AIP Publishing 发行） | Crossref `publisher` |
| ISSN | 2166-2746（print）/ 2166-2754（online） | Crossref `ISSN` |
| 类型 | journal-article（同行评审正刊） | Crossref `type` |
| DOI | **10.1116/6.0000648** | Crossref `DOI` |

### 1.2 可直接粘贴的三种格式

**GB/T 7714-2015（国内期刊/学位论文常用）**

```
BAN Y H, BONNECAZE R T. Minimizing filling time for ultraviolet nanoimprint
lithography with templates with multiple structures[J]. Journal of Vacuum Science &
Technology B, 2021, 39(1): 012601. DOI: 10.1116/6.0000648.
```

**APA 7th**

```
Ban, Y. H., & Bonnecaze, R. T. (2021). Minimizing filling time for ultraviolet
nanoimprint lithography with templates with multiple structures. Journal of Vacuum
Science & Technology B, 39(1), 012601. https://doi.org/10.1116/6.0000648
```

**BibTeX**

```bibtex
@article{Ban2021Minimizing,
  author  = {Ban, Yang H. and Bonnecaze, Roger T.},
  title   = {Minimizing filling time for ultraviolet nanoimprint lithography with
             templates with multiple structures},
  journal = {Journal of Vacuum Science \& Technology B},
  year    = {2021},
  volume  = {39},
  number  = {1},
  pages   = {012601},
  doi     = {10.1116/6.0000648}
}
```

### 1.3 四个容易写错的地方

1. **没有起止页码**。写成 "39(1): 1-12" 或 "39: 12601" 都是错的。AIP 该刊自 2010 年代起用六位文章号，正确写法就是 `39(1): 012601`。
2. **年份有 2020/2021 两种说法**。在线 2020-12-16、印刷 2021-01-01。**引 2021**（印刷年，也是卷 39 的归属年）。若审稿人用在线年，可加注 "(online 16 Dec 2020)"。
3. **作者只有两位**。不要因为题名与本组其他论文相近就加上 Jain 或 Cochrane —— 那两位是 Jain 2017 的作者，不是这篇的。
4. **DOI 前缀是 10.1116**（AIP/AVS 专用），不是 10.1016（Elsevier）。写成 10.1016/j.jvstb... 是常见笔误。

---

## 2 Ban & Bonnecaze 2020（同系列前一篇，常用于配对引用）

| 字段 | 值 |
|---|---|
| 题名 | Optimal placement of droplets for UV nanoimprint lithography |
| 作者 | Yang H. Ban; Roger T. Bonnecaze |
| 期刊 | Journal of Vacuum Science & Technology B（全称同上） |
| 卷(期) | **38(2)** |
| 文章号 | **022601** |
| 印刷 / 在线 | 2020-03-01 / 2020-03-20 |
| DOI | **10.1116/6.0000030** |

```
BAN Y H, BONNECAZE R T. Optimal placement of droplets for UV nanoimprint
lithography[J]. Journal of Vacuum Science & Technology B, 2020, 38(2): 022601.
DOI: 10.1116/6.0000030.
```

```bibtex
@article{Ban2020Optimal,
  author  = {Ban, Yang H. and Bonnecaze, Roger T.},
  title   = {Optimal placement of droplets for UV nanoimprint lithography},
  journal = {Journal of Vacuum Science \& Technology B},
  year    = {2020},
  volume  = {38},
  number  = {2},
  pages   = {022601},
  doi     = {10.1116/6.0000030}
}
```

> 注意：博士论文第 2 章脚注把版权年写作 2021，但该文实际出版年为 **2020**。以卷期为准。

---

## 3 Jain et al. 2017（本项目基线公式的原始出处）

| 字段 | 值 |
|---|---|
| 题名 | Fluid flow in UV nanoimprint lithography with patterned templates |
| 作者 | Akhilesh Jain; Andrew Spann; Andrew Cochrane; P. Randall Schunk; Roger T. Bonnecaze（**五位**） |
| 期刊 | Microelectronic Engineering |
| 卷 / 页 | **173 / 62–70** |
| 出版 | 2017 年 4 月 |
| DOI | **10.1016/j.mee.2017.04.001** |

```
JAIN A, SPANN A, COCHRANE A, et al. Fluid flow in UV nanoimprint lithography with
patterned templates[J]. Microelectronic Engineering, 2017, 173: 62-70.
DOI: 10.1016/j.mee.2017.04.001.
```

```bibtex
@article{Jain2017Fluid,
  author  = {Jain, Akhilesh and Spann, Andrew and Cochrane, Andrew and
             Schunk, P. Randall and Bonnecaze, Roger T.},
  title   = {Fluid flow in UV nanoimprint lithography with patterned templates},
  journal = {Microelectronic Engineering},
  year    = {2017},
  volume  = {173},
  pages   = {62--70},
  doi     = {10.1016/j.mee.2017.04.001}
}
```

> 注意：这篇**有**起止页码（62–70），与上面两篇 AIP 文章不同，别混着写。

---

## 4 博士论文本身（仅在需要引"完整推导/未发表章节"时用）

```
BAN Y H. Fluid Dynamics of Thin Films in Semiconductor Manufacturing Processes[D].
Austin: The University of Texas at Austin, 2021.
```

```bibtex
@phdthesis{Ban2021Dissertation,
  author = {Ban, Yang H.},
  title  = {Fluid Dynamics of Thin Films in Semiconductor Manufacturing Processes},
  school = {The University of Texas at Austin},
  year   = {2021},
  type   = {Ph.D. dissertation},
  note   = {Supervisor: Roger T. Bonnecaze}
}
```

**引用优先级**：期刊版 > 博士论文。理由：前者经同行评审，且卷期页可被审稿人一键核验；博士论文用于"第 3 章比期刊版多出的那部分内容"或"完整公式推导"。

---

## 5 三篇的年份-卷-文章号速查（防串行）

| 简称 | 卷(期) | 文章号/页码 | 年 | DOI |
|---|---|---|---|---|
| Jain 2017 | MEE **173** | **62–70**（页码） | 2017 | 10.1016/j.mee.2017.04.001 |
| Ban 2020 | JVST B **38(2)** | **022601**（文章号） | 2020 | 10.1116/6.0000030 |
| Ban 2021 | JVST B **39(1)** | **012601**（文章号） | 2021 | 10.1116/6.0000648 |

> 记忆口诀：**38 卷配 022601（2020），39 卷配 012601（2021）**。卷号与文章号前两位不相关，容易记反。

---

## 6 Crossref 原始返回（可复核）

### 6.1 10.1116/6.0000648

```json
{
  "title": ["Minimizing filling time for ultraviolet nanoimprint lithography with templates with multiple structures"],
  "author": [{"given": "Yang H.", "family": "Ban"}, {"given": "Roger T.", "family": "Bonnecaze"}],
  "container-title": ["Journal of Vacuum Science & Technology B, Nanotechnology and Microelectronics: Materials, Processing, Measurement, and Phenomena"],
  "volume": "39", "issue": "1", "page": null, "article-number": "012601",
  "published-print": {"date-parts": [[2021, 1, 1]]},
  "published-online": {"date-parts": [[2020, 12, 16]]},
  "publisher": "American Vacuum Society",
  "ISSN": ["2166-2746", "2166-2754"],
  "type": "journal-article"
}
```

### 6.2 10.1116/6.0000030

```json
{
  "title": ["Optimal placement of droplets for UV nanoimprint lithography"],
  "author": [{"given": "Yang H.", "family": "Ban"}, {"given": "Roger T.", "family": "Bonnecaze"}],
  "volume": "38", "issue": "2", "article-number": "022601",
  "published-print": {"date-parts": [[2020, 3, 1]]},
  "published-online": {"date-parts": [[2020, 3, 20]]}
}
```

### 6.3 10.1016/j.mee.2017.04.001

```json
{
  "title": ["Fluid flow in UV nanoimprint lithography with patterned templates"],
  "author": [
    {"given": "Akhilesh", "family": "Jain"},
    {"given": "Andrew", "family": "Spann"},
    {"given": "Andrew", "family": "Cochrane"},
    {"given": "P. Randall", "family": "Schunk"},
    {"given": "Roger T.", "family": "Bonnecaze"}
  ],
  "volume": "173", "page": "62-70",
  "issued": {"date-parts": [[2017, 4]]}
}
```

---

## 7 在论文里怎么用这三篇（建议句式）

**引言里建立"行业在用 + 从未被标定"：**

> 该闭合自 Jain 等[1]提出后，在同组后续工作[2,3]中仍按原式使用，其验证重点转向气液界面的毛细压力而非渗透率本身。

对应 `[1]=Jain2017`, `[2]=Ban2020`, `[3]=Ban2021`。

**方法节引润滑方程 + 有效渗透率张量形式：**

> 采用与 Ban 和 Bonnecaze[3]相同的 Reynolds 润滑表述，将图案阻力等效为渗透率张量 K，满足 ∂H/∂t = ∇·(K·∇p/μ)。

**如果审稿人问"你们和第 3 章多出来的内容有何不同"：**
答：第 3 章处理多图案交界处的布滴与填充时间，仍把 K 当输入；本文不涉及布滴优化，而是标定 K 本身的数值误差。对象不同，不构成重叠。
