"""
Control Agent for a Hydropower Station.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import List, Dict, Any

class HydropowerStationControlAgent(Agent):
    """
    A Control Agent for managing a complex Hydropower Station.

    It receives high-level goals for both power generation and total outflow,
    and translates them into specific commands for the station's turbines and gates.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 goal_topic: str,
                 state_topic: str,
                 turbine_action_topics: List[str],
                 gate_action_topics: List[str],
                 turbine_efficiency: float, # A simplified single efficiency for all turbines
                 rho: float = 1000,
                 g: float = 9.81):
        super().__init__(agent_id)
        self.bus = message_bus
        self.turbine_action_topics = turbine_action_topics
        self.gate_action_topics = gate_action_topics
        self.num_turbines = len(turbine_action_topics)
        self.num_gates = len(gate_action_topics)
        self.efficiency = turbine_efficiency
        self.rho = rho
        self.g = g

        # Agent's memory
        self.target_power: float = 0.0
        self.target_total_outflow: float = 0.0
        self.current_head: float = 0.0
        self.current_turbine_outflow: float = 0.0

        self.bus.subscribe(goal_topic, self.handle_goal_message)
        self.bus.subscribe(state_topic, self.handle_state_message)

        print(f"HydropowerStationControlAgent '{self.agent_id}' created.")

    def handle_goal_message(self, message: Dict[str, Any]):
        """Callback for processing new control goals."""
        self.target_power = message.get('target_power_generation', self.target_power)
        self.target_total_outflow = message.get('target_total_outflow', self.target_total_outflow)
        print(f"'{self.agent_id}' received new goals: Power={self.target_power}W, Outflow={self.target_total_outflow}m^3/s")

    def handle_state_message(self, message: State):
        """
        Callback for processing state updates.
        The perception agent is expected to provide head info in the state.
        """
        self.current_turbine_outflow = message.get('turbine_outflow', 0.0)
        # Assume upstream_head and downstream_head are published by the perception agent
        upstream_head = message.get('upstream_head', 0.0)
        downstream_head = message.get('downstream_head', 0.0)
        self.current_head = max(0, upstream_head - downstream_head)

    def run_control_logic(self):
        """
        Executes the control logic based on a simplified strategy:
        1. Use turbines to meet the power generation target.
        2. Use gates to meet any remaining outflow target.
        """
        # --- 1. Turbine Control ---
        required_flow_for_power = 0.0
        if self.target_power > 0 and self.current_head > 0:
            # Inverse power equation: Q = P / (η * ρ * g * H)
            denominator = self.efficiency * self.rho * self.g * self.current_head
            if denominator > 0:
                required_flow_for_power = self.target_power / denominator

        # Distribute required flow among turbines
        flow_per_turbine = required_flow_for_power / self.num_turbines if self.num_turbines > 0 else 0

        print(f"'{self.agent_id}' Control: Head={self.current_head:.2f}m. "
              f"Required flow for power: {required_flow_for_power:.2f} m^3/s. "
              f"Distributing {flow_per_turbine:.2f} m^3/s per turbine.")

        for topic in self.turbine_action_topics:
            self.bus.publish(topic, {'target_outflow': flow_per_turbine})

        # --- 2. Gate Control ---
        # This logic should ideally run after the turbine flow has updated.
        # In a real-time simulation, we use the most recent turbine outflow value.
        remaining_flow_target = self.target_total_outflow - self.current_turbine_outflow

        flow_per_gate = 0.0
        if remaining_flow_target > 0:
            flow_per_gate = remaining_flow_target / self.num_gates if self.num_gates > 0 else 0

        print(f"'{self.agent_id}' Control: Target total outflow={self.target_total_outflow:.2f}. "
              f"Current turbine outflow={self.current_turbine_outflow:.2f}. "
              f"Distributing {flow_per_gate:.2f} m^3/s per gate.")

        for topic in self.gate_action_topics:
            # The gate model can handle converting this to an opening
            self.bus.publish(topic, {'gate_target_outflow': flow_per_gate})

    def run(self, current_time: float):
        """
        The main execution loop for the agent, called at each simulation step.
        """
        self.run_control_logic()
