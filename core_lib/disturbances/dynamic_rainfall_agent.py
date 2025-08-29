from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Dict, Any

class DynamicRainfallAgent(Agent):
    """
    An agent that simulates a dynamic rainfall event (hydrograph).

    This agent generates a non-square wave inflow pattern, such as a
    triangular hydrograph, which is more realistic for demonstrating
    trend forecasting.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, config: Dict[str, Any]):
        """
        Initializes the DynamicRainfallAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The central message bus for communication.
            config: A dictionary containing the event parameters:
                - topic (str): The topic to publish the rainfall inflow to.
                - start_time (int): The simulation time in seconds to start the event.
                - peak_time (int): The simulation time to reach peak inflow.
                - end_time (int): The simulation time to end the event.
                - peak_inflow (float): The maximum inflow rate at the peak (m^3/s).
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = config["topic"]
        self.start_time = config["start_time"]
        self.peak_time = config["peak_time"]
        self.end_time = config["end_time"]
        self.peak_inflow = config["peak_inflow"]

        if not self.start_time < self.peak_time < self.end_time:
            raise ValueError("Rainfall event times must be in increasing order: start < peak < end.")

        print(f"DynamicRainfallAgent '{self.agent_id}' configured for topic '{self.topic}'.")

    def run(self, current_time: float):
        """
        Calculates and publishes the current inflow based on the hydrograph shape.
        """
        inflow = 0.0
        if self.start_time <= current_time < self.end_time:
            if current_time < self.peak_time:
                # Rising limb of the hydrograph
                time_fraction = (current_time - self.start_time) / (self.peak_time - self.start_time)
                inflow = self.peak_inflow * time_fraction
            else:
                # Receding limb of the hydrograph
                time_fraction = (self.end_time - current_time) / (self.end_time - self.peak_time)
                inflow = self.peak_inflow * time_fraction

        if inflow > 0:
            message = {'inflow_change': inflow}
            self.bus.publish(self.topic, message)
