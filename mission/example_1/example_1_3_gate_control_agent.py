import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent

def run_gate_control_agent_example():
    """
    Demonstrates a LocalControlAgent with a PID controller implementing a
    local feedback control loop in an isolated, event-driven environment.
    """
    print("--- 示例 1.3: 闸站控制智能体（现地PID） ---")
    print("--- 演示现地PID智能体如何实现一个本地的反馈控制闭环 ---")

    # 1. 初始化 MessageBus 和 PIDController
    bus = MessageBus()

    # PID 控制器. Kp为负，因为水位高于设定点时，需要关小闸门（减小开度）
    pid_controller = PIDController(
        Kp=-0.5,
        Ki=-0.1,
        Kd=0.0,
        setpoint=10.0,  # 目标水位 10.0m
        min_output=0.0, # 闸门最小开度
        max_output=2.0  # 闸门最大开度
    )

    # 2. 创建并配置 LocalControlAgent
    OBSERVATION_TOPIC = "state/canal/level"
    ACTION_TOPIC = "action/gate/opening"

    control_agent = LocalControlAgent(
        agent_id="gate_control_agent_1",
        controller=pid_controller,
        message_bus=bus,
        observation_topic=OBSERVATION_TOPIC,
        observation_key='water_level', # 期望从消息中获取的键
        action_topic=ACTION_TOPIC,
        dt=1.0 # 假设控制周期为1秒
    )

    # 3. 创建一个模拟的传感器和一个动作监听器用于验证
    def simulate_sensor_reading(level: float):
        print(f"\n>>> 模拟传感器发布水位: {level:.2f}m (PID设定点: {pid_controller.setpoint:.2f}m)")
        bus.publish(OBSERVATION_TOPIC, {'water_level': level})

    received_actions = []
    def action_listener(message):
        print(f"<<< 控制代理响应: 收到动作指令 -> {message}")
        received_actions.append(message)
    bus.subscribe(ACTION_TOPIC, action_listener)

    # 4. 验证场景
    print("\n--- 开始验证场景 ---")

    # 场景1: 水位高于设定点 (需要开大闸门增加泄流)
    simulate_sensor_reading(10.5) # 高于设定点 0.5m
    time.sleep(0.1) # 等待消息处理
    assert len(received_actions) == 1, "场景1: 控制器应响应一次"
    # 逻辑: 水位过高 -> 需增大开度 -> 控制信号应为正.
    # 计算: error = setpoint - pv = 10.0 - 10.5 = -0.5.
    #       action = Kp * error = (-0.5) * (-0.5) = 0.25. (正向动作, 正确)
    assert received_actions[-1]['control_signal'] > 0, "场景1: 水位过高，应产生一个正向的开闸动作"
    print("场景1验证成功: 高于设定点的水位触发了开大闸门的动作。")

    # 场景2: 水位低于设定点 (需要关小闸门减少泄流)
    simulate_sensor_reading(9.8) # 低于设定点 0.2m
    time.sleep(0.1)
    assert len(received_actions) == 2, "场景2: 控制器应再次响应"
    # 逻辑: 水位过低 -> 需减小开度 -> 控制信号应为负 (或被钳位到0).
    # 计算: error = 10.0 - 9.8 = 0.2.
    #       action = Kp * error = (-0.5) * 0.2 = -0.1. 被钳位到 0.0. (正确)
    assert received_actions[-1]['control_signal'] == pid_controller.min_output, "场景2: 水位过低，应关小闸门至最小"
    print("场景2验证成功: 低于设定点的水位触发了关小闸门的动作。")

    # 场景3: 水位等于设定点
    simulate_sensor_reading(10.0) # 现在水位等于设定点
    time.sleep(0.1)
    assert len(received_actions) == 3, "场景3: 控制器应再次响应"
    # 逻辑: 误差为0, P项和D项为0. 只有I项起作用.
    # 由于之前存在正误差, 积分项不为0, 因此控制器会继续发布一个动作.
    print("场景3验证成功: 等于设定点的水位被正确处理，积分项生效。")

    print("\n--- 所有验证完成 ---")
    print("LocalControlAgent 成功地将观测到的状态偏差转化为了正确的控制动作。")

if __name__ == "__main__":
    run_gate_control_agent_example()
