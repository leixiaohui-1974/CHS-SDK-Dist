"""
Simulation model for a Pump.
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class Pump(PhysicalObjectInterface):
    """
    Represents a controllable pump in a water system.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self._state.setdefault('power_draw_kw', 0)
        self.bus = message_bus
        self.action_topic = action_topic
        self.target_status = self._state.get('status', 0)

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Pump '{self.name}' subscribed to action topic '{self.action_topic}'.")

        print(f"Pump '{self.name}' created with initial state {self._state}.")

    def _calculate_flow(self, upstream_level: float, downstream_level: float) -> float:
        """
        Calculates the flow provided by the pump.
        """
        if self._state.get('status', 0) == 0:
            return 0.0

        max_head = self._params.get('max_head', 20)
        required_head = downstream_level - upstream_level

        if required_head > max_head:
            return 0.0

        return self._params.get('max_flow_rate', 10.0)

    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        new_target = message.get('control_signal')
        if new_target in [0, 1]:
            self.target_status = new_target

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the pump's state over a single time step.
        """
        control_signal = action.get('control_signal')
        if control_signal in [0, 1]:
            self.target_status = control_signal

        self._state['status'] = self.target_status

        upstream_level = action.get('upstream_head', 0)
        downstream_level = action.get('downstream_head', 0)
        outflow = self._calculate_flow(upstream_level, downstream_level)
        self._state['outflow'] = outflow

        if outflow > 0:
             self._state['power_draw_kw'] = self._params.get('power_consumption_kw', 50.0)
        else:
            self._state['power_draw_kw'] = 0.0

        return self.get_state()


class PumpStation(PhysicalObjectInterface):
    """
    Represents a pump station, which is a collection of individual pumps.
    It aggregates the flow and power consumption of all pumps within it.
    The control of individual pumps is handled by an external agent.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters, pumps: list[Pump]):
        super().__init__(name, initial_state, parameters)
        self.pumps = pumps
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('active_pumps', 0)
        self._state.setdefault('total_power_draw_kw', 0.0)
        print(f"PumpStation '{self.name}' created with {len(self.pumps)} pumps.")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Steps each pump in the station and aggregates their states.
        The `action` dict (containing upstream/downstream heads) is passed to each pump.
        """
        total_outflow = 0.0
        active_pumps = 0
        total_power = 0.0

        for pump in self.pumps:
            # Individual pump control signals are received via their own message bus subscriptions,
            # so they are not included in the station-level action.
            pump_state = pump.step(action, dt)
            total_outflow += pump_state.get('outflow', 0)
            total_power += pump_state.get('power_draw_kw', 0)
            if pump_state.get('status', 0) == 1:
                active_pumps += 1

        self._state['total_outflow'] = total_outflow
        self._state['active_pumps'] = active_pumps
        self._state['total_power_draw_kw'] = total_power

        return self._state

    @property
    def is_stateful(self) -> bool:
        return False
