# 教程 5: 模拟复杂网络

在之前的教程中，我们构建了一个复杂的多代理控制系统。然而，我们所有的示例都具有简单的线性拓扑结构：一个水库流入一条河道。现实世界的水系统很少如此简单。它们是具有多个源头、支流和分支路径的复杂网络。

本教程涵盖了智能水务平台迄今为止最重要的增强功能：一个**基于图的仿真平台**，它允许对任意复杂的、非线性的网络拓扑进行建模。

## 线性方法的局限性

之前的 `SimulationHarness` (仿真平台) 是硬编码来模拟一个特定的、线性的组件链。要模拟不同的结构，就需要修改平台内部的仿真循环。这是不灵活且不可扩展的。

为了克服这一点，我们重构了平台，使其将水系统不视为一个列表，而是一个**有向图 (directed graph)**。

## 基于图的拓扑结构

在这个新范式中，水系统是组件“节点”的集合，这些节点由代表水流方向的“边”连接起来。

-   **节点 (Nodes)**: 这些是物理组件 (`水库 (Reservoir)`、`闸门 (Gate)`、`河道 (RiverChannel)`)。
-   **边 (Edges)**: 这些代表组件之间的连接 (例如，一个 `闸门` 的输出流入一个 `河道`)。

这种方法非常灵活，使我们能够模拟现实世界的场景，例如：
-   一条由多个支流汇入的河流。
-   一条分叉成两条独立运河的渠道。
-   复杂的多水库系统。

### 新的 `SimulationHarness` API

为了支持这个新模型，`SimulationHarness` 的API已更新：

1.  **`add_component(component)`**: 这个方法保持不变，但它现在只是定义系统的一部分。它将一个组件（一个节点）添加到我们的图中。

2.  **`add_connection(upstream_id, downstream_id)`**: 这是定义网络结构新的核心方法。它在图中创建一个有向边，告知平台水从 `upstream_id` 组件流向 `downstream_id` 组件。

3.  **`build()`**: 在添加了所有组件和连接之后，您必须调用此方法。它对图执行**拓扑排序**，以确定正确的计算顺序（始终先处理上游组件，再处理下游组件），并检查任何物理上不可能的循环（例如，一条河流流回自身）。

## 示例：一个分支的河流网络

理解这一点的最佳方式是通读新的 `example_branched_network.py` 脚本，该脚本现在包含一个完整的多代理控制系统。

该示例模拟了以下网络：
- **水库1** -> **闸门1** -> **支流河道**
- **水库2** -> **闸门2** -> **主河道**
- **支流河道** 也汇入 **主河道** (一个汇流点)。
- **主河道** 通过最后的 **闸门3** 流出。

以下是该脚本的分解说明：

### 1. 导入和样板代码
```python
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher

def run_branched_network_example():
    # ...
```
我们首先导入物理组件和代理控制系统所需的所有类。

### 2. 初始化平台和组件
```python
    # 1. 设置仿真平台和消息总线
    simulation_config = {'duration': 1000, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. 定义物理组件
    res1 = Reservoir("res1", {'volume': 15e6, 'water_level': 10.0}, {'surface_area': 1.5e6})
    g1 = Gate("g1", {'opening': 0.1}, {'width': 10, 'max_rate_of_change': 0.1})
    trib_chan = RiverChannel("trib_chan", {'volume': 2e5, 'water_level': 2.0}, {'k': 0.0002})

    res2 = Reservoir("res2", {'volume': 30e6, 'water_level': 20.0}, {'surface_area': 1.5e6})
    g2 = Gate("g2", {'opening': 0.1}, {'width': 15, 'max_rate_of_change': 0.1})

    main_chan = RiverChannel("main_chan", {'volume': 8e5, 'water_level': 8.0}, {'k': 0.0001})
    g3 = Gate("g3", {'opening': 0.5}, {'width': 20}) # 不受控制的闸门

    physical_components = [res1, g1, trib_chan, res2, g2, main_chan, g3]
    for comp in physical_components:
        harness.add_component(comp)
```
首先，我们创建 `SimulationHarness`。然后，我们实例化构成我们网络的全部七个物理组件。最后，我们使用 `add_component()` 将它们全部添加到平台中。此时，平台知道这些节点，但不知道它们是如何连接的。

### 3. 定义拓扑结构
```python
    # 3. 定义网络拓扑
    print("\nDefining network connections...")
    harness.add_connection("res1", "g1")
    harness.add_connection("g1", "trib_chan")
    harness.add_connection("res2", "g2")
    harness.add_connection("trib_chan", "main_chan")
    harness.add_connection("g2", "main_chan")
    harness.add_connection("main_chan", "g3")
    print("Connections defined.")
```
这是新的、关键的部分。我们使用一系列 `add_connection()` 调用来定义水网的确切结构。这创建了平台将用于仿真的有向图，包括 `trib_chan` 和 `g2` 都流入 `main_chan` 的汇流点。

### 4. 定义多代理控制系统
```python
    # 4. 定义多代理系统
    # ... (DigitalTwinAgent, PIDController, LocalControlAgent, CentralDispatcher 实例)

    all_agents = twin_agents + [lca1, lca2, dispatcher]
    for agent in all_agents:
        harness.add_agent(agent)
```
这部分与之前的教程类似。我们创建了一个完整的分层控制系统：
-   用于水库和受控闸门的**数字孪生**，以发布它们的状态。
-   用于 `g1` 和 `g2` 的**PID控制器**。
-   **本地控制代理**来管理每个PID控制器，订阅相应的水库水位并向相应闸门的动作主题发布消息。
-   一个**中央调度器**，它监控两个水库的水位，并向本地代理发送高层的设定点命令。

### 5. 构建和运行
```python
    # 5. 构建并运行仿真
    print("\nBuilding simulation harness...")
    harness.build()
    harness.run_mas_simulation()
```
最后，我们调用 `harness.build()` 来最终确定拓扑结构。然后，`harness.run_mas_simulation()` 启动仿真。现在，平台会根据我们定义的图自动处理所有组件之间复杂的数据流。

## 结论

通过转向基于图的拓扑结构，智能水务平台现在能够模拟远比以前更真实、更复杂的场景。这一基础性变革为模拟整个水区、优化互联系统以及探索更复杂的控制策略打开了大门。
