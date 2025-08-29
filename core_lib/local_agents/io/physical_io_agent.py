import numpy as np
from typing import Dict, Any

from core_lib.core.interfaces import Agent, PhysicalObjectInterface
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

class PhysicalIOAgent(Agent):
    """
    An agent that simulates the physical I/O layer of a control system.

    - Simulates sensors by reading the true state from physical objects,
      adding noise, and publishing it to the message bus.
    - Simulates actuators by subscribing to action topics and setting
      target states on the physical objects, which then enact the change
      in their `step` methods.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 sensors_config: Dict[str, Dict[str, Any]],
                 actuators_config: Dict[str, Dict[str, Any]]):
        """
        Initializes the PhysicalIOAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            sensors_config: Configuration for sensors. Example:
                {
                    'canal_level_sensor': {
                        'obj': upstream_canal,
                        'state_key': 'water_level',
                        'topic': 'state.canal.level',
                        'noise_std': 0.01
                    }
                }
            actuators_config: Configuration for actuators. Example:
                {
                    'gate_actuator': {
                        'obj': control_gate,
                        'target_attr': 'target_opening',
                        'topic': 'action.gate.opening',
                        'control_key': 'control_signal'
                    }
                }
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.sensors = sensors_config
        self.actuators = actuators_config

        print(f"PhysicalIOAgent '{self.agent_id}' created.")
        self._subscribe_to_actions()

    def _subscribe_to_actions(self):
        """
        Internal method to subscribe to all necessary action topics based on config.
        """
        for name, config in self.actuators.items():
            topic = config['topic']
            # Use a lambda with default argument to capture the correct config
            # for each callback.
            callback = lambda message, cfg=config: self._handle_action(message, cfg)
            self.bus.subscribe(topic, callback)
            print(f"  - Subscribed to actuator topic '{topic}' for '{name}'.")

    def _handle_action(self, message: Message, config: Dict[str, Any]):
        """
        Generic callback to handle an incoming action message.
        """
        obj: PhysicalObjectInterface = config['obj']
        target_attr: str = config['target_attr']
        control_key: str = config['control_key']

        control_signal = message.get(control_key)
        if control_signal is not None:
            # Set the target attribute on the physical object.
            # e.g., control_gate.target_opening = 0.5
            setattr(obj, target_attr, control_signal)
            # print(f"[{self.agent_id}] Received action for '{obj.name}'. Setting '{target_attr}' to {control_signal}.")

    def run(self, current_time: float):
        """
        The "sensing" part of the agent's behavior.
        This is called at each simulation step.
        """
        # print(f"[{self.agent_id}] Running sensing cycle at time {current_time}.")
        for name, config in self.sensors.items():
            obj: PhysicalObjectInterface = config['obj']
            state_key: str = config['state_key']
            topic: str = config['topic']
            noise_std: float = config.get('noise_std', 0.0)

            # Read the true state from the physical object
            true_value = obj.get_state().get(state_key)
            if true_value is None:
                continue

            # Add Gaussian noise to simulate a real sensor
            noisy_value = true_value + np.random.normal(0, noise_std)

            # Publish the noisy sensor reading
            message = {state_key: noisy_value, 'timestamp': current_time}
            self.bus.publish(topic, message)
            # print(f"  - Publishing noisy state for '{name}' to '{topic}': {noisy_value:.4f}")
