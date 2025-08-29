"""
A central dispatch agent for global coordination and emergency override.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.reservoir import Reservoir

class CentralDispatcherAgent(Agent):
    """
    A high-level agent that monitors the overall system state and can
    issue overriding commands in emergencies, ensuring global objectives
    (like preventing catastrophic floods) are met.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, reservoir: Reservoir,
                 supply_gate_topic: str, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self.reservoir = reservoir
        self.supply_gate_topic = supply_gate_topic # The gate it can override
        self.config = config

        # The absolute emergency level for the reservoir
        self.emergency_flood_level = self.config['emergency_flood_level']

    def run(self, current_time: float):
        """
        Checks for emergency conditions and issues override commands if necessary.
        """
        current_level = self.reservoir.get_state().get('water_level', 0)

        # Emergency Override Logic
        if current_level > self.emergency_flood_level:
            print(f"\n!!! [{self.agent_id}] EMERGENCY OVERRIDE !!!")
            print(f"    Reservoir level {current_level:.2f}m has breached emergency level {self.emergency_flood_level:.2f}m.")
            print(f"    Forcing downstream supply gate closed to maximize flood discharge capacity.")

            # This is a high-priority message that overrides local agent decisions.
            # In a real system, this might use a separate, high-priority channel
            # or the message itself would have a priority flag. Here, we rely on
            # execution order: the dispatcher runs after local agents and its
            # message will be the last one the gate receives before the physics step.
            override_message = {'control_signal': 0.0, 'sender': self.agent_id}
            self.bus.publish(self.supply_gate_topic, override_message)
