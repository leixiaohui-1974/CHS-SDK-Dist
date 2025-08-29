import pandas as pd
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Dict, Any

class CsvReaderAgent(Agent):
    """
    An agent that reads time-series data from a CSV file and publishes it to
    a message bus topic at the specified times.

    This can be used to simulate external data feeds, such as historical
    inflows, sensor readings, or rainfall events.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus,
                 filepath: str, time_col: str, data_col: str, topic: str):
        """
        Initializes the CsvReaderAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The message bus instance for communication.
            filepath: The path to the CSV file.
            time_col: The name of the column in the CSV file that contains the time data.
            data_col: The name of the column that contains the data to be published.
            topic: The message bus topic to publish the data on.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = topic
        self.data_col = data_col

        try:
            # Load the data and set the time column as the index for efficient lookups
            self.data = pd.read_csv(filepath)
            self.data.set_index(time_col, inplace=True)
            print(f"Agent '{self.agent_id}' loaded data from '{filepath}'.")
        except FileNotFoundError:
            print(f"ERROR: Agent '{self.agent_id}' could not find data file at '{filepath}'.")
            self.data = pd.DataFrame() # Empty dataframe to prevent errors

    def run(self, current_time: float):
        """
        Checks if the current simulation time exists in the data file and,
        if so, publishes the corresponding data to the message bus.

        Args:
            current_time: The current simulation time in seconds.
        """
        if current_time in self.data.index:
            data_value = self.data.loc[current_time, self.data_col]

            # Ensure data_value is a native Python type for JSON compatibility if needed
            if pd.api.types.is_number(data_value):
                data_value = data_value.item()

            message = {'value': data_value, 'time': current_time}
            self.bus.publish(self.topic, message)
            print(f"Agent '{self.agent_id}' published data at time {current_time}: {data_value}")
