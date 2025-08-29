"""
A utility for writing simulation results to YAML format.
"""
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any

def save_history_to_yaml(history: List[Dict[str, Any]], output_path: str):
    """
    Saves the simulation history to a YAML file.

    The history is a list of dictionaries, where each dictionary represents
    a time step. This function writes it in a human-readable YAML format.

    Args:
        history: The simulation history data from SimulationHarness.
        output_path: The full path for the output YAML file.
    """
    output_path = Path(output_path)
    logging.info(f"Saving simulation history to '{output_path}'...")

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            # Use a custom Dumper to improve formatting if needed, but default is fine for now.
            # The block style is generally more readable for this kind of data.
            yaml.dump({'simulation_history': history}, f, default_flow_style=False, sort_keys=False)
        logging.info("Successfully saved history to YAML.")
    except Exception as e:
        logging.error(f"Failed to save history to YAML file at '{output_path}': {e}")
