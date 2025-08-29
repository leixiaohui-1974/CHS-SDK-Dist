import logging
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class FailureInjectionAgent(Agent):
    """Issues a shutdown command at a specific time."""
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = kwargs['target_topic']
        self.time = kwargs['failure_time']
        self.fault_injected = False
    def run(self, current_time: float):
        if not self.fault_injected and current_time >= self.time:
            logging.critical(f"[{self.agent_id}] Injecting failure at time {current_time:.2f}s on topic {self.topic}")
            self.bus.publish(self.topic, {'shutdown': True})
            self.fault_injected = True
