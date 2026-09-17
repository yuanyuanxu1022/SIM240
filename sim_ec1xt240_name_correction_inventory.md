# SIM-EC1XT240 名称纠正清单

## 扫描范围和规则

扫描根目录：`/home/dell/yuanyuanxu/SIM240`。首次扫描在任何名称修改之前完成，搜索
三种大小写形式：`EX240`、`ex240`和`Ex240`。排除`.git`以及编译目标、PNG/PDF、
VTI/VTM/PVD和OAS二进制内容，但另行扫描文件与目录名称。

首次文本扫描得到93个命中行、103个出现：大写形式35次、小写形式68次、混合大小写
形式0次，共40个文本文件。路径名扫描得到42个路径：7个目录、35个文件。

分类定义：A=文档正文/标题/注释；B=图题、输出描述或用户可见字符串；C=C++符号；
D=文件名；E=目录名；F=Makefile、脚本、运行命令或路径引用；G=历史输出、冻结报告、
manifest或哈希证据。一个位置可同时属于多个类别。

## 文本命中位置

|文件|行号|主要分类|本轮处理|
|---|---|---|---|
|`PROGRESS_SUMMARY.md`|25,76,80,99,141,157,172,173,178,179,180,181,182|A/F|纠正line 157的物理名称；其余均为历史路径引用并保留；新增正式名称声明|
|`grooveDNS/OpenLB_EX240_progress_report.md`|1,5,71,79|A/G|冻结历史进度报告，保留正文与文件hash；由新勘误覆盖名称解释|
|`grooveDNS/ex240_homogenization/Makefile`|1,7|F|构建目标/源码路径，保留|
|`grooveDNS/ex240_homogenization/ex240_h65_dns.cpp`|59,61,68,79|B/F/G|历史命令、run-id和VTK名，保留；无C++符号重命名|
|`grooveDNS/ex240_homogenization/ex240_h65_homogenization_report.md`|1,51,63,107|A/F/G|冻结结果报告及历史路径，保留|
|`grooveDNS/ex240_homogenization/homogenization_h65_summary.csv`|2,3|G|正式历史CSV中的run-id，保留|
|`grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907/result.txt`|1|G|历史run-id，保留|
|同目录`run.log`|1|G|历史run-id，保留|
|同目录`run_record.txt`|1,2|F/G|历史run-id和命令，保留|
|`grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907/result.txt`|1|G|历史run-id，保留|
|同目录`run.log`|1|G|历史run-id，保留|
|同目录`run_record.txt`|1,2|F/G|历史run-id和命令，保留|
|`grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907/result.txt`|1|G|历史run-id，保留|
|同目录`run.log`|1|G|历史run-id，保留|
|同目录`run_record.txt`|1,2|F/G|历史run-id和命令，保留|
|`grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907/result.txt`|1|G|历史run-id，保留|
|同目录`run.log`|1|G|历史run-id，保留|
|同目录`run_record.txt`|1,2|F/G|历史run-id和命令，保留|
|`grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907/result.txt`|1|G|早期失败/短测run-id，保留|
|同目录`run_record.txt`|1,2|F/G|历史run-id和命令，保留|
|`grooveDNS/ex240_homogenization/postprocess_h65.py`|10,11|F/G|读取既有输出路径，保留|
|`grooveDNS/ex240_homogenization/source_manifest.txt`|4,9,10|F/G|冻结源码哈希和命令，保留|
|`grooveDNS/stage1_mass_flux_audit/stage1_validation_archive_20260906_150939/postprocess_stage1.py`|450,454,460|A/G|冻结归档生成器，改动会改变复现输出，保留|
|同归档`stage1_validation_summary.md`|70,74,80|A/G|冻结阶段一归档报告，保留|
|`grooveDNS/stage2_blocking_audit/postprocess_stage2.py`|261,263|A/G|历史报告生成器，保留|
|`grooveDNS/stage2_blocking_audit/stage2_blocking_validation_report.md`|69,71|A/G|冻结阶段二报告，保留|
|`grooveDNS/stage3_design_review/figures/ex240_local_xy_plan.svg`|3|B|纠正图题；历史文件名保留|
|`grooveDNS/stage3_design_review/figures/ex240_local_xz_section.svg`|3|B|纠正图题；历史文件名保留|
|`grooveDNS/stage3_design_review/stage3_geometry_and_case_definition.md`|1,8,42,45,75,100,101,115,116,118|A/F|纠正正文/标题7处物理名称；3处历史链接保留|
|`grooveDNS/stage3_ex240_local/analyze_zouhe_pressure_candidate.py`|5|F/G|docstring中的历史工作路径，保留|
|`grooveDNS/stage3_ex240_local/geometry_generator.cpp`|31|B/F/G|既有材料场文件名，后处理依赖，保留|
|`grooveDNS/stage3_ex240_local/geometry_validation_report.md`|1,66|A/F/G|冻结几何报告和材料场路径，保留|
|`grooveDNS/stage3_ex240_local/postprocess_geometry.py`|9,11,12|B/F|纠正两处未来生成图题；历史VTI输入路径保留；未重新生成旧PNG/PDF|
|`grooveDNS/stage3_ex240_local/preconversion_longrun_run_manifest.txt`|3|G|冻结工作目录记录，保留|
|`grooveDNS/stage3_ex240_local/stage3_explicit_piston_10nm_validation_report.md`|1|A/G|冻结失败报告标题，保留|
|`grooveDNS/stage3_ex240_local/stage3_f3_upstream_root_cause_diagnosis_report.md`|4|F/G|历史工作路径，保留|
|`grooveDNS/stage3_ex240_local/stage3_real_moving_boundary_implementation_plan.md`|49,55,145,148|C/F/G|建议符号名和历史目录路径；不做符号/文件重命名|
|`grooveDNS/stage3_ex240_local/stage3_revised_plan.md`|1|A|纠正计划标题|
|`grooveDNS/stage3_ex240_local/stage3_static_lattice_integration_report.md`|8,79|A/G|冻结静态接入报告，保留|
|`grooveDNS/stage3_ex240_local/zouhe_pressure_candidate_run_manifest.txt`|3|G|冻结工作目录记录，保留|

类别C审查结论：当前已编译C++中没有必须纠正的实际变量、函数、类、namespace或macro；
`stage3_real_moving_boundary_implementation_plan.md`中的`ex240MovingPunchIndicator.h`只是历史
建议文件名。所有命中均可作为历史内部标识保留，不在本轮改变ABI、target或调用路径。

## 含历史缩写的目录名（E，共7项）

- `grooveDNS/ex240_homogenization/`
- `grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907/`
- `grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907/`
- `grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907/`
- `grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907/`
- `grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907/`
- `grooveDNS/stage3_ex240_local/`

以上目录全部保留，未创建别名、移动或重命名。

## 含历史缩写的文件名（D，共35项）

- 根目录：`ex240_layout_report.md`；
- 旧总报告：`grooveDNS/OpenLB_EX240_progress_report.md`；
- 等效化程序和产物：`ex240_h65_dns`、`ex240_h65_dns.cpp`、`ex240_h65_dns.d`、
  `ex240_h65_dns.o`、`ex240_h65_homogenization_report.md`；
- 设计图：`ex240_local_xy_plan.svg`、`ex240_local_xz_section.svg`；
- 静态材料场：`stage3_ex240_local/output/static_h65_dx5/ex240_material.vti`；
- 五个历史等效化输出目录中的25个VTK文件：每个目录各有两个step的`.vtm/.vti`和一个
  `.pvd`，完整目录和文件名如下：
  - `output/ex240_h65_dx5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000000.vtm`
  - 同目录`ex240_h65_short-x_iT0000000iC00000.vti`
  - 同目录`ex240_h65_short-x_iT0000100.vtm`
  - 同目录`ex240_h65_short-x_iT0000100iC00000.vti`
  - 同目录`vtkData/ex240_h65_short-x.pvd`
  - `output/ex240_h65_dx5_a1e5_short-x_20260907/`下对应同名5项
  - `output/ex240_h65_dx5_a1e5_short-y_20260907/`下
    `ex240_h65_short-y_iT0000000.vtm/.vti`、`iT0000100.vtm/.vti`及
    `ex240_h65_short-y.pvd`
  - `output/ex240_h65_dx5_a1e5_x_20260907/`下
    `ex240_h65_x_iT0000000.vtm/.vti`、`iT0001703.vtm/.vti`及`ex240_h65_x.pvd`
  - `output/ex240_h65_dx5_a1e5_y_20260907/`下
    `ex240_h65_y_iT0000000.vtm/.vti`、`iT0002255.vtm/.vti`及`ex240_h65_y.pvd`。

上述35个文件名全部是历史路径或构建产物，本轮均不重命名。

## 修改决策

直接修改6个非冻结文件：活动总览`PROGRESS_SUMMARY.md`、设计审查正文、两张设计SVG的
图题、静态几何后处理脚本中的未来图题，以及阶段三修订方案标题。新增本清单、
`SIM_EC1XT240_NAMING_CORRECTION.md`和最终报告。其余34个受保护的首次文本命中文件
全部保持字节不变。

这次清理不修改物理模型或结果，也不运行仿真。复查时，本清单和勘误文件因必须讨论
旧误写而会成为新的有意命中；这类元数据命中不表示模型名称仍未纠正。

## 路径名原始命中完整列表

以下为首次扫描得到的42个路径，逐项保留：

```text
./ex240_layout_report.md
./grooveDNS/OpenLB_EX240_progress_report.md
./grooveDNS/ex240_homogenization
./grooveDNS/ex240_homogenization/ex240_h65_dns
./grooveDNS/ex240_homogenization/ex240_h65_dns.cpp
./grooveDNS/ex240_homogenization/ex240_h65_dns.d
./grooveDNS/ex240_homogenization/ex240_h65_dns.o
./grooveDNS/ex240_homogenization/ex240_h65_homogenization_report.md
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000000.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000000iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000100.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000100iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-x_20260907/vtkData/ex240_h65_short-x.pvd
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907/vtkData/data/ex240_h65_short-y_iT0000000.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907/vtkData/data/ex240_h65_short-y_iT0000000iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907/vtkData/data/ex240_h65_short-y_iT0000100.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907/vtkData/data/ex240_h65_short-y_iT0000100iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_short-y_20260907/vtkData/ex240_h65_short-y.pvd
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907/vtkData/data/ex240_h65_x_iT0000000.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907/vtkData/data/ex240_h65_x_iT0000000iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907/vtkData/data/ex240_h65_x_iT0001703.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907/vtkData/data/ex240_h65_x_iT0001703iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_x_20260907/vtkData/ex240_h65_x.pvd
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907/vtkData/data/ex240_h65_y_iT0000000.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907/vtkData/data/ex240_h65_y_iT0000000iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907/vtkData/data/ex240_h65_y_iT0002255.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907/vtkData/data/ex240_h65_y_iT0002255iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_a1e5_y_20260907/vtkData/ex240_h65_y.pvd
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000000.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000000iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000100.vtm
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907/vtkData/data/ex240_h65_short-x_iT0000100iC00000.vti
./grooveDNS/ex240_homogenization/output/ex240_h65_dx5_short-x_20260907/vtkData/ex240_h65_short-x.pvd
./grooveDNS/stage3_design_review/figures/ex240_local_xy_plan.svg
./grooveDNS/stage3_design_review/figures/ex240_local_xz_section.svg
./grooveDNS/stage3_ex240_local
./grooveDNS/stage3_ex240_local/output/static_h65_dx5/ex240_material.vti
```
