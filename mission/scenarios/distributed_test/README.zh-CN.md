# “引绰济辽”工程仿真场景

本目录包含“引绰济辽”输水工程的数字孪生仿真模型。

## 场景简介

“引绰济辽”工程是内蒙古一项重要的跨流域、长距离调水工程，旨在将绰尔河的丰沛水量调引至辽河流域，以缓解沿线地区的缺水问题。

此仿真场景模拟了从**文得根水库**（`wendegen_reservoir`）取水，经过一系列隧洞、管道和控制闸门，最终将水输送至末端水池（`terminal_pool`）的全过程。

此目录包含两种运行方式：
1.  **数据驱动方式**: 通过 `run_scenario.py` 脚本加载本目录下的YAML配置文件来运行。
2.  **代码驱动方式**: 直接运行 `yinchuojiliao_main.py` 脚本。

## 系统构成

该仿真模型主要由以下几部分构成：

1.  **物理组件 (`components.yml`)**:
    *   **水库**: 文得根水库 (`wendegen_reservoir`), 连接池 (`connection_pool`), 末端水池 (`terminal_pool`)。
    *   **隧洞/渠道 (`Canal`)**: `tunnel_1`, `tunnel_2`, `tunnel_3`。
    *   **管道 (`Pipe`)**: `pipe_1`, `pipe_2`。
    *   **闸门/阀门 (`Gate`/`Valve`)**: 沿线分布的多个闸门和阀门，用于控制水流。

2.  **系统拓扑 (`topology.yml`)**:
    *   定义了所有物理组件之间的连接关系，形成一个从上游到下游的线性输水系统。

3.  **控制器与智能体 (`agents.yml`)**:
    *   **PID控制器**: 系统中包含多个PID控制器，用于自动调节关键节点的闸门开度和阀门设定，以维持稳定的水位或压力。例如，`taoriver_ctrl` 用于控制`tunnel_1`的水位。
    *   **数字孪生体 (`DigitalTwinAgent`)**: 为每一个物理组件都创建了一个数字孪生体，用于在信息空间中实时映射物理实体的状态。
    *   **中央调度智能体 (`CentralDispatcherAgent`)**: 模拟中央控制室的决策逻辑。它会监测末端水池的水位，并根据水位的高低来调整上游进水口的控制目标，实现全局需求响应。
    *   **应急处理智能体 (`EmergencyAgent`)**: 负责监测输水管道的压力。当压力低于安全阈值时，它会立即采取行动，例如关闭进水闸门，以防止事故发生。
    *   **数据输入智能体 (`CsvInflowAgent`)**: 从 `data/historical_inflow.csv` 文件中读取历史入流数据，作为文得根水库的上游来水输入。

4.  **仿真配置 (`config.yml`)**:
    *   设定了仿真的总时长（`duration`）和时间步长（`dt`）。

## 如何运行

### 方式一：数据驱动

在项目根目录下执行以下命令来运行此仿真场景：

```bash
python run_scenario.py mission/scenarios/yinchuojiliao
```

### 方式二：代码驱动

直接运行场景目录下的Python脚本：

```bash
python mission/scenarios/yinchuojiliao/yinchuojiliao_main.py
```

仿真结束后，两种方式的输出结果都将保存在 `mission/scenarios/yinchuojiliao/output.yml` 文件中。
