# 阀门模型 (Valve Model)

`阀门` (Valve) 模型代表了水网中一个可控的阀门。它模拟水流过一个可以被节流的管段。阀门的主要控制参数是其开启百分比，范围从0%（全关）到100%（全开）。

## 物理原理

通过阀门的流量使用简化的孔口流量方程计算：

`Q = C_d_eff * A * sqrt(2 * g * Δh)`

其中:
- `Q` 是体积流量 (m³/s)。
- `C_d_eff` 是有效流量系数。该值是通过将阀门的最大 `discharge_coefficient` (流量系数) 与其当前开启百分比进行缩放计算得出的。例如，一个开启50%的阀门的 `C_d_eff` 将是其最大值的一半。
- `A` 是管道的横截面积，由 `diameter` (直径) 参数确定。
- `g` 是重力加速度 (9.81 m/s²)。
- `Δh` 是阀门上游和下游节点之间的水头差。

该模型假设水流只在下游方向发生 (即，当 `Δh > 0` 时)。

## 参数

- `diameter` (float): 安装阀门的管道直径，单位为米。
- `discharge_coefficient` (float): 阀门在全开状态下的最大流量系数。这是一个无量纲值，通常在0.6到0.9之间。

## 状态

- `opening` (float): 阀门的当前开启度，以百分比表示 (0-100)。
- `flow_rate` (float): 当前时间步内计算出的通过阀门的流量，单位为 m³/s。

## 控制

`阀门`模型能感知消息，可以由一个代理（agent）通过发布到其指定的 `action_topic` (动作主题) 来进行控制。控制消息应包含一个带有期望开启百分比的 `control_signal` (控制信号)。

## 使用示例

以下是如何在仿真脚本中创建一个 `Valve` 实例：

```python
from swp.simulation_identification.physical_objects.valve import Valve
from swp.central_coordination.collaboration.message_bus import MessageBus

# 基于代理的控制需要一个消息总线
message_bus = MessageBus()

# 定义阀门参数和初始状态
valve_params = {'diameter': 0.5, 'discharge_coefficient': 0.9}
valve_state = {'opening': 0} # 初始状态为关闭

# 创建阀门实例
valve = Valve(
    valve_id="valve1",
    initial_state=valve_state,
    params=valve_params,
    message_bus=message_bus,
    action_topic="action.valve1.opening"
)

# 现在，一个代理可以通过向 "action.valve1.opening" 发布消息来控制阀门
# message_bus.publish("action.valve1.opening", Message(content={'control_signal': 50}))
```
