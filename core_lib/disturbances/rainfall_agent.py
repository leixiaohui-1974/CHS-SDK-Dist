"""
An agent that simulates a rainfall disturbance event.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any

class RainfallAgent(Agent):
    """
    A disturbance agent that simulates a rainfall event.

    This agent publishes a message containing an additional inflow rate to a
    specified topic during a defined time window. This allows for testing the
    resilience of the control system to external disturbances.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, topic: str,
                 start_time: float, duration: float, inflow_rate: float, **kwargs):
        """
        Initializes the RainfallAgent.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus.
            topic: The topic to publish the disturbance to.
            start_time: The simulation time to start the rainfall.
            duration: The duration of the rainfall event in seconds.
            inflow_rate: The constant inflow rate during the event (m^3/s).
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = topic
        self.start_time = start_time
        self.duration = duration
        self.inflow_rate = inflow_rate
        self.end_time = self.start_time + self.duration
        self.is_active = False

        if not self.topic:
            raise ValueError("RainfallAgent requires a 'topic'.")

        print(f"RainfallAgent '{self.agent_id}' created. Will trigger at t={self.start_time}s on topic '{self.topic}'.")

    def run(self, current_time: float):
        """
        The main execution logic for the agent.

        At each time step, it checks if the simulation time is within its
        active window. If it is, it publishes a disturbance message.
        """
        if self.start_time <= current_time < self.end_time:
            if not self.is_active:
                print(f"--- Rainfall event STARTED at t={current_time}s ---")
                self.is_active = True

            disturbance_message: Message = {'inflow_rate': self.inflow_rate}
            self.bus.publish(self.topic, disturbance_message)
        else:
            if self.is_active:
                print(f"--- Rainfall event ENDED at t={current_time}s ---")
                self.is_active = False
