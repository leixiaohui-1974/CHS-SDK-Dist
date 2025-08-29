"""
An agent that uses an ARIMA model to forecast future values.
"""
import warnings
import pandas as pd
from collections import deque
from statsmodels.tsa.arima.model import ARIMA
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Deque, Any, Dict, List, Optional

# Suppress warnings from statsmodels, which can be verbose
warnings.filterwarnings("ignore")

class ARIMAForecaster(Agent):
    """
    An agent that observes a data stream and provides quantitative forecasts
    using a statistical ARIMA model.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, config: Dict[str, Any]):
        """
        Initializes the ARIMAForecaster.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The central message bus for communication.
            config: A dictionary containing the agent's configuration:
                - observation_topic: The topic to subscribe to for data.
                - observation_key: The key for the value in the observation message.
                - forecast_topic: The topic to publish forecasts to.
                - history_size: The maximum number of observations to keep.
                - arima_order: The (p, d, q) order of the ARIMA model.
                - forecast_steps: The number of future steps to forecast.
                - refit_interval: The number of new observations to collect
                                  before refitting the model.
        """
        super().__init__(agent_id)
        self.bus = message_bus

        # Configuration
        self.obs_topic = config["observation_topic"]
        self.obs_key = config["observation_key"]
        self.forecast_topic = config["forecast_topic"]
        self.history_size = config.get("history_size", 100)
        self.arima_order = tuple(config.get("arima_order", (5, 1, 0)))
        self.forecast_steps = config.get("forecast_steps", 10)
        self.refit_interval = config.get("refit_interval", 10)

        # State
        self.history: Deque[float] = deque(maxlen=self.history_size)
        self.new_obs_since_fit = 0
        self.model_fit = None

        self.bus.subscribe(self.obs_topic, self.handle_observation_message)
        print(f"ARIMAForecaster '{self.agent_id}' created and subscribed to '{self.obs_topic}'.")

    def handle_observation_message(self, message: Message):
        """Callback to handle incoming observation messages."""
        value = message.get(self.obs_key)
        if isinstance(value, (int, float)):
            self.history.append(float(value))
            self.new_obs_since_fit += 1

    def _fit_and_forecast(self) -> Optional[List[float]]:
        """
        Fits the ARIMA model to the current history and returns a forecast.
        Returns None if fitting or forecasting fails.
        """
        # Do not attempt to fit if there is not enough data
        min_data_points = max(10, sum(self.arima_order) * 2) # Heuristic for minimum data
        if len(self.history) < min_data_points:
            return None

        print(f"  [{self.agent_id}] Refitting ARIMA model with {len(self.history)} data points...")
        series = pd.Series(list(self.history))
        model = ARIMA(series, order=self.arima_order)
        try:
            self.model_fit = model.fit()
            self.new_obs_since_fit = 0
            print(f"  [{self.agent_id}] Model refit successful.")

            # Generate and return the forecast immediately
            forecast = self.model_fit.forecast(steps=self.forecast_steps)
            return forecast.tolist()
        except Exception as e:
            print(f"  [{self.agent_id}] WARNING: ARIMA model fitting failed: {e}")
            self.model_fit = None
            return None

    def run(self, current_time: float):
        """
        Periodically fits the model and publishes a new forecast.
        """
        should_fit = False
        # Fit if we don't have a model but have enough data to start
        if self.model_fit is None and self.new_obs_since_fit >= self.refit_interval:
            should_fit = True
        # Fit if we do have a model and the refit interval has been reached
        elif self.model_fit is not None and self.new_obs_since_fit >= self.refit_interval:
            should_fit = True

        if should_fit:
            forecast_values = self._fit_and_forecast()
            if forecast_values is not None:
                self.publish_forecast(current_time, forecast_values)

    def publish_forecast(self, current_time: float, forecast_values: List[float]):
        """Publishes the forecast to the message bus."""
        forecast_message = {
            "timestamp": current_time,
            "forecast_steps": self.forecast_steps,
            "values": forecast_values
        }
        self.bus.publish(self.forecast_topic, forecast_message)
        print(f"  [{current_time}s] ARIMAForecaster '{self.agent_id}': Published forecast of {len(forecast_values)} steps.")
