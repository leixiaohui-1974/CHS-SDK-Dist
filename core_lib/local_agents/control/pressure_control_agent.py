"""
An agent for controlling a pump station to maintain pressure in a pipe network.
"""
import math
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.pump import PumpStation

class PressureControlAgent(Agent):
    """
    An agent that controls a PumpStation to maintain pressure within a target range.
    It implements a simple hysteresis (bang-bang) control logic.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, pump_station: PumpStation,
                 pressure_source_component: object, control_topic_prefix: str, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self.pump_station = pump_station
        self.pressure_source = pressure_source_component
        self.control_topic_prefix = control_topic_prefix
        self.config = config

        # Control parameters
        self.min_pressure = self.config['min_pressure']
        self.max_pressure = self.config['max_pressure']

        self.pumps = self.pump_station.pumps
        self.num_pumps = len(self.pumps)
        self.active_pumps = 0

    def execute_control_logic(self):
        """
        Executes the pressure control logic for one time step.
        """
        # In a real system, this would come from a sensor message.
        # Here, we read it directly from the component's state for simplicity.
        # We assume pressure is measured at the downstream end of the component.
        # For a pipe, this is equivalent to the intermediate head.
        current_pressure = self.pressure_source.get_state().get('downstream_head', 0)

        # Hysteresis control logic
        if current_pressure < self.min_pressure:
            # If pressure is too low, turn on one more pump (if available)
            self.active_pumps = min(self.active_pumps + 1, self.num_pumps)
            print(f"[{self.agent_id}] Pressure low ({current_pressure:.2f} < {self.min_pressure:.2f}). Activating {self.active_pumps} pumps.")
        elif current_pressure > self.max_pressure:
            # If pressure is too high, turn off one pump
            self.active_pumps = max(self.active_pumps - 1, 0)
            print(f"[{self.agent_id}] Pressure high ({current_pressure:.2f} > {self.max_pressure:.2f}). Deactivating to {self.active_pumps} pumps.")
        else:
            # Pressure is within the deadband, do nothing
            pass

        # Publish control signals to each pump
        for i, pump in enumerate(self.pumps):
            control_signal = 1 if i < self.active_pumps else 0
            topic = f"{self.control_topic_prefix}.{pump.name}"
            message = {'control_signal': control_signal, 'sender': self.agent_id}
            self.bus.publish(topic, message)

    async def run(self, current_time: float):
        pass
