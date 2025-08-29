"""
Simulation model for a Reservoir.
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class Reservoir(PhysicalObjectInterface):
    """
    Represents a reservoir, a fundamental object in a water system.
    Its state is determined by the balance of inflows and outflows.
    It can receive physical inflow from upstream components and data-driven
    inflow (e.g., rainfall, observed data) from the message bus.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, inflow_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)  # Ensure outflow is in the state
        if 'water_level' in self._state and 'volume' not in self._state:
            surface_area = self._params.get('surface_area', 1e6)
            self._state['volume'] = self._state['water_level'] * surface_area
        self.bus = message_bus
        self.inflow_topic = inflow_topic
        self.data_inflow = 0.0 # To store inflow from messages for the current step

        if self.bus and self.inflow_topic:
            self.bus.subscribe(self.inflow_topic, self.handle_inflow_message)
            print(f"Reservoir '{self.name}' subscribed to data inflow topic '{self.inflow_topic}'.")

        print(f"Reservoir '{self.name}' created with initial state {self._state}.")

    def handle_inflow_message(self, message: Message):
        """Callback to handle incoming data-driven inflow messages."""
        inflow_value = message.get('inflow_rate')  # Corrected key
        if isinstance(inflow_value, (int, float)):
            self.data_inflow += inflow_value

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Simulates the reservoir's change over a single time step.
        """
        # Physical inflow from upstream components is set by the harness via set_inflow()
        physical_inflow = self._inflow

        # Total inflow is the sum of physical and data-driven inflows
        total_inflow = physical_inflow + self.data_inflow

        # The harness calculates the required outflow from downstream demand and provides it in the action
        outflow = action.get('outflow', 0)

        current_volume = self._state.get('volume', 0)
        surface_area = self._params.get('surface_area', 1e6) # m^2

        # Water balance equation
        delta_volume = (total_inflow - outflow) * dt
        new_volume = current_volume + delta_volume

        self._state['volume'] = new_volume
        self._state['water_level'] = new_volume / surface_area # Simplified relationship

        # The outflow is already set by the harness, so we just keep it.

        # Reset the data-driven inflow for the next step
        self.data_inflow = 0.0

        return self._state

    @property
    def is_stateful(self) -> bool:
        return True
