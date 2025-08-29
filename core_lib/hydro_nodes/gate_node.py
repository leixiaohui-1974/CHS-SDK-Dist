import numpy as np
from .base_node import HydroNode

class GateNode(HydroNode):
    """
    Represents a gate structure connecting two reaches.

    The gate's behavior is defined by two equations:
    1. Continuity: Q_up = Q_down
    2. Hydraulics: A linearized orifice/weir equation relating flow to head difference.
    """
    g = 9.81  # Gravity

    def __init__(self, name: str, width: float, discharge_coeff: float = 0.62):
        """
        Initializes the GateNode.

        Args:
            name (str): The name of the gate.
            width (float): The width of the gate opening in meters.
            discharge_coeff (float): The discharge coefficient (Cd).
        """
        super().__init__(name)
        self.width = width
        self.discharge_coeff = discharge_coeff
        # The gate opening can be controlled externally, e.g., by a control agent
        self.opening = 1.0  # Default to fully open, can be changed during simulation
        self.flow_area = self.width * self.opening

    def set_opening(self, opening: float):
        """Sets the gate opening (as a fraction from 0.0 to 1.0)."""
        self.opening = np.clip(opening, 0.0, 1.0)
        self.flow_area = self.width * self.opening

    def get_equations(self, dt: float, theta: float) -> list:
        """
        Returns the linearized equations for the gate.
        """
        if not self.upstream_obj or not self.downstream_obj:
            raise RuntimeError(f"GateNode '{self.name}' is not linked to reaches.")

        # Get the current state variables from the linked reaches
        H_up = self.upstream_obj.H[self.upstream_idx]
        Q_up = self.upstream_obj.Q[self.upstream_idx]
        H_down = self.downstream_obj.H[self.downstream_idx]
        Q_down = self.downstream_obj.Q[self.downstream_idx]

        # --- Equation 1: Continuity Q_up = Q_down ---
        # Linearized form: 1*dQ_up - 1*dQ_down = -(Q_up_n - Q_down_n)
        eq1 = {
            (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
            (self.downstream_obj, 'Q', self.downstream_idx): -1.0,
            'RHS': -(Q_up - Q_down)
        }

        # --- Equation 2: Orifice Flow Hydraulics ---
        # Q = A * Cd * sqrt(2*g*(H_up - H_down))
        # Let f(H_up, H_down) = Q. We linearize:
        # dQ - (df/dH_up)*dH_up - (df/dH_down)*dH_down = -(Q_n - f(H_up_n, H_down_n))
        head_diff = H_up - H_down
        if head_diff <= 0 or self.flow_area < 1e-6:
            # No flow or gate is closed, simplified equation: Q = 0
            # Linearized: 1*dQ = -Q_n
            eq2 = {
                (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
                'RHS': -Q_up
            }
        else:
            sqrt_term = np.sqrt(2 * self.g * head_diff)
            Q_calc = self.flow_area * self.discharge_coeff * sqrt_term

            # Partial derivatives for linearization
            # df/dH_up = A*Cd*sqrt(2g) * (1/2) * (H_up-H_down)^(-1/2)
            # df/dH_down = -df/dH_up
            common_term = self.flow_area * self.discharge_coeff * np.sqrt(2 * self.g)
            dF_dHead = common_term * 0.5 / np.sqrt(head_diff)

            eq2 = {
                (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
                (self.upstream_obj, 'H', self.upstream_idx): -dF_dHead,
                (self.downstream_obj, 'H', self.downstream_idx): dF_dHead,
                'RHS': -(Q_up - Q_calc)
            }

        return [eq1, eq2]
