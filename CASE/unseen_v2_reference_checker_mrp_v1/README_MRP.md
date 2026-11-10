# URV-MRP-v1 检查器候选

从 v1.2 隔离复制，原 `check_results.py`、`evidence.py`、`read_fields.py` 和 `common/` 保持原字节。原77项软件测试保留；新增同输入 FMA、合成密度采集／损坏拒绝、精确修订绑定和静态审计拒绝等测试。本次最终103项通过，初始软件失败日志保留在本轮报告。

`analysis/contracts.py` 仅在原源码 anchor 不匹配且明确声明 MRP 修订时，进入 `analysis/revision.py` 的精确新源／最小 diff 核验。来源匹配不等于运行放行：修订 anchor 的 instruction_audit_status 必须 PASS；当前为 FAIL，故绑定检查拒绝本候选。旧 anchor、R1/R2和旧失败保持。

`analysis/mass_capture.py` 从 native 原始密度记录生成带 SHA 的最终索引，再由将来的完成记录绑定所有原始文件；该步骤不修补密度。离线重放独立实现两舍入路径及两补偿账本。

`analysis/check_mass_repair.py` 在外部分析目录内先调用原字节的 URV 检查器重新验收当前完成原始结果，避免信任任意伪造的 PASS 文件；再检查采样／全轨迹补偿列／双路径历史对照及物理输出守卫。差异先保存再拒绝。该完成结果流程没有真实新运行可供端到端验证，不能宣称已接受新 S0。

本轮没有准备新执行合同／正式运行器，也未调用完成结果 CLI 对真实新案例验收。禁止从旧 v1.2 复制授权绕过当前审计失败；S0 HOLD，S1未启动。
