"""
Perception Agent for a reservoir, acting as its digital twin.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class ReservoirPerceptionAgent(DigitalTwinAgent):
    """
    A specialized Digital Twin Agent for monitoring a Reservoir object.

    This provides a dedicated class for reservoir perception, making the
    architecture more consistent and allowing for future extension with
    reservoir-specific logic (e.g., evaporation estimation).
    """

    def __init__(self,
                 agent_id: str,
                 reservoir_model: Reservoir,
                 message_bus: MessageBus,
                 state_topic: str):
        """
        Initializes the ReservoirPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            reservoir_model: The Reservoir simulation model this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the reservoir's state.
        """
        super().__init__(agent_id=agent_id,
                         simulated_object=reservoir_model,
                         message_bus=message_bus,
                         state_topic=state_topic)

        print(f"ReservoirPerceptionAgent '{self.agent_id}' created for Reservoir '{reservoir_model.name}'.")
