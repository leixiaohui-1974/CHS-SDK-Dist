import pandas as pd
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class CsvDataSourceAgent(Agent):
    """
    An agent that reads time-series data from a CSV file and publishes it to
    the message bus at the appropriate simulation time.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, csv_filepath: str, publish_topic: str):
        """
        Initializes the CsvDataSourceAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The message bus instance for communication.
            csv_filepath: The path to the CSV file to be read.
            publish_topic: The topic to publish the data on.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = publish_topic

        try:
            self.data = pd.read_csv(csv_filepath)
            # Ensure timestamp is numeric for comparison
            self.data['timestamp'] = pd.to_numeric(self.data['timestamp'])
        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_filepath}")
            self.data = pd.DataFrame() # Empty dataframe

        self.last_published_index = -1
        print(f"CsvDataSourceAgent '{agent_id}' initialized, loaded {len(self.data)} records from {csv_filepath}.")

    def run(self, current_time: float):
        """
        Called at each simulation step. Checks if there is new data to publish.
        """
        if self.data.empty:
            return

        # Find all rows that should have been published by the current time
        # but have not been published yet.
        eligible_rows = self.data[(self.data['timestamp'] <= current_time) & (self.data.index > self.last_published_index)]

        if not eligible_rows.empty:
            # We publish the most recent eligible row
            latest_row = eligible_rows.iloc[-1]

            message = {
                'timestamp': latest_row['timestamp'],
                'value': latest_row['inflow'] # Assuming 'inflow' for now, could be generalized
            }

            self.bus.publish(self.topic, message)
            print(f"Agent '{self.agent_id}' at time {current_time:.2f}: Published data for timestamp {latest_row['timestamp']}.")

            # Update the index to prevent re-publishing
            self.last_published_index = latest_row.name
