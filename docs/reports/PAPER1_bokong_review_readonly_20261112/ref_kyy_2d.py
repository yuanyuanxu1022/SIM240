"""沿槽 Kyy 的二维精确降维求解器 —— 参照实现（供交叉核对，请先自己写）

为什么这是精确的
----------------
几何沿 y（沟槽方向）不变，流动沿 y。若令 u=w=0、v=v(x,z)，则 Stokes:
    ∂p/∂x = 0,  ∂p/∂z = 0   →  p = p(y)
    ∂p/∂y = μ(∂²v/∂x² + ∂²v/∂z²)
    ∂v/∂y = 0                →  连续性自动满足
所以"单向流"是 Stokes 的**精确解**，不是近似。取 μ=1、-∂p/∂y=1，得
    ∇²v = -1   于流体域,   v=0 于全部壁面
单位宽度导度  K_yy = (1/P)∫∫ v dA。

注意事项（第一版容易错的地方）
------------------------------
1. 壁面用**半格** Dirichlet：贴壁单元的对角系数减 2（不是减 1、也不是跳过该项）。
   写成整格会把有效流道收窄 dx/2，h=25 时能差 8%。
2. x 方向**周期**，(i+di) % nx。
3. 最后要除以周期 P 才是单位宽度导度；不除会差 240 倍。

验证目标（我本机 dx=1nm 的结果，你应当落在同一量级）
    h=25,d=100 : 3.41301e-23   与 LB 5nm 差 -0.50%
    h=50,d=120 : 6.84284e-23   差 -0.63%
    h=75,d=100 : 9.76266e-23   差 -0.73%
    h=100,d=100: 1.64384e-22   差 -0.66%   （h=100 是留出点）
    h=125,d=25 : 2.00340e-22   差 -0.46%
全部 19 几何：偏差 -1.96% ~ -0.46%，均值 -0.79%。
若你的结果与 LB 差 10% 以上，先查壁面半格处理。
"""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def Kyy_2d(
    h: float, d: float, w: float = 120.0, P: float = 240.0, dx: float = 1.0
) -> float:
    """返回沿槽单位宽度导度 K_yy [nm^3]。h,d,w,P,dx 全部用 nm。"""
    nx = int(round(P / dx))
    nz = int(round((h + d) / dx))
    xc = (np.arange(nx) + 0.5) * dx
    zc = (np.arange(nz) + 0.5) * dx
    X, Z = np.meshgrid(xc, zc, indexing="ij")
    H = np.where(X < w, h, h + d)  # 凸台区高 h，槽区高 h+d
    mask = Z < H  # 流体单元

    idx = -np.ones((nx, nz), dtype=int)
    idx[mask] = np.arange(mask.sum())
    n = int(mask.sum())

    rows, cols, vals = [], [], []
    rhs = np.zeros(n)
    for i in range(nx):
        for j in range(nz):
            if not mask[i, j]:
                continue
            k = idx[i, j]
            diag = 0.0
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii = (i + di) % nx  # x 周期
                jj = j + dj
                if jj < 0 or jj >= nz or not mask[ii, jj]:
                    diag -= 2.0  # 半格 Dirichlet
                else:
                    rows.append(k)
                    cols.append(idx[ii, jj])
                    vals.append(1.0)
                    diag -= 1.0
            rows.append(k)
            cols.append(k)
            vals.append(diag)
            rhs[k] = -dx * dx

    A = sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
    v = spla.spsolve(A, rhs)
    return v.sum() * dx * dx / P


if __name__ == "__main__":
    for h, d in [(25, 100), (50, 120), (75, 100), (100, 100), (125, 25)]:
        print(f"h={h:4d} d={d:4d}  K_yy = {Kyy_2d(h, d) * 1e-27:.5e} m^3")
