from collections import deque
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Deque, Any, Dict

class ForecastingAgent(Agent):
    """
    A simple agent that observes a data stream and predicts future trends.

    This agent listens to a specific topic, keeps a history of the observed
    values, and uses a simple heuristic to detect trends. If a trend is
    detected, it publishes a forecast message.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus,
                 observation_topic: str, observation_key: str,
                 forecast_topic: str, window_size: int = 5):
        """
        Initializes the ForecastingAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The central message bus for communication.
            observation_topic: The topic to subscribe to for observations.
            observation_key: The key to extract the value from the observation message.
            forecast_topic: The topic to publish forecasts to.
            window_size: The number of recent data points to consider for trend detection.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.observation_topic = observation_topic
        self.observation_key = observation_key
        self.forecast_topic = forecast_topic
        self.window_size = window_size

        self.history: Deque[float] = deque(maxlen=self.window_size)
        self.last_forecasted_trend: str = "stable"

        self.bus.subscribe(self.observation_topic, self.handle_observation_message)
        print(f"ForecastingAgent '{self.agent_id}' subscribed to '{self.observation_topic}'.")

    def handle_observation_message(self, message: Message):
        """Callback to handle incoming observation messages."""
        value = message.get(self.observation_key)
        if isinstance(value, (int, float)):
            self.history.append(float(value))

    def run(self, current_time: float):
        """
        Analyzes the history and publishes a forecast if a trend is detected.
        This is called at each simulation step by the harness.
        """
        if len(self.history) < self.window_size:
            # Not enough data to make a forecast yet
            return

        # Simple trend detection: is the latest value higher/lower than the oldest?
        # A more robust method might use linear regression, but this is fine for a demo.
        oldest_value = self.history[0]
        latest_value = self.history[-1]

        current_trend = "stable"
        if latest_value > oldest_value * 1.05: # Require a 5% increase to call it a trend
            current_trend = "increasing"
        elif latest_value < oldest_value * 0.95: # Require a 5% decrease
            current_trend = "decreasing"

        # Only publish if the trend has changed to avoid spamming the bus
        if current_trend != self.last_forecasted_trend:
            forecast_message = {
                "trend": current_trend,
                "current_value": latest_value,
                "window_size_s": self.window_size * self.bus.dt # Assuming harness dt is on bus
            }
            self.bus.publish(self.forecast_topic, forecast_message)
            self.last_forecasted_trend = current_trend
            print(f"  [{current_time}s] ForecastAgent '{self.agent_id}': Detected trend '{current_trend}'. Publishing forecast.")
