# 教程 4: 使用中央调度器的分层控制

欢迎来到我们入门系列的最后一个教程。在这里，我们将在教程3的事件驱动概念的基础上，创建一个**分层控制系统 (hierarchical control system)**。这是一种强大的模式，其中一个高层的“主管”代理管理一个或多个低层“操作员”代理的目标。

我们将探索 `example_hierarchical_control.py` 脚本，这是平台功能最先进的示例。

## 1. 场景概述

该场景演示了一个两级控制层次结构：
- **低层循环 (The "Operator")**: 一个 `LocalControlAgent` (本地控制代理) 负责对一个闸门进行直接的、实时的控制。其目标是维持水库的特定水位，它通过监听水库的状态并调节闸门开启度来实现这一目标。
- **高层循环 (The "Supervisor")**: 一个 `CentralDispatcher` (中央调度器) 代理充当系统范围的主管。它也监听水库的状态，但它的工作是做出战略决策。如果它检测到“洪水状况” (水位过高)，它将向 `LocalControlAgent` 发出命令，告知其采用一个新的、更低的水位设定点。

这创建了一个动态系统，其中一个中央“大脑”可以根据整体系统状态来管理本地控制器的目标。

## 2. 两级控制循环

该系统在两个通过 `MessageBus` (消息总线) 通信的、嵌套的、事件驱动的循环上运行：
1.  **低层状态/动作循环**:
    - `twin_agent_reservoir_1` 将水库的状态发布到 `state.reservoir.level` 主题。
    - `control_agent_gate_1` 接收此状态，用其PID控制器计算一个动作，并将其发布到 `action.gate.opening` 主题。
    - `gate_1` 模型接收到该动作并更新其目标。
2.  **高层状态/命令循环**:
    - `central_dispatcher_1` 也从 `state.reservoir.level` 主题接收状态。
    - 它应用其内部规则并决定设定点是否需要更改。
    - 如果需要更改，它会向 `command.gate1.setpoint` 主题发布一条新的设定点消息。
    - `control_agent_gate_1` (它也订阅了这个命令主题) 接收到新的设定点，并更新其内部PID控制器的目标。

## 3. 代码分解

让我们来检查 `example_hierarchical_control.py` 中新的和更新的部分。

### 3.1. 升级 `LocalControlAgent`
`LocalControlAgent` 现在用两个新的主题进行实例化：
- `command_topic`: 用于监听来自主管的新命令的主题。
- `feedback_topic`: 用于监听其所控制的组件（在本例中是闸门本身）的状态更新的主题。这创建了一个完整的闭环。

```python
control_agent = LocalControlAgent(
    agent_id="control_agent_gate_1",
    controller=pid_controller,
    message_bus=message_bus,
    observation_topic=RESERVOIR_STATE_TOPIC,
    observation_key='water_level',
    action_topic=GATE_ACTION_TOPIC,
    dt=simulation_dt,
    command_topic=GATE_COMMAND_TOPIC,
    feedback_topic=GATE_STATE_TOPIC
)
```
该代理的内部逻辑现在有一个 `handle_command_message` 方法来处理传入的命令，以及一个 `handle_feedback_message` 方法来接收来自其控制的执行器的更新。

### 3.2. 实现 `CentralDispatcher`
这是一种新型的代理，代表了更高层次的智能。它订阅一个或多个状态主题，并向一个或多个命令主题发布消息。其核心逻辑由一组规则定义。

```python
dispatcher_rules = {
    'flood_threshold': 18.0,   # 如果水位 > 18米，则有洪水风险
    'normal_setpoint': 15.0, # 正常目标水位
    'flood_setpoint': 12.0   # 紧急目标水位，以降低水量
}
dispatcher = CentralDispatcher(
    agent_id="central_dispatcher_1",
    message_bus=message_bus,
    state_subscriptions={'reservoir_level': RESERVOIR_STATE_TOPIC},
    command_topics={'gate1_command': GATE_COMMAND_TOPIC},
    rules=dispatcher_rules
)
```
在这个例子中，调度器的规则很简单：如果 `reservoir_level` (水库水位) 超过 `flood_threshold` (洪水阈值) 18.0米，它将向 `gate1_command` 主题发布一个命令，告知本地代理采用 `flood_setpoint` (洪水设定点) 12.0米。

## 4. 运行仿真并解读结果

在您的终端中执行该脚本：
```bash
python3 example_hierarchical_control.py
```
日志输出清楚地显示了层次结构的运作。

**第1步: 主管介入**
在最开始，水位是19.0米，高于18.0米的洪水阈值。
```
--- MAS Simulation Step 1, Time: 0.00s ---
  Phase 1: Triggering agent perception and action cascade.
PIDController setpoint updated from 15.0 to 12.0.
```
在第一步完成之前，`CentralDispatcher` 就已经收到了初始状态，评估了其规则，并发布了一个命令。`LocalControlAgent` 接收到这个命令，并立即将其PID控制器的设定点从默认的15.0更新为新的紧急设定点12.0。

**第2步: 操作员执行**
现在，使用新的设定点，`LocalControlAgent` 开始工作。
```
  Phase 2: Stepping physical models with interactions.
  State Update: Reservoir level = 19.000m, Gate opening = 0.600m
```
因为水位 (19.0m) 远高于新的目标 (12.0m)，PID控制器命令闸门开启。在接下来的几个步骤中，闸门持续开启直到达到其最大值，水库水位稳步下降。

这个例子为构建真正智能的、多层次的控制系统提供了基础，在这样的系统中，战略性的、系统范围的目标可以被转化为本地控制器具体、稳健执行的动作。
