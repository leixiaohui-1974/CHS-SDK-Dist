# 智能体架构设计文档

| **文档状态** | **版本号** | **最后更新日期** |
| :--- | :--- | :--- |
| 正式发布 | 1.0 | 2023-10-27 |

## 1. 简介

本文档是水系统智能控制平台的核心设计文档，旨在为平台开发提供一套标准、统一的智能体（Agent）架构。该架构基于**水系统控制论**，对现有代码库进行了深度分析和归纳，将所有智能体清晰地划分为“被控对象代理”、“控制对象代理”、“中央协调代理”和“任务与模拟支持智能体”四大类。

本文档的目标是：
*   **明确职责边界**：清晰定义每一类智能体的功能和通信范围。
*   **规范继承关系**：所有智能体设计严格遵循既有的代码基类，确保架构的一致性。
*   **提供开发参考**：罗列当前已实现和建议新增的智能体清单及其源码路径，作为未来开发的基准。

## 2. 核心架构原则

为了保证系统的稳定性、可扩展性和模块化，所有智能体的设计与实现均需遵循以下核心原则：

1.  **被控对象代理 (Controlled Object Agents)**
    *   **职责**：代表水系统中的物理单元（如水库、河道、泵站），其核心职责是**提供状态感知能力**，作为物理世界的数字孪生。
    *   **行为**：这类代理**不执行主动控制**，仅向上层或协调者报告自身状态。

2.  **控制对象代理 (Control Object Agents)**
    *   **职责**：代表具有主动控制能力的物理单元（如水泵、水闸、水电站）。
    *   **行为**：既具备被控对象的感知能力，又可**接收并执行控制指令**。控制逻辑可以分层，例如，站级代理（泵站）负责协调，并将具体指令（如启停、开度）下发给机组级代理（单个水泵）。

3.  **中央协调代理 (Central Agents)**
    *   **职责**：作为系统的最高决策层，负责**全局状态感知、优化计算和集中调度**。
    *   **行为**：仅与**控制对象代理**进行通信，下发宏观控制目标或指令，不直接干预被控对象。

4.  **代码基类继承 (Codebase Consistency)**
    *   **原则**：所有智能体的分类严格基于代码库中已定义的基类（如 `DigitalTwinAgent`, `LocalControlAgent`），不引入新的抽象概念，保证架构与代码实现的高度统一。

## 3. 智能体分类与清单

### 3.1 水系统被控对象代理 (Controlled Object Agents)
*   **继承关系**：继承自 `DigitalTwinAgent` 或其变体，扮演物理单元数字孪生的角色。
*   **核心功能**：状态感知与报告。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `ReservoirPerceptionAgent` | 水库感知，提供水位、库容等状态 | `core_lib/local_agents/perception/reservoir_perception_agent.py` |
| `PipelinePerceptionAgent` | 有压管道感知，提供流量、压力等状态 | `core_lib/local_agents/perception/pipeline_perception_agent.py` |
| `ChannelPerceptionAgent` | 无压渠道/河道感知，提供水位、流量等状态 | `core_lib/local_agents/perception/channel_perception_agent.py` |
| `HydropowerStationPerceptionAgent` | 水电站感知，提供上下游水位、总发电量等状态 | `core_lib/local_agents/perception/hydropower_station_perception_agent.py` |
| `PumpStationPerceptionAgent` | 泵站感知，提供集水池水位、总流量等站级状态 | `core_lib/local_agents/perception/pump_station_perception_agent.py` |
| `ValveStationPerceptionAgent` | 阀门/水闸站感知，提供上下游水位、总流量等站级状态 | `core_lib/local_agents/perception/valve_station_perception_agent.py` |

### 3.2 水系统控制对象代理 (Control Object Agents)
*   **继承关系**：继承自 `LocalControlAgent` 或其他自定义控制基类。
*   **核心功能**：接收指令，执行本地控制逻辑。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `HydropowerStationAgent` | 水电站控制，负责制定站级策略，并向下游发布针对单个水轮机或水闸的控制指令。 | `core_lib/local_agents/control/hydropower_station_agent.py` |
| `HydropowerStationControlAgent` | 水电站控制，同上。 | `core_lib/local_agents/control/hydropower_station_control_agent.py` |
| `PumpStationControlAgent` | 泵站控制，负责站级总调度（如决定开启泵的数量），并将指令下发给 `PumpControlAgent`。 | `core_lib/local_agents/control/pump_station_control_agent.py` |
| `PumpControlAgent` | 单个水泵控制，接收上级指令，负责单个水泵的启停、变频等具体操作。 | `core_lib/local_agents/control/pump_control_agent.py` |
| `ValveStationControlAgent` | 水闸站控制，负责实现站级流量或水位目标，并将计算出的开度指令下发给站内每个阀门。 | `core_lib/local_agents/control/valve_station_control_agent.py` |
| `LocalControlAgent` | 本地控制通用基类，定义了本地控制单元的基本行为。 | `core_lib/local_agents/control/local_control_agent.py` |
| `PressureControlAgent` | 压力控制，专用于需要维持特定压力的控制场景。 | `core_lib/local_agents/control/pressure_control_agent.py` |

### 3.3 中央协调代理 (Central Agents)
*   **继承关系**：无统一基类，为逻辑分组。
*   **核心功能**：全局感知、集中决策与调度。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `CentralDispatcherAgent` | 中央调度，系统的最高决策者，负责全局优化和指令分发。 | `core_lib/central_coordination/dispatch/central_dispatcher_agent.py`<br>`core_lib/local_agents/supervisory/central_dispatcher_agent.py` |
| `CentralMPCAgent` | 中央MPC控制，采用模型预测控制（MPC）算法进行全局优化调度。 | `core_lib/central_coordination/dispatch/central_mpc_agent.py` |
| `CentralPerceptionAgent` | 中央感知，汇集所有本地感知信息，形成全局态势图。 | `core_lib/central_coordination/perception/central_perception_agent.py` |

### 3.4 任务与模拟支持智能体 (Task & Simulation Support Agents)
*   **继承关系**：大多直接继承自 `Agent` 或 `BaseAgent`。
*   **核心功能**：提供数据输入、模拟扰动、执行特定任务（如预测、辨识）。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `CsvInflowAgent` | 从CSV文件读取并提供入流数据。 | `core_lib/data_access/csv_inflow_agent.py` |
| `EmergencyAgent` | 应急响应，监测特定条件并触发应急预案。 | `core_lib/local_agents/supervisory/emergency_agent.py` |
| `GridCommunicationAgent` | 电网通信，模拟或实际对接电网，获取电价或调度指令。 | `core_lib/local_agents/supervisory/grid_communication_agent.py` |
| `SupervisorAgent` | 监督/启动代理，负责启动和监控其他智能体。 | `core_lib/local_agents/supervisory/supervisor_agent.py` |
| `IdentificationAgent` | 参数辨识，在线或离线辨识物理模型的参数。 | `core_lib/identification/identification_agent.py` |
| `RainfallAgent` | 降雨模拟，根据预设模式提供降雨数据。 | `core_lib/disturbances/rainfall_agent.py` |
| `DynamicRainfallAgent` | 动态降雨模拟，可根据外部输入动态调整降雨过程。 | `core_lib/disturbances/dynamic_rainfall_agent.py` |
| `ForecastingAgent` | 预测通用代理。 | `core_lib/local_agents/prediction/forecasting_agent.py` |
| `InflowForecasterAgent` | 入流预测，基于历史数据和模型预测未来的入流量。 | `core_lib/local_agents/prediction/inflow_forecaster_agent.py` |
| `WaterUseAgent` | 用水模拟，模拟城市或农业的用水行为。 | `core_lib/local_agents/disturbances/water_use_agent.py` |
| `PhysicalIOAgent` | 物理I/O模拟，模拟与硬件（PLC、RTU）的交互。 | `core_lib/local_agents/io/physical_io_agent.py` |
| `InflowAgent` | 入流数据提供者，通用任务代理。 | `core_lib/mission/agents/inflow_agent.py` |
| `CsvReaderAgent` | CSV数据读取器，通用的CSV文件解析代理。 | `core_lib/disturbances/csv_reader_agent.py` |
| `OntologySimulationAgent` | 物理仿真本体，驱动物理模型进行仿真计算。 | `core_lib/local_agents/ontology_simulation_agent.py` |


## 4. 建议新增的智能体
为了使平台功能更完善、架构更清晰，建议基于现有原则新增以下智能体：

### 4.1 水系统被控对象代理
| 建议新增智能体 | 设计目的与职责 | 与现有架构的关联 |
| :--- | :--- | :--- |
| `RiverChannelPerceptionAgent` | 专注于不规则断面河道的感知，处理更复杂的河道水力学模型。 | 对应 `core_lib/physical_objects/river_channel.py` 物理模型，是 `ChannelPerceptionAgent` 在复杂场景下的特化与补充。 |
| `GatePerceptionAgent`<br>`PumpPerceptionAgent`<br>`ValvePerceptionAgent` | 针对单个闸门、水泵、阀门的感知，实现更细粒度的数字孪生和故障诊断。 | 将站级感知（如 `PumpStationPerceptionAgent`）细化到机组级，为精细化控制和运维提供数据基础。 |

### 4.2 水系统控制对象代理
| 建议新增智能体 | 设计目的与职责 | 与现有架构的关联 |
| :--- | :--- | :--- |
| `GateControlAgent`<br>`ValveControlAgent` | 负责单个闸门或阀门的独立控制，接收开度、流量等指令并执行。 | 与已有的 `PumpControlAgent` 形成对等，完善了机组级控制层，使站级控制代理（如 `ValveStationControlAgent`）可作为协调者，实现更清晰的分层控制。 |

### 4.3 中央协调代理
| 建议新增智能体 | 设计目的与职责 | 与现有架构的关联 |
| :--- | :--- | :--- |
| `CentralAnomalyDetectionAgent` | 订阅所有本地感知状态，利用全局算法（如图论、机器学习）识别跨区域的复杂异常模式。 | 提供比单个 `EmergencyAgent` 更全面的预警能力，是系统安全保障的高级补充。 |
| `DemandForecastingAgent` | 预测整个水系统的用水需求，为中央调度提供前瞻性的决策依据。 | 与专注于“来水”预测的 `InflowForecasterAgent` 形成互补，共同构成水量平衡预测的关键部分。 |

### 4.4 任务与模拟支持智能体
| 建议新增智能体 | 设计目的与职责 | 与现有架构的关联 |
| :--- | :--- | :--- |
| `ModelUpdaterAgent` | 订阅 `IdentificationAgent` 的输出，自动将新参数更新到相应的数字孪生模型中。 | 填补了“参数辨识”与“模型应用”之间的逻辑闭环，实现模型的在线自适应校准。 |
| `ScenarioAgent` | 根据预设脚本，在特定时间协调并触发各种扰动（如洪水、故障），用于自动化测试和应急演练。 | 作为 `RainfallAgent`、`WaterUseAgent` 等独立扰动智能体的更高层封装和协调器，提升了系统的测试和演练能力。 |
