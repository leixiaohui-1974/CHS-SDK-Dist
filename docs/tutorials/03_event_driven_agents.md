# 教程 3: 事件驱动的代理与消息总线

本教程介绍了智能水务平台最重要的架构演进：**多代理系统 (Multi-Agent System, MAS)** 架构。我们将从前两个示例中使用的集中式 `SimulationHarness` (仿真平台) 逻辑，转向探索一个使用 `example_mas_simulation.py` 脚本的、真正解耦的、事件驱动的系统。

## 1. 新架构：从编排到协作

在我们之前的示例中，`SimulationHarness` 扮演着一个中央编排者的角色。它了解每一个组件，直接调用控制器，并手动在组件之间传递数据。这种方式简单，但对于一个大型、分布式的系统来说，既不具备可扩展性，也不够真实。

MAS架构改变了这种模式：
- **代理是独立的 (Agents are independent)**: 它们彼此之间互不知晓；它们只知道 `MessageBus` (消息总线) 的存在。
- **通信是事件驱动的 (Communication is event-driven)**: 代理向命名的“主题 (topics)”发布信息 (消息)，并订阅它们关心的主题。这被称为**发布/订阅 (Publish/Subscribe)**模式。
- **平台被简化 (The Harness is simplified)**: `SimulationHarness` 变成一个简单的时间管理者和物理引擎。它不再包含控制逻辑。

这是一个强大的概念，它反映了现实世界中分布式控制系统的构建方式。

## 2. MAS架构中的关键组件

让我们看看实现这一架构的新的和升级的组件。

### 2.1. `消息总线 (MessageBus)`
`MessageBus` 是我们平台的中央神经系统。所有的代理和能感知消息的组件都连接到它。一个代理可以向特定主题 (例如, `"state.reservoir.level"`) `publish` (发布) 一条消息，并 `subscribe` (订阅) 任何它感兴趣的主题。当一条消息被发布到一个主题时，总线确保该主题的所有订阅者都能立即收到该消息。

### 2.2. `数字孪生代理 (DigitalTwinAgent)`
该代理的角色是充当一个物理组件的“数字孪生”，向系统的其余部分报告其状态。
```python
twin_agent = DigitalTwinAgent(
    agent_id="twin_agent_reservoir_1",
    simulated_object=reservoir,
    message_bus=message_bus,
    state_topic=RESERVOIR_STATE_TOPIC
)
```
它的 `run()` 方法现在有了一个明确的目的：在每个仿真步骤，平台调用 `run()`，该代理读取其物理模型 (`reservoir`) 的状态，并**发布**该状态到其 `state_topic`。

### 2.3. `本地控制代理 (LocalControlAgent)`
在 `example_mas_simulation.py` 中，`PIDController` 被一个 `LocalControlAgent` 封装。该代理处理所有的通信，使得控制器可以纯粹地专注于其算法本身。

```python
control_agent = LocalControlAgent(
    agent_id="control_agent_gate_1",
    controller=pid_controller,
    message_bus=message_bus,
    observation_topic=RESERVOIR_STATE_TOPIC,
    observation_key='water_level', # 告知代理使用消息的哪个部分
    action_topic=GATE_ACTION_TOPIC,
    dt=harness.dt # 代理需要知道仿真时间步长
)
```
这个代理的工作是：
1.  在其 `observation_topic` 上**监听**消息。
2.  当消息到达时，它使用 `observation_key` 来提取相关的值 (例如, `14.0`)。
3.  它将这个值和仿真时间步长 (`dt`) 传递给其内部的 `pid_controller`。
4.  它获取控制器的输出，并将其作为一条新消息**发布**到其 `action_topic`。

### 2.4. 能感知消息的物理模型
为了使系统完全解耦，物理模型本身也可以对消息做出反应。我们已经使 `Gate` (闸门) 模型能够感知消息。

```python
gate = Gate(
    gate_id="gate_1",
    ...,
    message_bus=message_bus,
    action_topic=GATE_ACTION_TOPIC
)
```
在实例化时，`Gate` 现在会**订阅**其 `action_topic`。当 `control_agent` 发布一个新的命令时，闸门的 `handle_action_message` 方法被触发，它会更新其内部的目标开启度。当平台稍后调用 `gate.step()` 方法时，闸门已经知道它应该移动到哪里。

## 3. MAS仿真循环

`SimulationHarness` 现在使用 `run_mas_simulation()` 方法。在每个时间步，它执行一个清晰的两阶段过程：

1.  **阶段1: 感知与动作级联 (Perception & Action Cascade)**: 平台调用 `DigitalTwinAgent` 的 `run()` 方法。
    -   孪生代理发布水库的当前状态。
    -   同步的 `message_bus` 立即将此状态消息传递给 `control_agent`。
    -   `control_agent` 的 `handle_observation` 方法被触发，它计算一个新的控制信号，并将其发布到动作主题。
    -   总线将动作消息传递给 `gate` 模型，该模型更新其内部目标。

2.  **阶段2: 物理步骤 (Physical Step)**: 平台调用每个物理模型的 `step()` 方法。
    -   平台计算物理交互 (从闸门流出的水量)。
    -   它根据物理原理和在阶段1中收到的动作，对 `reservoir` 和 `gate` 进行步进计算，更新它们的状态。

这个循环完美地展示了关注点分离：代理思考，模型行动。

## 4. 为何这个架构如此重要

- **可扩展性 (Scalability)**: 可以向系统中添加新的代理和组件，而无需修改现有的。我们只需要定义新的主题，并确保它们订阅了正确的主题。
- **解耦 (Decoupling)**: 控制逻辑与物理模型完全分离，可以轻松地替换算法。
- **真实性 (Realism)**: 这种架构更接近于现实世界中分布式控制系统的构建方式，为更高级的功能（如网络延迟仿真和硬件在环测试）铺平了道路。
