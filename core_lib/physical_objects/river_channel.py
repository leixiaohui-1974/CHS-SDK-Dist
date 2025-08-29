"""
Simulation model for a River Channel.
"""
from typing import Dict, Any
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters

class RiverChannel(PhysicalObjectInterface):
    """
    Represents a segment of a river using a linear reservoir model.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        print(f"RiverChannel '{self.name}' created with initial state {self._state}.")

    def step(self, action: Any, dt: float) -> State:
        """
        Simulates the river channel's change over a single time step.
        """
        inflow = self._inflow
        current_volume = self._state.get('volume', 0)

        # Outflow is proportional to storage (k * V)
        k = self._params.get('k', 0.0001) # Storage coefficient
        outflow = k * current_volume
        self._state['outflow'] = outflow

        # Water balance equation
        delta_volume = (inflow - outflow) * dt
        new_volume = current_volume + delta_volume
        self._state['volume'] = new_volume

        return self.get_state()

    @property
    def is_stateful(self) -> bool:
        return True
