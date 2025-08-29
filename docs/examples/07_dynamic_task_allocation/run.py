#!/usr/bin/env python3
"""
Example runner for Scenario 7: Dynamic Task Allocation.
"""

import sys
import os
import logging
import random
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TaskManagerAgent(Agent):
    """Manages a list of tasks, distributes them, and collects results."""
    def __init__(self, agent_id: str, message_bus: MessageBus, tasks: List[Any], task_topic: str, result_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.tasks_to_send = tasks
        self.task_topic = task_topic
        self.results_received = []
        self.total_tasks = len(tasks)
        self.bus.subscribe(result_topic, self.handle_result)
        logging.info(f"[{self.agent_id}] Initialized with {self.total_tasks} tasks.")

    def handle_result(self, message: Dict[str, Any]):
        logging.info(f"[{self.agent_id}] Received result: {message}")
        self.results_received.append(message)

    @property
    def all_tasks_complete(self) -> bool:
        return len(self.results_received) >= self.total_tasks

    def run(self, current_time: float):
        # Publish one task per run cycle if any are left
        if self.tasks_to_send:
            task = self.tasks_to_send.pop(0)
            task_message = {'task_id': f"task_{task}", 'payload': task}
            logging.info(f"[{self.agent_id}] Publishing task: {task_message}")
            self.bus.publish(self.task_topic, task_message)


class WorkerAgent(Agent):
    """Picks up tasks, processes them, and returns results."""
    def __init__(self, agent_id: str, message_bus: MessageBus, task_topic: str, result_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.task_topic = task_topic
        self.result_topic = result_topic
        self.is_busy = False
        self.bus.subscribe(task_topic, self.handle_task)

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


def run_task_allocation_simulation():
    """Sets up and runs the task allocation simulation."""
    scenario_path = Path(__file__).parent
    logging.info("--- Setting up Example 7: Dynamic Task Allocation ---")

    # Since there's no harness, we create the bus and agents directly
    message_bus = MessageBus()

    # Load agent configs
    import yaml
    agents_config = yaml.safe_load((scenario_path / 'agents.yml').read_text())

    agents = []
    task_manager = None
    for agent_conf in agents_config.get('agents', []):
        agent_id, cls, cfg = agent_conf['id'], agent_conf['class'], agent_conf.get('config', {})
        instance = None
        if cls == "TaskManagerAgent":
            instance = TaskManagerAgent(agent_id=agent_id, message_bus=message_bus, **cfg)
            task_manager = instance
        elif cls == "WorkerAgent":
            instance = WorkerAgent(agent_id=agent_id, message_bus=message_bus, **cfg)

        if instance:
            agents.append(instance)

    if not task_manager:
        logging.error("Task manager not found in agents.yml")
        return

    # Custom simulation loop
    logging.info("\n--- Running Simulation ---")
    current_time = 0
    while not task_manager.all_tasks_complete:
        logging.info(f"--- Simulation Step, Time: {current_time:.2f}s ---")
        # In each step, we give the manager a chance to publish a task
        task_manager.run(current_time)
        # The workers will react to the published message within the same step
        time.sleep(0.1) # A small delay to allow for message handling
        current_time += 1
        if current_time > 60: # Failsafe timeout
            logging.error("Simulation timed out.")
            break

    logging.info("\n--- Simulation Complete ---")
    logging.info(f"All {task_manager.total_tasks} tasks processed.")
    logging.info(f"Final results: {task_manager.results_received}")


if __name__ == "__main__":
    run_task_allocation_simulation()
