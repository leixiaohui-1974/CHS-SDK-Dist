"""
Control Agent for a Pump Station.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import List, Dict, Any

class PumpStationControlAgent(Agent):
    """
    A Control Agent responsible for managing a Pump Station.

    This agent makes decisions on which pumps to turn on or off based on
    high-level goals (e.g., target number of active pumps) it receives.
    It subscribes to goal topics and the station's own state topic for feedback,
    and publishes control commands directly to individual pumps.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 goal_topic: str,
                 state_topic: str,
                 pump_action_topics: List[str]):
        """
        Initializes the PumpStationControlAgent.

        Args:
            agent_id: The unique ID of this agent.
            message_bus: The system's message bus for communication.
            goal_topic: The topic to listen on for new control goals.
            state_topic: The topic to listen on for the station's current state.
            pump_action_topics: A list of the action topics for each pump in the station.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.pump_action_topics = pump_action_topics
        self.num_pumps = len(pump_action_topics)

        # Agent's memory
        self.target_active_pumps: int = 0
        self.current_active_pumps: int = 0

        # Subscribe to relevant topics
        self.bus.subscribe(goal_topic, self.handle_goal_message)
        self.bus.subscribe(state_topic, self.handle_state_message)

        print(f"PumpStationControlAgent '{self.agent_id}' created.")
        print(f"  - Subscribed to goal topic: '{goal_topic}'")
        print(f"  - Subscribed to state topic: '{state_topic}'")
        print(f"  - Controls {self.num_pumps} pumps.")

    def handle_goal_message(self, message: Dict[str, Any]):
        """Callback for processing new control goals."""
        new_target = message.get('target_active_pumps')
        if isinstance(new_target, int) and 0 <= new_target <= self.num_pumps:
            if new_target != self.target_active_pumps:
                print(f"'{self.agent_id}' received new goal: Turn on {new_target} pumps.")
                self.target_active_pumps = new_target
                self.run_control_logic()
        else:
            print(f"'{self.agent_id}' received invalid goal: {message}")

    def handle_state_message(self, message: State):
        """Callback for processing state updates from the perception agent."""
        self.current_active_pumps = message.get('active_pumps', 0)
        # Optional: Could trigger control logic here if there's a deviation
        # from the target, but for now, we'll keep it simple and only react to new goals.

    def run_control_logic(self):
        """
        Executes the core control logic to align the station's state with the target.

        This is a simple strategy: turn pumps on or off sequentially to meet the target.
        A more advanced implementation would use an economic strategy table.
        """
        print(f"'{self.agent_id}' running control logic. Target: {self.target_active_pumps}, Current: {self.current_active_pumps}")

        # Turn pumps on/off to match the target
        for i, topic in enumerate(self.pump_action_topics):
            # The desired state for this pump (1 for on, 0 for off)
            desired_status = 1 if i < self.target_active_pumps else 0

            print(f"  - Sending control signal {desired_status} to pump {i+1} on topic '{topic}'")
            self.bus.publish(topic, {'control_signal': desired_status})

    def run(self, current_time: float):
        """
        The main execution loop for the agent.
        For this reactive agent, the primary logic is in the message handlers.
        This run method could be used for periodic checks or logging if needed.
        """
        pass # The logic is event-driven (reacts to messages)
