from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class InflowAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus,
                 inflow_topic: str, inflow_rate: float):
        super().__init__(agent_id)
        self.bus = message_bus
        self.inflow_topic = inflow_topic
        self.inflow_rate = inflow_rate

    def run(self, current_time: float):
        # Publish inflow at every step
        self.bus.publish(self.inflow_topic, {'inflow_rate': self.inflow_rate})
