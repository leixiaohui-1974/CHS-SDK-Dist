import logging
import random
import time
from typing import Dict, Any
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class WorkerAgent(Agent):
    """Picks up tasks, processes them, and returns results."""
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.task_topic = kwargs['task_topic']
        self.result_topic = kwargs['result_topic']
        self.is_busy = False
        self.bus.subscribe(self.task_topic, self.handle_task)

    def handle_task(self, message: Dict[str, Any]):
        if self.is_busy:
            return # Already working on a task

        self.is_busy = True
        task_id = message.get('task_id', 'unknown_task')
        payload = message.get('payload')
        logging.info(f"[{self.agent_id}] Picked up task: {task_id}")

        # Simulate work
        processing_time = random.uniform(0.5, 2.0)
        time.sleep(processing_time)
        result = payload * payload # Square the number

        result_message = {'task_id': task_id, 'result': result, 'worker_id': self.agent_id}
        self.bus.publish(self.result_topic, result_message)
        logging.info(f"[{self.agent_id}] Completed task: {task_id}, result: {result}")
        self.is_busy = False

    def run(self, current_time: float):
        pass # Reactive agent
