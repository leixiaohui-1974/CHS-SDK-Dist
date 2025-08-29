# 培训 1: 构建一个基础仿真

本教程将指导您使用智能水务平台从零开始构建一个简单的仿真。我们将构建一个水电站仿真，其代码示例位于 `swp/examples/example_hydropower_simulation.py`。

## 1. 核心概念

该平台围绕几个核心概念构建：

-   **物理模型 (Physical Models)**: 这些是代表水系统中物理组件的Python类，例如 `湖泊 (Lake)`、`管道 (Pipe)` 或 `闸门 (Gate)`。它们必须继承自 `PhysicalObjectInterface`。
-   **仿真平台 (Simulation Harness)**: 这是管理仿真的主引擎。您可以将您的物理模型添加到平台中，定义它们之间的连接方式，然后运行仿真。
-   **状态 (State) 和 参数 (Parameters)**: 每个模型都有一个随时间变化的 `状态` (例如，当前水量)，以及静态的 `参数` (例如，管道直径)。

## 2. 设置仿真文件

首先，创建一个新的Python文件。我们称之为 `my_first_simulation.py`。

## 3. 导入必要的类

您需要导入 `SimulationHarness` 以及您想要使用的物理模型。

```python
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.simulation_identification.physical_objects.lake import Lake
from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine
from swp.simulation_identification.physical_objects.canal import Canal
```

## 4. 初始化仿真平台

仿真平台通过一个配置字典进行初始化，该字典指定了仿真的 `duration` (持续时间，单位为秒) 和 `dt` (时间步长，单位为秒)。

```python
# 模拟1天，时间步长为1小时
config = {'duration': 86400, 'dt': 3600}
harness = SimulationHarness(config)
```

## 5. 创建物理模型

现在，创建您想要仿真的模型的实例。每个模型都需要一个唯一的 `name` (名称)，一个 `initial_state` (初始状态) 字典，以及一个 `parameters` (参数) 字典。

```python
# 上游湖泊
initial_lake_volume = 40e6
lake_surface_area = 2e6
upper_lake = Lake(
    name="upper_lake",
    initial_state={'volume': initial_lake_volume, 'water_level': initial_lake_volume / lake_surface_area},
    params={'surface_area': lake_surface_area, 'max_volume': 50e6}
)

# 水轮机
turbine = WaterTurbine(
    name="turbine_1",
    initial_state={'power': 0, 'outflow': 0},
    params={'efficiency': 0.85, 'max_flow_rate': 150}
)

# 尾水渠
tailrace_canal = Canal(
    name="tailrace_canal",
    initial_state={'volume': 100000, 'water_level': 2.1},
    params={
        'bottom_width': 20,
        'length': 5000,
        'slope': 0.0002,
        'side_slope_z': 2,
        'manning_n': 0.025
    }
)
```

## 6. 向平台添加组件

将您创建的模型添加到仿真平台中。

```python
harness.add_component(upper_lake)
harness.add_component(turbine)
harness.add_component(tailrace_canal)
```

## 7. 定义拓扑结构

定义组件之间的连接方式。这些连接代表了水的流向。

```python
harness.add_connection("upper_lake", "turbine_1")
harness.add_connection("turbine_1", "tailrace_canal")
```

## 8. 构建并运行仿真

最后，构建平台（它会计算出运行模型的正确顺序）并运行仿真。

```python
harness.build()
harness.run_simulation()
```

就是这样！您已经成功构建并运行了您的第一个仿真。`run_simulation` 方法将在每个时间步打印出每个组件的状态。
