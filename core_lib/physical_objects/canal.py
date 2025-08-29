import math
from typing import Optional

from core_lib.core.interfaces import PhysicalObjectInterface, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message


class Canal(PhysicalObjectInterface):
    """
    Represents a canal with a trapezoidal cross-section using Manning's equation for flow.

    This model simulates the water flow and volume changes in a canal segment.
    The outflow is calculated based on the hydraulic properties derived from the
    current water level.

    It can now also subscribe to a message bus topic to receive additional,
    data-driven inflow (e.g., from a rainfall forecast).

    State Variables:
        - volume (float): The current volume of water in the canal (m^3).
        - water_level (float): The current water level in the canal (m).
        - outflow (float): The calculated outflow from the canal for the current step (m^3/s).

    Parameters:
        - bottom_width (float): The width of the bottom of the canal (m).
        - length (float): The length of the canal segment (m).
        - slope (float): The longitudinal slope of the canal bed (dimensionless).
        - side_slope_z (float): The slope of the canal sides (z in z:1, horizontal:vertical).
        - manning_n (float): Manning's roughness coefficient.
    """

    def __init__(self, name: str, initial_state: State, parameters: dict,
                 message_bus: Optional[MessageBus] = None, inflow_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        # Parameters are accessed via self._params, but can be copied to attributes for convenience
        self.bottom_width = self._params['bottom_width']
        self.length = self._params['length']
        self.slope = self._params['slope']
        self.side_slope_z = self._params['side_slope_z']
        self.manning_n = self._params['manning_n']

        # For data-driven inflow from the message bus
        self.bus = message_bus
        self.inflow_topic = inflow_topic
        self.data_inflow = 0.0

        if self.bus and self.inflow_topic:
            self.bus.subscribe(self.inflow_topic, self.handle_inflow_message)
            print(f"Canal '{self.name}' subscribed to data inflow topic '{self.inflow_topic}'.")

    def handle_inflow_message(self, message: Message):
        """Callback to handle incoming data-driven inflow messages."""
        inflow_rate = message.get('inflow_rate')
        if inflow_rate is not None:
            self.data_inflow = float(inflow_rate)
        else:
            # Reset if a message without the key is sent, or handle as needed
            self.data_inflow = 0.0

    def step(self, action: any, dt: float) -> State:
        """
        Advances the canal simulation for one time step.
        """
        # Physical inflow is set by the harness from upstream components
        physical_inflow = self._inflow

        # Total inflow is the sum of physical inflow and data-driven inflow
        inflow = physical_inflow + self.data_inflow

        # Approximate water level from volume. For a trapezoid, this is more complex.
        # V = L * (b*y + z*y^2) -> z*y^2 + b*y - V/L = 0
        # Solving the quadratic equation for y (water_level)
        a = self.side_slope_z
        b = self.bottom_width
        c = -self._state['volume'] / self.length if self.length > 0 else 0

        if a == 0:  # Rectangular channel case
            water_level = self._state['volume'] / (self.bottom_width * self.length) if (self.bottom_width * self.length) > 0 else 0
        else:
            # Quadratic formula: y = (-b + sqrt(b^2 - 4ac)) / 2a
            discriminant = b**2 - 4 * a * c
            if discriminant >= 0:
                water_level = (-b + math.sqrt(discriminant)) / (2 * a)
            else:
                water_level = 0

        self._state['water_level'] = water_level

        # If the harness provides an outflow value (for stateful components), use it.
        # Otherwise, calculate it using Manning's equation (for open-ended components).
        if action and action.get('outflow') is not None:
            outflow = action['outflow']
        else:
            # Calculate hydraulic properties for a trapezoidal channel
            if water_level > 0:
                area = (self.bottom_width + self.side_slope_z * water_level) * water_level
                wetted_perimeter = self.bottom_width + 2 * water_level * math.sqrt(1 + self.side_slope_z**2)
                hydraulic_radius = area / wetted_perimeter if wetted_perimeter > 0 else 0
            else:
                area = 0
                hydraulic_radius = 0

            # Calculate outflow using Manning's equation
            # Q = (1/n) * A * R_h^(2/3) * S^(1/2)
            outflow = (1 / self.manning_n) * area * (hydraulic_radius**(2/3)) * (self.slope**0.5) if area > 0 else 0

        self._state['outflow'] = outflow

        # Update volume based on inflow and outflow using mass balance
        self._state['volume'] += (inflow - outflow) * dt
        self._state['volume'] = max(0, self._state['volume']) # Volume cannot be negative

        return self.get_state()

    @property
    def is_stateful(self) -> bool:
        """A canal stores water, so it is a stateful component."""
        return True
