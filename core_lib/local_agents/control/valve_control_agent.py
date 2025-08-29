"""
Control agent for a valve.
"""
from core_lib.local_agents.control.local_control_agent import LocalControlAgent

class ValveControlAgent(LocalControlAgent):
    """
    A control agent specifically for managing a single valve.

    This agent is a specialization of the LocalControlAgent, tailored to
    subscribe to relevant valve state topics, compute necessary adjustments,
    and publish control commands for the valve.
    """
    def __init__(self, **kwargs):
        """
        Initializes the ValveControlAgent.
        Inherits the base functionality from LocalControlAgent.
        """
        super().__init__(**kwargs)
        print(f"ValveControlAgent '{self.agent_id}' initialized.")
