#!/usr/bin/env python3
"""
Example simulation script for Tutorial 2: A multi-component system.

This script demonstrates a more complex simulation with multiple, interconnected
components and two independent controllers.

The physical topology is:
Reservoir -> Gate 1 -> RiverChannel -> Gate 2

The control objectives are:
1. Control the Reservoir's water level by adjusting Gate 1.
2. Control the RiverChannel's volume by adjusting Gate 2.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def run_multi_component_simulation():
    """
    Sets up and runs the multi-component simulation.
    """
    print("--- Setting up Tutorial 2: Multi-Component Simulation ---")

    # 1. --- Component Setup ---

    # Reservoir
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'water_level': 15.0, 'volume': 15.0 * 1e6},
        parameters={'surface_area': 1e6}
    )

    # Gate 1 (downstream of Reservoir)
    gate1 = Gate(
        name="gate_1",
        initial_state={'opening': 0.25},
        parameters={'discharge_coefficient': 0.8, 'width': 12}
    )

    # River Channel (downstream of Gate 1)
    channel = RiverChannel(
        name="channel_1",
        initial_state={'volume': 500000},
        parameters={'k': 0.0001} # Storage coefficient
    )

    # Gate 2 (downstream of River Channel)
    gate2 = Gate(
        name="gate_2",
        initial_state={'opening': 0.5},
        parameters={'discharge_coefficient': 0.7, 'width': 10}
    )

    # 2. --- Controller Setup ---

    # Controller 1: Reservoir Level Control (controls gate_1)
    # This is a direct-acting process: to raise the level, we need to close the gate (reduce opening).
    # A positive error (level is too low) should result in a negative action (closing the gate).
    # Therefore, the gains should be negative.
    controller1 = PIDController(
        Kp=-0.2, Ki=-0.01, Kd=-0.05,
        setpoint=18.0, # Target reservoir level
        min_output=0.0, max_output=1.0
    )

    # Controller 2: Channel Volume Control (controls gate_2)
    # This is a reverse-acting process: to lower the volume, we need to open the gate (increase opening).
    # A positive error (volume is too high) should result in a positive action (opening the gate).
    # Therefore, the gains should be negative.
    controller2 = PIDController(
        Kp=-1e-5, Ki=-1e-7, Kd=-1e-6,
        setpoint=4e5, # Target channel volume
        min_output=0.0, max_output=1.0
    )

    # 3. --- Simulation Harness Setup ---

    harness = SimulationHarness(config={'duration': 500, 'dt': 1.0})

    # Add all components
    harness.add_component(reservoir)
    harness.add_component(gate1)
    harness.add_component(channel)
    harness.add_component(gate2)

    # Define the physical connections to establish the topology
    harness.add_connection("reservoir_1", "gate_1")
    harness.add_connection("gate_1", "channel_1")
    harness.add_connection("channel_1", "gate_2")

    # Add the controllers and wire them to the system
    harness.add_controller(
        controller_id="res_level_ctrl",
        controller=controller1,
        controlled_id="gate_1",
        observed_id="reservoir_1",
        observation_key="water_level"
    )
    harness.add_controller(
        controller_id="chan_vol_ctrl",
        controller=controller2,
        controlled_id="gate_2",
        observed_id="channel_1",
        observation_key="volume"
    )

    # Finalize the harness setup
    harness.build()

    # 4. --- Run Simulation ---
    print("\n--- Running Simulation ---")
    harness.run_simulation()
    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_multi_component_simulation()
