"""
Mission Example 5.2: Multi-Turbine Coordination and Grid Interaction

Goal: Demonstrate how a local control agent can coordinate multiple turbines
to meet a power target and react to external events from the grid.

This simulation uses the Multi-Agent System (MAS) framework with a MessageBus.
"""
import matplotlib.pyplot as plt
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

# Import the newly created agents
from mission.agents.hydropower_control_agent import HydropowerControlAgent
from mission.agents.grid_communication_agent import GridCommunicationAgent

# A simple agent to kick off the simulation with a power target
class SupervisorAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus,
                 power_target_topic: str, initial_target_mw: float):
        super().__init__(agent_id)
        self.bus = message_bus
        self.power_target_topic = power_target_topic
        self.initial_target_mw = initial_target_mw
        self._sent = False

    def run(self, current_time: float):
        if not self._sent and current_time >= 0:
            self.bus.publish(self.power_target_topic, {'target_mw': self.initial_target_mw})
            self._sent = True

# A simple agent to provide constant inflow to the reservoir
class InflowAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus,
                 inflow_topic: str, inflow_rate: float):
        super().__init__(agent_id)
        self.bus = message_bus
        self.inflow_topic = inflow_topic
        self.inflow_rate = inflow_rate

    def run(self, current_time: float):
        # Publish inflow at every step
        self.bus.publish(self.inflow_topic, {'inflow_rate': self.inflow_rate})


def run_multi_turbine_coordination_example():
    print("--- Setting up the Multi-Turbine Coordination MAS Example ---")

    # --- 1. Simulation Setup ---
    harness = SimulationHarness(config={'duration': 300, 'dt': 1.0})
    bus = harness.message_bus

    # --- 2. Define Communication Topics ---
    POWER_TARGET_TOPIC = "target/power/total"
    GRID_LIMIT_TOPIC = "grid/power/limit"
    RESERVOIR_INFLOW_TOPIC = "data/inflow/reservoir"
    RESERVOIR_STATE_TOPIC = "state/reservoir/forebay"
    TURBINE_ACTION_TOPICS = [f"action/turbine/{i+1}" for i in range(6)]

    # --- 3. Create Physical Components ---
    # A large reservoir to provide a stable upstream head
    # Initial water level is 15m (volume / area)
    reservoir = Reservoir(
        name="forebay_reservoir",
        initial_state={'volume': 75e6, 'water_level': 15.0},
        parameters={'surface_area': 5e6},
        message_bus=bus,
        inflow_topic=RESERVOIR_INFLOW_TOPIC
    )
    harness.add_component(reservoir)

    turbines = []
    for i in range(6):
        turbine = WaterTurbine(
            name=f"turbine_{i+1}",
            initial_state={'outflow': 0, 'power': 0},
            parameters={'efficiency': 0.9, 'max_flow_rate': 100},
            message_bus=bus,
            action_topic=TURBINE_ACTION_TOPICS[i]
        )
        turbines.append(turbine)
        harness.add_component(turbine)
        harness.add_connection(reservoir.name, turbine.name)

    # --- 4. Create Agents ---
    supervisor = SupervisorAgent(
        agent_id="supervisor",
        message_bus=bus,
        power_target_topic=POWER_TARGET_TOPIC,
        initial_target_mw=12.0
    )

    # This agent provides a constant source of water into the reservoir
    inflow_agent = InflowAgent(
        agent_id="inflow_provider",
        message_bus=bus,
        inflow_topic=RESERVOIR_INFLOW_TOPIC,
        inflow_rate=85.0 # m^3/s
    )

    # This agent observes the reservoir and broadcasts its state
    twin_agent = DigitalTwinAgent(
        agent_id="reservoir_twin",
        simulated_object=reservoir,
        message_bus=bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    # The control agent now needs to listen to the reservoir's state to get the head
    control_agent = HydropowerControlAgent(
        agent_id="hydropower_controller",
        message_bus=bus,
        turbine_action_topics=TURBINE_ACTION_TOPICS,
        power_target_topic=POWER_TARGET_TOPIC,
        grid_limit_topic=GRID_LIMIT_TOPIC,
        head_m=15.0 # Will be updated by messages
    )
    # Subscribe the control agent to the reservoir's state topic to get head updates
    bus.subscribe(RESERVOIR_STATE_TOPIC, lambda msg: setattr(control_agent, 'head', msg['water_level']))


    grid_agent = GridCommunicationAgent(
        agent_id="grid_simulator",
        message_bus=bus,
        grid_limit_topic=GRID_LIMIT_TOPIC,
        rejection_time_s=150.0,
        new_limit_mw=6.0 # New limit is half the initial target
    )

    harness.add_agent(supervisor)
    harness.add_agent(inflow_agent)
    harness.add_agent(twin_agent)
    harness.add_agent(control_agent)
    harness.add_agent(grid_agent)

    # --- 5. Run Simulation ---
    harness.build()
    harness.run_mas_simulation()

    # --- 6. Collect and Plot Results ---
    raw_history = harness.history

    def parse_history(raw_history):
        parsed = {'time': []}
        if not raw_history: return parsed

        first_step = raw_history[0]
        for comp_name, state_dict in first_step.items():
            if comp_name == 'time': continue
            for state_key in state_dict.keys():
                parsed[f"{comp_name}.{state_key}"] = []

        for step in raw_history:
            parsed['time'].append(step['time'])
            for comp_name, state_dict in step.items():
                if comp_name == 'time': continue
                for state_key, value in state_dict.items():
                    # Handle cases where a key might be missing in a step
                    if f"{comp_name}.{state_key}" in parsed:
                        parsed[f"{comp_name}.{state_key}"].append(value)
        return parsed

    history = parse_history(raw_history)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    fig.suptitle('Mission 5.2: Multi-Turbine Coordination & Grid Interaction', fontsize=16)

    power_lists = [history[f'turbine_{i+1}.power'] for i in range(6)]
    total_power_watts = [sum(powers_at_t) for powers_at_t in zip(*power_lists)]
    total_power_mw = [p / 1e6 for p in total_power_watts]
    ax1.plot(history['time'], total_power_mw, label='Total Generated Power (MW)')

    ax1.axhline(y=12.0, color='g', linestyle='--', label='Initial Target (12 MW)')
    ax1.axhline(y=6.0, color='r', linestyle='--', label='Grid Limit (6 MW)')
    ax1.axvline(x=150, color='gray', linestyle=':', label='Grid Event')

    ax1.set_ylabel('Power (MW)')
    ax1.set_title('Total Power Generation vs. Targets')
    ax1.legend()
    ax1.grid(True)

    for i in range(6):
        ax2.plot(history['time'], history[f'turbine_{i+1}.outflow'], label=f'Turbine {i+1} Outflow')

    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Outflow (m^3/s)')
    ax2.set_title('Individual Turbine Outflows')
    ax2.legend(loc='best')
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("mission_5_2_results.png")
    print("\nSaved plot to mission_5_2_results.png")
    plt.show()

if __name__ == "__main__":
    run_multi_turbine_coordination_example()
