# 剩余固定输入的后台顺序运行准备（2026-11-12）

作者明确选择：“把剩余固定输入准备成一条后台顺序命令，遇验收失败即停”。本目录仅为既有v2.1冻结运行器的外部串行调度，不修改CASE内源码、协议、参数、网格、阈值或release。由作者执行tmux命令才启动；准备、预检和合成测试不启动任何求解。

原26输入已完成并独立接收9份，剩余17份。已完成的T基准2%一致性FAIL明确保留，不重跑、不改为PASS；此次授权覆盖其余固定输入。遇到任何新的局部接收失败、参考网格/代数失败、2%一致性FAIL或基准方向比/角差FAIL，立即停止后续输入。未完成项保留未运行，不重试、不加网格、不更换几何、不拟合。已知T失败不会被当作此次新增故障，但在最终记录中持续列出。

## 固定顺序

1. h75/d100 P：tight。
2. h50/d120 P：coarse→mid→fine→tight。
3. h125/d120 P：coarse→mid→fine→tight。
4. h25/d100 T：coarse→mid→fine→tight。
5. h125/d120 T：coarse→mid→fine→tight。

只有源层通过完整独立读回才允许原run_one进入后续映射。每个输入仅调用一次原run_one.py --execute，单进程串行。每次结束后调用原冻结postprocess.assess，核查完整回执/日志/原场/mesh/映射来源；另按原数值进行已有网格与代数检查。新增方向完成时按原2%及基准输出门槛判定，不延后掩盖失败。coarse/mid不施加最细0.1%门槛。

代码/清单及235原绑定项在预检和每次启动前核身份；9份已有receipt额外绑定，目标17份不得出现已有runtime/referenceEvidence/0.5，不允许覆盖、恢复或自动重试。execution目录以原子创建避免重复批次。批次完整性由batch_manifest绑定，Python解释器固定/usr/bin/python3，不依赖Conda。

## 防休眠与日志

start_remaining.sh加载Foundation13并使用systemd-inhibit临时持有sleep/idle抑制锁，只有批次存活时生效，不修改系统持久配置。短暂/usr/bin/true探测成功；不是数值运行。电脑需保持开机供电，可锁屏或关闭终端，不保证断电/强制关机恢复。tmux任务独立于聊天。

原单例资源上限全部保留，较慢T分支可能数小时；每例12小时等是原安全上限，不能承诺一夜完成全部17项。完成或失败后批次退出、抑制锁释放。不自动重跑。

execution/status.json是批次当前停点；每例.runner.log及.assessment.json保存过程与独立读回；batch_console.log保存控制器输出。当前此目录尚无execution，未启动。报告、测试和原始结果身份不能据此升级为物理验证/全域精度/投稿准备完成。论文数字、三项项目资格false及历史FAIL保持。

本轮14项合成测试只验证串行和停止机制；真实预检只读已有证据，不运行网格工具/映射/求解。明早由AI读取execution/status.json和实际结果继续，不依赖当前聊天或私有记忆。
