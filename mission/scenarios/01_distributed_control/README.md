# Example 1: Distributed Control

This example demonstrates a simple distributed control scenario.

## Scenario

We have a central reservoir whose water level is monitored. The reservoir has two outflow gates. A central supervisory control agent monitors the water level of the reservoir. If the water level exceeds a certain threshold, the supervisory agent commands the two gate controller agents to open the gates. When the water level is back to normal, the gates are commanded to close.

This illustrates a fundamental pattern in distributed systems: a central agent making decisions and sending commands to distributed agents to perform actions.

## Components

*   **Reservoir**: A physical water reservoir.
*   **Gate 1 & 2**: Two physical gates that control the outflow of the reservoir.
*   **Reservoir-Sensor**: A digital twin agent that publishes the water level of the reservoir.
*   **Gate-Controller-1 & 2**: Agents responsible for controlling each gate.
*   **Supervisory-Control-Agent**: A central agent that subscribes to the reservoir's water level, and sends commands to the gate controllers.

## How to Run

To run this simulation, execute the `run.py` script in this directory:

```bash
python run.py
```

The simulation will run for a predefined duration. You will see the log messages from the agents, indicating the water level and the gate commands.
