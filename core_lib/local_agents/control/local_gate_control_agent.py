import logging
from typing import Dict, Any, Optional
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class LocalGateControlAgent(Agent):
    """Controls a gate based on a dynamic setpoint and can be shut down."""
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.action_topic = kwargs['action_topic']
        self.setpoint = kwargs.get('setpoint') or kwargs.get('initial_setpoint') # support both
        self.state_subscription_topic = kwargs.get('subscribed_topic') or kwargs.get('state_subscription_topic')
        self.command_subscription_topic = kwargs.get('command_subscription_topic')
        self.shutdown_topic = kwargs.get('shutdown_topic')

        self.is_active = True
        self.gate_is_open = False
        logging.info(f"[{self.agent_id}] Initialized with setpoint {self.setpoint:.2f}m")
        self.bus.subscribe(self.state_subscription_topic, self.handle_state_message)
        if self.command_subscription_topic:
            self.bus.subscribe(self.command_subscription_topic, self.handle_command_message)
        if self.shutdown_topic:
            self.bus.subscribe(self.shutdown_topic, self.handle_shutdown_message)

    def handle_state_message(self, message: Dict[str, Any]):
        if not self.is_active: return
        water_level = message.get('water_level')
        if water_level is None: return
        if water_level > self.setpoint and not self.gate_is_open:
            logging.info(f"[{self.agent_id}] Level {water_level:.2f}m > setpoint {self.setpoint:.2f}m. Opening gate.")
            self.bus.publish(self.action_topic, {'opening': 1.0})
            self.gate_is_open = True
        elif water_level <= self.setpoint and self.gate_is_open:
            logging.info(f"[{self.agent_id}] Level {water_level:.2f}m <= setpoint {self.setpoint:.2f}m. Closing gate.")
            self.bus.publish(self.action_topic, {'opening': 0.0})
            self.gate_is_open = False

    def handle_command_message(self, message: Dict[str, Any]):
        if not self.is_active: return
        new_setpoint = message.get('setpoint')
        if new_setpoint is not None:
            logging.info(f"[{self.agent_id}] Received new setpoint command: {new_setpoint:.2f}m. Previous was {self.setpoint:.2f}m.")
            self.setpoint = new_setpoint

    def handle_shutdown_message(self, message: Dict[str, Any]):
        if message.get('shutdown') == True:
            logging.warning(f"[{self.agent_id}] Received SHUTDOWN command. Ceasing operations.")
            self.is_active = False

    def run(self, current_time: float): pass
