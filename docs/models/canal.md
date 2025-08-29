# 渠道模型 (Canal Model)

`渠道` (Canal) 模型代表一段具有梯形横截面的渠道。它使用曼宁方程 (Manning's equation) 来模拟水流。

## 状态变量

-   `volume` (float): 渠道段当前的水量 (m³)。
-   `water_level` (float): 渠道当前的水位 (m)。
-   `outflow` (float): 当前时间步内计算出的渠道出流量 (m³/s)。

## 参数

-   `bottom_width` (float): 渠道底部的宽度 (m)。
-   `length` (float): 渠道段的长度 (m)。
-   `slope` (float): 渠道河床的纵向坡度 (无量纲)。
-   `side_slope_z` (float): 渠道边坡的坡度 (z:1 中的 z，水平:垂直)。
-   `manning_n` (float): 曼宁糙率系数。

## 使用示例

```python
from swp.simulation_identification.physical_objects.canal import Canal

canal = Canal(
    name="my_canal",
    initial_state={'volume': 100000, 'water_level': 2.1, 'outflow': 0},
    params={
        'bottom_width': 20,
        'length': 5000,
        'slope': 0.0002,
        'side_slope_z': 2,
        'manning_n': 0.025
    }
)
```
