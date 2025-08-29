# -*- coding: utf-8 -*-

"""
Main simulation script for the Yin Chuo Ji Liao Water Transfer Project.

This script sets up and runs a multi-agent simulation for the entire water transfer
system, based on the hierarchical control architecture described in the project
documentation.
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt

# Physical Components
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.canal import Canal
from core_lib.physical_objects.pipe import Pipe
from core_lib.physical_objects.valve import Valve

# Core Simulation Infrastructure
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core.interfaces import Agent

# Agent Components
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
from mission.agents.emergency_agent import EmergencyAgent
from mission.agents.central_dispatcher_agent import CentralDispatcherAgent
from mission.agents.csv_inflow_agent import CsvInflowAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def run_simulation():
    """
    Initializes and runs the full project simulation.
    """
    logging.info("Initializing the Yin Chuo Ji Liao Project simulation...")

    # --- Core Infrastructure ---
    harness = SimulationHarness(config={'duration': 168, 'dt': 1.0}) # 1 week simulation
    message_bus = MessageBus()

    # --- 1. Define and Add Physical Components ---
    logging.info("Creating physical components...")
    components = [
        Reservoir(name="wendegen_reservoir", initial_state={'water_level': 350.0}, parameters={'surface_area': 5e7}),
        Gate(name="water_intake_gate", initial_state={'opening': 0.5}, parameters={'width': 15, 'discharge_coefficient': 0.6}),
        Canal(name="tunnel_1", initial_state={'water_level': 349.0, 'volume': 7e7}, parameters={'length': 70000, 'bottom_width': 20, 'slope': 0.0001, 'side_slope_z': 2, 'manning_n': 0.03}),
        Gate(name="taoriver_gate", initial_state={'opening': 0.6}, parameters={}),
        Canal(name="tunnel_2", initial_state={'water_level': 325.0, 'volume': 8e6}, parameters={'length': 8000, 'bottom_width': 20, 'slope': 0.0001, 'side_slope_z': 2, 'manning_n': 0.03}),
        Gate(name="guiliu_gate", initial_state={'opening': 0.6}, parameters={}),
        Canal(name="tunnel_3", initial_state={'water_level': 322.0, 'volume': 1e8}, parameters={'length': 100000, 'bottom_width': 20, 'slope': 0.0001, 'side_slope_z': 2, 'manning_n': 0.03}),
        Reservoir(name="connection_pool", initial_state={'water_level': 320.0}, parameters={'surface_area': 1e4}),
        Pipe(name="pipe_1", initial_state={'flow': 15.0, 'pressure': 0.8}, parameters={'length': 20000, 'diameter': 3.0, 'friction_factor': 0.015}),
        Valve(name="online_valve", initial_state={'setting': 0.7}, parameters={}),
        Pipe(name="pipe_2", initial_state={'flow': 15.0, 'pressure': 0.7}, parameters={'length': 80000, 'diameter': 3.0, 'friction_factor': 0.015}),
        Valve(name="terminal_valve", initial_state={'setting': 0.5}, parameters={}),
        Reservoir(name="terminal_pool", initial_state={'water_level': 212.0}, parameters={'surface_area': 1e5})
    ]
    for comp in components:
        harness.add_component(comp)
    comp_map = {c.name: c for c in components}

    # --- 2. Define and Add Agents ---
    agents = []
    logging.info("Creating agents...")

    # 2.1 Perception Layer
    for comp in components:
        agents.append(DigitalTwinAgent(f"twin_{comp.name}", comp, message_bus, f"state/{comp.name}"))

    # 2.2 Local Control Layer
    pid_taoriver = PIDController(Kp=-0.1, Ki=-0.01, Kd=-0.05, setpoint=324.20, min_output=0, max_output=1)
    harness.add_controller('taoriver_ctrl', pid_taoriver, 'taoriver_gate', 'tunnel_1', 'water_level')
    pid_guiliu = PIDController(Kp=-0.1, Ki=-0.01, Kd=-0.05, setpoint=320.38, min_output=0, max_output=1)
    harness.add_controller('guiliu_ctrl', pid_guiliu, 'guiliu_gate', 'tunnel_2', 'water_level')
    pid_online_valve = PIDController(Kp=0.2, Ki=0.02, Kd=0.1, setpoint=0.65, min_output=0, max_output=1)
    harness.add_controller('online_valve_ctrl', pid_online_valve, 'online_valve', 'pipe_2', 'pressure')
    pid_terminal_valve = PIDController(Kp=-0.05, Ki=-0.005, Kd=-0.02, setpoint=212.5, min_output=0, max_output=1)
    harness.add_controller('terminal_valve_ctrl', pid_terminal_valve, 'terminal_valve', 'terminal_pool', 'water_level')
    pid_intake_gate = PIDController(Kp=-0.1, Ki=-0.01, Kd=-0.05, setpoint=349.5, min_output=0, max_output=1)
    harness.add_controller('intake_gate_ctrl', pid_intake_gate, 'water_intake_gate', 'tunnel_1', 'water_level')

    # 2.3 Supervisory and Emergency Layer
    agents.append(EmergencyAgent('emergency_agent', message_bus, ['state/pipe_1', 'state/pipe_2'], 0.3, 'control/water_intake_gate'))
    dispatcher_config = {'low_level': 212.0, 'high_level': 213.0, 'low_setpoint': 349.8, 'high_setpoint': 349.2}
    agents.append(CentralDispatcherAgent('central_dispatcher', message_bus, 'state/terminal_pool', 'water_level', 'command/intake_gate_ctrl', dispatcher_config))
    def intake_setpoint_updater(message):
        pid_intake_gate.set_setpoint(message.get('new_setpoint', pid_intake_gate.setpoint))
    message_bus.subscribe('command/intake_gate_ctrl', intake_setpoint_updater)

    # 2.4 Data Input Layer
    agents.append(CsvInflowAgent('csv_inflow', comp_map['wendegen_reservoir'], 'data/historical_inflow.csv', 'time', 'inflow'))

    for agent in agents:
        harness.add_agent(agent)

    # --- 3. Define Physical Topology ---
    logging.info("Connecting physical components...")
    # (Connections are defined in the component list order for this linear system)
    for i in range(len(components) - 1):
        harness.add_connection(components[i].name, components[i+1].name)

    # --- 4. Build and Run Simulation ---
    logging.info("Building and running simulation...")
    harness.build()

    # Manually simulate a pipe burst to test emergency response
    def simulate_burst(current_time):
        if int(current_time) == 100:
            logging.warning(f"!!! Manually simulating pipe burst at time {current_time} !!!")
            comp_map['pipe_1'].pressure = 0.1

    # The MAS run method will call agent.run() which includes our custom burst simulation agent logic
    harness.add_agent(BurstAgent("burst_agent", comp_map))

    harness.run_mas_simulation()
    logging.info("Simulation complete.")

    # --- 5. Plotting and Verification ---
    # Process history from harness
    history = harness.history
    log_data = []
    for step_data in history:
        time = step_data['time']
        entry = {'time': time}
        for comp_name, state in step_data.items():
            if comp_name == 'time': continue
            for key, value in state.items():
                entry[f"{comp_name}_{key}"] = value
        # also log the pid setpoint
        entry['intake_pid_setpoint'] = pid_intake_gate.setpoint
        log_data.append(entry)
    log_df = pd.DataFrame(log_data)
    log_df.set_index('time', inplace=True)

    fig, axes = plt.subplots(4, 1, figsize=(15, 20), sharex=True)
    fig.suptitle('Yin Chuo Ji Liao Project Simulation Results', fontsize=16)
    axes[0].plot(log_df.index, log_df['wendegen_reservoir_water_level'], label='Wendegen Reservoir')
    axes[0].plot(log_df.index, log_df['tunnel_1_water_level'], label='Tunnel 1')
    axes[0].plot(log_df.index, log_df['terminal_pool_water_level'], label='Terminal Pool')
    axes[0].set_ylabel('Water Level (m)'); axes[0].legend(); axes[0].grid(True); axes[0].set_title('Water Levels')
    axes[1].plot(log_df.index, log_df['water_intake_gate_opening'], label='Intake Gate')
    axes[1].plot(log_df.index, log_df['taoriver_gate_opening'], label='Taoriver Gate')
    axes[1].set_ylabel('Opening (0-1)'); axes[1].legend(); axes[1].grid(True); axes[1].set_title('Gate Openings')
    axes[1].axvline(x=100, color='k', linestyle=':', label='Pipe Burst')
    axes[2].plot(log_df.index, log_df.get('pipe_2_pressure', pd.Series(0, index=log_df.index)), label='Pipe 2 Pressure')
    axes[2].axhline(y=0.3, color='r', linestyle='--', label='Emergency Threshold')
    axes[2].set_ylabel('Pressure (MPa)'); axes[2].legend(); axes[2].grid(True); axes[2].set_title('Pipeline Pressure')
    axes[2].axvline(x=100, color='k', linestyle=':', label='Pipe Burst')
    axes[3].plot(log_df.index, log_df['intake_pid_setpoint'], label='Intake PID Setpoint', drawstyle='steps-post')
    axes[3].set_ylabel('Setpoint (m)'); axes[3].legend(); axes[3].grid(True); axes[3].set_title('Central Dispatcher Action')

    plt.xlabel('Time (hours)'); plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    output_filename = "yinchuojiliao_simulation_results.png"
    plt.savefig(output_filename)
    logging.info(f"Saved plot to {output_filename}")


# Helper agent to inject the pipe burst event
class BurstAgent(Agent):
    def __init__(self, agent_id: str, component_map: dict):
        super().__init__(agent_id)
        self.comp_map = component_map

    def run(self, current_time: float):
        if int(current_time) == 100:
            logging.warning(f"!!! Manually simulating pipe burst at time {current_time} !!!")
            self.comp_map['pipe_1'].pressure = 0.1

if __name__ == "__main__":
    run_simulation()
