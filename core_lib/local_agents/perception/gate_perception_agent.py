"""
Perception agent for a gate.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

class GatePerceptionAgent(DigitalTwinAgent):
    """
    A perception agent specifically for a gate, acting as its digital twin.

    This agent is responsible for reading the state of a gate simulation model,
    potentially enhancing it, and publishing it for other agents. It is a
    specialization of the DigitalTwinAgent.
    """
    def __init__(self, **kwargs):
        """
        Initializes the GatePerceptionAgent.
        Inherits the base functionality from DigitalTwinAgent.
        """
        super().__init__(**kwargs)
        print(f"GatePerceptionAgent '{self.agent_id}' initialized.")
