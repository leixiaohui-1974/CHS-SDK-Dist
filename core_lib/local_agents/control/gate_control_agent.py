"""
Control agent for a gate.
"""
from core_lib.local_agents.control.local_control_agent import LocalControlAgent

class GateControlAgent(LocalControlAgent):
    """
    A control agent specifically for managing a single gate.

    This agent is a specialization of the LocalControlAgent, tailored to
    subscribe to relevant gate state topics, compute necessary adjustments
    (e.g., opening, closing), and publish control commands for the gate.
    """
    def __init__(self, **kwargs):
        """
        Initializes the GateControlAgent.
        Inherits the base functionality from LocalControlAgent.
        """
        super().__init__(**kwargs)
        print(f"GateControlAgent '{self.agent_id}' initialized.")
