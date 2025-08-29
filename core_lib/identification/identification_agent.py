"""
An agent responsible for orchestrating the parameter identification process.
"""
from core_lib.core.interfaces import Agent, Identifiable
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, List

class ParameterIdentificationAgent(Agent):
    """
    An agent that collects simulated and observed data and triggers the
    parameter identification process for a target model.
    """

    def __init__(self, agent_id: str, target_model: Identifiable,
                 message_bus: MessageBus, config: Dict[str, Any]):
        """
        Initializes the ParameterIdentificationAgent.

        Args:
            agent_id: The unique ID for this agent.
            target_model: The model instance whose parameters are to be identified.
            message_bus: The system's message bus.
            config: A dictionary containing the agent's configuration:
                - sim_data_topic: Topic for the simulated data.
                - obs_data_topic: Topic for the observed data.
                - data_key: Key to extract the value from the data messages.
                - identification_interval: Number of data points to collect
                                           before running identification.
                - identification_data_map: A dictionary mapping the keys required
                                           by the model's identify_parameters method
                                           (e.g., 'rainfall', 'observed_runoff') to
                                           the topics they correspond to.
        """
        super().__init__(agent_id)
        self.target_model = target_model
        self.bus = message_bus

        # Configuration
        self.id_interval = config.get("identification_interval", 100)
        self.data_map = config["identification_data_map"]

        # Internal state
        self.data_history: Dict[str, List[float]] = {key: [] for key in self.data_map.keys()}
        self.new_data_count = 0

        # Subscribe to all necessary data topics
        for model_key, topic in self.data_map.items():
            # The lambda captures the 'model_key' for the handler
            self.bus.subscribe(topic, lambda msg, key=model_key: self.handle_data_message(msg, key))
            print(f"[{self.agent_id}] Subscribed to topic '{topic}' for data key '{model_key}'.")

    def handle_data_message(self, message: Message, model_key: str):
        """Callback to store incoming data."""
        value = message.get("value") # Assuming a simple {'value': ...} message
        if isinstance(value, (int, float)):
            self.data_history[model_key].append(value)
            if model_key == list(self.data_map.keys())[0]: # Increment counter only for one stream
                self.new_data_count += 1

    def run(self, current_time: float):
        """
        Checks if enough data has been collected and triggers identification.
        """
        if self.new_data_count >= self.id_interval:
            print(f"  [{current_time}s] [{self.agent_id}] Collected {self.new_data_count} new data points. Triggering parameter identification.")

            # Prepare data for the model
            # The model's identify_parameters expects numpy arrays
            import numpy as np
            data_for_model = {key: np.array(values) for key, values in self.data_history.items()}

            # Trigger identification
            self.target_model.identify_parameters(data_for_model)

            # Reset for the next batch
            self.clear_history()

    def clear_history(self):
        """Clears the collected data history."""
        self.data_history = {key: [] for key in self.data_map.keys()}
        self.new_data_count = 0
        print(f"  [{self.agent_id}] Data history cleared. Ready for next identification cycle.")
