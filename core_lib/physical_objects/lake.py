from core_lib.core.interfaces import PhysicalObjectInterface, State

class Lake(PhysicalObjectInterface):
    """
    Represents a lake or reservoir with a fixed surface area.

    This model accounts for inflow, outflow, and evaporation to track the volume
    and water level of the lake. The outflow is not calculated by this model,
    but is determined by the downstream component and set by the simulation harness.

    State Variables:
        - volume (float): The current volume of water in the lake (m^3).
        - water_level (float): The current water level (m), calculated from volume and surface area.
        - outflow (float): The outflow from the lake for the current step (m^3/s). This is set by the harness.

    Parameters:
        - surface_area (float): The surface area of the lake (m^2).
        - max_volume (float): The maximum storage capacity of the lake (m^3).
        - evaporation_rate_m_per_s (float): The rate of evaporation in meters per second.
    """

    def __init__(self, name: str, initial_state: State, parameters: dict):
        super().__init__(name, initial_state, parameters)
        self.surface_area = self._params['surface_area']
        self.max_volume = self._params['max_volume']
        self.evaporation_rate_m_per_s = self._params.get('evaporation_rate_m_per_s', 0) # Default to 0 if not provided

        # Ensure initial state has required keys
        self._state.setdefault('outflow', 0.0)

    def step(self, action: any, dt: float) -> State:
        """
        Advances the lake simulation for one time step.
        """
        inflow = self._inflow

        # Evaporation is a loss of volume from the surface
        evaporation_volume_per_second = self.evaporation_rate_m_per_s * self.surface_area

        # The outflow for the step is determined by the downstream component's request,
        # which is calculated by the harness in a prior pass and stored in the state.
        # We must ensure the requested outflow is physically possible.
        available_volume = self._state['volume']
        max_possible_outflow = available_volume / dt if dt > 0 else 0

        # The harness calculates prospective outflow and provides it in the action.
        # We must ensure the requested outflow is physically possible.
        outflow = action.get('outflow', 0)
        outflow = min(outflow, max_possible_outflow)
        self._state['outflow'] = outflow

        # Update volume with the mass balance equation
        delta_volume = (inflow - outflow - evaporation_volume_per_second) * dt
        self._state['volume'] += delta_volume

        # Enforce physical constraints
        self._state['volume'] = max(0, min(self._state['volume'], self.max_volume))

        # Update water level based on the new volume
        self._state['water_level'] = self._state['volume'] / self.surface_area if self.surface_area > 0 else 0

        return self.get_state()

    @property
    def is_stateful(self) -> bool:
        return True
