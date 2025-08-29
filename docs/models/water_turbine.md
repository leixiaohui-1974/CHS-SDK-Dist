# 水轮机模型 (Water Turbine Model)

`水轮机` (WaterTurbine) 模型代表一个用于水力发电的水轮机。它根据通过它的水流量以及其两端的水力压头差来计算产生的功率。

## 状态变量

-   `outflow` (float): 通过水轮机的水流量 (m³/s)。
-   `power` (float): 水轮机产生的电功率 (瓦特)。

## 参数

-   `efficiency` (float): 水轮机的转换效率 (0.0 到 1.0)。
-   `max_flow_rate` (float): 水轮机可以处理的最大流量 (m³/s)。

## 使用示例

```python
from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine

turbine = WaterTurbine(
    name="my_turbine",
    initial_state={'power': 0, 'outflow': 0},
    params={'efficiency': 0.85, 'max_flow_rate': 150}
)
```
