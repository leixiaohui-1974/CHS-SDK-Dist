import math
import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core_lib.physical_objects.canal import Canal
from core_lib.physical_objects.gate import Gate
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent

# Define parameters in a scope accessible by both the function and the main block
canal_params = {'bottom_width': 20.0, 'length': 1000.0, 'slope': 0.001, 'side_slope_z': 2.0, 'manning_n': 0.025}

def run_physical_io_agent_example(upstream_canal, control_gate, bus):
    """
    Demonstrates an independent PhysicalIOAgent simulating sensor perception
    and actuator physical actions.
    """
    print("--- 示例 1.2: 传感器与执行器仿真智能体 ---")
    print("--- 演示 PhysicalIOAgent 如何模拟传感器的感知和执行器的物理动作 ---")

    # 2. 创建并配置 PhysicalIOAgent
    STATE_TOPIC = "state/canal/level"
    ACTION_TOPIC = "action/gate/opening"

    io_agent = PhysicalIOAgent(
        agent_id="io_agent_1",
        message_bus=bus,
        sensors_config={
            'canal_level_sensor': {
                'obj': upstream_canal,
                'state_key': 'water_level',
                'topic': STATE_TOPIC,
                'noise_std': 0.02  # Standard deviation of sensor noise in meters
            }
        },
        actuators_config={
            'gate_actuator': {
                'obj': control_gate,
                'target_attr': 'target_opening', # The agent will set this attribute on the gate
                'topic': ACTION_TOPIC,
                'control_key': 'target_opening'
            }
        }
    )

    # 3. 创建一个简单的指令发送函数和消息监听器
    def send_command(target_opening: float):
        print(f"\n>>> 发送指令: 设置闸门目标开度为 {target_opening}m.")
        bus.publish(ACTION_TOPIC, {'target_opening': target_opening})

    received_messages = []
    def message_listener(message):
        received_messages.append(message)
    bus.subscribe(STATE_TOPIC, message_listener)

    # 4. 仿真循环
    dt = 1.0
    duration = 50
    num_steps = int(duration / dt)

    print(f"\n开始仿真... 时长: {duration}s, 步长: {dt}s")

    for i in range(num_steps):
        current_time = i * dt

        # 在 t=5s 时发送一个新指令
        if i == 5:
            send_command(target_opening=0.5)

        # a. 运行 agent (触发 agent 的 sensing)
        #    Sensing is done on a clock tick.
        io_agent.run(current_time)

        # Note: Acting (receiving commands) happens asynchronously whenever
        # a message is published to the action topic. We triggered this
        # with send_command() at t=5s.

        # c. 手动推进物理模型 (与示例1.1类似)
        #    注意：这里我们简化了物理过程，重点是验证IO Agent的行为
        canal_state = upstream_canal.get_state()
        canal_water_level = canal_state['water_level']

        # Gate's step method will now use the 'target_opening' set by the IO agent
        gate_action = {'upstream_head': canal_water_level, 'downstream_head': 0}
        gate_state = control_gate.step(gate_action, dt)

        # 在这个简化的例子中，我们不更新渠池状态，因为重点是IO

        print(f"Time: {current_time:2.0f}s | "
              f"Gate Opening (True): {gate_state['opening']:.3f}m | "
              f"Gate Target: {control_gate.target_opening:.3f}m")

        # 暂停一小段时间以模拟实时性
        time.sleep(0.05)

    print("\n仿真结束。")

    # 5. 验证结果
    print("\n--- 结果验证 ---")

    # 验证1: 传感器是否发布了带噪声的数据?
    assert len(received_messages) == num_steps, f"应收到 {num_steps} 条状态消息, 但收到了 {len(received_messages)}"
    true_level_final = upstream_canal.get_state()['water_level']
    sensed_level_final = received_messages[-1]['water_level']
    # A non-zero noise standard deviation should result in a different value,
    # but there's a tiny chance the noise is exactly zero. A better check is
    # to see if the standard deviation of the error is close to the configured noise.
    # For this test, we'll just check they are not exactly equal.
    if io_agent.sensors['canal_level_sensor']['noise_std'] > 0:
        assert true_level_final != sensed_level_final, "传感器读数应与真值有差异（因为有噪声）"
    print(f"验证成功: PhysicalIOAgent 发布了 {len(received_messages)} 条带噪声的状态消息。")
    print(f"  - 最终真实水位: {true_level_final:.4f}m")
    print(f"  - 最终感知水位: {sensed_level_final:.4f}m")

    # 验证2: 执行器是否正确执行了指令?
    final_opening = control_gate.get_state()['opening']
    # 初始开度0.2, t=5s时目标变为0.5, 速率0.05m/s, 需要(0.5-0.2)/0.05 = 6s
    # 所以在t=11s时应达到目标。仿真时长50s，肯定能达到。
    assert abs(final_opening - 0.5) < 1e-9, f"最终开度应为 0.5m, 但为 {final_opening:.3f}m"
    print(f"验证成功: PhysicalIOAgent 成功接收指令并将闸门开度驱动至目标值 {final_opening:.3f}m。")

# This helper is needed to correctly initialize the canal's water level from its volume.
def _recalculate_level_from_volume(canal: Canal) -> float:
    L = canal.length
    b = canal.bottom_width
    z = canal.side_slope_z
    volume = canal.get_state()['volume']

    c_quad = -volume / L if L > 0 else 0

    if z == 0: # Rectangular channel
        return volume / (b * L) if (b * L) > 0 else 0
    else: # Trapezoidal channel
        discriminant = b**2 - 4 * z * c_quad
        if discriminant >= 0:
            return (-b + math.sqrt(discriminant)) / (2 * z)
        return 0

if __name__ == "__main__":
    # 1. Initialize all components in the main block
    bus = MessageBus()

    gate_params = {'discharge_coefficient': 0.8, 'width': 10.0, 'max_opening': 3.0, 'max_rate_of_change': 0.05}
    control_gate = Gate(name="control_gate", initial_state={'opening': 0.2}, parameters=gate_params)

    initial_volume = 100000
    initial_state = {'volume': initial_volume, 'outflow': 0}
    temp_canal_for_init = Canal(name="temp", initial_state=initial_state, parameters=canal_params)
    initial_level = _recalculate_level_from_volume(temp_canal_for_init)
    initial_state['water_level'] = initial_level
    upstream_canal = Canal(name="upstream_canal", initial_state=initial_state, parameters=canal_params)

    # 2. Pass them to the simulation function
    run_physical_io_agent_example(upstream_canal, control_gate, bus)
