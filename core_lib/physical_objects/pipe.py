"""
Simulation model for a Pipe.
"""
import math
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from typing import Dict, Any

class Pipe(PhysicalObjectInterface):
    """
    Represents a pipe, which transports water between two points.
    This model uses the Darcy-Weisbach equation to calculate flow.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self._state.setdefault('head_loss', 0)

        g = 9.81
        area = (math.pi / 4) * (self._params['diameter'] ** 2)
        self.flow_coefficient = area * math.sqrt(2 * g * self._params['diameter'] / (self._params['friction_factor'] * self._params['length']))

        print(f"Pipe '{self.name}' created with flow coefficient {self.flow_coefficient:.4f}.")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Calculates the flow through the pipe for one time step.
        """
        if self._inflow > 0:
            # If there's an active inflow (e.g. from a pump), that dictates the flow.
            outflow = self._inflow
            self._state['head_loss'] = (outflow / self.flow_coefficient)**2 if self.flow_coefficient > 0 else 0
        else:
            # Otherwise, calculate flow from head difference.
            upstream_head = action.get('upstream_head', 0)
            downstream_head = action.get('downstream_head', 0)
            head_difference = upstream_head - downstream_head

            if head_difference > 0:
                outflow = self.flow_coefficient * math.sqrt(head_difference)
                self._state['head_loss'] = head_difference
            else:
                outflow = 0
                self._state['head_loss'] = 0

        self._state['outflow'] = outflow

        return self.get_state()
