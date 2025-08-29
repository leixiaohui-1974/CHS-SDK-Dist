"""
An agent for controlling a hydropower station with multiple objectives.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.reservoir import Reservoir


class HydropowerStationAgent(Agent):
    """
    An agent that manages a hydropower station with multiple devices and objectives.

    Objectives (in order of priority):
    1. Flood Control: Keep the reservoir level below a critical flood level.
    2. Water Supply: Ensure a minimum downstream supply is met.
    3. Power Generation: Maximize power generation without violating other constraints.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, reservoir: Reservoir,
                 flood_gate_topic: str, supply_gate_topic: str, turbine_gate_topics: list[str],
                 config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self.reservoir = reservoir
        self.flood_gate_topic = flood_gate_topic
        self.supply_gate_topic = supply_gate_topic
        self.turbine_gate_topics = turbine_gate_topics
        self.config = config

        # Subscribe to relevant sensor topics if needed (e.g., power demand)
        # For this example, we'll keep it simple and use fixed demands.

    def execute_control_logic(self):
        """
        The core decision-making logic for the hydropower station.
        """
        # Get current state from the reservoir
        reservoir_state = self.reservoir.get_state()
        current_level = reservoir_state.get('water_level', 0)

        # Get operational parameters from config
        normal_level = self.config['normal_level']
        flood_warning_level = self.config['flood_warning_level']
        # This agent is simplified and controls openings directly based on config.
        min_supply_opening = self.config.get('min_supply_opening', 0.1) # 10% opening to meet supply

        # Initialize control signals
        flood_gate_opening = 0.0
        supply_gate_opening = 0.0
        turbine_gate_openings = [0.0] * len(self.turbine_gate_topics)

        # Decision logic based on priority
        # Priority 1: Flood Control
        if current_level > flood_warning_level:
            print(f"[{self.agent_id}] FLOOD WARNING: Level {current_level:.2f}m > {flood_warning_level:.2f}m. Prioritizing flood control.")
            # Open flood gate fully to release water
            flood_gate_opening = 1.0 # Assuming max opening is 1.0
            # Close turbines to protect them during flood
            turbine_gate_openings = [0.0] * len(self.turbine_gate_topics)
            # Maintain minimum water supply if possible
            supply_gate_opening = min_supply_opening

        # Priority 2 & 3: Normal Operation (Water Supply & Power Gen)
        else:
            print(f"[{self.agent_id}] Normal Operation: Level {current_level:.2f}m. Balancing supply and power.")
            # Keep flood gate closed
            flood_gate_opening = 0.0
            # Meet minimum water supply
            supply_gate_opening = min_supply_opening
            # Use remaining capacity for power generation
            if current_level > normal_level + 0.2: # Only generate max power if level is safely above normal
                 turbine_gate_openings = [0.8] * len(self.turbine_gate_topics) # Reduced from 1.0
            else:
                 turbine_gate_openings = [0.4] * len(self.turbine_gate_topics) # Reduced from 0.5

        # Publish control messages
        self.publish_control_signal(self.flood_gate_topic, flood_gate_opening)
        self.publish_control_signal(self.supply_gate_topic, supply_gate_opening)
        for i, topic in enumerate(self.turbine_gate_topics):
            self.publish_control_signal(topic, turbine_gate_openings[i])

    def publish_control_signal(self, topic: str, signal: float):
        """Helper to publish a control message to the bus."""
        message = {'control_signal': signal, 'sender': self.agent_id}
        self.bus.publish(topic, message)

    async def run(self):
        pass
