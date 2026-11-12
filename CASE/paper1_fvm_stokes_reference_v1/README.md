# 第一篇：OpenFOAM 13 显式沟槽 Stokes 独立参考（准备版）

本目录落实固定4几何6方向；当前没有求解结果。先读[PROTOCOL.md](PROTOCOL.md)，具体参数与数量见[run_config.md](run_config.md)。

- `solver/paper1StokesReference.C`：P为标量Poisson，T为去惯性稳态Stokes；K由解输出。
- `prepare.py`：只生成字典，拒覆盖，不启动OpenFOAM。
- `prepared_manifest.json`、`comparison_inputs.json`：26份准备输入及六方向历史K5锚点；哈希绑定，未执行。
- `postprocess.py`：只读积分/逐级接收/公式比较，缺receipt或参考未接收时返回不可裁决。
- `run_one.py`：未来单例启动控制器；本次未调用，不自动下一个网格/方向。
- `release_manifest.json`：在编译、检查、审查后生成的准备快照。它不是运行结果。
- `tests/`：归一化/方向/坏输入/缺证据的合成核对，不是数值基准。

局部`bin/`、`solver/Make/linux*`、`prepared/*/constant/polyMesh`和未来时间目录/场文件只留本地，不提交大型结果或可执行文件。本轮不提交推送，亦不改论文母稿。状态入口为项目`docs/reports/SIM240_AI_CONTEXT.md`。
