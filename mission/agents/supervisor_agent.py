from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class SupervisorAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus,
                 power_target_topic: str, initial_target_mw: float):
        super().__init__(agent_id)
        self.bus = message_bus
        self.power_target_topic = power_target_topic
        self.initial_target_mw = initial_target_mw
        self._sent = False

    def run(self, current_time: float):
        if not self._sent and current_time >= 0:
            self.bus.publish(self.power_target_topic, {'target_mw': self.initial_target_mw})
            self._sent = True
