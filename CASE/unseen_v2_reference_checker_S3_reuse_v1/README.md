# S3 隔离检查器

common与check_results.py/evidence.py/read_fields.py保持S2原字节。contracts.py仅增加S3来源分支；stage_s3.py、revision_s3_reuse.py、s3_baselines.py提供阶段/来源/基准控制。旧stage_s2与revision_s2仅用于验证S2原来源；S3不得冒充S2。

本轮仅软件测试，不启动原生/VTK读取；保留未评价、历史FAIL与参考资格边界。
