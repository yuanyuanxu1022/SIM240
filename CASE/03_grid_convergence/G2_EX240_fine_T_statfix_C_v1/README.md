# 细 T 方案 C（独立统计修复）

[冻结协议](PROTOCOL.md)是验收依据。本目录从历史细 T 生成源码机械复制，只增加质量统计、双账本和新版本结果字段。旧源码、诊断 v1/v2、历史结果与 FAIL 均不修改。

`scripts/prepare_and_precheck.py` 仅做算术测试、编译、来源绑定和零推进 `precheck T`，生成 `reports/build_precheck.json`。预检通过后，`scripts/run_formal.py --prepare-only` 只建立唯一正式运行目录；`--run-id ... --execute` **只有用户在独立终端明确启动时**才推进最多 60000 步。正式运行完成后需另开结果审查任务，不凭本目录或预检结果报告 K 正式 PASS。
