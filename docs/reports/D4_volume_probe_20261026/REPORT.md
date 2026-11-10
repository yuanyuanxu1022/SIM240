# 专用工作卷与持久目录准备：等待管理员挂载

2026-10-26。用户明确授权准备实际卷/目录和限定无求解探针，求解保持关闭。

当前结论 **PARTIAL_ENVIRONMENT_PREPARATION_ADMIN_MOUNT_REQUIRED**。已完成目录准备和持久磁盘小文件实测；专用tmpfs尚未挂载，后续真实卷探针没有执行。阻碍是本机sudo要求管理员密码，而不是缺少本次项目授权。代理没有询问、读取或保存密码，没有尝试替代提权路径。

## 1. 已完成的实际动作

- 新建仓库外`/home/dell/yuanyuanxu/SIM240_runtime_records`及其`reference_pilot_n8_20261026`子目录，并建立`/run/user/1000/sim240_pilot_n8_work_20261026`空挂载目录。三者uid/gid=1000:1000、权限0700；没有覆盖既有路径。证据`evidence/directories_created.json`。
- 在新持久目录下的唯一`volume_probe_persistent_931b6ba97250/`写入1048576字节已知内容，对文件与目录执行fsync，重新读取SHA一致。原文件及probe_result.json保留在该目录。独立exit0，见`evidence/persistent_probe.json`和`persistent_probe.exit_code`。
- 独立复核已写文件大小和SHA一致；358条v3.1来源、319份旧v3文件、4233历史保护文件保持。见`evidence/independent_verification.json`；不相加为总文件数。
- 真实挂载预查路径已执行并拒绝继续：`probe_volume.py --phase mounted`独立exit2、REFUSED_LAYOUT_NOT_READY。目录现在存在、权限和普通盘要求符合；work目前继承公共/run/user/1000的约3.1GiB容量，不是专用512MiB挂载点。代码没有在公共卷上执行写满试验。见`evidence/mounted_precheck.json`与exit_code。
- `/usr/bin/sudo -n true`独立exit1，stderr为`sudo: a password is required`；没有进行挂载。见`evidence/permission_check.json`。

## 2. 已准备但尚未执行的限定探针

`probe_volume.py`只提供persistent和mounted两种探针阶段，不包含mount、PDE、建网、组装、真实worker或批准包入口。mounted阶段先调用已审v3.1的只读layout检查，必须通过才进行后续：

1. 在专用卷中编译并另进程加载一个仅返回240的微型共享库；临时文件/JIT类缓存放在专用卷，固定编译器/加载器、短超时，超时杀整个进程组。不是OpenLB编译或有限元JIT组装。
2. 按1MiB块实际写满专用卷，最多尝试513MiB、≤60秒，要求ENOSPC；卷满时独立小进程记录写入失败退出码到普通盘。只删除该次明确列出的探针文件，保留字节/错误/hash证据。
3. 用v3.1现有固定人工success/failure夹具在实际卷中走记录与归档；始终标SYNTHETIC_PROCESS_NOT_PDE、合同false。成功副本独立数值关系读回，失败保留exit7和部分文件；只清理由该探针产生、已哈希核准的源文件，持久副本保留。
4. 恢复工作卷为空，再做完整静态路径检查。只有这些探针完成后，才有“实际无求解卷核查通过”的证据。

目前上列全部未执行。已执行的persistent/拒绝检查使用的源快照保存在`evidence/executed_probe_source.py`，其SHA与执行输出一致；当前入口在此基础上给尚未执行的编译器/加载器增加进程组超时终止，语法检查通过，不把未执行分支称为测试通过。

## 3. 用户需完成的一步系统操作

当前两个目标目录已准备且work为空。用户在**当前这台Linux电脑的终端**执行以下唯一挂载命令，在本机输入管理员密码：

```bash
sudo /usr/bin/mount -t tmpfs -o rw,exec,nosuid,nodev,size=512M,mode=0700,uid=1000,gid=1000 sim240-pilot-n8 /run/user/1000/sim240_pilot_n8_work_20261026
```

挂载源名sim240-pilot-n8只标识本专用tmpfs；不改fstab、服务或其他卷。执行前如发现该路径已被别处挂载或有数据，应先停止核对。本报告不能证明用户已经执行。成功可能无文字输出；需要用户反馈实际终端输出后，代理先核mountinfo和512MiB容量，再继续准备好的mounted探针；不凭“命令已给出”断言挂载成功。

本轮没有启动任何求解。原合同false/null、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，预测HOLD。没有拟合、原科学协议/阈值/G4锁/旧FAIL变更、Git提交或推送。新目录和1MiB人工探针文件保留；专用卷未挂载，尚无实际计算run_id。
