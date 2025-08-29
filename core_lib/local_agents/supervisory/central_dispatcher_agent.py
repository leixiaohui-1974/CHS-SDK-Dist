"""
A central dispatching agent for high-level, rule-based control.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any
import logging

class CentralDispatcherAgent(Agent):
    """
    Implements a high-level dispatching logic based on the state of a key system
    component, often a terminal reservoir. It adjusts the setpoint of a remote
    controller to manage the overall system inventory.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 subscribed_topic: str,
                 observation_key: str,
                 command_topic: str,
                 dispatcher_params: Dict[str, Any]):
        """
        Initializes the CentralDispatcherAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The system's message bus.
            subscribed_topic: The state topic to monitor (e.g., terminal reservoir state).
            observation_key: The key within the state message to observe (e.g., 'water_level').
            command_topic: The topic to publish setpoint change commands to.
            dispatcher_params: A dictionary containing the control logic parameters, e.g.,
                               {'low_level', 'high_level', 'low_setpoint', 'high_setpoint'}.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.subscribed_topic = subscribed_topic
        self.observation_key = observation_key
        self.command_topic = command_topic
        self.params = dispatcher_params
        self.current_observed_value = None

        self.bus.subscribe(self.subscribed_topic, self.handle_state_message)
        logging.info(f"CentralDispatcherAgent '{self.agent_id}' initialized. Monitoring '{self.observation_key}' on topic '{self.subscribed_topic}'.")

    def handle_state_message(self, message: Message):
        """Callback to update the agent's knowledge of the observed value."""
        observed_value = message.get(self.observation_key)
        if observed_value is not None:
            self.current_observed_value = observed_value

    def run(self, current_time: float):
        """
        The main execution logic, called at each simulation step. It checks the
        current state and decides whether to issue a new command.
        """
        if self.current_observed_value is None:
            # No data received yet, do nothing.
            return

        low_level = self.params['low_level']
        high_level = self.params['high_level']
        new_setpoint = None

        # Simple hysteresis (bang-bang) control logic
        if self.current_observed_value < low_level:
            new_setpoint = self.params['high_setpoint'] # Level is too low, increase inflow by raising upstream setpoint
        elif self.current_observed_value > high_level:
            new_setpoint = self.params['low_setpoint'] # Level is too high, decrease inflow by lowering upstream setpoint

        if new_setpoint is not None:
            # Check if this is a change from the last command to avoid flooding the bus
            # (A more robust implementation would store the last commanded setpoint)
            logging.info(f"Dispatcher '{self.agent_id}' is issuing a new setpoint: {new_setpoint}")
            command_message: Message = {'new_setpoint': new_setpoint}
            self.bus.publish(self.command_topic, command_message)
            # We can reset the observed value to prevent re-issuing the same command
            # until a new state message arrives, but for simplicity we don't here.
