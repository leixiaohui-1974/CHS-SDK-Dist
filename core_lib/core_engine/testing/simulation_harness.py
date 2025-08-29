"""
A testing and simulation harness for running the Smart Water Platform.
"""
from collections import deque
from core_lib.core.interfaces import Simulatable, Agent, Controller
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
from typing import List, Dict, Any, NamedTuple

class ControllerSpec(NamedTuple):
    """Defines the wiring for a controller in a simple simulation."""
    controller: Controller
    controlled_id: str
    observed_id: str
    observation_key: str

class SimulationHarness:
    """
    Manages the setup and execution of a simulation scenario using a graph-based topology.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.duration = config.get('duration', 100)
        self.dt = config.get('dt', 1.0)
        self.history = []

        self.components: Dict[str, Simulatable] = {}
        self.agents: List[Agent] = []
        self.controllers: Dict[str, ControllerSpec] = {}

        # Graph representation: adjacency lists for downstream and upstream connections
        self.topology: Dict[str, List[str]] = {}
        self.inverse_topology: Dict[str, List[str]] = {}
        self.sorted_components: List[str] = []

        self.message_bus = MessageBus()
        print("SimulationHarness created.")

    def add_component(self, component: Simulatable):
        """Adds a physical or logical component to the simulation."""
        # Try to get ID from a `_id` attribute, otherwise fall back to `name`
        id_attr = next((attr for attr in dir(component) if attr.endswith('_id')), None)
        if id_attr:
            component_id = getattr(component, id_attr)
        elif hasattr(component, 'name'):
            component_id = component.name
        else:
            raise ValueError("Component does not have a valid ID attribute (e.g., 'pipe_id') or a 'name' attribute.")
        if component_id in self.components:
            raise ValueError(f"Component with ID '{component_id}' already exists.")
        self.components[component_id] = component
        self.topology[component_id] = []
        self.inverse_topology[component_id] = []
        print(f"Component '{component_id}' added.")

    def add_connection(self, upstream_id: str, downstream_id: str):
        """Adds a directional connection between two components."""
        if upstream_id not in self.components:
            raise ValueError(f"Upstream component '{upstream_id}' not found.")
        if downstream_id not in self.components:
            raise ValueError(f"Downstream component '{downstream_id}' not found.")

        self.topology[upstream_id].append(downstream_id)
        self.inverse_topology[downstream_id].append(upstream_id)
        print(f"Connection added: {upstream_id} -> {downstream_id}")

    def add_agent(self, agent: Agent):
        """Adds an agent to the simulation."""
        self.agents.append(agent)

    def add_controller(self, controller_id: str, controller: Controller, controlled_id: str, observed_id: str, observation_key: str):
        """Associates a controller with a specific component and its observation source."""
        spec = ControllerSpec(controller, controlled_id, observed_id, observation_key)
        self.controllers[controller_id] = spec
        print(f"Controller '{controller_id}' associated with component '{controlled_id}'.")

    def _topological_sort(self):
        """
        Performs a topological sort of the components graph.
        This determines the correct order for stepping through the physical models.
        """
        in_degree = {u: 0 for u in self.topology}
        for u in self.topology:
            for v in self.topology[u]:
                in_degree[v] += 1

        queue = deque([u for u in self.topology if in_degree[u] == 0])

        self.sorted_components = []
        while queue:
            u = queue.popleft()
            self.sorted_components.append(u)

            for v in self.topology[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(self.sorted_components) != len(self.components):
            raise Exception("Graph has at least one cycle, which is not allowed in a water system topology.")

        print("Topological sort complete. Update order determined.")

    def build(self):
        """Finalizes the harness setup by sorting the component graph."""
        self._topological_sort()
        print("Simulation harness build complete and ready to run.")

    def _step_physical_models(self, dt: float, controller_actions: Dict[str, Any] = None):
        if controller_actions is None:
            controller_actions = {}

        new_states = {}
        current_step_outflows = {}

        for component_id in self.sorted_components:
            component = self.components[component_id]
            action = {'control_signal': controller_actions.get(component_id)}

            total_inflow = 0
            for upstream_id in self.inverse_topology.get(component_id, []):
                total_inflow += current_step_outflows.get(upstream_id, 0)

            component.set_inflow(total_inflow)

            if hasattr(component, 'is_stateful') and component.is_stateful:
                total_outflow = 0
                for downstream_id in self.topology.get(component_id, []):
                    downstream_comp = self.components[downstream_id]
                    downstream_action = {}
                    downstream_action['upstream_head'] = component.get_state().get('water_level', 0)

                    if self.topology.get(downstream_id):
                        dds_id = self.topology[downstream_id][0]
                        downstream_action['downstream_head'] = self.components[dds_id].get_state().get('water_level', 0)

                    import copy
                    temp_downstream_comp = copy.deepcopy(downstream_comp)

                    temp_next_state = temp_downstream_comp.step(downstream_action, dt)
                    total_outflow += temp_next_state.get('outflow', 0)

                action['outflow'] = total_outflow

            else:
                if self.inverse_topology.get(component_id):
                    up_id = self.inverse_topology[component_id][0]
                    action['upstream_head'] = self.components[up_id].get_state().get('water_level', 0)
                if self.topology.get(component_id):
                    down_id = self.topology[component_id][0]
                    action['downstream_head'] = self.components[down_id].get_state().get('water_level', 0)

            new_states[component_id] = component.step(action, dt)
            current_step_outflows[component_id] = new_states[component_id].get('outflow', 0)

        for component_id, state in new_states.items():
            self.components[component_id].set_state(state)

    def run_simulation(self):
        """
        Runs a simple, centralized control simulation loop using the graph topology.
        """
        if not self.sorted_components:
            raise Exception("Harness has not been built. Call harness.build() before running.")

        num_steps = int(self.duration / self.dt)
        print(f"Starting simple simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        self.history = []
        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            # 1. Compute control actions
            actions = {}
            for cid, spec in self.controllers.items():
                observed_component = self.components.get(spec.observed_id)
                if not observed_component: continue

                observation_state = observed_component.get_state()
                process_variable = observation_state.get(spec.observation_key)

                if process_variable is not None:
                    control_signal = spec.controller.compute_control_action({'process_variable': process_variable}, self.dt)
                    actions[spec.controlled_id] = control_signal
                    print(f"  Controller '{cid}': Target for '{spec.controlled_id}' = {control_signal:.2f}")

            # 2. Step the physical models in order
            self._step_physical_models(self.dt, actions)

            # 3. Store history
            step_history = {'time': current_time}
            for cid in self.sorted_components:
                step_history[cid] = self.components[cid].get_state()
            self.history.append(step_history)

            # 4. Print state summary (optional)
            # You can customize this to print states of interest
            print("  State Update:")
            for cid in self.sorted_components:
                state = self.components[cid].get_state()
                print(f"    {cid}: {state}")
            print("")

    def run_mas_simulation(self):
        """
        Runs a full Multi-Agent System (MAS) simulation using the graph topology.
        """
        if not self.sorted_components:
            raise Exception("Harness has not been built. Call harness.build() before running.")

        num_steps = int(self.duration / self.dt)
        print(f"Starting MAS simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        self.history = []
        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- MAS Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            print("  Phase 1: Triggering agent perception and action cascade.")
            for agent in self.agents:
                agent.run(current_time)

            print("  Phase 2: Stepping physical models with interactions.")
            self._step_physical_models(self.dt)

            # Store history
            step_history = {'time': current_time}
            for cid in self.sorted_components:
                step_history[cid] = self.components[cid].get_state()
            self.history.append(step_history)

            # Print state summary (optional)
            print("  State Update:")
            for cid in self.sorted_components:
                state_str = ", ".join(f"{k}={v:.2f}" for k, v in self.components[cid].get_state().items())
                print(f"    {cid}: {state_str}")
            print("")

        print("MAS Simulation finished.")
