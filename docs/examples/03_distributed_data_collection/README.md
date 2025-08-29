# Example 3: Distributed Data Collection

This example demonstrates a simple distributed data collection scenario.

## Scenario

We have two reservoirs, each with a sensor agent that measures the water level. These sensor agents periodically send their data to a central data aggregator agent. The aggregator agent collects the data and logs it.

This illustrates a fundamental pattern in distributed systems: collecting data from multiple distributed sources for central processing or monitoring.

## Components

*   **Reservoir 1 & 2**: Two physical water reservoirs.
*   **Sensor Agent 1 & 2**: Agents responsible for reading the water level from each reservoir.
*   **Data Aggregator Agent**: A central agent that subscribes to the data from the sensor agents and logs the aggregated data.

## How to Run

To run this simulation, execute the `run.py` script in this directory:

```bash
python run.py
```

The simulation will run for a predefined duration, and the aggregated data will be printed to the console. You can also see the output in the `output.yml` file.
