from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class GridCommunicationAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus, grid_limit_topic: str,
                 rejection_time_s: float, new_limit_mw: float):
        super().__init__(agent_id)
        self.bus = message_bus
        self.grid_limit_topic = grid_limit_topic
        self.rejection_time_s = rejection_time_s
        self.new_limit_mw = new_limit_mw
        self._sent = False

    def run(self, current_time: float):
        if not self._sent and current_time >= self.rejection_time_s:
            self.bus.publish(self.grid_limit_topic, {'limit_mw': self.new_limit_mw})
            self._sent = True
