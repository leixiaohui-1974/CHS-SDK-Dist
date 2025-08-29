"""
An agent that simulates a water use disturbance event by publishing to a topic.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any

class WaterUseAgent(Agent):
    """
    A disturbance agent that simulates a water user (e.g., for agriculture or industry).

    This agent publishes a message containing a negative inflow rate (i.e., an outflow)
    to a specified topic during a defined time window. This allows for testing
    system resilience to demand-side disturbances.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, topic: str,
                 start_time: float, duration: float, demand_rate: float, **kwargs):
        """
        Initializes the WaterUseAgent.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus.
            topic: The topic to publish the disturbance to.
            start_time: The simulation time to start the water use.
            duration: The duration of the water use event in seconds.
            demand_rate: The water demand rate (m^3/s). This will be
                         published as a negative inflow.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = topic
        self.start_time = start_time
        self.duration = duration
        # Demand is modeled as a negative inflow
        self.inflow_rate = -abs(demand_rate)
        self.end_time = self.start_time + self.duration
        self.is_active = False

        if not self.topic:
            raise ValueError("WaterUseAgent requires a 'topic'.")

        print(f"WaterUseAgent '{self.agent_id}' created. Will trigger at t={self.start_time}s on topic '{self.topic}'.")

    def run(self, current_time: float):
        """
        The main execution logic for the agent.

        At each time step, it checks if the simulation time is within its
        active window. If it is, it publishes a disturbance message.
        """
        if self.start_time <= current_time < self.end_time:
            if not self.is_active:
                print(f"--- Water use event STARTED at t={current_time}s ---")
                self.is_active = True

            disturbance_message: Message = {'inflow_rate': self.inflow_rate}
            self.bus.publish(self.topic, disturbance_message)
        else:
            if self.is_active:
                print(f"--- Water use event ENDED at t={current_time}s ---")
                self.is_active = False
