import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# All necessary imports
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.canal import Canal
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_coordination.dispatch.central_mpc_agent import CentralMPCAgent
from core_lib.disturbances.rainfall_agent import RainfallAgent
from core_lib.disturbances.water_use_agent import WaterUseAgent

# A helper agent to provide forecasts to the MPC
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import Message

class InflowForecasterAgent(Agent):
    def __init__(self, agent_id, bus, topic, forecast_data):
        super().__init__(agent_id)
        self.bus = bus
        self.topic = topic
        self.forecast_data = forecast_data
    def run(self, current_time):
        # In a real system, this would run a forecasting model. Here, we just publish static data.
        if current_time == 0: # Publish once at the beginning
            print(f"--- InflowForecaster '{self.agent_id}' is publishing a forecast. ---")
            self.bus.publish(self.topic, {'inflow_forecast': self.forecast_data})

def run_hierarchical_control_example():
    """
    The final, complete example demonstrating a hierarchical, multi-agent
    control system responding to forecasted and un-forecasted disturbances.
    """
    print("--- 示例 2.2: 分层分布式控制与复杂扰动应对 ---")

    # 1. 设置仿真
    SIM_DURATION = 3600 * 12 # 12 hours
    DT = 3600 # 1 hour
    harness = SimulationHarness(config={'duration': SIM_DURATION, 'dt': DT})
    bus = harness.message_bus

    # 2. 定义消息主题
    # Sensor/State Topics
    RAW_UPSTREAM_LEVEL_TOPIC = "state/canal_upstream/level/raw"
    SMOOTHED_UPSTREAM_LEVEL_TOPIC = "state/canal_upstream/level/smoothed"
    RAW_DOWNSTREAM_LEVEL_TOPIC = "state/canal_downstream/level/raw" # Topic for downstream state

    # Disturbance Topics
    INFLOW_DISTURBANCE_TOPIC = "disturbance/inflow/upstream"
    WATER_USE_TOPIC = "disturbance/outflow/downstream" # Not used by WaterUseAgent, but good practice

    # Forecast Topic
    INFLOW_FORECAST_TOPIC = "forecast/inflow/upstream"

    # Command & Action Topics
    MPC_COMMAND_TOPIC = "command/pid/setpoint"
    PID_ACTION_TOPIC = "action/gate/opening"

    # 3. 创建物理组件
    canal_params = {'bottom_width': 20.0, 'length': 5000.0, 'slope': 0.0001, 'side_slope_z': 2.0, 'manning_n': 0.03}

    # Properly initialize water level from volume before starting
    import math
    def _recalculate_level_from_volume(volume, params):
        L, b, z = params['length'], params['bottom_width'], params['side_slope_z']
        c_quad = -volume / L if L > 0 else 0
        if z == 0: return volume / (b * L) if (b * L) > 0 else 0
        discriminant = b**2 - 4 * z * c_quad
        return (-b + math.sqrt(discriminant)) / (2 * z) if discriminant >= 0 else 0

    # To test pre-emptive draining, the initial level MUST be higher than the emergency setpoint.
    initial_upstream_volume = 652500 # This corresponds to ~4.5m
    initial_upstream_level = _recalculate_level_from_volume(initial_upstream_volume, canal_params)

    upstream_canal = Canal(name="upstream_canal", initial_state={'volume': initial_upstream_volume, 'water_level': initial_upstream_level}, parameters=canal_params, message_bus=bus, inflow_topic=INFLOW_DISTURBANCE_TOPIC)
    downstream_canal = Canal(name="downstream_canal", initial_state={'volume': 400000}, parameters=canal_params)

    gate_params = {'discharge_coefficient': 0.7, 'width': 15.0, 'max_opening': 5.0, 'max_rate_of_change': 0.5}
    control_gate = Gate(name="control_gate", initial_state={'opening': 0.3}, parameters=gate_params)

    harness.add_component(upstream_canal)
    harness.add_component(control_gate)
    harness.add_component(downstream_canal)
    harness.add_connection("upstream_canal", "control_gate")
    harness.add_connection("control_gate", "downstream_canal")

    # 4. 创建智能体

    # a. 扰动智能体
    # Baseline flow agent
    baseline_inflow = 20 # m3/s
    base_flow_agent = RainfallAgent("base_flow_1", bus, {"topic": INFLOW_DISTURBANCE_TOPIC, "start_time": 0, "duration": SIM_DURATION, "inflow_rate": baseline_inflow})

    # Forecasted rainfall event (starts after 5 hours)
    rainfall_inflow = 100 # m3/s
    rainfall_agent = RainfallAgent("rainfall_1", bus, {"topic": INFLOW_DISTURBANCE_TOPIC, "start_time": 3600*5, "duration": 3600*7, "inflow_rate": rainfall_inflow})

    # Un-forecasted water use (starts after 6 hours)
    water_use_agent = WaterUseAgent("water_user_1", downstream_canal, start_time=3600*6, duration=3600*4, diversion_rate=40, dt=DT)

    # b. 预测智能体 - Forecast must include the baseline flow
    total_forecast_data = [baseline_inflow]*5 + [baseline_inflow + rainfall_inflow]*7
    forecaster = InflowForecasterAgent("forecaster_1", bus, INFLOW_FORECAST_TOPIC, total_forecast_data)

    # c. 感知与执行智能体 (IO Layer)
    io_agent = PhysicalIOAgent("io_agent_1", bus,
        sensors_config={
            'upstream_sensor': {'obj': upstream_canal, 'state_key': 'water_level', 'topic': RAW_UPSTREAM_LEVEL_TOPIC, 'noise_std': 0.05},
            'downstream_sensor': {'obj': downstream_canal, 'state_key': 'water_level', 'topic': RAW_DOWNSTREAM_LEVEL_TOPIC, 'noise_std': 0.05}
        },
        actuators_config={'gate_actuator': {'obj': control_gate, 'target_attr': 'target_opening', 'topic': PID_ACTION_TOPIC, 'control_key': 'control_signal'}}
    )

    # d. 数字孪生智能体 (Cognitive Layer)
    twin_agent = DigitalTwinAgent("twin_agent_1", upstream_canal, bus, SMOOTHED_UPSTREAM_LEVEL_TOPIC, smoothing_config={'water_level': 0.4})

    # e. 本地PID控制智能体 (Local Control Layer)
    # The PID needs to react to the raw, real-time data, not the smoothed data.
    # The gains MUST be tuned for the large timestep (dt=3600).
    # The initial setpoint is the MPC's target, to start draining immediately.
    pid_controller = PIDController(Kp=-0.6, Ki=-0.00005, Kd=-0.1, setpoint=4.0, min_output=0.0, max_output=gate_params['max_opening'])
    pid_agent = LocalControlAgent("pid_agent_1", pid_controller, bus,
        observation_topic=RAW_UPSTREAM_LEVEL_TOPIC,
        observation_key='water_level',
        action_topic=PID_ACTION_TOPIC,
        dt=DT,
        command_topic=MPC_COMMAND_TOPIC
    )

    # f. 中央MPC调度智能体 (Supervisory Control Layer)
    mpc_config = {
        "prediction_horizon": 12, "dt": DT, "q_weight": 1.0, "r_weight": 0.8,
        "state_keys": ['upstream', 'downstream'],
        "state_subscriptions": {
            'upstream': RAW_UPSTREAM_LEVEL_TOPIC,
            'downstream': RAW_DOWNSTREAM_LEVEL_TOPIC,
        },
        "forecast_subscription": INFLOW_FORECAST_TOPIC,
        "command_topics": {
            'upstream_cmd': MPC_COMMAND_TOPIC,
            'downstream_cmd': 'dummy_topic', # Not used in this scenario
        },
        "normal_setpoints": [5.0, 5.0], "emergency_setpoint": 4.0, "flood_thresholds": [6.5, 6.0],
        "canal_surface_areas": [2e5, 2e5], "outflow_coefficient": 1500
    }

    mpc_agent = CentralMPCAgent("mpc_dispatcher_1", bus, mpc_config)

    # Add all agents to the harness
    harness.add_agent(base_flow_agent)
    harness.add_agent(rainfall_agent)
    harness.add_agent(water_use_agent)
    harness.add_agent(forecaster)
    harness.add_agent(io_agent)
    harness.add_agent(twin_agent)
    harness.add_agent(pid_agent)
    harness.add_agent(mpc_agent)

    # 5. 运行仿真
    harness.build()
    harness.run_mas_simulation()

    # 6. 验证结果
    print("\n--- 最终结果 ---")
    final_pid_setpoint = pid_controller.setpoint
    max_level_achieved = max(h['upstream_canal']['water_level'] for h in harness.history)

    print(f"仿真结束时，最终的PID设定点为: {final_pid_setpoint:.2f}m")
    print(f"整个仿真过程中，上游渠池达到的最高水位为: {max_level_achieved:.2f}m")

    assert max_level_achieved < mpc_config["flood_thresholds"][0], "系统未能防止洪水，水位超过了阈值"
    print("\n验证成功: 分层控制系统成功预见并应对了扰动，将水位保持在安全范围内。")

if __name__ == "__main__":
    run_hierarchical_control_example()
