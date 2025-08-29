from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class HydropowerControlAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus, turbine_action_topics: list,
                 power_target_topic: str, grid_limit_topic: str, head_m: float):
        super().__init__(agent_id)
        self.bus = message_bus
        self.turbine_action_topics = turbine_action_topics
        self.power_target_topic = power_target_topic
        self.grid_limit_topic = grid_limit_topic
        self.head_m = head_m
        self.power_target_mw = 0
        self.grid_limit_mw = float('inf')
        self.bus.subscribe(self.power_target_topic, self.handle_power_target)
        self.bus.subscribe(self.grid_limit_topic, self.handle_grid_limit)

    def handle_power_target(self, message):
        self.power_target_mw = message['target_mw']

    def handle_grid_limit(self, message):
        self.grid_limit_mw = message['limit_mw']

    def run(self, current_time: float):
        effective_target_mw = min(self.power_target_mw, self.grid_limit_mw)
        num_turbines = len(self.turbine_action_topics)
        flow_per_turbine = self.calculate_flow_for_power(effective_target_mw / num_turbines, self.head_m)
        for topic in self.turbine_action_topics:
            self.bus.publish(topic, {'flow_rate': flow_per_turbine})

    def calculate_flow_for_power(self, power_mw, head_m):
        # Simplified calculation, assuming constant efficiency
        g = 9.81  # gravity
        rho = 1000  # water density
        efficiency = 0.9
        if head_m <= 0:
            return 0
        power_watts = power_mw * 1e6
        flow = power_watts / (rho * g * head_m * efficiency)
        return flow
