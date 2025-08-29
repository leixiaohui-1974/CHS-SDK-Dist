"""
Control Agent for a Valve Station.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import List, Dict, Any

class ValveStationControlAgent(Agent):
    """
    A Control Agent responsible for managing a Valve Station.

    This agent adjusts the opening of all valves in the station to meet a
    high-level total outflow target. It uses a simple proportional control
    strategy.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 goal_topic: str,
                 state_topic: str,
                 valve_action_topics: List[str],
                 kp: float = 0.1):
        """
        Initializes the ValveStationControlAgent.

        Args:
            agent_id: The unique ID of this agent.
            message_bus: The system's message bus for communication.
            goal_topic: The topic to listen on for new control goals.
            state_topic: The topic to listen on for the station's current state.
            valve_action_topics: A list of the action topics for each valve.
            kp: The proportional gain for the controller.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.valve_action_topics = valve_action_topics
        self.kp = kp

        # Agent's memory
        self.target_total_flow: float = 0.0
        self.current_total_flow: float = 0.0
        self.current_valve_opening: float = 50.0 # Assume a starting opening

        # Subscribe to relevant topics
        self.bus.subscribe(goal_topic, self.handle_goal_message)
        self.bus.subscribe(state_topic, self.handle_state_message)

        print(f"ValveStationControlAgent '{self.agent_id}' created.")
        print(f"  - Subscribed to goal topic: '{goal_topic}'")
        print(f"  - Subscribed to state topic: '{state_topic}'")

    def handle_goal_message(self, message: Dict[str, Any]):
        """Callback for processing new control goals."""
        new_target = message.get('target_total_flow')
        if isinstance(new_target, (int, float)):
            if new_target != self.target_total_flow:
                print(f"'{self.agent_id}' received new flow target: {new_target:.2f}")
                self.target_total_flow = new_target
        else:
            print(f"'{self.agent_id}' received invalid goal: {message}")

    def handle_state_message(self, message: State):
        """Callback for processing state updates from the perception agent."""
        self.current_total_flow = message.get('total_outflow', 0)

    def run_control_logic(self):
        """
        Executes the proportional control logic.
        """
        error = self.target_total_flow - self.current_total_flow

        # Proportional control action
        adjustment = self.kp * error

        # Update the opening for all valves
        self.current_valve_opening += adjustment

        # Clamp the opening to the valid range [0, 100]
        self.current_valve_opening = max(0.0, min(100.0, self.current_valve_opening))

        print(f"'{self.agent_id}' Control Loop: Target={self.target_total_flow:.2f}, "
              f"Current={self.current_total_flow:.2f}, Error={error:.2f}, "
              f"New Opening={self.current_valve_opening:.1f}%")

        # Publish the new control signal to all valves
        for topic in self.valve_action_topics:
            self.bus.publish(topic, {'control_signal': self.current_valve_opening})

    def run(self, current_time: float):
        """
        The main execution loop for the agent, called at each simulation step.
        """
        self.run_control_logic()
