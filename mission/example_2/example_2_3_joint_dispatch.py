import sys
import os
import math

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Imports for physical components
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.canal import Canal
from core_lib.examples.helpers import setup_logging

# Imports for agents and controllers
from core_lib.core.interfaces import Controller
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from core_lib.disturbances.rainfall_agent import RainfallAgent
from core_lib.disturbances.water_use_agent import WaterUseAgent
from typing import Dict, Any


class HydropowerController(Controller):
    """
    A custom controller to manage a hydropower station with a turbine and a bypass gate.
    It receives a target total outflow from the Central Dispatcher and decides how
    to allocate it between the turbine and the gate.
    """
    def __init__(self, turbine_max_flow: float, setpoint: float = 0.0):
        self.setpoint = setpoint  # Target total outflow in m^3/s
        self.turbine_max_flow = turbine_max_flow

    def compute_control_action(self, observation: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Computes the required target outflows for the turbine and the gate.
        The 'observation' is the full state dictionary of the upstream reservoir.
        """
        # The total outflow required by the central dispatcher
        target_total_outflow = self.setpoint

        # The inflow to the station is the outflow from the reservoir in the previous step.
        # This is a simplification; a real system might use predicted inflow.
        inflow_to_station = observation.get('outflow', 0)

        # The turbine is always used first, up to its maximum capacity.
        turbine_flow = min(inflow_to_station, self.turbine_max_flow)

        # The flood gate must release any remaining flow to meet the dispatcher's target.
        gate_flow = max(0, target_total_outflow - turbine_flow)

        # The actions are published as a dictionary, with keys matching the 'action_key'
        # or expected message format of the target components.
        return {
            "turbine_target_outflow": turbine_flow, # For the WaterTurbine
            "gate_target_outflow": gate_flow      # For the Gate
        }

    def update_setpoint(self, message: Dict[str, Any]):
        """Receives a command message from the Central Dispatcher."""
        self.setpoint = message.get('new_setpoint', self.setpoint)
        print(f"  [HydropowerController] Received new command. Total outflow setpoint: {self.setpoint} m^3/s")


def run_joint_dispatch_example():
    """
    Example 2.3: Joint Watershed Dispatch

    This simulation demonstrates a complex, multi-agent system for water resource management.
    It models a basin with a hydropower station and a downstream water user, facing a
    simultaneous flood and peak demand event.

    The system showcases hierarchical control:
    - A CentralDispatcher makes high-level strategic decisions.
    - LocalControlAgents execute these decisions by controlling physical assets.
    """
    setup_logging()
    print("--- Example 2.3: Joint Watershed Dispatch ---")

    # 1. Simulation Setup
    SIM_DURATION = 3600 * 24 * 3 # 3 days
    DT = 3600 # 1 hour
    harness = SimulationHarness(config={'duration': SIM_DURATION, 'dt': DT})
    bus = harness.message_bus

    # 2. Communication Topics
    # Defines the "channels" for agent communication.
    RESERVOIR_STATE_TOPIC = "state/reservoir/all"
    INFLOW_DISTURBANCE_TOPIC = "disturbance/inflow/reservoir"
    WATER_DEMAND_TOPIC = "disturbance/outflow/diversion"
    HYDRO_COMMAND_TOPIC = "command/hydro_station/outflow"
    TURBINE_ACTION_TOPIC = "action/turbine/flow"
    FLOOD_GATE_ACTION_TOPIC = "action/gate/flow"
    DIVERSION_COMMAND_TOPIC = "command/diversion/gate"
    DIVERSION_ACTION_TOPIC = "action/diversion/opening"

    # 3. Physical Components
    # a. Upstream Reservoir
    reservoir_params = {'surface_area': 2e6, 'max_volume': 50e6}
    initial_reservoir_volume = 35e6 # 70% full
    upper_reservoir = Reservoir(
        name="upper_reservoir",
        initial_state={'volume': initial_reservoir_volume, 'water_level': initial_reservoir_volume / reservoir_params['surface_area']},
        parameters=reservoir_params,
        message_bus=bus,
        inflow_topic=INFLOW_DISTURBANCE_TOPIC
    )

    # b. Hydropower Station (Turbine + parallel Flood Gate)
    turbine = WaterTurbine(
        name="station_turbine",
        parameters={'efficiency': 0.9, 'max_flow_rate': 150},
        initial_state={'power': 0, 'outflow': 0},
        message_bus=bus,
        action_topic=TURBINE_ACTION_TOPIC,
        action_key="turbine_target_outflow"
    )
    flood_gate = Gate(
        name="station_flood_gate",
        parameters={'discharge_coefficient': 0.6, 'width': 10, 'max_opening': 3.0, 'max_rate_of_change': 0.5},
        initial_state={'opening': 0.0},
        message_bus=bus,
        action_topic=FLOOD_GATE_ACTION_TOPIC
    )

    # c. Tailrace Canal (enlarged to handle flood discharge)
    canal_params = {'bottom_width': 50, 'length': 5000, 'slope': 0.001, 'side_slope_z': 2, 'manning_n': 0.025}
    tailrace_canal = Canal(
        name="tailrace_canal",
        parameters=canal_params,
        initial_state={'volume': 100000, 'water_level': 2.1}
    )

    # d. Downstream Diversion Point (Gate + Canal)
    diversion_gate = Gate(
        name="diversion_gate",
        parameters={'discharge_coefficient': 0.8, 'width': 5, 'max_opening': 2.0},
        initial_state={'opening': 1.0}, # Normally open
        message_bus=bus,
        action_topic=DIVERSION_ACTION_TOPIC,
        action_key='opening'
    )
    diversion_canal = Canal(
        name="diversion_canal",
        parameters=canal_params,
        initial_state={'volume': 50000, 'water_level': 1.5},
        message_bus=bus,
        inflow_topic=WATER_DEMAND_TOPIC
    )

    # 4. Intelligent Agents
    # a. Disturbance Agents (Simulate external events)
    flood_agent = RainfallAgent("flood_event", bus, {"topic": INFLOW_DISTURBANCE_TOPIC, "start_time": 3600*12, "duration": 3600*24, "inflow_rate": 300})
    water_user = WaterUseAgent("water_user", bus, {"topic": WATER_DEMAND_TOPIC, "start_time": 3600*18, "duration": 3600*12, "demand_rate": 50})

    # b. Perception Agent (Provides data to other agents)
    reservoir_twin = DigitalTwinAgent("reservoir_twin", upper_reservoir, bus, RESERVOIR_STATE_TOPIC)

    # c. Local Control Agents (Execute high-level commands)
    hydro_controller = HydropowerController(turbine_max_flow=150, setpoint=100)
    hydro_agent = LocalControlAgent(
        agent_id="hydro_station_agent",
        controller=hydro_controller,
        message_bus=bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key=None, # Pass the full state dict to the controller
        action_topic=[TURBINE_ACTION_TOPIC, FLOOD_GATE_ACTION_TOPIC],
        dt=DT,
        command_topic=HYDRO_COMMAND_TOPIC
    )

    class DirectGateController(Controller):
        def __init__(self, setpoint=1.0): self.setpoint = setpoint
        def compute_control_action(self, obs, dt): return {'opening': self.setpoint}
        def update_setpoint(self, msg): self.setpoint = msg.get('new_setpoint', self.setpoint)
    diversion_controller = DirectGateController()
    diversion_agent = LocalControlAgent(
        agent_id="diversion_agent",
        controller=diversion_controller,
        message_bus=bus,
        observation_topic=None,
        observation_key=None,
        action_topic=DIVERSION_ACTION_TOPIC,
        dt=DT,
        command_topic=DIVERSION_COMMAND_TOPIC
    )

    # d. Central Dispatch Agent (The "Brain")
    dispatcher_rules = {
        "profiles": {
            "flood": {
                "condition": lambda states: states.get('reservoir', {}).get('water_level', 0) > 22.0,
                "commands": {
                    "hydro_station_control": {"new_setpoint": 400}, # Command high outflow
                    "diversion_gate_control": {"new_setpoint": 0.0}  # Command diversion gate to close
                }
            },
            "normal": {
                "condition": lambda states: True, # Default profile if no other conditions are met
                "commands": {
                    "hydro_station_control": {"new_setpoint": 100}, # Normal outflow
                    "diversion_gate_control": {"new_setpoint": 1.0}   # Normal diversion
                }
            }
        }
    }
    dispatcher = CentralDispatcher(
        agent_id="central_dispatcher",
        message_bus=bus,
        state_subscriptions={'reservoir': RESERVOIR_STATE_TOPIC},
        command_topics={
            'hydro_station_control': HYDRO_COMMAND_TOPIC,
            'diversion_gate_control': DIVERSION_COMMAND_TOPIC
        },
        rules=dispatcher_rules
    )

    # 5. Add all components and agents to the harness
    for component in [upper_reservoir, turbine, flood_gate, tailrace_canal, diversion_gate, diversion_canal]:
        harness.add_component(component)
    for agent in [flood_agent, water_user, reservoir_twin, hydro_agent, diversion_agent, dispatcher]:
        harness.add_agent(agent)

    # 6. Define physical connections
    harness.add_connection("upper_reservoir", "station_turbine")
    harness.add_connection("upper_reservoir", "station_flood_gate")
    harness.add_connection("station_turbine", "tailrace_canal")
    harness.add_connection("station_flood_gate", "tailrace_canal")
    harness.add_connection("tailrace_canal", "diversion_gate")
    harness.add_connection("diversion_gate", "diversion_canal")

    # 7. Build and run the simulation
    harness.build()
    harness.run_mas_simulation()

    # 8. Verification
    print("\n--- Final Results ---")
    max_level_achieved = max(h['upper_reservoir']['water_level'] for h in harness.history)
    flood_threshold = 22.0
    dam_safety_limit = 25.0
    print(f"Reservoir flood threshold: {flood_threshold:.2f}m")
    print(f"Peak reservoir level during simulation: {max_level_achieved:.2f}m")
    print(f"Dam safety limit: {dam_safety_limit:.2f}m")

    assert max_level_achieved < dam_safety_limit, \
        f"DISPATCH FAILED: Peak level {max_level_achieved:.2f}m exceeded dam safety limit of {dam_safety_limit:.2f}m."

    print("\nVERIFICATION SUCCESS: The multi-agent system successfully managed the flood event, keeping the reservoir level within safe limits.")


if __name__ == "__main__":
    run_joint_dispatch_example()
