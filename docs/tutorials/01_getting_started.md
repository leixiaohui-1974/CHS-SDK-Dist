# 教程 1: 您的第一个仿真 - 一个简单的水库-闸门系统

欢迎来到智能水务平台！本教程将指导您完成设置并运行您的第一个仿真。我们将以 `example_simulation.py` 脚本为指南。

本场景的目标是模拟一个水位过高的单一水库。我们将使用一个PID控制器来调节下游的闸门，通过开启闸门放水，使水位降低到期望的设定值。

此示例演示了平台非代理式的、集中式仿真模式的核心概念：
- **模块化 (Modularity)**: 物理组件 (`水库 (Reservoir)`、`闸门 (Gate)`) 和控制逻辑 (`PID控制器 (PIDController)`) 是独立的、解耦的对象。
- **组合 (Composition)**: `仿真平台 (SimulationHarness)` 将这些独立的组件组装成一个可运行的系统。
- **编排 (Orchestration)**: 平台以步进循环的方式直接调用组件和控制器来运行仿真。

## 第1步: 理解组件

让我们来分解 `example_simulation.py` 中的代码。

### `水库 (Reservoir)` 模型
```python
from swp.simulation_identification.physical_objects.reservoir import Reservoir

reservoir_params = {
    'surface_area': 1.5e6, # 平方米
}
reservoir_initial_state = {
    'volume': 21e6, # 立方米, 相当于 14m * 1.5e6 m^2
    'water_level': 14.0 # 米, 初始水位高于设定值
}
reservoir = Reservoir(
    reservoir_id="reservoir_1",
    initial_state=reservoir_initial_state,
    params=reservoir_params
)
```
在这里，我们创建了一个 `水库` 模型的实例。它通过一个唯一的ID、一个 `initial_state` (我们从14.0米的水位开始)，以及一个用于其静态物理参数的 `params` 字典进行初始化。

### `闸门 (Gate)` 模型
```python
from swp.simulation_identification.physical_objects.gate import Gate

gate_params = {
    'max_rate_of_change': 0.1,
    'discharge_coefficient': 0.6,
    'width': 10
}
gate_initial_state = {
    'opening': 0.5 # 50% 开启
}
gate = Gate(
    gate_id="gate_1",
    initial_state=gate_initial_state,
    params=gate_params
)
```
同样，我们创建了一个 `闸门`。它的参数定义了它的操作方式 (例如，它可以多快地开启/关闭) 以及用于计算水流的物理特性。

### `PID控制器 (PIDController)`
```python
from swp.local_agents.control.pid_controller import PIDController

# 对于一个反作用过程 (开启闸门会降低水位),
# 控制器的增益必须为负。
pid_controller = PIDController(
    Kp=-0.5,
    Ki=-0.01,
    Kd=-0.1,
    setpoint=12.0, # 目标水位，单位为米
    min_output=0.0,
    max_output=1.0 # 闸门开启度是一个百分比
)
```
这是我们的控制逻辑。我们实例化了一个PID控制器，其 `setpoint` (目标) 为12.0米。

至关重要的是，其增益 (`Kp`, `Ki`, `Kd`) 是**负数**。这是因为我们的系统是**反作用**的：增加控制变量 (闸门开启度) 会导致测量变量 (水位) 下降。负增益确保了当水位过高 (一个正误差) 时，控制器输出也为正 (开启闸门)。

## 第2步: 使用 `SimulationHarness` 组装系统

`SimulationHarness` (仿真平台) 是运行仿真的引擎。我们配置它，添加我们的组件和控制器，然后命令它运行。

```python
from swp.core_engine.testing.simulation_harness import SimulationHarness

simulation_config = {
    'duration': 300, # 模拟300秒
    'dt': 1.0        # 时间步长为1秒
}
harness = SimulationHarness(config=simulation_config)

# 将组件添加到平台中
harness.add_component(reservoir)
harness.add_component(gate)

# 添加控制器并将其与它所控制的组件关联起来
harness.add_controller(controlled_object_id="gate_1", controller=pid_controller)
```
请注意我们是如何独立添加每个组件的。然后，我们将 `pid_controller` 与ID为 `gate_1` 的组件链接起来。现在，平台知道这个控制器负责为 `gate_1` 提供控制动作。

## 第3步: 运行仿真

最后一步很简单：
```python
harness.run_simulation()
```
要运行整个脚本，请在您的终端中导航到项目的根目录并执行：
```bash
python3 example_simulation.py
```

## 第4步: 解读输出

您将看到一个逐步骤的日志打印到您的控制台。对于第一步，您应该看到：

```
--- Simulation Step 1, Time: 0.00s ---
  Controller for 'gate_1': Target opening = 1.00 (based on reservoir level 14.00m)
  Interaction: Discharge from 'gate_1' = 49.720 m^3/s
  State Update: Reservoir water level = 14.000m
```

让我们来分析一下：
1.  控制器看到水库水位 (14.0m) 高于其设定值 (12.0m)。由于是负增益，它计算出一个大的正向控制动作，该动作被限制在最大值 `1.00` (100% 开启)。
2.  平台根据当前水位和闸门开启度计算出闸门的 `Discharge` (流量)。
3.  平台更新水库的状态，将此流量作为 `outflow` (出流量) 应用。水位开始下降 (尽管由于操作顺序的原因，可能在日志的下一步才能看到变化)。

通过观察日志中的 `State Update` 行，您可以看到水位逐渐向12.0米的目标值下降，证明我们简单的控制系统按预期工作。

恭喜！您已成功使用智能水务平台运行了您的第一个仿真。现在您可以尝试修改 `example_simulation.py` 中的参数 (例如，控制器增益或设定值)，然后重新运行仿真，观察系统行为的变化。
