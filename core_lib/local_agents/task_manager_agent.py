import logging
from typing import Dict, Any, List
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TaskManagerAgent(Agent):
    """Manages a list of tasks, distributes them, and collects results."""
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.tasks = kwargs['tasks']
        self.task_topic = kwargs['task_topic']
        self.result_topic = kwargs['result_topic']
        self.results_received = []
        self.total_tasks = len(self.tasks)
        self.bus.subscribe(self.result_topic, self.handle_result)
        logging.info(f"[{self.agent_id}] Initialized with {self.total_tasks} tasks.")

    def handle_result(self, message: Dict[str, Any]):
        logging.info(f"[{self.agent_id}] Received result: {message}")
        self.results_received.append(message)

    @property
    def all_tasks_complete(self) -> bool:
        return len(self.results_received) >= self.total_tasks

    def run(self, current_time: float):
        # Publish one task per run cycle if any are left
        if self.tasks:
            task = self.tasks.pop(0)
            task_message = {'task_id': f"task_{task}", 'payload': task}
            logging.info(f"[{self.agent_id}] Publishing task: {task_message}")
            self.bus.publish(self.task_topic, task_message)
