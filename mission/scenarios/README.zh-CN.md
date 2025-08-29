# 数据驱动的仿真场景

该目录包含由 YAML 配置文件定义的独立仿真场景。这种数据驱动的方法允许在不更改核心仿真代码的情况下，快速开发和测试不同的系统配置。

## 运行场景

每个场景都可以使用位于项目根目录的通用 `run_scenario.py` 脚本来执行。您必须将要运行的特定场景目录的路径作为命令行参数传递。

例如，要运行 `yinchuojiliao` 场景，请从项目的根目录执行以下命令：

```bash
python run_scenario.py mission/scenarios/yinchuojiliao
```

仿真完成后，输出数据将作为 `output.yml` 保存在相应的场景目录中。

## 场景目录结构

每个场景必须是一个包含以下四个 YAML 文件的目录：

- `config.yml`：定义全局仿真参数。
- `components.yml`：定义所有物理组件（例如，水库、管道）。
- `topology.yml`：定义物理组件之间的连接。
- `agents.yml`：定义所有软件代理和控制器。
- `data/`（可选）：一个用于存放任何补充数据文件的目录，例如用于入流数据的 CSV 文件。

### `config.yml`

该文件指定仿真运行的总体设置。

**结构：**
```yaml
simulation:
  duration: 168  # 仿真的总持续时间（小时）
  dt: 1.0      # 每次迭代的时间步长（小时）
```

### `components.yml`

该文件定义了仿真中的每个物理对象。

**结构：**
```yaml
components:
  - id: my_component_id          # 组件的唯一标识符
    class: Reservoir             # 组件模型的 Python 类名
    initial_state:               # 组件的初始状态
      water_level: 350.0
      # ... 其他状态变量
    parameters:                  # 组件的固定物理参数
      surface_area: 5.0e+7
      # ... 其他参数
```

### `topology.yml`

该文件定义了物理组件如何以有向图的形式相互连接。

**结构：**
```yaml
connections:
  - upstream: component_id_1     # 上游组件的 ID
    downstream: component_id_2   # 下游组件的 ID
  # ... 更多连接
```

### `agents.yml`

该文件定义了系统的所有“大脑”：代理和简单的控制器。

**结构：**
该文件有两个主键：`controllers` 和 `agents`。

- **`controllers`**：用于由仿真平台直接连接的简单控制器（如 PID）。
  ```yaml
  controllers:
    - id: my_pid_controller
      class: PIDController
      controlled_id: gate_to_control   # 要控制的组件的 ID
      observed_id: reservoir_to_watch  # 要观察的组件的 ID
      observation_key: water_level     # 用作输入的状态变量
      config:                          # 控制器构造函数的参数
        Kp: -0.1
        Ki: -0.01
        # ... 其他 PID 参数
  ```

- **`agents`**：用于参与主代理式仿真循环的更复杂的代理。
  ```yaml
  agents:
    - id: my_digital_twin
      class: DigitalTwinAgent
      config:
        simulated_object_id: component_to_twin # 该代理作为其孪生体的组件的 ID
        state_topic: "state/my_topic"          # 用于发布状态的消息总线主题

    - id: my_csv_reader
      class: CsvInflowAgent
      config:
        target_component_id: reservoir_to_fill # 接收入流的组件
        csv_file: data/inflow_data.csv         # 数据文件的路径，相对于场景目录
        time_column: time_hr
        data_column: inflow_m3s
  ```
每个代理的 `config` 块包含其构造函数所需的特定参数。YAML 加载器会根据其 `class` 动态构建代理。
