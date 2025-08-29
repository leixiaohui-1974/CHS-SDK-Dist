"""
Mission Example 5.1: Water Turbine and Spillway Gate Simulation (Simplified)

Goal: Independently demonstrate the physical behavior of a single water turbine
and spillway gate, and the effect of downstream tailwater elevation (顶托).

This script simplifies the problem by running two separate simulations:
1. A network with only a turbine.
2. A network with only a gate.

This avoids the complexity of parallel network modeling, which the current solver
does not support, but still allows for the verification of the components' physical
behavior as requested in the mission prompt.
"""
import numpy as np
import matplotlib.pyplot as plt

from core_lib.core_engine.solver.network_solver import NetworkSolver
from core_lib.physical_objects.st_venant_reach import StVenantReach
from core_lib.hydro_nodes.turbine_node import TurbineNode
from core_lib.hydro_nodes.gate_node import GateNode

def run_single_component_simulation(component_type: str):
    """
    Sets up and runs a simple simulation for a single component (turbine or gate).
    """
    print(f"\n--- Setting up Simulation for: {component_type.upper()} ---")

    # --- 1. Simulation Parameters ---
    sim_dt = 10.0
    num_steps = 100

    # --- 2. Physical & Initial Conditions ---
    initial_depth = 15.0
    initial_inflow = 150.0

    # --- 3. Create Components ---
    forebay = StVenantReach(
        name="forebay", length=1000, num_points=11,
        bottom_width=20, side_slope_z=2, manning_n=0.03, slope=0.001,
        initial_H=np.full(11, initial_depth),
        initial_Q=np.full(11, initial_inflow)
    )
    tailrace = StVenantReach(
        name="tailrace", length=1000, num_points=11,
        bottom_width=20, side_slope_z=2, manning_n=0.03, slope=0.001,
        initial_H=np.full(11, initial_depth - 5.0), # Start with a 5m head diff
        initial_Q=np.full(11, initial_inflow)
    )

    if component_type == 'turbine':
        node = TurbineNode(name="turbine1", equivalent_area=25.0, discharge_coeff=0.9)
    elif component_type == 'gate':
        node = GateNode(name="gate1", width=15, discharge_coeff=0.62)
    else:
        raise ValueError("Invalid component type")

    # --- 4. Build Network ---
    solver = NetworkSolver(dt=sim_dt, theta=0.8)
    solver.add_component(forebay)
    solver.add_component(tailrace)
    solver.add_component(node)

    node.link_to_reaches(up_obj=forebay, down_obj=tailrace)

    # --- 5. Boundary Conditions ---
    solver.add_boundary_condition(forebay, 'Q', 0, lambda t: initial_inflow)
    # Dynamic tailrace level to show 顶托 effect (tailwater elevation effect)
    # The tailrace level will rise from 10m to 12m over the simulation
    solver.add_boundary_condition(tailrace, 'H', -1, lambda t: (initial_depth - 5.0) + 2.0 * (t / (num_steps * sim_dt)))

    # --- 6. Simulation ---
    results = {'time': [], 'H_up': [], 'H_down': [], 'Q': []}

    print(f"--- Starting {component_type.upper()} Simulation ---")
    for i in range(num_steps):
        current_time = i * solver.dt

        # Change gate opening mid-simulation if it's a gate
        if isinstance(node, GateNode) and i == num_steps // 2:
            print("!!! Reducing Gate Opening !!!")
            node.set_opening(0.2)

        solver.step(current_time)

        results['time'].append(current_time)
        results['H_up'].append(forebay.H[-1])
        results['H_down'].append(tailrace.H[0])
        results['Q'].append(forebay.Q[-1])

    print("--- Simulation Finished ---")
    return results

if __name__ == "__main__":
    turbine_results = run_single_component_simulation('turbine')
    gate_results = run_single_component_simulation('gate')

    # --- 7. Plotting ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    fig.suptitle('Mission 5.1: Turbine & Gate Behavior with Tailwater Effects', fontsize=16)

    # Plot water levels and flows for Turbine
    ax1.plot(turbine_results['time'], turbine_results['H_up'], 'b-', label='Upstream Head (Turbine)')
    ax1.plot(turbine_results['time'], turbine_results['H_down'], 'b--', label='Downstream Head (Turbine)')
    ax1_twin = ax1.twinx()
    ax1_twin.plot(turbine_results['time'], turbine_results['Q'], 'c-', label='Turbine Flow (Q)', alpha=0.7)
    ax1.set_ylabel('Water Level (m)')
    ax1_twin.set_ylabel('Flow (m^3/s)')
    ax1.set_title('Turbine Simulation')
    ax1.grid(True)
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1_twin.legend(lines + lines2, labels + labels2, loc='upper right')

    # Plot water levels and flows for Gate
    ax2.plot(gate_results['time'], gate_results['H_up'], 'r-', label='Upstream Head (Gate)')
    ax2.plot(gate_results['time'], gate_results['H_down'], 'r--', label='Downstream Head (Gate)')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(gate_results['time'], gate_results['Q'], 'm-', label='Gate Flow (Q)', alpha=0.7)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Water Level (m)')
    ax2_twin.set_ylabel('Flow (m^3/s)')
    ax2.set_title('Gate Simulation')
    ax2.grid(True)
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2_twin.legend(lines + lines2, labels + labels2, loc='upper right')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("mission_5_1_results.png")
    print("\nSaved combined plot to mission_5_1_results.png")
    plt.show()
