"""
An agent for controlling a pump station to meet a flow demand.
"""
import math
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.pump import PumpStation


class PumpControlAgent(Agent):
    """
    An agent that controls a PumpStation to meet a specified flow demand.
    It listens for demand messages and turns individual pumps on or off to
    collectively meet the target flow rate.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, pump_station: PumpStation,
                 demand_topic: str, control_topic_prefix: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.pump_station = pump_station
        self.demand_topic = demand_topic
        self.control_topic_prefix = control_topic_prefix
        self.pumps = self.pump_station.pumps

        # Assume all pumps have the same flow rate for simplicity
        self.pump_flow_rate = self.pumps[0].get_parameters().get('max_flow_rate', 1.0) if self.pumps else 0

        # Subscribe to the demand topic
        self.bus.subscribe(self.demand_topic, self.handle_demand_message)
        self.current_demand = 0.0
        print(f"Agent '{self.agent_id}' created and subscribed to demand topic '{self.demand_topic}'.")

    def handle_demand_message(self, message: Message):
        """Callback to update the flow demand when a message is received."""
        demand = message.get('value')
        if isinstance(demand, (int, float)):
            self.current_demand = demand
            print(f"[{self.agent_id}] Received new flow demand: {self.current_demand:.2f} m^3/s")

    async def run(self):
        """
        The main loop for the agent. In a real-time system, this would run
        continuously. For this simulation, we will call the logic manually.
        """
        pass

    def execute_control_logic(self):
        """
        Contains the core logic for the agent. It calculates the number of pumps
        needed and sends control signals to them via the message bus.
        """
        if not self.pumps or self.pump_flow_rate <= 0:
            return

        # Calculate the number of pumps required to meet the current demand.
        # Use ceiling to ensure demand is met or exceeded.
        num_pumps_needed = math.ceil(self.current_demand / self.pump_flow_rate)

        # Ensure the number of pumps does not exceed the available pumps.
        num_pumps_needed = min(num_pumps_needed, len(self.pumps))

        print(f"[{self.agent_id}] Demand is {self.current_demand:.2f} m^3/s. Activating {num_pumps_needed} of {len(self.pumps)} pumps.")

        # Publish control signals to each pump's specific topic.
        for i, pump in enumerate(self.pumps):
            control_signal = 1 if i < num_pumps_needed else 0
            topic = f"{self.control_topic_prefix}.{pump.name}"
            # The pump's handler expects a 'control_signal' key in the message dict.
            message = {'control_signal': control_signal, 'sender': self.agent_id}
            self.bus.publish(topic, message)
            # print(f"[{self.agent_id}] Sending control_signal={control_signal} to {pump.name} on topic {topic}")
