"""
Central Dispatcher Agent for hierarchical, high-level coordination.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any

class CentralDispatcher(Agent):
    """
    The central coordinating agent for the entire water system.

    It operates at a higher level than local controllers. It subscribes to key
    system state information and forecasts, and uses a high-level strategy
    to send updated commands (like new setpoints) to the local agents.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus,
                 state_subscriptions: Dict[str, str],
                 command_topics: Dict[str, str],
                 forecast_subscriptions: Dict[str, str] = None,
                 rules: Any = None):
        """
        Initializes the CentralDispatcher.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus.
            state_subscriptions: A dict mapping local names to state topics to subscribe to.
            command_topics: A dict mapping local command names to command topics.
            forecast_subscriptions: A dict mapping local names to forecast topics.
            rules: A set of rules or a function that defines the dispatch logic.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.command_topics = command_topics
        self.rules = rules or {}
        self.latest_states: Dict[str, State] = {}
        self.forecasts: Dict[str, Dict] = {}
        self.active_setpoint_name = "normal"

        if state_subscriptions:
            for name, topic in state_subscriptions.items():
                self.bus.subscribe(topic, lambda msg, name=name: self.handle_state_message(msg, name))

        if forecast_subscriptions:
            for name, topic in forecast_subscriptions.items():
                self.bus.subscribe(topic, lambda msg, name=name: self.handle_forecast_message(msg, name))

        print(f"CentralDispatcher '{self.agent_id}' created.")

    def handle_state_message(self, message: Message, name: str):
        """Stores the latest received state from a subscribed topic."""
        self.latest_states[name] = message

    def handle_forecast_message(self, message: Message, name: str):
        """Stores the latest received forecast from a subscribed topic."""
        self.forecasts[name] = message
        print(f"  [{self.agent_id}] Received forecast '{name}': {message}")

    def run(self, current_time: float):
        """
        Evaluates the system state against a set of rules and activates a
        corresponding control profile. This is a generic, stateless implementation.
        """
        # Determine which profile's conditions are met
        active_profile_name = "normal" # Default profile
        for profile_name, profile_data in self.rules.get("profiles", {}).items():
            condition = profile_data.get("condition")
            if condition and condition(self.latest_states):
                active_profile_name = profile_name
                break # First matching profile wins

        # If the active profile has changed, publish the new commands
        if active_profile_name != self.active_setpoint_name:
            self.active_setpoint_name = active_profile_name
            print(f"  [{current_time}s] [{self.agent_id}] System state change. Activating '{self.active_setpoint_name}' profile.")

            # Get the commands for the active profile
            commands_to_publish = self.rules.get("profiles", {}).get(active_profile_name, {}).get("commands", {})

            # Send a new command message for each managed entity in the profile
            for command_name, message_body in commands_to_publish.items():
                if command_name in self.command_topics:
                    topic = self.command_topics[command_name]
                    print(f"  [{self.agent_id}] -> Publishing to topic '{topic}': {message_body}")
                    self.bus.publish(topic, message_body)
