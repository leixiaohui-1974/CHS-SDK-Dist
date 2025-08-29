import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.central_coordination.dispatch.central_mpc_agent import CentralMPCAgent

def run_central_dispatcher_example():
    """
    Demonstrates the CentralMPCAgent in an isolated environment.
    It receives a prediction and a current state, and outputs a new
    optimized PID setpoint.
    """
    print("--- 示例 1.5: 中心MPC调度智能体 ---")
    print("--- 演示 CentralDispatcher 如何根据预测信息输出高层调度指令 ---")

    # 1. 初始化 MessageBus
    bus = MessageBus()

    # 2. 为 CentralMPCAgent 定义配置
    # Note: The agent is designed for a 2-canal system. We will configure it
    # as such, but only interact with the first canal's topics for this example.
    HORIZON = 10
    STATE_TOPIC_UPSTREAM = "state/canal_upstream/level"
    STATE_TOPIC_DOWNSTREAM = "state/canal_downstream/level"
    FORECAST_TOPIC = "forecast/inflow"
    COMMAND_TOPIC_UPSTREAM = "command/gate_upstream/setpoint"
    COMMAND_TOPIC_DOWNSTREAM = "command/gate_downstream/setpoint"

    mpc_config = {
        "prediction_horizon": HORIZON,
        "dt": 3600,  # Time step in seconds (e.g., 1 hour)
        "q_weight": 1.0,  # Penalty on deviation from target setpoint
        "r_weight": 0.5,  # Penalty on setpoint changes
        "state_keys": ['upstream', 'downstream'],
        "state_subscriptions": {
            'upstream': STATE_TOPIC_UPSTREAM,
            'downstream': STATE_TOPIC_DOWNSTREAM,
        },
        "forecast_subscription": FORECAST_TOPIC,
        "command_topics": {
            'upstream_cmd': COMMAND_TOPIC_UPSTREAM,
            'downstream_cmd': COMMAND_TOPIC_DOWNSTREAM,
        },
        "normal_setpoints": [10.0, 8.0],  # Normal target level for upstream and downstream
        "emergency_setpoint": 8.5,     # Emergency target level (lower to create buffer)
        "flood_thresholds": [12.0, 10.0],
        "canal_surface_areas": [1.5e6, 1.5e6], # m^2
        "outflow_coefficient": 1000 # Simplified model parameter
    }

    # 3. 创建 CentralMPCAgent 实例
    dispatcher = CentralMPCAgent(
        agent_id="central_dispatcher_1",
        message_bus=bus,
        config=mpc_config
    )

    # 4. 创建监听器以捕获输出
    received_commands = []
    def command_listener(message):
        print(f"<<< MPC调度器响应: 收到新设定点指令 -> {message}")
        received_commands.append(message)
    bus.subscribe(COMMAND_TOPIC_UPSTREAM, command_listener)


    # 5. 模拟并验证
    print("\n--- 开始验证 ---")

    # a. 手动发布一个初始状态
    print(">>> 发布初始状态: 上游水位 = 10.1m")
    bus.publish(STATE_TOPIC_UPSTREAM, {'water_level': 10.1})
    bus.publish(STATE_TOPIC_DOWNSTREAM, {'water_level': 8.0}) # Provide state for both

    # b. 手动发布一个未来的入流预测 (e.g., a flood wave is coming)
    #    A forecast > 0 will trigger the emergency setpoint logic.
    forecast = [50.0] * HORIZON
    print(f">>> 发布洪水预警: 未来 {HORIZON} 小时有持续大流量入流")
    bus.publish(FORECAST_TOPIC, {'inflow_forecast': forecast})

    # c. 调用 dispatcher 的 run() 方法
    print(">>> 运行MPC调度器...")
    dispatcher.run(current_time=0)
    time.sleep(0.1)

    # 6. 验证调度器是否发布了正确的指令
    assert len(received_commands) == 1, "调度器应发布一个新指令"
    new_setpoint = received_commands[0]['new_setpoint']

    print(f"\n--- 结果验证 ---")
    print(f"正常设定点: {mpc_config['normal_setpoints'][0]}m")
    print(f"紧急设定点: {mpc_config['emergency_setpoint']}m")
    print(f"MPC计算出的新设定点: {new_setpoint:.3f}m")

    # Because a flood is predicted, the MPC should lower the setpoint
    # from the normal value to create a buffer. It should be close to the
    # emergency setpoint, but optimized.
    assert new_setpoint < mpc_config['normal_setpoints'][0], "面对洪水预警, 新设定点应低于正常值"
    assert new_setpoint > 5.0, "新设定点应在合理范围内" # Sanity check

    print("\n验证成功: CentralMPCAgent 在收到洪水预警后，向本地控制器发布了一个更低的、经过优化的新设定点。")


if __name__ == "__main__":
    # The scipy library is required for the MPC controller
    try:
        import scipy
    except ImportError:
        print("\n错误: 本示例需要 'scipy' 库。")
        print("请运行: pip install scipy\n")
        sys.exit(1)

    run_central_dispatcher_example()
