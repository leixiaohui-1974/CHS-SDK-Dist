"""
An agent that reads time-series data from a CSV and injects it into the simulation.
"""
from core_lib.core.interfaces import Agent, Simulatable
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
import pandas as pd
import logging
from typing import Optional

class CsvInflowAgent(Agent):
    """
    Reads a time-series from a CSV file and publishes it to a message bus topic
    at the corresponding simulation time. This is useful for driving a simulation
    with historical data (e.g., inflows, demands).
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 target_component: Simulatable,
                 csv_file_path: str,
                 time_column: str,
                 data_column: str,
                 inflow_topic: Optional[str] = None):
        """
        Initializes the CsvInflowAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The system's message bus.
            target_component: The simulation component to which the inflow is conceptually applied.
                              The agent will publish to this component's specific inflow topic.
            csv_file_path: The path to the CSV file.
            time_column: The name of the column in the CSV file that contains the time data.
            data_column: The name of the column that contains the inflow data.
            inflow_topic: The specific topic to publish inflow data on. If None, a default
                          is constructed e.g., 'inflow/{component_name}'.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.target_component_name = target_component.name

        if inflow_topic:
            self.inflow_topic = inflow_topic
        else:
            self.inflow_topic = f"inflow/{self.target_component_name}"

        try:
            self.data = pd.read_csv(csv_file_path)
            self.data = self.data.set_index(time_column)
            self.data_column = data_column
            logging.info(f"CsvInflowAgent '{self.agent_id}' initialized. Loaded data from '{csv_file_path}'.")
        except FileNotFoundError:
            logging.error(f"CsvInflowAgent '{self.agent_id}': CSV file not found at '{csv_file_path}'.")
            self.data = None
        except KeyError:
            logging.error(f"CsvInflowAgent '{self.agent_id}': Columns '{time_column}' or '{data_column}' not found in '{csv_file_path}'.")
            self.data = None

    def run(self, current_time: float):
        """
        The main execution logic. At each time step, it checks if there is a
        corresponding entry in the CSV data and publishes it.
        """
        if self.data is None:
            return

        # Find the data point for the current time.
        # We use interpolation for cases where the simulation timestep (dt)
        # is smaller than the data's timestep.
        try:
            # Find the closest index before or at the current time
            # This is a simple way to handle time alignment. More complex methods exist.
            relevant_data = self.data.index[self.data.index <= current_time]
            if not relevant_data.empty:
                closest_time = relevant_data.max()
                inflow_value = self.data.loc[closest_time, self.data_column]

                message: Message = {'inflow_rate': float(inflow_value)}
                self.bus.publish(self.inflow_topic, message)
                # logging.debug(f"Agent '{self.agent_id}' published inflow {inflow_value} at time {current_time}")

        except Exception as e:
            # This can happen if time is out of bounds, etc.
            # logging.warning(f"CsvInflowAgent '{self.agent_id}': Could not retrieve data for time {current_time}. Error: {e}")
            pass
