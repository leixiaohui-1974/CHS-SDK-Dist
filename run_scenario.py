# -*- coding: utf-8 -*-

"""
Generic Simulation Scenario Runner

This script provides a command-line interface to run any simulation scenario
that is defined by a directory of YAML configuration files.
"""
import logging
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path to allow imports from core_lib
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationLoader
from core_lib.io.yaml_writer import save_history_to_yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """
    Loads and runs a simulation scenario from a path specified on the command line.
    """
    parser = argparse.ArgumentParser(description="Run a simulation scenario from a directory of YAML files.")
    parser.add_argument("scenario_path", type=str, help="The path to the scenario directory.")
    args = parser.parse_args()

    scenario_path = Path(args.scenario_path)
    if not scenario_path.is_dir():
        logging.error(f"Error: Provided scenario path is not a valid directory: {scenario_path}")
        sys.exit(1)

    logging.info(f"--- Starting Simulation Scenario: {scenario_path.name} ---")

    # 1. Initialize the loader with the path to our scenario
    logging.info(f"Loading scenario from: {scenario_path}")
    loader = SimulationLoader(scenario_path=str(scenario_path))

    # 2. Load the simulation harness
    # The loader reads the YAML files, instantiates all objects, and wires them up.
    harness = loader.load()

    # 3. Run the simulation
    # The original simulation had a manual pipe burst event. For now, we will run
    # the simulation without it to test the data-driven setup. This can be
    # added back later as a specialized "event injector" agent in agents.yml.
    logging.info("Starting MAS simulation run...")
    harness.run_mas_simulation()

    logging.info("Simulation run complete.")

    # 4. Process and save results
    history = harness.history
    logging.info(f"Simulation generated {len(history)} steps of history data.")

    output_path = scenario_path / "output.yml"
    save_history_to_yaml(history, str(output_path))

if __name__ == "__main__":
    main()
