# A1 两条 S0 启动绑定复核：准备检查通过，待明确正式授权

日期：2026-11-02。本轮只读复核与文档准备，没有调用原生程序，没有重建或修改源码、检查器、阈值和封存合同。没有签发正式启动合同或命令，没有启动正式计算。

已验证：当前准备合同 SHA 为 d58019c2843454ce0ec1b2548e83fb6af66f4081d20acd54b695d665c916766c，1545项绑定输入全部符合；默认控制器只读检查退出0，solver_executed=false。连同旧保护集合、本轮使用的上轮报告和准备合同，共2018项既有文件保持。A1 ELF仍为 c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af。

两方向身份为 URV_S0_P_A1_20261102_01（沿槽+y）和 URV_S0_T_A1_20261102_01（横槽+x）；各steady目录只有run_config.txt和run_manifest.txt，没有日志、completion或launch_attempts。可读取进程中未见本A1原生程序或控制器，tmux当前无会话（退出1）；进程权限不足的PID保留于startup_snapshot.json，因此不声称核遍全机所有用户进程。此项目的目录、合同与启动记录均支持正式未启动。

资源只读快照：MemAvailable=24345653248 bytes（22.67 GiB），磁盘空闲341742227456 bytes（318.27 GiB），满足原12 GiB／100 GiB启动门槛；实际启动前必须刷新。其余原1进程／线程、8 GiB地址空间、每方向3600 s、边界与平均定义／1013窗口／58800步上限不变。

当前simulation_authorized=false，approved_run_ids=[]。用户本轮原话和解释见authorization_review.json。“获准后的”保留条件性质；现有记录没有明确的现在授权A1两条新身份的原话。URV-MRP-v1 PROTOCOL.md第7节要求根据真实用户授权另存启动合同，且旧v1.2许可不可转用；这来自冻结项目协议，不来自Skill额外审批。没有新指令或证据矛盾，无需新Astra裁定。

已把具体待签发内容准备为launch_release_plan.json：精确两条身份、对应配置、准备合同与ELF SHA、候选新合同路径、顺序与失败即停条款。该文件无执行命令、无真实授权，不会被当成launch release。用户明确授权后才另存新合同，重新核对封存与资源，验证新合同及独立SHA，更新共享交接，交付一条命令由用户手动启动。流程仍为P→捕获索引及completion→原URV与密度重放／补偿／物理输出守卫→全部通过才T；不重试、不进入S1。

S0 HOLD；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。原零步PASS／限定静态PASS仅保持其证据范围，真实steady密度捕获端到端仍待正式运行。旧v1.2 T拒绝、380差异和历史唯一归因NOT_ESTABLISHED不变；reference_qualified=false、strict_error_bound_established=false、submission_ready=false。既有107项／10项软件测试本轮未重跑，未伪称新增测试。

记录脚本最初误把.sha256旁文件名写成.json.sha256，退出1；已按实际文件名修正并完成核查，见recording_error.json。这是报告路径假设错误，无输入漂移或合同变更。

本报告为AI辅助证据记录，不是独立人工科学签字。采用scientific-writing整理证据边界；技能来源已核当前公开记录：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, https://doi.org/10.48550/arXiv.2609.00065 （当前v2，无期刊发表记录）。该来源只说明技能，不是本项目数值证据。未向网络发送项目资料。未提交或推送。
