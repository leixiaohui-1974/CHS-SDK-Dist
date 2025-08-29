import sys
import os
import numpy as np

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.canal import Canal
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.disturbances.rainfall_agent import RainfallAgent

def run_local_closed_loop_example():
    """
    Demonstrates a complete local closed-loop control system.
    - A PhysicalIOAgent reads the canal's water level.
    - A LocalControlAgent receives the level and computes a PID action.
    - The PhysicalIOAgent receives the action and actuates the gate.
    - The SimulationHarness manages the physical interactions.
    """
    print("--- 示例 2.1: 现地闭环控制 ---")
    print("--- 验证一个由现地PID智能体独立工作的完整闭环控制系统 ---")

    # 1. 设置仿真
    harness = SimulationHarness(config={'duration': 2000, 'dt': 10.0})
    bus = harness.message_bus

    # 2. 定义消息主题
    UPSTREAM_LEVEL_TOPIC = "state/canal_upstream/level"
    GATE_ACTION_TOPIC = "action/gate/opening"

    # 3. 创建物理组件
    canal_params = {'bottom_width': 20.0, 'length': 1000.0, 'slope': 0.001, 'side_slope_z': 2.0, 'manning_n': 0.025}
    INFLOW_TOPIC = "disturbance/inflow"

    # Start the system at the desired setpoint volume for better stability check
    pid_setpoint = 4.0 # Target water level in meters
    initial_volume = 112100.0 # Volume corresponding to ~4.0m level

    upstream_canal = Canal(
        name="upstream_canal",
        initial_state={'volume': initial_volume},
        parameters=canal_params,
        message_bus=bus,
        inflow_topic=INFLOW_TOPIC
    )
    downstream_canal = Canal(
        name="downstream_canal",
        initial_state={'volume': 50000},
        parameters=canal_params
    )

    gate_params = {'discharge_coefficient': 0.8, 'width': 10.0, 'max_opening': 3.0, 'max_rate_of_change': 0.05}
    control_gate = Gate(
        name="control_gate",
        # Start with an opening that roughly balances the inflow at the setpoint
        initial_state={'opening': 0.38},
        parameters=gate_params
    )

    harness.add_component(upstream_canal)
    harness.add_component(control_gate)
    harness.add_component(downstream_canal)
    harness.add_connection("upstream_canal", "control_gate")
    harness.add_connection("control_gate", "downstream_canal")

    # 4. 创建智能体
    # a. PID 控制器 - Tuned for better stability
    pid_controller = PIDController(
        Kp=-0.8, Ki=-0.002, Kd=0.0, # Tuned gains for upstream level control
        setpoint=pid_setpoint,
        min_output=0.0, max_output=gate_params['max_opening']
    )

    # b. 本地控制智能体
    control_agent = LocalControlAgent(
        agent_id="pid_agent_1",
        controller=pid_controller,
        message_bus=bus,
        observation_topic=UPSTREAM_LEVEL_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=harness.dt
    )

    # c. 物理IO智能体
    io_agent = PhysicalIOAgent(
        agent_id="io_agent_1",
        message_bus=bus,
        sensors_config={
            'canal_level_sensor': {
                'obj': upstream_canal,
                'state_key': 'water_level',
                'topic': UPSTREAM_LEVEL_TOPIC,
                'noise_std': 0.01
            }
        },
        actuators_config={
            'gate_actuator': {
                'obj': control_gate,
                'target_attr': 'target_opening',
                'topic': GATE_ACTION_TOPIC,
                'control_key': 'control_signal'
            }
        }
    )

    harness.add_agent(control_agent)
    harness.add_agent(io_agent)

    # d. 扰动智能体 (模拟恒定入流)
    inflow_disturbance_agent = RainfallAgent(
        agent_id="inflow_disturbance_1",
        message_bus=bus,
        config={
            "topic": INFLOW_TOPIC,
            "start_time": 0,
            "duration": harness.duration, # Last for the whole simulation
            "inflow_rate": 15.0
        }
    )
    harness.add_agent(inflow_disturbance_agent)

    # 5. 运行仿真
    harness.build()
    harness.run_mas_simulation()

    # 6. 验证结果
    print("\n--- 结果验证 ---")
    final_state = harness.history[-1]['upstream_canal']
    final_level = final_state['water_level']

    print(f"PID 设定点: {pid_setpoint:.3f} m")
    print(f"最终实际水位: {final_level:.3f} m")

    # The final level should be very close to the setpoint
    assert abs(final_level - pid_setpoint) < 0.1, "系统未能将水位稳定在设定点附近"
    print("\n验证成功: 系统成功地将上游水位稳定在PID设定点附近。")

if __name__ == "__main__":
    run_local_closed_loop_example()
