# SIM-EC1XT240 模型名称纠正报告

## 结果

正式物理/模型名称已统一声明为 **SIM-EC1XT240**。本轮只修改6个非冻结文件中的名称
表述，并新增勘误、清单和本报告；没有修改物理模型、源码算法、边界、参数或仿真结果。

> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

## 修改和新增文件

- 修改`PROGRESS_SUMMARY.md`：
  - 把“已验证完整 EX240 版图”纠正为“已验证完整 SIM-EC1XT240 版图”；
  - 在文件开头加入正式名称与历史路径保留声明；
  - 其中所有仍含旧缩写的内容都是反引号内的历史路径。
- 修改`grooveDNS/stage3_design_review/stage3_geometry_and_case_definition.md`：纠正标题及
  6处正文物理名称，保留3处历史路径引用。
- 修改两张既有设计SVG：只纠正图题，不改几何图形或文件名。
- 修改`grooveDNS/stage3_ex240_local/postprocess_geometry.py`：纠正未来生成图的两处标题，
  保留历史VTI输入路径；没有运行脚本或覆盖旧PNG/PDF。
- 修改`grooveDNS/stage3_ex240_local/stage3_revised_plan.md`：纠正标题。
- 新增`SIM_EC1XT240_NAMING_CORRECTION.md`：统一勘误和后续写作规则。
- 新增`sim_ec1xt240_name_correction_inventory.md`：首次扫描的全部文本文件、行号、分类
  及42个路径名完整列表。
- 新增本报告。

没有修改任何其他既有文件。

## 有意保留的历史标识

以下类别继续保留旧缩写：

- `stage3_ex240_local`、`ex240_homogenization`等既有目录；
- `ex240_h65_dns`等二进制、源码文件名和Makefile target；
- 所有`output/ex240_*`历史run-id、日志、结果及VTK数据集名称；
- `OpenLB_EX240_progress_report.md`等既有报告文件名；
- 冻结报告正文、生成脚本、manifest中的路径、命令和hash记录。

C++审查未发现需要本轮重命名的实际变量、函数、类、namespace或macro。对历史目标和
路径做符号替换会影响Makefile、回归命令、结果路径与hash，因此没有执行。

二次扫描中，排除本轮新增的勘误/清单/报告文件后，原项目仍有81个命中行、37个文件、91个
出现：大写旧缩写22次、小写历史标识69次、混合大小写0次。活动总览仅剩一处大写命中，
它位于历史文件路径`grooveDNS/OpenLB_EX240_progress_report.md`；其余用户可见物理名称已
改用SIM-EC1XT240或由勘误文件明确覆盖。冻结报告中仍存在的旧正文不做追溯改写。

## 冻结文件与hash

首次扫描命中的34个受保护既有文件（不含上述6个允许修改的非冻结文件）在修改前后的
联合SHA-256均为：

`6d724cda5b8ef246d4919bbe696f0518dbadb90f679ba8ead927bff7bf74cb00`

因此没有改变这些冻结报告、结果、manifest、脚本或源码的字节与hash。编译过程也没有
重写任何历史结果。

## 构建检查

只执行编译检查，没有启动仿真：

```text
cd grooveDNS/stage3_ex240_local
make openlb-zouhe-pressure-candidate
make openlb-zouhe-preconversion-longrun
```

两个目标均返回退出码0，并报告现有可执行文件为up to date。历史目录名保留没有破坏
构建或依赖路径。

## 一致性确认

- 正式名称：**SIM-EC1XT240**；
- 冻结文件hash：未修改；
- 仿真：未运行；
- 几何、Bouzidi、Zou/He pressure、材料号、converter、物性、壁速、压力、周期和192条
  跨周期固壁link：全部未修改；
- C650、2000步观察设置及所有历史数值结果：全部未修改。
