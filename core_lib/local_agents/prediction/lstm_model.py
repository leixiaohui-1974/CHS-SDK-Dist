"""
A simple LSTM model for time series forecasting, built with PyTorch.
"""
import torch
import torch.nn as nn

class LSTMModel(nn.Module):
    """
    A sequence-to-sequence LSTM model for forecasting.
    """
    def __init__(self, input_size: int, hidden_layer_size: int, num_layers: int, output_size: int):
        """
        Initializes the LSTM model architecture.

        Args:
            input_size: The number of features in the input sequence (e.g., 1 for univariate).
            hidden_layer_size: The number of neurons in the LSTM's hidden layer.
            num_layers: The number of LSTM layers to stack.
            output_size: The number of time steps to predict into the future.
        """
        super().__init__()
        self.hidden_layer_size = hidden_layer_size
        self.num_layers = num_layers

        # Define the LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_layer_size,
            num_layers=num_layers,
            batch_first=True # Expect input tensors with batch dimension first
        )

        # Define the fully connected output layer
        self.linear = nn.Linear(
            in_features=hidden_layer_size,
            out_features=output_size
        )

    def forward(self, input_seq: torch.Tensor) -> torch.Tensor:
        """
        Defines the forward pass of the model.

        Args:
            input_seq: The input sequence tensor. Shape: (batch_size, sequence_length, input_size)

        Returns:
            The prediction tensor. Shape: (batch_size, output_size)
        """
        # Initialize hidden and cell states
        h0 = torch.zeros(self.num_layers, input_seq.size(0), self.hidden_layer_size).to(input_seq.device)
        c0 = torch.zeros(self.num_layers, input_seq.size(0), self.hidden_layer_size).to(input_seq.device)

        # We only care about the final output of the LSTM layer
        # lstm_out shape: (batch_size, sequence_length, hidden_layer_size)
        lstm_out, _ = self.lstm(input_seq, (h0, c0))

        # We pass the output of the last time step to the linear layer
        # lstm_out[:, -1, :] gets the last time step's output for all batches
        predictions = self.linear(lstm_out[:, -1, :])

        return predictions
