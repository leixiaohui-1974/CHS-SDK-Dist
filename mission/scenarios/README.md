# Data-Driven Simulation Scenarios

This directory contains self-contained simulation scenarios that are defined by YAML configuration files. This data-driven approach allows for rapid development and testing of different system configurations without changing the core simulation code.

## Running a Scenario

Each scenario can be executed using the generic `run_scenario.py` script located in the project root. You must pass the path to the specific scenario directory you wish to run as a command-line argument.

For example, to run the `yinchuojiliao` scenario, execute the following command from the project's root directory:

```bash
python run_scenario.py mission/scenarios/yinchuojiliao
```

After the simulation completes, the output data will be saved as `output.yml` inside the corresponding scenario directory.

## Scenario Directory Structure

Each scenario must be a directory containing the following four YAML files:

- `config.yml`: Defines global simulation parameters.
- `components.yml`: Defines all physical components (e.g., reservoirs, pipes).
- `topology.yml`: Defines the connections between the physical components.
- `agents.yml`: Defines all software agents and controllers.
- `data/` (Optional): A directory to hold any supplementary data files, such as CSVs for inflow data.

### `config.yml`

This file specifies the overall settings for the simulation run.

**Structure:**
```yaml
simulation:
  duration: 168  # Total duration of the simulation in hours
  dt: 1.0      # The time step for each iteration in hours
```

### `components.yml`

This file defines every physical object in the simulation.

**Structure:**
```yaml
components:
  - id: my_component_id          # A unique identifier for the component
    class: Reservoir             # The Python class name of the component model
    initial_state:               # The starting state of the component
      water_level: 350.0
      # ... other state variables
    parameters:                  # Fixed physical parameters of the component
      surface_area: 5.0e+7
      # ... other parameters
```

### `topology.yml`

This file defines how the physical components are connected to each other in a directed graph.

**Structure:**
```yaml
connections:
  - upstream: component_id_1     # The ID of the upstream component
    downstream: component_id_2   # The ID of the downstream component
  # ... more connections
```

### `agents.yml`

This file defines all the "brains" of the system: the agents and simple controllers.

**Structure:**
The file has two main keys: `controllers` and `agents`.

- **`controllers`**: For simple controllers (like PIDs) that are wired directly by the simulation harness.
  ```yaml
  controllers:
    - id: my_pid_controller
      class: PIDController
      controlled_id: gate_to_control   # ID of the component to control
      observed_id: reservoir_to_watch  # ID of the component to observe
      observation_key: water_level     # The state variable to use as input
      config:                          # Parameters for the controller's constructor
        Kp: -0.1
        Ki: -0.01
        # ... other PID parameters
  ```

- **`agents`**: For more complex agents that participate in the main agent-based simulation loop.
  ```yaml
  agents:
    - id: my_digital_twin
      class: DigitalTwinAgent
      config:
        simulated_object_id: component_to_twin # The ID of the component this agent is a twin of
        state_topic: "state/my_topic"          # The message bus topic to publish state to

    - id: my_csv_reader
      class: CsvInflowAgent
      config:
        target_component_id: reservoir_to_fill # The component to receive the inflow
        csv_file: data/inflow_data.csv         # Path to the data file, relative to the scenario dir
        time_column: time_hr
        data_column: inflow_m3s
  ```
The `config` block for each agent contains the specific parameters needed for its constructor. The YAML loader dynamically constructs the agent based on its `class`.
