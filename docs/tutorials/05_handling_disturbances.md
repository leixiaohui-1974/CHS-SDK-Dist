# 教程 5: 处理扰动

在现实世界的水系统中，完美的稳定是一种幻觉。系统不断受到外部因素或“扰动”的影响。一个强大的控制系统必须能够对这些事件做出反应，以维持其期望的状态。

本教程演示了我们的多代理系统如何能够对这类扰动具有弹性。我们将引入一个 `RainfallAgent` (降雨代理)，它会向我们的水库注入一股突然的大量来水，我们将观察分层控制系统如何运作以减轻其影响。

## 关键概念

### 1. 扰动代理

扰动仅仅是影响物理组件状态的事件，其源于正常的控制回路之外。我们可以使用专门的代理来模拟这些事件。在我们的案例中，我们创建了 `RainfallAgent`。

- **基于时间的触发器**: 该代理被配置为在仿真中的特定时间 (`start_time`) 激活，并持续一定的 `duration` (时长)。
- **发布扰动**: 当激活时，它会在一个特定的“扰动主题” (例如, `disturbance.rainfall.inflow`) 上发布一条消息，其中包含一个有效载荷 (例如, `{'inflow': 150}`)。

### 2. 能感知消息的物理模型

为了使扰动产生效果，物理模型必须能够接收和处理它。我们通过使 `Reservoir` (水库) 模型“能感知消息”来实现这一点。

- **订阅扰动**: `Reservoir` 现在用一个它应该订阅的 `disturbance_topics` (扰动主题) 列表进行初始化。
- **内部状态更新**: 当在这些主题之一上收到消息时，水库的内部 `handle_message` 方法被调用，该方法根据消息的有效载荷更新其入流量。这直接影响其在下一个仿真步骤中的物理状态。

### 3. 系统弹性

这个例子展示了分层控制架构的全部威力：
- **本地控制代理 (Local Control Agent)** 作为第一道防线，立即对由扰动引起的与设定点的微小偏差做出反应。
- **中央调度器 (Central Dispatcher)** 监控整个系统的状态。如果扰动足够大，以至于将系统推向危险状态 (例如，超过 `flood_threshold` (洪水阈值))，调度器可以通过向本地代理发布一个新的、更安全的设定点来进行干预。

## 示例: `example_with_disturbance.py`

该脚本直接建立在分层控制示例的基础上。

[include-code: example_with_disturbance.py]

### 设置

1.  **`RainfallAgent`**: 我们创建一个 `RainfallAgent` 的实例，配置它在 `t=300s` 时开始一场持续 `200s` 的强降雨事件。
    ```python
    rainfall_config = {
        "topic": RAINFALL_TOPIC,
        "start_time": 300,
        "duration": 200,
        "inflow_rate": 150 # 一个显著的入流量
    }
    rainfall_agent = RainfallAgent("rainfall_agent_1", message_bus, rainfall_config)
    ```
2.  **能感知消息的水库**: 我们用 `disturbance_topics` 参数实例化 `Reservoir`，告诉它监听 `RAINFALL_TOPIC` 上的消息。
    ```python
    reservoir = Reservoir(
        # ...
        message_bus=message_bus,
        disturbance_topics=[RAINFALL_TOPIC]
    )
    ```
3.  **调度器规则**: `CentralDispatcher` 被配置了一个 `flood_threshold` 为 13.0米。如果水位超过此值，它将发布一个紧急的 `flood_setpoint` (洪水设定点) 为 11.0米。
    ```python
    dispatcher_rules = {
        'flood_threshold': 13.0,
        'normal_setpoint': 12.0,
        'flood_setpoint': 11.0
    }
    ```

### 运行仿真

当您运行该脚本时，您将观察到以下行为：

1.  **初始稳定**: 在前300秒，系统是稳定的。`LocalControlAgent` 将水库水位稳定地保持在 `normal_setpoint` 12.0米。
2.  **扰动事件**: 在 `t=300s`，`RainfallAgent` 激活并开始发布入流消息。
    ```
    --- Rainfall event STARTED at t=300.0s ---
    ```
3.  **系统反应**: 由于新的入流，水库的水量和水位开始上升。`LocalControlAgent` 的PID控制器立即检测到这个误差（上升的水位与12.0米设定点之间的差异），并开始开启闸门以释放更多的水。
4.  **成功缓解**: 在这个场景中，扰动是显著的但并非灾难性的。PID控制器通过开启闸门有效地抵消了降雨，防止水位达到13.0米的 `flood_threshold`。`CentralDispatcher` 看到了水位上升，但由于阈值从未被突破，它继续命令 `normal_setpoint`。
    ```
    [central_dispatcher_1] Reservoir level is 12.02m. Commanding setpoint: 12.00m
    ```
5.  **恢复**: 在 `t=500s`，降雨事件结束。`LocalControlAgent` 仍然试图达到12.0米的设定点，但现在它的闸门开得太大了。水位开始下降。PID控制器通过逐渐关闭闸门来纠正这个“超调”，直到系统在原来的12.0米设定点重新稳定下来。

这个例子展示了MAS和分层控制结构的鲁棒性和智能性。系统自动处理了一个重大的外部事件，而无需高层干预，证明了本地控制器的有效性。它也表明，如果情况变得更加严重，中央调度器已经准备好接管指挥的框架已经就位。
