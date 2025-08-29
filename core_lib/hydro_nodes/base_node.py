from abc import ABC, abstractmethod
import numpy as np

class HydroNode(ABC):
    """
    Abstract base class for a hydraulic structure node in the network.

    A node represents a point connection between two reaches (or a boundary condition).
    It provides a set of linear equations that describe its hydraulic behavior,
    connecting the variables (H, Q) of the upstream point to the downstream point.
    """

    def __init__(self, name: str):
        self.name = name
        # Pointers to the upstream and downstream reaches/nodes will be set by the solver
        self.upstream_obj = None
        self.downstream_obj = None
        # Indices of the specific points being connected
        self.upstream_idx = -1 # Typically the last point of the upstream reach
        self.downstream_idx = 0 # Typically the first point of the downstream reach

    def link_to_reaches(self, up_obj, down_obj):
        """Sets the upstream and downstream objects this node connects."""
        self.upstream_obj = up_obj
        self.downstream_obj = down_obj

    @abstractmethod
    def get_equations(self, dt: float, theta: float) -> list:
        """
        Returns the linearized hydraulic equations for this node.

        Each equation is represented as a dictionary mapping (object, variable, index)
        tuples to coefficients, plus a RHS value. This is a flexible way to build
        the global matrix.

        Example for one equation:
        {
            (up_obj, 'H', -1): coeff1,
            (up_obj, 'Q', -1): coeff2,
            (down_obj, 'H', 0): coeff3,
            (down_obj, 'Q', 0): coeff4,
            'RHS': value
        }
        """
        pass

    def update_state(self, dH, dQ):
        """
        Updates the internal state of the node, if any.
        Most simple nodes are stateless.
        """
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"
