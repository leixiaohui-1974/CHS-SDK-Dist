# Example 5: Hierarchical Control

This example demonstrates a simple two-level hierarchical control architecture. A central agent issues high-level commands to a local agent, which is then responsible for the low-level control actions.

## Scenario

This scenario builds directly on Example 4. We have the same reservoir-gate system with a local gate control agent.

The hierarchy is structured as follows:
1.  **Local Level**: The `LocalGateControlAgent` is responsible for opening or closing the gate based on its current water level setpoint (initially 51.0m).
2.  **Supervisory Level**: A new `CentralCommandAgent` is introduced. After 200 seconds have passed in the simulation, this agent issues a command to change the system's target setpoint to a more conservative 50.5m.

The local agent receives this new setpoint and adjusts its behavior accordingly, without the central agent needing to know the low-level details of how the gate is operated. This illustrates the separation of concerns in a hierarchical control system.

## Components and Agents

*   **Main Reservoir & Flood Gate**: The physical components.
*   **Inflow Agent**: Provides a constant inflow to the reservoir.
*   **Reservoir Twin Agent**: Publishes the reservoir's state.
*   **Local Gate Control Agent**: Subscribes to the reservoir state and a new command topic. It controls the gate to maintain the current setpoint.
*   **Central Command Agent**: A custom agent that publishes a new setpoint to the command topic after 200 seconds.

## How to Run

To run this simulation, execute the `run.py` script in this directory:

```bash
python run.py
```
You will observe the gate controller maintaining the initial 51.0m setpoint. After 200 seconds, the central agent will issue a new command, and the local controller will begin working to achieve the new 50.5m setpoint.
