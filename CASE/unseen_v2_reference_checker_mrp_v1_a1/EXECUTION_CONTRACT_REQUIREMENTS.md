# v1.1 检查器要求的未来执行合同

本文件是格式与校验要求，**不是已批准的合同**。当前没有符合该要求的真实新执行记录，S0保持未启动。

沿用原 protocol_id=URV-v1，新增 schema_version=URV-EXEC-1.1。未来生效合同必须另行取得真实外部历史确认和阶段授权；批准字段不能从软件测试复制。原准备封存不能作为正式构建。

## 来源角色

`inputs_sha256` 使用实际存在文件的规范化绝对路径。`provenance` 必须含以下角色，所有角色文件及其闭包均被该清单覆盖：

| 字段 | 要求 |
|---|---|
| native_binary | 实际正式二进制；与构建记录的路径、SHA一致 |
| native_sources | cpp/h源列表；哈希与构建记录一致，并匹配原物理内核锚点 |
| build_recipe | 正式构建配方，与构建记录路径/SHA一致 |
| build_environment | 本次真实构建记录，其自身也被绑定 |
| dependency_file | 本次编译器生成的.d；独立解析首个规则的全部依赖，不以手填短清单替代 |
| ldd_record | 本次运行库解析记录；所有可解析库路径必须完整对应捕获的动态库清单 |

构建记录至少包含：compile_exit_code、preparation_only_build、binary_path/binary_sha256、build_recipe_path/build_recipe_sha256、compile_command、native_sources_sha256、dependency_file_path、compile_working_directory、dependency_sha256、link_library_sha256、dynamic_library_sha256、compiler_executable/compiler_sha256。编译命令的 URV_PREPARATION_ONLY 必须唯一明确为0；准备构建被拒绝。OpenLB core、z、tinyxml2 的实际链接库和捕获的动态库必须覆盖。所有源/依赖/库/编译器的捕获哈希须与总清单及当前文件相符。

总清单同时覆盖本检查器全部 analysis/*.py 和 common/文件。原物理锚点由 common/source_preparation_anchor.json 提供。本轮没有变更原物理内核；若未来需要改物理源码，应另立研究/构建范围，不能套用本修订版本冒充纯检查器更新。

这些校验检查受信合同中的覆盖与一致性，不是对作者声明或编译记录的密码学真实性证明；外部保存的合同 SHA、真实构建证据、原始日志与独立退出仍是必要来源。测试中的惰性程序/库占位字节只用于反例，不是可执行程序或真实构建。

## 逐条运行身份

stage 限原六阶段之一；approved_run_ids 与 approved_runs 一一对应，不得重复。每条 approved_runs 必须包含：

- run_id；planned_case_id，后者必须属于该 stage 的原矩阵；
- run_config_path；run_config_sha256，该文件必须在 inputs_sha256 内；
- output_directory，规范化绝对路径；必须等于配置内 output_directory；
- 配置必须为该运行目录的 run_config.txt，mode=steady，编号、方向、物理输入、时间和帧计划均与原矩阵/协议一致。

配置、case、目录不能复用，运行目录不能相互嵌套。完成记录的编号/case/配置字节及实际目录再逐条核对。原生预检或初始化输出仍不能作为完成结果。完成记录的原始产物/前后输入/独立退出要求沿用原协议。

此格式变更服务于 F03；F04 多合同汇总尚未实现，不能将全24条先合并成一个跨阶段授权来绕过它。
