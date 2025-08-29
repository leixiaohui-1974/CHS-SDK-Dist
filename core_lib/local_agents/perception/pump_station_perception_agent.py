"""
Perception Agent for a pump station, acting as its digital twin.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.pump import PumpStation
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class PumpStationPerceptionAgent(DigitalTwinAgent):
    """
    A specialized Digital Twin Agent for monitoring a PumpStation object.

    This agent wraps a PumpStation simulation model, periodically fetching its
    aggregated state (total outflow, active pumps, etc.) and publishing it
    to a designated topic on the message bus.
    """

    def __init__(self,
                 agent_id: str,
                 pump_station_model: PumpStation,
                 message_bus: MessageBus,
                 state_topic: str):
        """
        Initializes the PumpStationPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            pump_station_model: The PumpStation simulation model this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the pump station's state.
        """
        super().__init__(agent_id=agent_id,
                         simulated_object=pump_station_model,
                         message_bus=message_bus,
                         state_topic=state_topic)

        print(f"PumpStationPerceptionAgent '{self.agent_id}' created for PumpStation '{pump_station_model.name}'.")
