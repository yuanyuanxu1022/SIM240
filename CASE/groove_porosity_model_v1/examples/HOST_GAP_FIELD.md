# 把当前间隙交给 grooveDarcy

本说明对应 Foundation 13 的现有 `grooveDarcy` 子类。配置片段见 [fvModels.gapField](fvModels.gapField)；它不能单独启动流场计算。原公式/V2及其适用范围不变。

模型内部已经实现：

```text
宿主更新 mesaGap [m]
    → 标准 porosityForce 调用 grooveDarcy
    → 每个目标单元读取当前 h
    → 计算 K_parallel(h, depth, width)、K_perpendicular(h, depth, width)
    → 计算 H = h + (width/period)*depth
    → 计算 D_parallel = H/K_parallel、D_perpendicular = H/K_perpendicular
    → 按槽向旋转，装配动量阻力
```

`h` 是凸台至基底的最小间隙；`H` 是液体体积除以平面面积得到的平均厚度。当前速度约定是液体体积平均速度，所以J=HU。若把用户公式 `d_i=h/K_i` 中的h理解为这个平均厚度，公式对应；若h指最小间隙，不能直接替代H。光滑极限depth=0时两者相同，D=12/h²。

宿主至少需要做两件事。

1. 在网格的对象注册表中创建一个名为 `mesaGap` 的 `volScalarField`，单位为长度。例如在宿主初始化中读取实际算例提供的字段：

```cpp
volScalarField mesaGap
(
    IOobject
    (
        "mesaGap", runTime.name(), mesh,
        IOobject::MUST_READ, IOobject::AUTO_WRITE
    ),
    mesh
);
```

2. 若间隙变化，在装配下一次多孔阻力前，由宿主更新这个字段；均匀与逐单元间隙都可表示。子类每次装配重新读取，不只在创建时或时间步变化时刷新。只放一个字段文件而不由宿主创建对象，或只修改字段文件但不更新已注册对象，都不等于更新了模型使用的间隙。

这一接口没有替宿主实现间隙运动规律。固定几何时保持字段不变即可；如要应用于动态挤压，宿主还须一致实现 `∂tH + div(HU) = 0`，并处理真实网格/储液体积/边界排液。更新D不会自动产生这些作用。

适用前提：全充液、单相、xy二维empty平均模型，使用总未解析壁面阻力。当前实现不能直接移植到含真实上下壁剪切或液气相权重的宿主而假定等价。未指定实际宿主时，不代写其运动、相分率或压力修正方程。
