# 水泵模型 (Pump Model)

`水泵` (Pump) 模型代表一个为水系统增加能量以将水从低海拔输送到高海拔的水泵。它是模拟逆自然水力梯度输水的基础组件。

## 物理原理

当前的 `水泵` 模型是一个简化的、具有固定速率运行的表示。其行为由以下规则控制：

1.  **开关状态:** 水泵有两个主要状态：'开' (`status` = 1) 和 '关' (`status` = 0)。
2.  **流量:** 当水泵处于'开'状态时，只要满足运行约束条件，它就会提供其 `max_flow_rate` (最大流量)。当处于'关'状态时，流量为零。
3.  **扬程约束:** 只有当所需的扬程（下游和上游水位之差）小于或等于其 `max_head` (最大扬程) 参数时，水泵才能运行。如果所需扬程超过最大值，即使水泵处于'开'状态，流量也会降至零。
4.  **功耗:** 当水泵处于'开'状态并成功产生流量时，它会消耗由 `power_consumption_kw` (千瓦功耗) 指定的固定功率。

该模型旨在将来进行扩展，以支持更复杂的物理特性，例如变速驱动或水泵性能曲线（流量 vs. 扬程）。

## 参数

- `max_flow_rate` (float): 当水泵开启并在其扬程限制内运行时，提供的固定流量，单位为 m³/s。
- `max_head` (float): 水泵可以克服的最大扬程差，单位为米。
- `power_consumption_kw` (float): 当水泵活动并产生流量时消耗的功率，单位为千瓦。

## 状态

- `status` (int): 水泵的运行状态。0代表'关'，1代表'开'。
- `flow_rate` (float): 当前时间步内由水泵产生的计算流量，单位为 m³/s。
- `power_draw_kw` (float): 当前时间步内水泵消耗的功率，单位为千瓦。

## 控制

`水泵`模型能感知消息。代理（agent）可以通过向其 `action_topic` (动作主题) 发布消息来开启或关闭它。消息中的 `control_signal` (控制信号) 应为 `1` 以开启水泵，为 `0` 以关闭水泵。

## 使用示例

```python
from swp.simulation_identification.physical_objects.pump import Pump
from swp.central_coordination.collaboration.message_bus import MessageBus

# 基于代理的控制需要一个消息总线
message_bus = MessageBus()

# 定义水泵参数和初始状态
pump_params = {'max_flow_rate': 5, 'max_head': 20, 'power_consumption_kw': 75}
pump_state = {'status': 0} # 初始状态为关闭

# 创建水泵实例
pump = Pump(
    pump_id="pump1",
    initial_state=pump_state,
    params=pump_params,
    message_bus=message_bus,
    action_topic="action.pump1.status"
)

# 现在，一个代理可以开启水泵
# message_bus.publish("action.pump1.status", Message(content={'control_signal': 1}))
```
