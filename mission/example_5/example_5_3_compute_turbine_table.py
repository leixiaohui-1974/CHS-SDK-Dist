"""
Mission Example 5.3: Compute Turbine Economic Operation Table

This script generates a lookup table for the most efficient distribution of a
total power target among a set of non-identical turbines. This is a classic
economic dispatch problem. The resulting table can be used by a control agent
for real-time decision-making, converting a complex optimization problem into a
fast table lookup.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from itertools import combinations
import os

# --- Constants ---
NUM_TURBINES = 6
RHO = 1000  # Water density
G = 9.81    # Gravity

def get_turbine_efficiency(power_mw: float, head_m: float, params: dict) -> float:
    """
    Calculates the efficiency of a single turbine based on its power output and head.
    This is a placeholder model. Real-world curves are much more complex.

    Args:
        power_mw: Power output of the turbine in MW.
        head_m: The hydraulic head in meters.
        params: A dictionary of parameters for the turbine's curve.

    Returns:
        The efficiency (0.0 to 1.0).
    """
    p_opt = params['p_opt']
    p_max = params['p_max']
    base_eff = params['base_eff']

    if power_mw <= 0 or power_mw > p_max:
        return 0

    # Efficiency penalty for deviating from optimal power
    power_penalty = ((power_mw - p_opt) / p_opt)**2

    # Efficiency penalty for deviating from optimal head (e.g., 12m)
    head_penalty = ((head_m - 12) / 12)**2

    efficiency = base_eff * (1 - power_penalty - head_penalty)
    return max(0, efficiency)

def power_to_flow(power_mw: float, head_m: float, efficiency: float) -> float:
    """Calculates flow rate (m^3/s) required for a given power output."""
    if efficiency <= 0:
        return float('inf') # Infinite flow for zero efficiency
    power_watts = power_mw * 1e6
    return power_watts / (efficiency * RHO * G * head_m)

def objective_function(power_allocations, head_m, turbine_params):
    """The function to minimize: total flow rate."""
    total_flow = 0
    for i, p_mw in enumerate(power_allocations):
        eff = get_turbine_efficiency(p_mw, head_m, turbine_params[i])
        total_flow += power_to_flow(p_mw, head_m, eff)
    return total_flow

def optimize_for_combination(target_power, head, num_active, turbine_indices, all_params):
    """
    Finds the best power distribution for a given set of active turbines.
    """
    active_params = [all_params[i] for i in turbine_indices]

    # Constraint: sum of power allocations must equal the target power
    constraints = ({'type': 'eq', 'fun': lambda p: np.sum(p) - target_power})

    # Bounds for each active turbine (p_min to p_max)
    bounds = [(p['p_min'], p['p_max']) for p in active_params]

    # Initial guess: equal distribution
    initial_guess = [target_power / num_active] * num_active

    result = minimize(
        objective_function,
        initial_guess,
        args=(head, active_params),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    if result.success:
        final_allocations = np.zeros(NUM_TURBINES)
        total_flow = result.fun
        for i, idx in enumerate(turbine_indices):
            final_allocations[idx] = result.x[i]
        return total_flow, final_allocations
    else:
        return float('inf'), np.zeros(NUM_TURBINES)

def generate_economic_dispatch_table():
    """
    Main function to generate and save the dispatch table.
    """
    print("--- Generating Turbine Economic Operation Table ---")

    # Define slightly different parameters for each of the 6 turbines
    turbine_params = [
        {'id': 1, 'p_min': 2, 'p_opt': 10, 'p_max': 15, 'base_eff': 0.90},
        {'id': 2, 'p_min': 2, 'p_opt': 11, 'p_max': 15, 'base_eff': 0.91},
        {'id': 3, 'p_min': 2, 'p_opt': 9.5, 'p_max': 14, 'base_eff': 0.89},
        {'id': 4, 'p_min': 2.5, 'p_opt': 12, 'p_max': 16, 'base_eff': 0.92},
        {'id': 5, 'p_min': 2.5, 'p_opt': 10.5, 'p_max': 15, 'base_eff': 0.90},
        {'id': 6, 'p_min': 3, 'p_opt': 12, 'p_max': 16, 'base_eff': 0.91},
    ]

    # Define the grid of setpoints to calculate
    head_range = np.arange(10, 15.5, 0.5)
    power_range = np.arange(5, 101, 1) # Total power from 5 to 100 MW

    table_data = []

    for head in head_range:
        for p_total in power_range:
            print(f"Calculating for Head: {head:.1f}m, Total Power: {p_total} MW...")

            best_flow = float('inf')
            best_allocations = np.zeros(NUM_TURBINES)

            # --- Exhaustive search over on/off combinations ---
            for num_on in range(1, NUM_TURBINES + 1):
                # Iterate through all combinations of 'num_on' turbines
                for turbine_indices in combinations(range(NUM_TURBINES), num_on):

                    # Simple check to prune combinations that cannot meet the power target
                    max_power_for_combo = sum(turbine_params[i]['p_max'] for i in turbine_indices)
                    min_power_for_combo = sum(turbine_params[i]['p_min'] for i in turbine_indices)
                    if p_total < min_power_for_combo or p_total > max_power_for_combo:
                        continue

                    flow, allocations = optimize_for_combination(p_total, head, num_on, turbine_indices, turbine_params)

                    if flow < best_flow:
                        best_flow = flow
                        best_allocations = allocations

            # Store the best result found for this head/power setpoint
            if best_flow != float('inf'):
                overall_efficiency = (p_total * 1e6) / (best_flow * RHO * G * head)
                row = {
                    'target_power_mw': p_total,
                    'head_m': head,
                    'total_flow_m3s': best_flow,
                    'overall_efficiency': overall_efficiency
                }
                for i in range(NUM_TURBINES):
                    row[f'turbine_{i+1}_power_mw'] = best_allocations[i]
                table_data.append(row)

    # --- Save the table to a CSV file ---
    if not table_data:
        print("No valid operating points found. Table is empty.")
        return

    df = pd.DataFrame(table_data)

    output_dir = "mission/data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, "turbine_economic_table.csv")
    df.to_csv(output_path, index=False)

    print(f"\nSuccessfully generated and saved economic dispatch table to:\n{output_path}")
    print("\nTable Preview:")
    print(df.head())
    print("...")
    print(df.tail())

if __name__ == "__main__":
    generate_economic_dispatch_table()
