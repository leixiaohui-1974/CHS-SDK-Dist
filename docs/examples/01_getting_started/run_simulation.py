#!/usr/bin/env python3
"""
Example simulation script for Tutorial 1: A simple reservoir-gate system.

This script demonstrates the basic, non-agent-based simulation mode of the platform.
It sets up a single reservoir with a high water level and a PID controller that
opens a downstream gate to bring the water level down to a desired setpoint.
"""

import sys
import os

# Add the project root to the Python path
# This is necessary to run the script directly from the command line
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def run_getting_started_simulation():
    """
    Sets up and runs the reservoir-gate simulation.
    """
    print("--- Setting up Tutorial 1: Getting Started Simulation ---")

    # 1. --- Component Setup ---

    # Reservoir Model
    reservoir_params = {
        'surface_area': 1.5e6,  # m^2
    }
    reservoir_initial_state = {
        'volume': 21e6,  # m^3, equivalent to 14m * 1.5e6 m^2
        'water_level': 14.0  # m, initial level is above the setpoint
    }
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state=reservoir_initial_state,
        parameters=reservoir_params
    )

    # Gate Model
    gate_params = {
        'max_rate_of_change': 0.1,
        'discharge_coefficient': 0.6,
        'width': 10
    }
    gate_initial_state = {
        'opening': 0.5  # 50% open
    }
    gate = Gate(
        name="gate_1",
        initial_state=gate_initial_state,
        parameters=gate_params
    )

    # PID Controller
    # For a reverse-acting process (opening gate lowers level),
    # the controller gains must be negative.
    pid_controller = PIDController(
        Kp=-0.5,
        Ki=-0.01,
        Kd=-0.1,
        setpoint=12.0,      # Target water level in meters
        min_output=0.0,
        max_output=1.0      # Gate opening is a percentage
    )

    # 2. --- Simulation Harness Setup ---

    simulation_config = {
        'duration': 300,  # Simulate for 300 seconds
        'dt': 1.0         # Time step of 1 second
    }
    harness = SimulationHarness(config=simulation_config)

    # Add components to the harness
    harness.add_component(reservoir)
    harness.add_component(gate)

    # Define the physical connection
    harness.add_connection("reservoir_1", "gate_1")

    # Add the controller and link it to the component it controls and observes
    harness.add_controller(
        controller_id="pid_controller_1",
        controller=pid_controller,
        controlled_id="gate_1",
        observed_id="reservoir_1",
        observation_key="water_level"
    )

    # Finalize the harness setup
    harness.build()

    # 3. --- Run Simulation ---
    print("\n--- Running Simulation ---")
    harness.run_simulation()
    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_getting_started_simulation()
