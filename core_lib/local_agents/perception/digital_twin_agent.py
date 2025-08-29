"""
Digital Twin Agent for state synchronization, enhancement, and publication.
"""
from core_lib.core.interfaces import Agent, Simulatable, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional, Dict, Any

class DigitalTwinAgent(Agent):
    """
    A Perception Agent that acts as a digital twin for a physical object.

    Its primary responsibility is to maintain an internal simulation model and
    publish its state to the message bus. It can also perform "cognitive"
    enhancements on the raw state, such as smoothing noisy data.
    """

    def __init__(self,
                 agent_id: str,
                 simulated_object: Simulatable,
                 message_bus: MessageBus,
                 state_topic: str,
                 smoothing_config: Optional[Dict[str, float]] = None):
        """
        Initializes the DigitalTwinAgent.

        Args:
            agent_id: The unique ID of this agent.
            simulated_object: The simulation model this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the object's state.
            smoothing_config: Optional config for applying EMA smoothing.
                Example: {'water_level': 0.3, 'outflow': 0.5}
                The value is the alpha (smoothing factor).
        """
        super().__init__(agent_id)
        self.model = simulated_object
        self.bus = message_bus
        self.state_topic = state_topic
        self.smoothing_config = smoothing_config
        self.smoothed_states: Dict[str, float] = {}

        model_id = self.model.name
        print(f"DigitalTwinAgent '{self.agent_id}' created for model '{model_id}'. Will publish state to '{self.state_topic}'.")
        if self.smoothing_config:
            print(f"  - Smoothing enabled for keys: {list(self.smoothing_config.keys())}")

    def _apply_smoothing(self, state: State) -> State:
        """Applies Exponential Moving Average (EMA) smoothing to configured state variables."""
        if not self.smoothing_config:
            return state

        smoothed_state = state.copy()
        for key, alpha in self.smoothing_config.items():
            if key in smoothed_state:
                raw_value = smoothed_state[key]
                last_smoothed = self.smoothed_states.get(key, raw_value) # Initialize with first raw value
                new_smoothed = alpha * raw_value + (1 - alpha) * last_smoothed
                smoothed_state[key] = new_smoothed
                self.smoothed_states[key] = new_smoothed
        return smoothed_state

    def publish_state(self):
        """
        Fetches the current state, applies enhancements (e.g., smoothing),
        and publishes it.
        """
        raw_state = self.model.get_state()
        enhanced_state = self._apply_smoothing(raw_state)

        message: Message = enhanced_state
        self.bus.publish(self.state_topic, message)

    def run(self, current_time: float):
        """
        The main execution logic for the agent.

        In a simulation context, this method is called at each time step
        by the harness to make the agent publish its current state.

        Args:
            current_time: The current simulation time (ignored by this agent).
        """
        self.publish_state()
