"""
Simulation model for a Valve.
"""
import math
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class Valve(PhysicalObjectInterface):
    """
    Represents a controllable valve in a water system.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self.bus = message_bus
        self.action_topic = action_topic
        self.target_opening = self._state.get('opening', 100.0)

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Valve '{self.name}' subscribed to action topic '{self.action_topic}'.")

        print(f"Valve '{self.name}' created with initial state {self._state}.")

    def _calculate_flow(self, upstream_level: float, downstream_level: float) -> float:
        """
        Calculates the flow through the valve using a modified orifice equation.
        """
        C_d_max = self._params.get('discharge_coefficient', 0.8)
        diameter = self._params.get('diameter', 0.5)
        g = 9.81

        opening_percent = self._state.get('opening', 0)
        effective_C_d = C_d_max * (opening_percent / 100.0)

        area = math.pi * (diameter / 2)**2
        head_diff = upstream_level - downstream_level

        if head_diff <= 0:
            return 0

        flow = effective_C_d * area * (2 * g * head_diff)**0.5
        return flow

    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        new_target = message.get('control_signal')
        if isinstance(new_target, (int, float)):
            self.target_opening = max(0.0, min(100.0, new_target))

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the valve's state over a single time step.
        """
        control_signal = action.get('control_signal')
        if control_signal is not None:
             if isinstance(control_signal, (int, float)):
                self.target_opening = max(0.0, min(100.0, control_signal))

        self._state['opening'] = self.target_opening

        opening_percent = self._state.get('opening', 0)

        if self._inflow > 0:
            if opening_percent > 0:
                outflow = self._inflow
            else:
                outflow = 0
        else:
            upstream_level = action.get('upstream_head', 0)
            downstream_level = action.get('downstream_head', 0)
            outflow = self._calculate_flow(upstream_level, downstream_level)

        self._state['outflow'] = outflow

        return self.get_state()


class ValveStation(PhysicalObjectInterface):
    """
    Represents a valve station, which is a collection of individual valves.
    It aggregates the flow of all valves within it. The control of individual
    valves is handled by an external agent.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters, valves: list[Valve]):
        super().__init__(name, initial_state, parameters)
        self.valves = valves
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('valve_count', len(self.valves))
        print(f"ValveStation '{self.name}' created with {len(self.valves)} valves.")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Steps each valve in the station and aggregates their states.
        The `action` dict (containing upstream/downstream heads) is passed to each valve.
        """
        total_outflow = 0.0

        for valve in self.valves:
            # Individual valve control signals are received via their own message bus subscriptions.
            valve_state = valve.step(action, dt)
            total_outflow += valve_state.get('outflow', 0)

        self._state['total_outflow'] = total_outflow

        return self._state

    @property
    def is_stateful(self) -> bool:
        return False
