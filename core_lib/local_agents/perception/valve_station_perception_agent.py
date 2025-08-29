"""
Perception Agent for a valve station, acting as its digital twin.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.valve import ValveStation
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class ValveStationPerceptionAgent(DigitalTwinAgent):
    """
    A specialized Digital Twin Agent for monitoring a ValveStation object.

    This agent wraps a ValveStation simulation model, periodically fetching its
    aggregated state (e.g., total outflow) and publishing it to a designated
    topic on the message bus.
    """

    def __init__(self,
                 agent_id: str,
                 valve_station_model: ValveStation,
                 message_bus: MessageBus,
                 state_topic: str):
        """
        Initializes the ValveStationPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            valve_station_model: The ValveStation model this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the valve station's state.
        """
        super().__init__(agent_id=agent_id,
                         simulated_object=valve_station_model,
                         message_bus=message_bus,
                         state_topic=state_topic)

        print(f"ValveStationPerceptionAgent '{self.agent_id}' created for ValveStation '{valve_station_model.name}'.")
