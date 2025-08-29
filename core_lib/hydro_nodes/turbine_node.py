import numpy as np
from .base_node import HydroNode

class TurbineNode(HydroNode):
    """
    Represents a hydropower turbine.

    This is a simplified placeholder model that treats the turbine as an energy-dissipating
    orifice, similar to a gate. A real model would use complex performance curves.
    """
    g = 9.81  # Gravity

    def __init__(self, name: str, equivalent_area: float, discharge_coeff: float = 0.9):
        """
        Initializes the TurbineNode.

        Args:
            name (str): The name of the turbine.
            equivalent_area (float): The equivalent flow area of the turbine (m^2).
            discharge_coeff (float): The discharge coefficient.
        """
        super().__init__(name)
        self.flow_area = equivalent_area
        self.discharge_coeff = discharge_coeff
        self.is_on = True

    def get_equations(self, dt: float, theta: float) -> list:
        """
        Returns the linearized equations for the turbine.
        """
        if not self.upstream_obj or not self.downstream_obj:
            raise RuntimeError(f"TurbineNode '{self.name}' is not linked to reaches.")

        H_up = self.upstream_obj.H[self.upstream_idx]
        Q_up = self.upstream_obj.Q[self.upstream_idx]
        H_down = self.downstream_obj.H[self.downstream_idx]
        Q_down = self.downstream_obj.Q[self.downstream_idx]

        flow_area = self.flow_area if self.is_on else 0.0

        # Equation 1: Continuity Q_up = Q_down
        eq1 = {
            (self.upstream_obj, 'Q', self.upstream_idx): 1.0,
            (self.downstream_obj, 'Q', self.downstream_idx): -1.0,
            'RHS': -(Q_up - Q_down)
        }

        # Equation 2: Orifice Flow Hydraulics
        head_diff = H_up - H_down
        if head_diff <= 0 or flow_area < 1e-6:
            # No flow or turbine is off
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
