import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from core_lib.physical_objects.st_venant_reach import StVenantReach
from core_lib.hydro_nodes.base_node import HydroNode

class NetworkSolver:
    """
    Solves the 1D hydrodynamic equations for a network of reaches and nodes.

    This solver assembles a global system of linearized equations from all
    components in the network and solves it simultaneously for each time step.
    """

    def __init__(self, dt: float, theta: float = 0.6):
        self.dt = dt
        self.theta = theta
        self.components = []
        self.reaches = []
        self.nodes = []
        self.boundary_conditions = []
        self.var_map = {}
        self.num_vars = 0
        self.matrix_A = None
        self.vector_b = None
        print("NetworkSolver initialized.")

    def add_component(self, component):
        """Adds a reach or a node to the network."""
        self.components.append(component)
        if isinstance(component, StVenantReach):
            self.reaches.append(component)
        elif isinstance(component, HydroNode):
            self.nodes.append(component)
        else:
            raise TypeError(f"Unsupported component type: {type(component)}")

    def add_boundary_condition(self, component, var: str, point_idx: int, value_func):
        """
        Adds a boundary condition to the system.

        Args:
            component: The reach object where the BC is applied.
            var (str): The variable to fix ('H' or 'Q').
            point_idx (int): The index of the point in the reach.
            value_func (callable): A function that takes time `t` and returns the value for the BC.
                                   For a fixed value, use `lambda t: my_value`.
        """
        self.boundary_conditions.append({
            'comp': component, 'var': var, 'idx': point_idx, 'func': value_func
        })

    def _build_variable_map(self):
        """Creates a mapping from each state variable (H/Q at a point) to a matrix column index."""
        self.var_map.clear()
        idx = 0
        for reach in self.reaches:
            for i in range(reach.num_points):
                self.var_map[(reach, 'H', i)] = idx
                idx += 1
                self.var_map[(reach, 'Q', i)] = idx
                idx += 1
        self.num_vars = idx
        print(f"Variable map built. Total variables: {self.num_vars}")

    def build_system(self, t: float):
        """Assembles the global sparse matrix (A) and RHS vector (b) for time t."""
        if not self.var_map:
            self._build_variable_map()

        self.matrix_A = lil_matrix((self.num_vars, self.num_vars), dtype=float)
        self.vector_b = np.zeros(self.num_vars, dtype=float)

        eq_idx = 0

        # --- Equations from Reaches ---
        for reach in self.reaches:
            reach_eqs = reach.get_equations(self.dt, self.theta)
            for i, (Ai, Bi, Ci) in enumerate(reach_eqs):
                h_i_idx = self.var_map[(reach, 'H', i)]
                q_i_idx = self.var_map[(reach, 'Q', i)]
                h_i1_idx = self.var_map[(reach, 'H', i + 1)]
                q_i1_idx = self.var_map[(reach, 'Q', i + 1)]

                self.matrix_A[eq_idx, h_i_idx] = Bi[0, 0]; self.matrix_A[eq_idx, q_i_idx] = Bi[0, 1]
                self.matrix_A[eq_idx, h_i1_idx] = Ai[0, 0]; self.matrix_A[eq_idx, q_i1_idx] = Ai[0, 1]
                self.vector_b[eq_idx] = Ci[0]
                eq_idx += 1

                self.matrix_A[eq_idx, h_i_idx] = Bi[1, 0]; self.matrix_A[eq_idx, q_i_idx] = Bi[1, 1]
                self.matrix_A[eq_idx, h_i1_idx] = Ai[1, 0]; self.matrix_A[eq_idx, q_i1_idx] = Ai[1, 1]
                self.vector_b[eq_idx] = Ci[1]
                eq_idx += 1

        # --- Equations from Nodes ---
        for node in self.nodes:
            node_eqs = node.get_equations(self.dt, self.theta)
            for eq in node_eqs:
                rhs = eq.pop('RHS')
                for (obj, var, idx), coeff in eq.items():
                    # Handle negative indices for nodes
                    point_idx = idx if idx >= 0 else obj.num_points + idx
                    col_idx = self.var_map[(obj, var, point_idx)]
                    self.matrix_A[eq_idx, col_idx] += coeff
                self.vector_b[eq_idx] = rhs
                eq_idx += 1

        # --- Equations from Boundary Conditions ---
        for bc in self.boundary_conditions:
            comp, var, idx = bc['comp'], bc['var'], bc['idx']
            point_idx = idx if idx >= 0 else comp.num_points + idx
            col_idx = self.var_map[(comp, var, point_idx)]

            # Equation: 1 * dVar = TargetValue - CurrentValue
            self.matrix_A[eq_idx, col_idx] = 1.0

            current_val = comp.H[point_idx] if var == 'H' else comp.Q[point_idx]
            target_val = bc['func'](t)
            self.vector_b[eq_idx] = target_val - current_val
            eq_idx += 1

        if eq_idx != self.num_vars:
            raise RuntimeError(f"System is not square! Equations ({eq_idx}) != Variables ({self.num_vars}). Check network connectivity and BCs.")

    def step(self, t: float):
        """Performs one simulation time step at time t."""
        self.build_system(t)

        try:
            solution = spsolve(self.matrix_A.tocsc(), self.vector_b)

            if np.isnan(solution).any():
                raise ValueError("Solver returned NaN values. System may be unstable.")

            for reach in self.reaches:
                dH = np.zeros(reach.num_points)
                dQ = np.zeros(reach.num_points)
                for i in range(reach.num_points):
                    h_idx = self.var_map.get((reach, 'H', i))
                    q_idx = self.var_map.get((reach, 'Q', i))
                    if h_idx is not None: dH[i] = solution[h_idx]
                    if q_idx is not None: dQ[i] = solution[q_idx]
                reach.update_state(dH, dQ)

            for node in self.nodes:
                node.update_state(None, None)

        except Exception as e:
            print(f"Error during solver step: {e}")
            # np.savetxt("matrix_A_error.csv", self.matrix_A.toarray(), delimiter=",")
            # np.savetxt("vector_b_error.csv", self.vector_b, delimiter=",")
            raise

    def run_simulation(self, num_steps: int):
        """Runs the full simulation for a given number of steps."""
        print("\n--- Starting Hydrodynamic Simulation ---")
        for i in range(num_steps):
            current_time = i * self.dt
            print(f"\n--- Time Step {i+1}/{num_steps} (t={current_time:.1f}s) ---")
            self.step(current_time)
        print("\n--- Simulation Finished ---")
