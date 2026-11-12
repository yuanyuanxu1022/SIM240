# 第一篇显式沟槽参考 v2.1_stopping_fix

PREPARED_NOT_RUN；正式比较尚无数值结果。先读PROTOCOL.md与run_config.md。

本轮仅修停止语义、tight分层、seed来源链、零值与预算；C++源码/二进制不变，无需编译。acceptance.py为共享机器规则执行器，prepared_manifest.json保存唯一acceptance_rule。postprocess.py独立从日志与CSV重算，不能把回执布尔当证据。

旧v2已完整归档到docs/reports/PAPER1_fvm_v21_review_20261111/，旧未放行release不删除不冒用。v1与其T平板FAIL原样保留。新release须指定Astra复核，无计算启动授权；不提供自动执行或批跑。

固定26输入：四沟槽几何六方向×三网格及六tight，另两平板；不加点。先当前release两平板合格，再沟槽。所有比较与论文口径保持不变。
