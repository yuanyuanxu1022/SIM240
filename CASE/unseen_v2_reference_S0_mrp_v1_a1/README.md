# URV-MRP-v1-A1：体积项原舍入路径已恢复，尚未运行

本轮依据用户采用的 A1 附属修订，从上一失败候选新建隔离目录，只增加单项体积的局部 binary64 舍入屏障。原 Makefile、mass_stats.h、质量 helper、密度采集器和采样表字节保持。主源码与已采用补丁逐字相符。

实际构建成功；两个测量主干均为两乘、单项double存取、独立加法。全部57600个体积空间前缀与原分开乘加一致；107项软件测试通过。本次已采用的观察量修订范围内静态审计PASS，没有声称全程序机器形式证明或实际流场结果等价。

完整记录：`../../docs/reports/URV_MRP_v1_A1_implementation_20261102/REPORT.md`；实际编译及依赖绑定：evidence/build_environment.json；采用记录：evidence/adoption.json。上一次候选及其FAIL全部保留在旧目录。

没有runs目录、正式run_id、启动合同或命令，没有调用native的describe/precheck/initialize/steady。原生零步安装及正式h75回归仍待；S0 HOLD，新数值／几何／结果验收NOT_EVALUATED。源码／静态检查通过不构成启动授权。
