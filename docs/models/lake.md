# 湖泊模型 (Lake Model)

`湖泊` (Lake) 模型代表一个具有固定表面积的湖泊或水库。它通过计算入流、出流和蒸发来追踪水量和水位。

## 状态变量

-   `volume` (float): 湖中当前的水量 (m³)。
-   `water_level` (float): 当前的水位 (m)，根据水量和表面积计算得出。
-   `outflow` (float): 当前时间步内湖泊的出流量 (m³/s)。该值由下游需水量决定，并由仿真平台设置。

## 参数

-   `surface_area` (float): 湖泊的表面积 (m²)。
-   `max_volume` (float): 湖泊的最大蓄水容量 (m³)。
-   `evaporation_rate_m_per_s` (float): 蒸发速率，单位为米/秒。

## 使用示例

```python
from swp.simulation_identification.physical_objects.lake import Lake

initial_lake_volume = 40e6
lake_surface_area = 2e6

lake = Lake(
    name="my_lake",
    initial_state={'volume': initial_lake_volume, 'water_level': initial_lake_volume / lake_surface_area, 'outflow': 0},
    params={'surface_area': lake_surface_area, 'max_volume': 50e6, 'evaporation_rate_m_per_s': 2.31e-8}
)
```
