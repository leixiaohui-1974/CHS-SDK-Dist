"""
An agent that simulates downstream water demand.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class WaterUseAgent(Agent):
    """
    Simulates time-varying water demand from a downstream user (e.g., city, farm).
    It publishes control signals to a supply gate based on a predefined daily pattern.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, supply_gate_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.supply_gate_topic = supply_gate_topic

    def run(self, current_time: float):
        """
        Determines the water demand based on the time of day and publishes a control signal.
        """
        # Simulate a daily pattern: higher demand during the day, lower at night.
        hour_of_day = (current_time / 3600) % 24

        if 7 <= hour_of_day < 19:
            # Daytime: high demand
            target_opening = 0.8 # 80% open
        else:
            # Nighttime: low demand
            target_opening = 0.2 # 20% open

        message = {'control_signal': target_opening, 'sender': self.agent_id}
        self.bus.publish(self.supply_gate_topic, message)
        # print(f"[{self.agent_id}] Time: {hour_of_day:.1f}h, setting supply gate to {target_opening*100}%.")
