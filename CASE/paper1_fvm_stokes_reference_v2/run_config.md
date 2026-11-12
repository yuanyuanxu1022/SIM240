# v2.1 配置

PREPARED_NOT_RUN，PENDING_ASTRA_V21_RECHECK；没有数值启动授权。

|层|endTime|墙钟秒|
|---|---:|---:|
|coarse|60000|1800|
|mid|120000|14400|
|fine|200000|43200|
|tight|250000|43200|
|flat|60000|3600|

普通p/U/v<1e-10；tight<1e-11，tight线性容差1e-13、其他1e-12，relTol=0。P查v；T查完整活跃分量与p。T flat限定幅值例外见PROTOCOL及acceptance_rule，P平板不走该例外。正常上限结束可经完整检查接收，墙钟超时拒收。预算表是上限而非工期预测。

固定h75/d100 P/T、h25/d100 T、h50/d120 P、h125/d120 P/T；dx=1.25/.625/.3125nm，tight与fine同网格。mid/fine/tight从绑定源末态mapFields到0.5，并保存输入副本。26输入无新增几何。物性、驱动、边界、K单位m³与既有比较门槛见PROTOCOL；无改动。
