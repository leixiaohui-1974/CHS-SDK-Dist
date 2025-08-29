"""
An agent that monitors system state for emergencies and takes predefined action.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List
import logging

class EmergencyAgent(Agent):
    """
    Monitors specific message bus topics for emergency conditions (e.g., low pressure
    indicating a pipe burst) and publishes a command to a specified topic to
    initiate a shutdown or other emergency procedure.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 subscribed_topics: List[str],
                 pressure_threshold: float,
                 action_topic: str):
        """
        Initializes the EmergencyAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The system's message bus.
            subscribed_topics: A list of state topics to monitor for pressure readings.
            pressure_threshold: The pressure value below which an emergency is declared.
            action_topic: The topic to publish the emergency action command to.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.subscribed_topics = subscribed_topics
        self.pressure_threshold = pressure_threshold
        self.action_topic = action_topic
        self.emergency_declared = False

        # Subscribe to all relevant topics
        for topic in self.subscribed_topics:
            self.bus.subscribe(topic, self.handle_state_message)

        logging.info(f"EmergencyAgent '{self.agent_id}' initialized. Monitoring {self.subscribed_topics} for pressure below {self.pressure_threshold}.")

    def handle_state_message(self, message: Message):
        """Callback function to process incoming state messages."""
        if self.emergency_declared:
            return  # Don't do anything if an emergency is already active

        pressure = message.get('pressure')
        if pressure is not None and pressure < self.pressure_threshold:
            self.declare_emergency()

    def declare_emergency(self):
        """Declares an emergency and publishes the action command."""
        logging.critical(f"EMERGENCY DECLARED by '{self.agent_id}'! Pressure dropped below threshold.")
        # Set flag to prevent multiple declarations
        self.emergency_declared = True

        # The action message could be structured to command a specific component.
        # For example, telling a PID controller to change its setpoint to 0
        # or telling a gate to close.
        emergency_message: Message = {
            'command': 'EMERGENCY_SHUTDOWN',
            'details': f'Triggered by {self.agent_id}',
            # A common convention is to reset a setpoint to force a closure.
            'new_setpoint': 0.0
        }
        self.bus.publish(self.action_topic, emergency_message)
        logging.info(f"EmergencyAgent '{self.agent_id}' published shutdown command to '{self.action_topic}'.")

    def run(self, current_time: float):
        """
        The run method for this agent is passive. It only acts based on messages
        received by its callback handler. This method could be used for periodic
        checks if needed, but is not required for this implementation.
        """
        pass
