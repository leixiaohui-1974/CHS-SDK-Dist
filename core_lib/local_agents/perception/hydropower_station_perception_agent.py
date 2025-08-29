"""
Perception Agent for a hydropower station, acting as its digital twin.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.hydropower_station import HydropowerStation
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class HydropowerStationPerceptionAgent(DigitalTwinAgent):
    """
    A specialized Digital Twin Agent for monitoring a HydropowerStation object.

    This agent wraps a HydropowerStation simulation model, periodically fetching
    its aggregated state (total outflow, total power generation, etc.) and
    publishing it to a designated topic on the message bus.
    """

    def __init__(self,
                 agent_id: str,
                 hydropower_station_model: HydropowerStation,
                 message_bus: MessageBus,
                 state_topic: str):
        """
        Initializes the HydropowerStationPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            hydropower_station_model: The HydropowerStation model this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the station's state.
        """
        super().__init__(agent_id=agent_id,
                         simulated_object=hydropower_station_model,
                         message_bus=message_bus,
                         state_topic=state_topic)

        print(f"HydropowerStationPerceptionAgent '{self.agent_id}' created for HydropowerStation '{hydropower_station_model.name}'.")
