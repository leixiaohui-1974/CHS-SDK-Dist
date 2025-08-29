"""
Perception agent for a river channel.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

class RiverChannelPerceptionAgent(DigitalTwinAgent):
    """
    A perception agent specifically for a river channel, acting as its digital twin.

    This agent is responsible for reading the state of a river channel simulation model,
    potentially enhancing it (e.g., through smoothing or filtering), and publishing
    it for other agents to consume. It is a specialization of the DigitalTwinAgent,
    tailored for river channel objects.
    """
    def __init__(self, **kwargs):
        """
        Initializes the RiverChannelPerceptionAgent.
        Inherits the base functionality from DigitalTwinAgent.
        """
        super().__init__(**kwargs)
        print(f"RiverChannelPerceptionAgent '{self.agent_id}' initialized.")
