"""
Simulation model for a Hydropower Station.
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.physical_objects.gate import Gate
from typing import Dict, Any, List

class HydropowerStation(PhysicalObjectInterface):
    """
    Represents a hydropower station, a complex facility that includes both
    power-generating water turbines and spillway gates for water management.

    This model aggregates the behavior of all its components. The control of
    individual turbines and gates is handled by an external agent, which sends
p    control signals to them via the message bus.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 turbines: List[WaterTurbine], gates: List[Gate]):
        super().__init__(name, initial_state, parameters)
        self.turbines = turbines
        self.gates = gates

        # Initialize aggregated state variables
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('total_power_generation', 0.0)
        self._state.setdefault('turbine_outflow', 0.0)
        self._state.setdefault('spillway_outflow', 0.0)

        print(f"HydropowerStation '{self.name}' created with {len(self.turbines)} turbines and {len(self.gates)} gates.")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Steps each component (turbine and gate) in the station and aggregates their states.

        The `action` dict, containing upstream and downstream head levels, is passed
        to each component to calculate its performance for the time step.
        """
        # The total inflow to the station is set by the simulation harness
        # This inflow needs to be distributed among the turbines and gates.
        # For this model, we assume the control agent's logic (setting target outflows)
        # implicitly handles this distribution. The step methods of the components
        # will respect the total available inflow.

        total_turbine_outflow = 0.0
        total_power = 0.0
        for turbine in self.turbines:
            # The turbine's step method will use the inflow provided to it.
            # In a networked simulation, the harness would set each component's inflow.
            # Here we pass the station's total inflow to each for now.
            turbine.set_inflow(self._inflow)
            turbine_state = turbine.step(action, dt)
            total_turbine_outflow += turbine_state.get('outflow', 0.0)
            total_power += turbine_state.get('power', 0.0)

        total_spillway_outflow = 0.0
        for gate in self.gates:
            gate.set_inflow(self._inflow) # Also inform gate of available inflow
            gate_state = gate.step(action, dt)
            total_spillway_outflow += gate_state.get('outflow', 0.0)

        # Update aggregated state
        self._state['turbine_outflow'] = total_turbine_outflow
        self._state['spillway_outflow'] = total_spillway_outflow
        self._state['total_outflow'] = total_turbine_outflow + total_spillway_outflow
        self._state['total_power_generation'] = total_power

        return self.get_state()

    @property
    def is_stateful(self) -> bool:
        # A hydropower station is typically located at a dam with a reservoir,
        # which is a stateful component. However, the station model itself
        # does not store water; it just processes it. The associated reservoir
        # model would be the stateful component in the simulation.
        return False
