"""
Agent for updating model parameters online.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict

class ModelUpdaterAgent(Agent):
    """
    An agent that listens for newly identified model parameters and applies
    them to the corresponding simulation models (digital twins).

    This creates a closed loop where the system can self-calibrate and adapt
    over time.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, parameter_topic: str, models: Dict):
        """
        Initializes the ModelUpdaterAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            parameter_topic: The topic where new parameter estimates are published.
            models: A dictionary of the simulation models in the system, keyed by name.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.parameter_topic = parameter_topic
        self.models = models

        self.bus.subscribe(self.parameter_topic, self.handle_new_parameters)

        print(f"ModelUpdaterAgent '{self.agent_id}' initialized. Subscribed to '{self.parameter_topic}'.")

    def handle_new_parameters(self, message: Message):
        """
        Callback to handle a message containing new model parameters.
        """
        model_name = message.get("model_name")
        new_params = message.get("parameters")

        if model_name and new_params and model_name in self.models:
            target_model = self.models[model_name]
            # Assuming the model has a 'set_parameters' method
            if hasattr(target_model, 'set_parameters'):
                target_model.set_parameters(new_params)
                print(f"[{self.agent_id}] Updated parameters for model '{model_name}': {new_params}")
            else:
                print(f"[{self.agent_id}] Warning: Model '{model_name}' has no 'set_parameters' method.")
        else:
            print(f"[{self.agent_id}] Warning: Invalid parameter update message received: {message}")


    def run(self, current_time: float):
        """
        This agent is event-driven, so the run loop is a no-op.
        """
        pass
