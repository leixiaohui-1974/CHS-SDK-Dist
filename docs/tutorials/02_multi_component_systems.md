# 教程 2: 构建一个多组件系统

本教程在教程1的基础上进行了扩展，演示了如何模拟一个包含多个相互连接的组件和多个独立控制器的更复杂的系统。我们将使用 `example_multi_gate_river.py` 脚本进行学习。

## 1. 场景概述

我们将构建的系统遵循以下物理拓扑结构：
**`水库 (Reservoir)` -> `闸门1 (Gate 1)` -> `河道 (RiverChannel)` -> `闸门2 (Gate 2)`**

这代表了一种常见的水系统配置。我们有两个不同的控制目标，将由我们的中央 `SimulationHarness` (仿真平台) 进行管理：
1.  **目标1**: 通过调节 `闸门1` 的开启度来控制 `水库` 的水位。目标是将水位从15米提升到18米。
2.  **目标2**: 通过调节 `闸门2` 的开启度来控制 `河道` 的水量。目标是将水量从500,000立方米降低到400,000立方米。

这种设置使我们能够探究一个系统的不同部分如何被独立控制，以及它们的行为如何相互影响。

## 2. 代码分解

让我们来检查 `example_multi_gate_river.py` 的关键部分。

### 2.1. 实例化组件
我们首先为所有四个物理组件创建实例。每个组件都被赋予一个唯一的ID (例如, `reservoir_id="reservoir_1"`)，这对于平台识别和连接它们至关重要。

```python
# 所有四个组件都用它们各自的初始状态和参数创建
reservoir = Reservoir(reservoir_id="reservoir_1", ...)
gate1 = Gate(gate_id="gate_1", ...)
channel = RiverChannel(channel_id="channel_1", ...)
gate2 = Gate(gate_id="gate_2", ...)
```

### 2.2. 配置多个独立的控制器
本示例的一个关键部分是使用两个独立的PID控制器来实现两个不同的目标。

**控制器1: 水库水位控制**
```python
controller1 = PIDController(
    Kp=0.2, Ki=0.01, Kd=0.05, setpoint=18.0,
    min_output=0.0, max_output=1.0
)
```
该控制器的目标是将水库水位提升到18.0米。为此，它需要*关闭* `gate_1`。由于正误差 (水位过低) 应导致负向动作 (关闭闸门)，这是一个**正作用**控制器，其增益为正。(注意：本示例中的平台逻辑经过简化，并未完全展示这一点，但增益理论是正确的)。

**控制器2: 河道水量控制**
```python
controller2 = PIDController(
    Kp=-1e-5, Ki=-1e-7, Kd=-1e-6, setpoint=4e5,
    min_output=0.0, max_output=1.0
)
```
该控制器的目标是将河道水量降低到400,000立方米。为此，它需要*开启* `gate_2`。由于正误差 (水量过高) 必须导致正向动作 (开启闸门)，这是一个**反作用**过程，其增益必须为负。

### 2.3. 使用平台组装系统
现在，`add_controller` 方法更加明确，要求我们定义完整的控制回路连接。

```python
harness.add_controller(
    controller_id="res_level_ctrl",  # 控制器逻辑的唯一名称
    controller=controller1,
    controlled_id="gate_1",          # 该控制器发送动作的目标组件
    observed_id="reservoir_1",       # 该控制器获取其状态的源组件
    observation_key="water_level"    # 要监视的特定状态变量
)
harness.add_controller(
    controller_id="chan_vol_ctrl",
    controller=controller2,
    controlled_id="gate_2",
    observed_id="channel_1",
    observation_key="volume"
)
```
这个新的函数签名使平台中的 `run_simulation` 方法变得更加强大，因为它现在可以将任何控制器连接到任何组件的状态变量，并控制任何其他组件。

## 3. 理解仿真逻辑

广义的 `run_simulation` 方法现在执行以下步骤：
1.  **遍历控制器**: 对于每个定义的控制器 (例如, `res_level_ctrl`)，它找到 `observed_id` 组件 (`reservoir_1`)。
2.  **获取观测值**: 它从该组件的状态中检索指定的 `observation_key` (`water_level`)。
3.  **计算动作**: 它将此观测值传递给控制器，控制器计算出一个控制信号。
4.  **存储动作**: 平台存储此动作，并将其映射到 `controlled_id` (`gate_1`)。
5.  **重复**: 对所有控制器重复此过程。
6.  **应用动作**: 它将所有存储的动作应用于目标组件。
7.  **模拟物理过程**: 它执行为 `水库 -> 闸门 -> 河道 -> 闸门` 拓扑结构硬编码的物理过程，计算流量并更新组件状态。

## 4. 运行示例

在您的终端中执行该脚本：
```bash
python3 example_multi_gate_river.py
```
观察输出。您将看到 `gate_1` 和 `gate_2` 的控制器独立工作以实现各自的目标。

```
--- Simulation Step 1, Time: 0.00s ---
  Controller 'res_level_ctrl': Target for 'gate_1' = 0.75
  Controller 'chan_vol_ctrl': Target for 'gate_2' = 1.00
  State Update: Res Level=16.67m, Chan Vol=499970.59m^3, G1 Open=0.25, G2 Open=0.55
```
在这里，您可以看到两个控制器同时计算它们期望的目标。然后，您可以追踪 `Res Level` (水库水位) 和 `Chan Vol` (河道水量) 如何随时间响应两个闸门的开启和关闭而变化。这演示了一个在编排仿真中进行多变量控制的简单而强大的例子。
