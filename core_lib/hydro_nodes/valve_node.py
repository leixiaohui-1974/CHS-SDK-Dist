import numpy as np
from .base_node import HydroNode

class ValveNode(HydroNode):
    """
    Represents a valve in a pipe, controlling flow.

    This model is functionally similar to a GateNode and uses a linearized
    orifice equation to relate flow to head difference.
    """
    g = 9.81  # Gravity

    def __init__(self, name: str, diameter: float, discharge_coeff: float = 0.8):
        """
        Initializes the ValveNode.

        Args:
            name (str): The name of the valve.
            diameter (float): The diameter of the valve opening in meters.
            discharge_coeff (float): The discharge coefficient (Cv).
        """
        super().__init__(name)
        self.diameter = diameter
        self.max_flow_area = np.pi * (diameter / 2)**2
        self.discharge_coeff = discharge_coeff
        # The valve opening can be controlled externally
        self.opening = 1.0  # Fraction from 0.0 to 1.0

    def set_opening(self, opening: float):
        """Sets the valve opening (as a fraction from 0.0 to 1.0)."""
        self.opening = np.clip(opening, 0.0, 1.0)

    def get_equations(self, dt: float, theta: float) -> list:
        """
        Returns the linearized equations for the valve.
        """
        if not self.upstream_obj or not self.downstream_obj:
            raise RuntimeError(f"ValveNode '{self.name}' is not linked to reaches.")

        H_up = self.upstream_obj.H[self.upstream_idx]
        Q_up = self.upstream_obj.Q[self.upstream_idx]
        H_down = self.downstream_obj.H[self.downstream_idx]
        Q_down = self.downstream_obj.Q[self.downstream_idx]

        flow_area = self.max_flow_area * self.opening

        # Equation 1: Continuity Q_up = Q_down
        eq1 = {
            (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
            (self.downstream_obj, 'Q', self.downstream_idx): -1.0,
            'RHS': -(Q_up - Q_down)
        }

        # Equation 2: Orifice Flow Hydraulics
        head_diff = H_up - H_down
        if head_diff <= 0 or flow_area < 1e-6:
            # No flow or valve is closed
            eq2 = {
                (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
                'RHS': -Q_up
            }
        else:
            sqrt_term = np.sqrt(2 * self.g * head_diff)
            Q_calc = flow_area * self.discharge_coeff * sqrt_term

            common_term = flow_area * self.discharge_coeff * np.sqrt(2 * self.g)
            dF_dHead = common_term * 0.5 / np.sqrt(head_diff)

            eq2 = {
                (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
                (self.upstream_obj, 'H', self.upstream_idx): -dF_dHead,
                (self.downstream_obj, 'H', self.downstream_idx): dF_dHead,
                'RHS': -(Q_up - Q_calc)
            }

        return [eq1, eq2]
