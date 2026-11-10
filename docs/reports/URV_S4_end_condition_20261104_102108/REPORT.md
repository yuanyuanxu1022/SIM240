# S4结束条件核查：批次仍运行，完整分析暂缓

本轮用户范围为确认批次实际结束后按URV-v1／MRP／A1／S4-MIP-v1／S4-FRD-v1完整独立分析已有结果，不重跑、不加时、不进入S5。

单次只读快照2026-11-04T10:21:08.556587+08:00至2026-11-04T10:21:08.576984+08:00：控制器PID1701694、原生PID1711573及会话urv_s4_formal_v1_20261104_01仍存在；原生正在第5条URV_S4_P_dx1p25_reuse_v1_20261103_01。前四条5/2.5nm P/T有completion及自动acceptance，原生独立退出0、无超时/资源停止，自动NUMERICAL_GATE=PASS、RESULT_PASS=true、geometry_PASS=true、independent_exit_code=0，身份/合同SHA相符。第5条无完成/接受，第6条1.25nm T未启动；S4_completed.json和S4_grid_report.json未生成。

结束条件未满足，故未运行独立检查器/VTK或计算三格接受，不读取正在写入的诊断作结果分析。前四条只引用已有自动回执，不声明本轮完成独立验收，不认定整个S4已通过。未查询步数、吞吐量或预测剩余时间；第5/6条原12h各上限保持，不作为预计耗时或加时理由。

正式release文件SHA e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b与交付一致；本轮未重核全部3284输入。源/合同/原始结果未修改。原S0–S3接受、旧失败/例外/归因限制保持，reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、submission_ready=false、F04 OPEN。

本轮单次结束条件核查后仅处理本地保存快照并更新文档，不再查询进程或日志。原生/控制器/检查器/VTK新调用0、重跑0、加时0、构建0、持续轮询0，无新仿真或物理验证。无需重复启动。本任务停在结束条件未满足，不后台等待或注册监控。

下一动作：实际批次结束后按既定范围完整分析已有材料；若失败停止亦如实保留完成前缀和失败，不自动重跑、加时或进S5。证据status_snapshot.json、disposition.json；共享状态原样备份见before文件。
