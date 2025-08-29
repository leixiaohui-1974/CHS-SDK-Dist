# Example 7: Dynamic Task Allocation

This example moves away from physical simulation to demonstrate a common distributed computing pattern: dynamic task allocation using a manager-worker architecture, where workers pull tasks from a central manager.

## Scenario

This simulation showcases how a central manager can distribute a queue of computational tasks to a pool of available workers based on their readiness.

The system is composed of:
1.  **A `TaskManagerAgent`**: This agent acts as the "manager". It holds a queue of tasks. It waits for workers to announce their availability.
2.  **A pool of `WorkerAgent`s**: We instantiate three worker agents. When a worker is ready to work (at the start, and after completing a task), it publishes a `worker_ready` message to a common request topic. The manager receives this and sends a single task to that specific worker's private topic. The worker performs its computation and sends the result back to a common results topic.

This "pull-based" architecture ensures that each task is only processed by one worker, and that work is dynamically balanced across the available pool. The simulation ends once the manager has received all the results for the tasks it distributed.

## Components and Agents

*   **TaskManagerAgent**: The central manager.
*   **WorkerAgent (x3)**: A pool of three identical agents that perform the computations.

This example does not use any physical components.

## How to Run

To run this simulation, execute the `run.py` script in this directory:

```bash
python run.py
```
You will see the manager publishing tasks and the workers picking them up and processing them in parallel. The output will show the final aggregated results.
