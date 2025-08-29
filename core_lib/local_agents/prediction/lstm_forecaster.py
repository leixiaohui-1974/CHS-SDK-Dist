"""
An agent that uses an LSTM neural network to forecast future values.
"""
import torch
import torch.nn as nn
import numpy as np
from collections import deque
from sklearn.preprocessing import MinMaxScaler

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.local_agents.prediction.lstm_model import LSTMModel
from typing import Deque, Any, Dict, List, Tuple

class LSTMFlowForecaster(Agent):
    """
    An agent that uses a deep learning LSTM model for forecasting.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, config: Dict[str, Any]):
        super().__init__(agent_id)
        self.bus = message_bus

        # Config
        self.obs_topic = config["observation_topic"]
        self.obs_key = config["observation_key"]
        self.forecast_topic = config["forecast_topic"]
        self.history_size = config.get("history_size", 200)
        self.refit_interval = config.get("refit_interval", 50)

        # LSTM specific config
        self.input_window_size = config.get("input_window_size", 30)
        self.output_window_size = config.get("output_window_size", 5)
        self.epochs = config.get("epochs", 50)
        self.learning_rate = config.get("learning_rate", 0.001)
        self.hidden_size = config.get("hidden_size", 50)
        self.num_layers = config.get("num_layers", 1)

        # State
        self.history: Deque[float] = deque(maxlen=self.history_size)
        self.new_obs_since_fit = 0
        self.model = LSTMModel(1, self.hidden_size, self.num_layers, self.output_window_size)
        self.scaler = MinMaxScaler(feature_range=(-1, 1))

        self.bus.subscribe(self.obs_topic, self.handle_observation_message)
        print(f"LSTMFlowForecaster '{self.agent_id}' created.")

    def handle_observation_message(self, message: Message):
        value = message.get(self.obs_key)
        if isinstance(value, (int, float)):
            self.history.append(float(value))
            self.new_obs_since_fit += 1

    def _create_sequences(self, data: np.ndarray) -> Tuple[torch.Tensor, torch.Tensor]:
        inout_seq = []
        L = len(data)
        for i in range(L - self.input_window_size - self.output_window_size):
            train_seq = data[i:i + self.input_window_size]
            train_label = data[i + self.input_window_size : i + self.input_window_size + self.output_window_size]
            inout_seq.append((train_seq, train_label))

        # Convert to tensors, ensuring labels are flattened
        X = torch.FloatTensor(np.array([seq for seq, _ in inout_seq]))
        y = torch.FloatTensor(np.array([label.flatten() for _, label in inout_seq]))
        return X.view(-1, self.input_window_size, 1), y

    def _fit_model(self):
        if len(self.history) < self.input_window_size + self.output_window_size:
            return

        print(f"  [{self.agent_id}] Preprocessing data and training LSTM model...")

        # 1. Preprocess data
        data_np = np.array(self.history).reshape(-1, 1)
        data_scaled = self.scaler.fit_transform(data_np)
        X_train, y_train = self._create_sequences(data_scaled)

        # 2. Train model
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        loss_function = nn.MSELoss()

        for i in range(self.epochs):
            for seq, labels in zip(X_train, y_train):
                optimizer.zero_grad()
                y_pred = self.model(seq.unsqueeze(0))
                single_loss = loss_function(y_pred, labels.unsqueeze(0))
                single_loss.backward()
                optimizer.step()

        self.new_obs_since_fit = 0
        print(f"  [{self.agent_id}] LSTM model training complete.")

    def _forecast(self) -> List[float]:
        if len(self.history) < self.input_window_size:
            return []

        # Take the last `input_window_size` points from history
        last_sequence = np.array(list(self.history)[-self.input_window_size:]).reshape(-1, 1)
        last_sequence_scaled = self.scaler.transform(last_sequence)

        with torch.no_grad():
            self.model.eval()
            input_tensor = torch.FloatTensor(last_sequence_scaled).view(1, self.input_window_size, 1)
            prediction_scaled = self.model(input_tensor)

        # Inverse transform the prediction to get the real value
        prediction = self.scaler.inverse_transform(prediction_scaled.numpy())
        return prediction.flatten().tolist()

    def run(self, current_time: float):
        # Check if it's time to refit the model
        if self.new_obs_since_fit >= self.refit_interval:
            self._fit_model()
            forecast_values = self._forecast()
            if forecast_values:
                self.publish_forecast(current_time, forecast_values)

    def publish_forecast(self, current_time: float, forecast_values: List[float]):
        forecast_message = {
            "timestamp": current_time,
            "forecast_steps": len(forecast_values),
            "values": forecast_values
        }
        self.bus.publish(self.forecast_topic, forecast_message)
        print(f"  [{current_time}s] LSTMFlowForecaster '{self.agent_id}': Published forecast.")
