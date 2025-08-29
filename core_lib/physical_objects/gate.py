"""
Simulation model for a Gate.
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional
import math

class Gate(PhysicalObjectInterface):
    """
    Represents a controllable gate in a water system.
    Its outflow is calculated based on the upstream and downstream water levels.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None,
                 action_key: str = 'opening'):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self.bus = message_bus
        self.action_topic = action_topic
        self.action_key = action_key
        self.target_opening = self._state.get('opening', 0)
        # Store last known head diff for inverse calculation
        self.last_head_diff = 1

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Gate '{self.name}' subscribed to action topic '{self.action_topic}'.")

        print(f"Gate '{self.name}' created with initial state {self._state}.")

    def _calculate_outflow(self, upstream_level: float, downstream_level: float = 0) -> float:
        """
        Calculates the outflow through the gate using the orifice equation.
        Q = C * A * sqrt(2 * g * h)
        """
        C = self._params.get('discharge_coefficient', 0.6)
        width = self._params.get('width', 10)
        g = 9.81

        opening = self._state.get('opening', 0)
        area = opening * width

        head = upstream_level - downstream_level
        self.last_head_diff = head # Cache for inverse calculation
        if head <= 0:
            return 0

        outflow = C * area * (2 * g * head)**0.5
        return outflow

    def _calculate_opening_for_flow(self, target_flow: float) -> float:
        """
        Inverse of the orifice equation to find the required gate opening for a given flow.
        opening = Q / (C * width * sqrt(2 * g * h))
        """
        C = self._params.get('discharge_coefficient', 0.6)
        width = self._params.get('width', 10)
        g = 9.81

        if self.last_head_diff <= 0:
            return 0 # Cannot achieve flow with no head difference

        denominator = C * width * math.sqrt(2 * g * self.last_head_diff)
        if denominator == 0:
            return self._params.get('max_opening', 1.0) # Cannot calculate, open fully if flow is desired

        return target_flow / denominator

    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        # Handle direct opening commands
        if self.action_key in message:
            new_target = message.get(self.action_key)
            if new_target is not None:
                self.target_opening = float(new_target)

        # Handle target outflow commands
        elif 'gate_target_outflow' in message:
            target_flow = message.get('gate_target_outflow')
            if target_flow is not None:
                self.target_opening = self._calculate_opening_for_flow(float(target_flow))

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the gate's state over a single time step.
        """
        # Direct control via action dict for non-MAS simulations
        if 'control_signal' in action and action['control_signal'] is not None:
            self.target_opening = action['control_signal']

        max_roc = self._params.get('max_rate_of_change', 0.05)
        current_opening = self._state.get('opening', 0)

        if self.target_opening > current_opening:
            new_opening = min(current_opening + max_roc * dt, self.target_opening)
        else:
            new_opening = max(current_opening - max_roc * dt, self.target_opening)

        max_opening = self._params.get('max_opening', 1.0)
        self._state['opening'] = max(0.0, min(new_opening, max_opening))

        upstream_level = action.get('upstream_head', 0)
        downstream_level = action.get('downstream_head', 0)
        self._state['outflow'] = self._calculate_outflow(upstream_level, downstream_level)

        return self.get_state()
