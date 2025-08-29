"""
Central agent for demand forecasting.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List, Dict

class DemandForecastingAgent(Agent):
    """
    A central agent responsible for forecasting water demand for the system.

    This agent can use historical data, weather forecasts, and other external
    factors to predict future water needs, providing crucial input for
    the central dispatch and MPC agents.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, historical_data_topics: List[str], forecast_topic: str):
        """
        Initializes the DemandForecastingAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            historical_data_topics: Topics to subscribe to for historical usage data.
            forecast_topic: The topic to publish demand forecasts to.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.historical_data_topics = historical_data_topics
        self.forecast_topic = forecast_topic
        self.historical_data: Dict[str, List] = {topic: [] for topic in historical_data_topics}

        for topic in self.historical_data_topics:
            self.bus.subscribe(topic, self.handle_data)

        print(f"DemandForecastingAgent '{self.agent_id}' initialized. Subscribed to {len(self.historical_data_topics)} data topics.")

    def handle_data(self, message: Message, topic: str):
        """Callback to collect historical data."""
        self.historical_data[topic].append(message)

    def run(self, current_time: float):
        """
        The main execution logic. Periodically generates and publishes a new forecast.
        """
        # Placeholder for forecasting logic
        # For example, run the forecast every 24 hours (86400 seconds)
        if int(current_time) % 86400 == 0:
            self.generate_forecast(current_time)

    def generate_forecast(self, current_time: float):
        """
        Generates a demand forecast based on the collected historical data.
        """
        # This is where a forecasting model (e.g., ARIMA, LSTM) would be used.
        print(f"[{self.agent_id} at {current_time}] Generating new demand forecast...")

        # Placeholder forecast
        forecast = {"start_time": current_time, "horizon": 24, "demands": [10, 11, 10.5]} # Example

        self.bus.publish(self.forecast_topic, forecast)
        print(f"[{self.agent_id}] Published new forecast to '{self.forecast_topic}'.")
