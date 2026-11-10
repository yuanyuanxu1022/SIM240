# URV-MRP-v1 + A1 本轮采用范围

科学／数值门槛沿用未改URV-v1；观察量实现依据原URV-MRP-v1及用户本轮采用的A1。采用原话与草案／补丁SHA见evidence/adoption.json；原草案未被回写为新历史记录。

本候选只允许相对上一候选对volume项增加局部double舍入屏障，恢复RN(volume+RN(RN(dx*dx)*dx))。无全局浮点选项、物理／收敛或原门槛改动。真实构建和限定范围静态审计已完成，旧FAIL不改。

本轮不含native零步或正式运行。当前SOURCE_REVISION_AUDIT=PASS仅适用于已采用的静态审计范围；全传递机器证明、真实密度采集、两方向精确回归和结果验收均未取得。S0保持HOLD，不自动进入S1。
