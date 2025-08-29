import logging
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class SupervisoryAgent(Agent):
    """Monitors two reservoirs and takes corrective action if they deviate."""
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.state_topic_A = kwargs['state_topic_A']
        self.state_topic_B = kwargs['state_topic_B']
        self.command_topic_B = kwargs['command_topic_B']
        self.threshold = kwargs['deviation_threshold']
        self.corrective_setpoint = kwargs['corrective_setpoint']
        self.level_A, self.level_B = None, None
        self.corrective_action_taken = False
        self.bus.subscribe(self.state_topic_A, self.handle_state_A)
        self.bus.subscribe(self.state_topic_B, self.handle_state_B)

    def handle_state_A(self, msg): self.level_A = msg.get('water_level')
    def handle_state_B(self, msg): self.level_B = msg.get('water_level')

    def run(self, current_time: float):
        if self.corrective_action_taken or self.level_A is None or self.level_B is None:
            return
        deviation = abs(self.level_A - self.level_B)
        if deviation > self.threshold:
            logging.warning(f"[{self.agent_id}] Deviation ({deviation:.2f}m) exceeds threshold ({self.threshold:.2f}m). Taking corrective action.")
            command_message = {'setpoint': self.corrective_setpoint}
            self.bus.publish(self.command_topic_B, command_message)
            self.corrective_action_taken = True
