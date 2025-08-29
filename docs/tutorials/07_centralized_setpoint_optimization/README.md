# 教程 7: 集中式设定点协同优化

## 1. 场景目标

本教程旨在演示一种比紧急干预更精细的**集中式控制**应用：**远程设定点优化**。

我们将构建一个由两个水库串联而成的系统。一个**中央调度智能体**的核心任务是维持下游水库的水位在一个理想的区间内（例如，8m到10m之间）。为了实现这个全局目标，它需要远程调整上游水库出口闸门的**控制设定点**。

通过本示例，您将学习到：
- `CentralDispatcherAgent` 的标准用法。
- 如何通过调整远程控制器的设定点，来实现一个更高层级的、基于目标的全局控制策略。
- 分层控制中“目标设定层”（中央）与“目标执行层”（地方）的解耦设计。

## 2. 系统配置

本场景的配置分为以下几个文件：

- **`components.yml`**: 定义了三个物理组件：
  - `upper_reservoir`: 上游水库，拥有持续的外部入流。
  - `middle_gate`: 连接两个水库的闸门。
  - `lower_reservoir`: 下游水库，其水位是我们的主要调控目标。
- **`topology.yml`**: 定义了清晰的串联拓扑：`upper_reservoir` -> `middle_gate` -> `lower_reservoir`。
- **`config.yml`**: 定义了仿真的总时长和时间步长。
- **`agents.yml`**: 定义了系统的智能体：
  - `lower_reservoir_twin`: 数字孪生智能体，感知 `lower_reservoir` 的实时水位，并发布到主题 `state/reservoir/lower`。
  - `central_dispatcher`: **本场景的核心**。它订阅 `state/reservoir/lower` 来监控下游水位。它的配置参数（`dispatcher_params`）中定义了目标水位的上下限（`low_level`, `high_level`）以及对应的远程设定点（`low_setpoint`, `high_setpoint`）。
    - 当下游水位**低于** `low_level`，它会向 `command/gate/middle` 主题发布一个**较高**的设定点，命令闸门控制器加大放水。
    - 当下游水位**高于** `high_level`，它会向 `command/gate/middle` 主题发布一个**较低**的设定点，命令闸门控制器减小放水。
  - **`middle_gate_controller` (概念)**: 这是一个本地PID控制智能体。它的**过程变量**是 `middle_gate` 的实际开度，而它的**设定点**则由 `central_dispatcher` 通过 `command/gate/middle` 主题动态下发。

## 3. 预期结果

在一个包含所有组件（包括必要但无法从YAML加载的本地控制器）的完整系统中，您将观察到：
1.  仿真开始后，`central_dispatcher` 会根据 `lower_reservoir` 的初始水位发出第一个设定点指令。
2.  `middle_gate` 的开度会根据本地PID控制器的调节，逐渐趋近于中央下发的设定点。
3.  当 `lower_reservoir` 的水位触及预设的上下限时，`central_dispatcher` 会发布一个新的设定点指令。
4.  `middle_gate_controller` 接收到新指令后，会驱动闸门开度向新的设定点调节。

整个过程体现了一个典型的分层控制回路：中央智能体负责制定策略（决定设定点），而地方智能体负责战术执行（通过PID调节来达到该设定点）。
