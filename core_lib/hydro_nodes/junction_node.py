from .base_node import HydroNode
from typing import List, Tuple

class JunctionNode(HydroNode):
    """
    Represents a junction where multiple reaches converge or diverge.

    This node enforces two physical laws:
    1.  Continuity: The sum of all flows entering the junction equals the sum of all flows leaving.
    2.  Common Head: The water level (head) is the same for all connected points at the junction.
    """
    def __init__(self, name: str):
        super().__init__(name)
        # A junction can connect multiple upstream and downstream reaches.
        self.in_connections: List[Tuple[object, int]] = []
        self.out_connections: List[Tuple[object, int]] = []

    def add_in_connection(self, obj, idx: int = -1):
        """Adds a connection that flows INTO the junction."""
        self.in_connections.append((obj, idx))

    def add_out_connection(self, obj, idx: int = 0):
        """Adds a connection that flows OUT of the junction."""
        self.out_connections.append((obj, idx))

    def get_equations(self, dt: float, theta: float) -> list:
        """
        Returns the linearized equations for the junction.
        """
        all_connections = self.in_connections + self.out_connections
        if len(all_connections) < 2:
            # A junction needs at least two connections to be meaningful.
            return []

        equations = []

        # --- Equation 1: Continuity ---
        # Sum of inflows - Sum of outflows = 0
        # Linearized: Sum(d_inflows) - Sum(d_outflows) = -(Sum(Q_in_n) - Sum(Q_out_n))
        eq_continuity = {}
        rhs_continuity = 0.0

        for obj, idx in self.in_connections:
            eq_continuity[(obj, 'Q', idx)] = 1.0
            rhs_continuity -= obj.Q[idx]

        for obj, idx in self.out_connections:
            eq_continuity[(obj, 'Q', idx)] = -1.0
            rhs_continuity += obj.Q[idx]

        eq_continuity['RHS'] = rhs_continuity
        equations.append(eq_continuity)

        # --- Head Equations (N-1 equations) ---
        # H_1 = H_2, H_2 = H_3, ...
        # This creates N-1 equations to ensure all heads are equal.
        first_conn_obj, first_conn_idx = all_connections[0]

        for i in range(1, len(all_connections)):
            next_conn_obj, next_conn_idx = all_connections[i]

            h_first = first_conn_obj.H[first_conn_idx]
            h_next = next_conn_obj.H[next_conn_idx]

            eq_head = {
                (first_conn_obj, 'H', first_conn_idx): 1.0,
                (next_conn_obj, 'H', next_conn_idx): -1.0,
                'RHS': -(h_first - h_next)
            }
            equations.append(eq_head)

        return equations
