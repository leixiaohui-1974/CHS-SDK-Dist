"""
Agent for managing and executing test scenarios.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import List, Dict, Any

class ScenarioAgent(Agent):
    """
    Manages the execution of a predefined scenario script.

    A scenario consists of a timeline of events, such as injecting disturbances
    (e.g., sudden rainfall, pipe burst) or issuing high-level commands
    at specific simulation times. This is useful for testing the system's
    response to various situations.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, scenario_script: List[Dict[str, Any]]):
        """
        Initializes the ScenarioAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            scenario_script: A list of timed events. Each event is a dict
                             with 'time', 'topic', and 'message' keys.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.script = sorted(scenario_script, key=lambda x: x['time'])
        self.event_index = 0

        print(f"ScenarioAgent '{self.agent_id}' initialized with a script of {len(self.script)} events.")

    def run(self, current_time: float):
        """
        Checks the scenario script and executes any events scheduled for the current time.
        """
        while self.event_index < len(self.script) and self.script[self.event_index]['time'] <= current_time:
            event = self.script[self.event_index]

            topic = event['topic']
            message = event['message']

            self.bus.publish(topic, message)

            print(f"[{self.agent_id} at {current_time}] Executed scenario event: Published to '{topic}' -> {message}")

            self.event_index += 1
