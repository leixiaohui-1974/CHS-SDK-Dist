from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus


class ConstantInflowAgent(Agent):
    """
    A simple agent that provides a constant inflow to a target component.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.target_component_id = kwargs['target_component_id']
        self.inflow_rate = kwargs['inflow_rate']
        self.inflow_topic = f"inflow/{self.target_component_id}"


    def run(self, current_time: float):
        message = {'inflow_rate': self.inflow_rate}
        self.message_bus.publish(self.inflow_topic, message)
