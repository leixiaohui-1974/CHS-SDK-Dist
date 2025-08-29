"""
Perception agent for a pump.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

class PumpPerceptionAgent(DigitalTwinAgent):
    """
    A perception agent specifically for a pump, acting as its digital twin.

    This agent is responsible for reading the state of a pump simulation model,
    potentially enhancing it, and publishing it for other agents. It is a
    specialization of the DigitalTwinAgent.
    """
    def __init__(self, **kwargs):
        """
        Initializes the PumpPerceptionAgent.
        Inherits the base functionality from DigitalTwinAgent.
        """
        super().__init__(**kwargs)
        print(f"PumpPerceptionAgent '{self.agent_id}' initialized.")
