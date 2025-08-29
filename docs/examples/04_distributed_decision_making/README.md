# Example 4: Distributed Decision Making

This example demonstrates a simple distributed, agent-based control system. An autonomous agent makes a control decision based on local information without the need for a central coordinator.

## Scenario

We have a reservoir that is being filled by a constant inflow. Downstream of the reservoir is a gate. A dedicated gate control agent monitors the reservoir's water level.

The agent's logic is as follows:
- If the water level in the reservoir exceeds a setpoint of 52 meters, the agent will send a command to open the gate.
- If the water level is below 52 meters, the agent will command the gate to close.

This creates a simple "bang-bang" control system where the gate's state is managed decentrally, based only on the perceived state of its direct neighbor.

## Components and Agents

*   **Main Reservoir**: The physical water reservoir.
*   **Flood Gate**: The physical gate.
*   **Inflow Agent**: An agent providing a constant inflow of 15 m^3/s to the reservoir.
*   **Reservoir Twin Agent**: A perception agent that publishes the reservoir's state to the message bus.
*   **Local Gate Control Agent**: A custom control agent that subscribes to the reservoir's state and sends open/close commands to the gate.

## How to Run

To run this simulation, execute the `run.py` script in this directory:

```bash
python run.py
```
You will see the simulation running and the gate control agent logging its decisions as the water level changes.
