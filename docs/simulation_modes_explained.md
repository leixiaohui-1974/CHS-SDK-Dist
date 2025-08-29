# 仿真模式详解 (Simulation Modes Explained)

## 1. 概述 (Overview)

本平台支持多种仿真范式，它们并非相互排斥，而是代表了不同层次的系统复杂度和控制策略。理解这些模式有助于高效地利用本平台进行从简单物理过程模拟到复杂智能系统测试的各种任务。

核心概念包括三种：
- **状态式仿真 (State-Based Simulation)**: 纯物理过程模拟，是所有仿真的基础核心。
- **代理式仿真 (Agent-Based Simulation)**: 分布式、事件驱动的智能系统，是平台的主要架构。
- **集中式仿真 (Centralized Simulation)**: 在代理式架构下实现的一种分层、目标驱动的控制策略。

---

## 2. 状态式仿真 (State-Based Simulation): 物理核心

**概念 (Concept):**
这是最基础的仿真层次，仅模拟系统中各个物理组件（如水库、管道、闸门）的行为，完全遵循预设的物理和水力学规律。此模式下不涉及任何智能决策或主动控制，旨在观察系统在给定输入和边界条件下的自然演化过程。

**代码实现 (Code Implementation):**
- **物理模型**: 所有物理组件的数学模型都定义在 `core_lib/physical_objects/` 目录下（例如 `Reservoir`, `Canal`, `Gate`）。这些类都实现了 `Simulatable` 接口。
- **拓扑与加载**: `SimulationLoader` 根据 `components.yml` 和 `topology.yml` 文件实例化物理组件，并构建它们之间的连接关系图。
- **仿真引擎**: 核心驱动逻辑位于 `SimulationHarness._step_physical_models()` 方法中。该方法会按照拓扑排序（保证水流方向的计算正确性）依次调用每个物理组件的 `.step()` 方法，更新其状态。

**如何运行 (How to Run):**
在你的场景配置中，提供一个空的 `agents.yml` 文件，或者文件中不包含任何控制或感知类的智能体。当 `run_scenario.py` 执行时，`SimulationHarness.run_mas_simulation()` 的主循环中，智能体执行阶段将无事可做，只有物理模型演化阶段 `_step_physical_models()` 会被有效执行，从而实现纯粹的状态式仿真。

---

## 3. 代理式仿真 (Agent-Based Simulation): 分布式智能

**概念 (Concept):**
这是平台设计的核心架构，即一个多智能体系统 (Multi-Agent System, MAS)。在此模式下，多个拥有自主行为的智能体（Agent）通过一个中央消息总线进行通信，形成一个分布式的感知-决策-行动系统。每个智能体通常只负责一个局部任务，系统的宏观智能行为由所有智能体的交互涌现而出。

**代码实现 (Code Implementation):**
- **仿真引擎**: `SimulationHarness.run_mas_simulation()` 方法是此模式的专用执行器。其主循环在每个时间步分为两个阶段：
    1.  **智能体行动**: 循环调用所有已加载智能体的 `.run()` 方法。
    2.  **物理世界演化**: 调用 `_step_physical_models()` 更新物理状态。
- **感知 (Perception)**: 以 `DigitalTwinAgent` 为代表的感知智能体是物理世界到信息世界的桥梁。在它的 `.run()` 方法中，它会调用 `self.model.get_state()` 从其关联的物理模型获取状态，然后通过 `self.bus.publish()` 将状态发布到 `MessageBus` 的指定主题上。
- **通信 (Communication)**: `core_lib/central_coordination/collaboration/message_bus.py` 中定义的 `MessageBus` 是所有智能体异步通信的中枢。
- **行动 (Action)**: 控制类智能体（如 `LocalControlAgent` 的子类）订阅 `MessageBus` 上的相关主题以获取状态或指令。在做出决策后，它们可以直接调用其持有的物理组件实例的方法（例如 `gate.set_opening()`），或发布新的指令消息到总线，供其他智能体使用。

**如何运行 (How to Run):**
在 `agents.yml` 文件中定义所有你需要的感知、控制、扰动等智能体。`SimulationLoader` 会负责将它们实例化，并注入 `MessageBus` 和其他依赖，最终“装配”出一个完整的多智能体系统。

---

## 4. 集中式仿真 (Centralized Simulation): 分层控制策略

**概念 (Concept):**
集中式仿真并非一个与代理式并列的独立模式，而是**在代理式仿真架构下实现的一种高级控制策略**。它通过引入一个或多个拥有全局视野的“中央”智能体，来实现对下层“地方”智能体的协调和调度，构成一个分层控制系统。

**代码实现 (Code Implementation):**
- **中央智能体**: 以 `CentralDispatcherAgent` 为例，这类智能体被设计用来监控全局的关键绩效指标（KPI）或系统状态。
- **全局决策**: 中央智能体在其 `.run()` 逻辑中，会评估全局状态。例如，`CentralDispatcherAgent` 会检查水库的全局水位。
- **顶层指令**: 当满足某个全局条件时（如水位超过防洪限制），中央智能体便会向 `MessageBus` 发布一个高优先级的指令消息。这个消息的目标通常是某个或某些地方智能体。
- **分层执行**: 地方智能体（如某个闸门的控制智能体）除了执行自己的本地控制逻辑外，也订阅来自中央智能体的指令主题。当收到顶层指令时，它会服从该指令，覆盖掉自己原来的决策。这就实现了一个清晰的“中央调度-地方执行”的分层控制链路。

**如何运行 (How to Run):**
在你的 `agents.yml` 配置文件中，除了定义所有地方智能体外，再加入一个或多个中央协调类的智能体（如 `CentralDispatcherAgent`）。只要这个智能体被加载到系统中，整个代理式仿真就自动具备了集中式、分层控制的特性。

---

## 5. (附录) 简单集中控制模式 (Appendix: Simple Centralized Control Mode)

**概念 (Concept):**
这是一个为简化测试而存在的、同步的仿真模式。它完全绕过了智能体和 `MessageBus` 架构，允许控制器（Controller）直接与物理模型交互。

**代码实现 (Code Implementation):**
- **仿真引擎**: 此模式由 `SimulationHarness.run_simulation()` 方法实现。
- **同步循环**: 在每个仿真步，该方法会：
    1.  直接遍历所有注册的 `Controller` 对象。
    2.  从每个控制器所观察的物理模型中获取状态。
    3.  调用 `controller.compute_control_action()` 计算出控制信号。
    4.  将所有控制信号统一传递给 `_step_physical_models()` 方法，作用于物理模型。

**使用场景 (Use Case):**
此模式非常适合用来快速验证一个独立的、简单的反馈控制器（如PID控制器）的性能，而无需配置和运行一整套复杂的智能体系统。注意，标准的 `run_scenario.py` 脚本调用的是 `run_mas_simulation()`，因此该模式主要用于代码内部的编程式调用和单元测试。
