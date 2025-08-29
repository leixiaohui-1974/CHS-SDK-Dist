import sys
import os
import numpy as np

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.canal import Canal
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

def run_digital_twin_agent_example():
    """
    Demonstrates a DigitalTwinAgent performing a cognitive function:
    smoothing noisy data using an Exponential Moving Average (EMA) filter.
    """
    print("--- 示例 1.4: 数字孪生智能体（高级功能） ---")
    print("--- 演示 DigitalTwinAgent 如何对收到的数据进行平滑处理 ---")

    # 1. 初始化 MessageBus 和一个基础物理模型
    bus = MessageBus()
    canal_params = {'bottom_width': 20.0, 'length': 1000.0, 'slope': 0.001, 'side_slope_z': 2.0, 'manning_n': 0.025}
    # The agent only needs the model for its get_state method, so initial state can be simple.
    upstream_canal = Canal(name="upstream_canal", initial_state={'water_level': 10.0}, parameters=canal_params)

    # 2. 创建并配置 DigitalTwinAgent，启用平滑功能
    SMOOTHED_STATE_TOPIC = "state/canal/level/smoothed"

    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_1",
        simulated_object=upstream_canal,
        message_bus=bus,
        state_topic=SMOOTHED_STATE_TOPIC,
        smoothing_config={
            'water_level': 0.3  # Alpha for EMA filter. Lower alpha = more smoothing.
        }
    )

    # 3. 创建一个监听器来捕获 agent 的输出
    received_messages = []
    def message_listener(message):
        received_messages.append(message)
    bus.subscribe(SMOOTHED_STATE_TOPIC, message_listener)

    # 4. 仿真循环，并手动注入带噪声的数据
    print("\n--- 开始仿真 ---")
    print("手动向渠池模型注入带噪声的水位，并观察数字孪生体发布的平滑后状态。")

    raw_data_history = []
    true_level = 10.0
    noise_std = 0.5 # Use significant noise to make smoothing obvious

    for i in range(30):
        # a. 生成并注入带噪声的数据
        noisy_level = true_level + np.random.normal(0, noise_std)
        raw_data_history.append(noisy_level)
        upstream_canal.set_state({'water_level': noisy_level})

        # b. 运行 agent
        twin_agent.run(current_time=i)

        smoothed_level = received_messages[-1]['water_level']
        print(f"Step {i+1:2d} | Raw Level: {noisy_level:6.3f}m | Smoothed Level: {smoothed_level:6.3f}m")

    print("\n仿真结束。")

    # 5. 验证结果
    print("\n--- 结果验证 ---")
    # A simple way to verify smoothing is to check if the variance of the
    # smoothed data is lower than the variance of the raw data.
    raw_variance = np.var(raw_data_history)
    smoothed_data = [msg['water_level'] for msg in received_messages]
    smoothed_variance = np.var(smoothed_data)

    print(f"原始数据方差: {raw_variance:.4f}")
    print(f"平滑后数据方差: {smoothed_variance:.4f}")

    assert smoothed_variance < raw_variance, "平滑后数据的方差应小于原始数据"
    print("\n验证成功: DigitalTwinAgent 成功地对数据进行了平滑处理。")

if __name__ == "__main__":
    run_digital_twin_agent_example()
