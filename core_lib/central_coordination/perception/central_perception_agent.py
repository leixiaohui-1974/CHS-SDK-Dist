"""
Central Perception Agent for aggregating distributed state information.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import List, Dict, Any

class CentralPerceptionAgent(Agent):
    """
    The Central Perception Agent acts as the "sensory cortex" of the MAS.

    It subscribes to the state topics of multiple distributed perception agents
    and aggregates their individual states into a single, unified view of the
    entire network. This global state can then be used by central dispatchers
    or for high-level system monitoring.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 subscribed_topics: Dict[str, str],
                 global_state_topic: str):
        """
        Initializes the CentralPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            message_bus: The system's message bus for communication.
            subscribed_topics: A dictionary mapping a component ID to its state topic.
                               Example: {'pump_station_1': 'state.pumps.1', 'valve_station_1': 'state.valves.1'}
            global_state_topic: The topic on which to publish the aggregated state.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.subscribed_topics = subscribed_topics
        self.global_state_topic = global_state_topic

        # The unified, global state of the network
        self.global_state: Dict[str, State] = {comp_id: {} for comp_id in self.subscribed_topics.keys()}

        # Subscribe to each component's state topic
        for comp_id, topic in self.subscribed_topics.items():
            # Use a lambda with a default argument to capture the comp_id correctly
            self.bus.subscribe(topic, lambda msg, cid=comp_id: self.handle_state_message(cid, msg))
            print(f"'{self.agent_id}' subscribed to topic '{topic}' for component '{comp_id}'.")

    def handle_state_message(self, component_id: str, message: State):
        """
        Callback to update a part of the global state when a message is received.
        """
        print(f"'{self.agent_id}' received state update from '{component_id}': {message}")
        self.global_state[component_id] = message
        # In a real system, we might publish the global state on every update
        # or on a fixed interval. For simplicity, we'll make the run() method publish.

    def publish_global_state(self):
        """Publishes the entire aggregated state to the global topic."""
        print(f"'{self.agent_id}' publishing global state to '{self.global_state_topic}'.")
        self.bus.publish(self.global_state_topic, self.global_state)

    def run(self, current_time: float):
        """
        The main execution loop for the agent.

        This agent's primary role is reactive, but the run loop is used to
        periodically publish the complete, aggregated state.
        """
        self.publish_global_state()
