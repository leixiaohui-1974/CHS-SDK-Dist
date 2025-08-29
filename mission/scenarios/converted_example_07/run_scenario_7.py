import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationLoader
from core_lib.io.yaml_writer import save_history_to_yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """
    Loads and runs the task allocation simulation scenario.
    """
    scenario_path = Path(__file__).parent
    logging.info(f"--- Starting Simulation Scenario: {scenario_path.name} ---")

    # 1. Initialize the loader with the path to our scenario
    logging.info(f"Loading scenario from: {scenario_path}")
    loader = SimulationLoader(scenario_path=str(scenario_path))

    # 2. Load the simulation harness
    harness = loader.load()

    # 3. Get the task manager agent
    task_manager = None
    for agent in harness.agents:
        if agent.agent_id == 'task_manager':
            task_manager = agent
            break

    if not task_manager:
        logging.error("Task manager agent not found in the simulation harness.")
        sys.exit(1)

    # 4. Define the stop condition
    def stop_condition():
        return task_manager.all_tasks_complete

    # 5. Run the simulation with the stop condition
    logging.info("Starting MAS simulation run with a custom stop condition...")
    harness.run_mas_simulation(stop_condition=stop_condition)

    logging.info("Simulation run complete.")

    # 6. Process and save results
    history = harness.history
    logging.info(f"Simulation generated {len(history)} steps of history data.")

    output_path = scenario_path / "output.yml"
    save_history_to_yaml(history, str(output_path))

if __name__ == "__main__":
    main()
