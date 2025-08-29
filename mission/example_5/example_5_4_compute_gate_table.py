"""
Mission Example 5.4: Compute Spillway Gate Flow Allocation Table

This script generates a lookup table for operating a series of 5 spillway gates
based on a total discharge target and the current hydraulic head. The logic
follows a set of pre-defined safety and operational rules to ensure structural
safety and prevent adverse hydraulic conditions (like flow deviation).
"""
import numpy as np
import pandas as pd
import os

# --- Constants ---
NUM_GATES = 5
G = 9.81    # Gravity
RHO = 1000  # Water density

# --- Gate Physical Parameters (assuming identical gates) ---
GATE_WIDTH = 10.0  # meters
DISCHARGE_COEFF = 0.65
MAX_OPENING = 5.0 # meters

def get_flow_for_opening(opening, head):
    """Calculates flow for a single gate given its opening and head."""
    if head <= 0 or opening <= 0:
        return 0.0
    area = GATE_WIDTH * opening
    flow = DISCHARGE_COEFF * area * np.sqrt(2 * G * head)
    return flow

def get_opening_for_flow(flow, head):
    """Calculates the required opening for a single gate to pass a given flow."""
    if head <= 0 or flow <= 0:
        return 0.0

    denominator = DISCHARGE_COEFF * GATE_WIDTH * np.sqrt(2 * G * head)
    if denominator < 1e-6:
        return float('inf') # Cannot achieve flow

    opening = flow / denominator
    return min(opening, MAX_OPENING) # Cap at max opening

def calculate_gate_openings(total_target_flow, head):
    """
    Calculates the individual openings for 5 gates based on a total flow target,
    following a strict set of operational rules.

    Rules:
    1. Symmetrical opening sequence for stability: 3 -> 2&4 -> 1&5
    2. Sequential operation: A gate is only opened after the previous ones in the
       sequence are fully open.
    3. All active paired gates (2&4, 1&5) must have the same opening.
    """
    openings = np.zeros(NUM_GATES)
    flow_achieved = 0.0
    flow_remaining = total_target_flow

    # Opening sequence: Central gate first, then pairs outwards.
    # Indices: Gate 3 is at index 2, Gate 2/4 at 1/3, Gate 1/5 at 0/4
    sequence = [(2,), (1, 3), (0, 4)]

    for indices in sequence:
        if flow_remaining <= 0:
            break

        # Calculate the required opening for the next gate(s) in the sequence
        num_gates_in_group = len(indices)

        # Flow to be handled by this group
        target_flow_per_gate = flow_remaining / num_gates_in_group

        # Calculate the opening required for this flow
        required_opening = get_opening_for_flow(target_flow_per_gate, head)

        # Apply the opening to all gates in the current group
        for idx in indices:
            openings[idx] = required_opening

        # Update the flow achieved and remaining
        flow_from_this_group = get_flow_for_opening(required_opening, head) * num_gates_in_group
        flow_achieved += flow_from_this_group
        flow_remaining -= flow_from_this_group

        # If the gates in this group are not fully open, we are done.
        if required_opening < MAX_OPENING:
            break

    return openings

def generate_gate_allocation_table():
    """
    Main function to generate and save the gate flow allocation table.
    """
    print("--- Generating Spillway Gate Flow Allocation Table ---")

    # Define the grid of setpoints to calculate
    head_range = np.arange(10, 15.5, 0.5)  # Upstream water level
    # Total flow from 0 to 2500 m^3/s, which should be enough to open all gates
    flow_range = np.arange(0, 2501, 10)

    table_data = []

    for head in head_range:
        for target_flow in flow_range:
            # For simplicity, assuming downstream head is 0 (free discharge)
            # A more complex model could include tailwater level.
            effective_head = head

            if effective_head <= 0:
                continue

            openings = calculate_gate_openings(target_flow, effective_head)

            row = {'target_flow_m3s': target_flow, 'head_m': head}
            for i in range(NUM_GATES):
                row[f'gate_{i+1}_opening_m'] = openings[i]
            table_data.append(row)

    # --- Save the table to a CSV file ---
    df = pd.DataFrame(table_data)

    output_dir = "mission/data"
    # The directory should already exist from the previous step, but check just in case
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, "gate_flow_allocation_table.csv")
    df.to_csv(output_path, index=False)

    print(f"\nSuccessfully generated and saved gate allocation table to:\n{output_path}")
    print("\nTable Preview (example at Head = 12.0m):")
    print(df[df['head_m'] == 12.0].iloc[::25]) # Print every 25th row for this head

if __name__ == "__main__":
    generate_gate_allocation_table()
