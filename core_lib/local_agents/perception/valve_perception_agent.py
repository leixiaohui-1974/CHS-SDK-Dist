"""
Perception agent for a valve.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

class ValvePerceptionAgent(DigitalTwinAgent):
    """
    A perception agent specifically for a valve, acting as its digital twin.

    This agent is responsible for reading the state of a valve simulation model,
    potentially enhancing it, and publishing it for other agents. It is a
    specialization of the DigitalTwinAgent.
    """
    def __init__(self, **kwargs):
        """
        Initializes the ValvePerceptionAgent.
        Inherits the base functionality from DigitalTwinAgent.
        """
        super().__init__(**kwargs)
        print(f"ValvePerceptionAgent '{self.agent_id}' initialized.")
