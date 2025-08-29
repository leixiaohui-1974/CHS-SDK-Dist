import logging
from typing import Dict, Any, List
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class DataAggregator(Agent):
    """
    A custom agent that subscribes to topics and aggregates the data it receives.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.subscribed_topics = kwargs['subscribed_topics']
        self.aggregated_data: Dict[str, List[Any]] = {topic: [] for topic in self.subscribed_topics}
        self.log = []

        for topic in self.subscribed_topics:
            # Use a factory function (or lambda) to create a listener that captures the topic
            listener = self._create_listener(topic)
            self.message_bus.subscribe(topic, listener)

    def _create_listener(self, topic: str):
        """Creates a callback function that knows which topic it's for."""
        def listener(message: Dict[str, Any]):
            log_entry = f"[{self.agent_id}] Received on '{topic}': {message}"
            logging.info(log_entry)
            self.log.append(log_entry)
            self.aggregated_data[topic].append(message)
        return listener

    def run(self, current_time: float):
        """
        The agent's main loop. For this reactive agent, it does nothing.
        """
        pass
