import numpy as np
from .base_node import HydroNode

class PumpNode(HydroNode):
    """
    Represents a pump, which adds energy to the flow.

    This is a simplified placeholder model. It assumes a fixed head increase
    and enforces continuity of flow.
    """

    def __init__(self, name: str, fixed_head_increase: float = 10.0):
        """
        Initializes the PumpNode.

        Args:
            name (str): The name of the pump.
            fixed_head_increase (float): The fixed head (pressure) increase in meters.
        """
        super().__init__(name)
        self.head_increase = fixed_head_increase
        self.is_on = True # Pump can be turned on or off

    def get_equations(self, dt: float, theta: float) -> list:
        """
        Returns the linearized equations for the pump.
        """
        if not self.upstream_obj or not self.downstream_obj:
            raise RuntimeError(f"PumpNode '{self.name}' is not linked to reaches.")

        H_up = self.upstream_obj.H[self.upstream_idx]
        Q_up = self.upstream_obj.Q[self.upstream_idx]
        H_down = self.downstream_obj.H[self.downstream_idx]
        Q_down = self.downstream_obj.Q[self.downstream_idx]

        # Equation 1: Continuity Q_up = Q_down
        eq1 = {
            (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
            (self.downstream_obj, 'Q', self.downstream_idx): -1.0,
            'RHS': -(Q_up - Q_down)
        }

        # Equation 2: Head increase H_down = H_up + dH
        # Linearized: dH_down - dH_up = -(H_down_n - H_up_n - dH)
        head_increase = self.head_increase if self.is_on else 0.0

        eq2 = {
            (self.downstream_obj, 'H', self.downstream_idx): 1.0,
            (self.upstream_obj, 'H', self.upstream_idx): -1.0,
            'RHS': -(H_down - H_up - head_increase)
        }

        return [eq1, eq2]
