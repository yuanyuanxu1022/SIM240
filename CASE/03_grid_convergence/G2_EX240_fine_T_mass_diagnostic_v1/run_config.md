# h75 fine-T 诊断运行清单（未执行）

|参数|冻结值|
|---|---|
|h / 槽深 / 槽宽 / 周期|75 / 100 / 120 / 240 nm|
|Lx / Ly / Href|240 / 240 / 125 nm|
|dx / dt / tau|1.25e-9 m / 2.604166666666667e-13 s / 1|
|rho / nu / mu|1000 kg/m³ / 1e-6 m²/s / 1e-3 Pa·s|
|物理加速度 / 压力梯度|+x 1e5 m/s² / 1e8 Pa/m|
|格子加速度 / 黏度 / 速度映射|5.425347222222223e-12 / 1/6 / 4800 m/s|
|描述子/碰撞|D3Q19_FORCE / ForcedBGK / double|
|周期/固壁|x,y / 原Bouzidi静止精确几何，q0.5|
|rank / cuboid / overlap / 计算线程|1 / 1 / 3 / 1|
|诊断步数/样本数|4000推进 / 4001行；原60000上限保留|
|原稳态窗口|1000格子步，sample std(n−1)，原提前停止规则保留|
|未来binary|本目录build/fine_T_diagnostic，当前不存在|
|未来输出|本目录runs下新的唯一run_id，当前未创建|
|执行授权|false；本轮不编译/运行|

相似性：dt=(tau−0.5)dx²/(3nu)，a_lat=a_phys dt²/dx。只有T一个工况；不会自动运行P、其他dx/高度或多个力。

资源：一个rank/CPU计算线程，建议预留8 GiB RAM与2 GiB磁盘。core=192×192×145，fluid=3686400；一套含halo的19分布double约0.84 GiB，其他格子字段/边界/通信另计。观察器三组vector的有效载荷约84.4 MiB（mask/rho/peak）；10个rho快照+一份mask约309.4 MiB，另加原VTK/CSV/日志及容器capacity开销。只作为预算，真实峰值RSS待测。

每步全core材料指纹和高精度累加增加计算开销；不能按4000/29548直接给墙钟比例。未给未经测量的运行时长承诺。准备时的机器available内存快照见manifest，不能把快照当将来已保留的资源。运行前需检查当时资源与其他计算占用。
