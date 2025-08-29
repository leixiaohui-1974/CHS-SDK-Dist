"""
Loads a simulation scenario from a set of YAML configuration files.
"""
import yaml
from pathlib import Path
import logging
import importlib

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class SimulationLoader:
    """
    Reads a directory of YAML files to configure and instantiate a simulation,
    including the physical components, topology, agents, and controllers.
    """

    def __init__(self, scenario_path: str):
        """
        Initializes the loader with the path to the scenario directory.

        Args:
            scenario_path: The path to the directory containing config.yml,
                           components.yml, topology.yml, and agents.yml.
        """
        self.scenario_path = Path(scenario_path)
        self.config = self._load_yaml('config.yml')
        self.components_config = self._load_yaml('components.yml')
        self.topology_config = self._load_yaml('topology.yml')
        self.agents_config = self._load_yaml('agents.yml')

        self.harness = None
        self.message_bus = None
        self.component_instances = {}

        logging.info(f"SimulationLoader initialized for scenario: {self.scenario_path.name}")

    def _load_yaml(self, file_name: str):
        """Loads a single YAML file from the scenario directory."""
        file_path = self.scenario_path / file_name
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {file_path}")
            return None
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file {file_path}: {e}")
            return None

    def load(self) -> SimulationHarness:
        """
        Loads, instantiates, and wires up the full simulation.

        Returns:
            A fully configured SimulationHarness instance, ready to be run.
        """
        if not all([self.config, self.components_config, self.topology_config, self.agents_config]):
            raise ValueError("One or more configuration files failed to load. Cannot build simulation.")

        self._setup_infrastructure()
        self._load_components()
        self._load_topology()
        self._load_agents_and_controllers()

        logging.info("Simulation loaded successfully. Building harness...")
        self.harness.build()
        logging.info("Harness built. Loader is ready.")
        return self.harness

    def _get_class(self, class_path: str):
        """Dynamically imports and returns a class object from a string path."""
        try:
            # We need to map the short class names from YAML (e.g., "Reservoir")
            # to their full Python paths (e.g., "core_lib.physical_objects.reservoir.Reservoir").
            # This is a hardcoded but clear mapping. A more complex system could use reflection.

            # This mapping translates short names from YAML to full Python class paths.
            CLASS_MAP = {
                # Physical Components
                "Reservoir": "core_lib.physical_objects.reservoir.Reservoir",
                "Gate": "core_lib.physical_objects.gate.Gate",
                "RiverChannel": "core_lib.physical_objects.river_channel.RiverChannel",
                "Canal": "core_lib.physical_objects.canal.Canal",
                "Pipe": "core_lib.physical_objects.pipe.Pipe",
                "Valve": "core_lib.physical_objects.valve.Valve",
                "Pump": "core_lib.physical_objects.pump.Pump",
                "Lake": "core_lib.physical_objects.lake.Lake",
                "WaterTurbine": "core_lib.physical_objects.water_turbine.WaterTurbine",

                # Controllers
                "PIDController": "core_lib.local_agents.control.pid_controller.PIDController",

                # Agents
                "DigitalTwinAgent": "core_lib.local_agents.perception.digital_twin_agent.DigitalTwinAgent",
                "LocalControlAgent": "core_lib.local_agents.control.local_control_agent.LocalControlAgent",
                "EmergencyAgent": "core_lib.local_agents.supervisory.emergency_agent.EmergencyAgent",
                "CentralDispatcherAgent": "core_lib.local_agents.supervisory.central_dispatcher_agent.CentralDispatcherAgent",
                "CsvInflowAgent": "core_lib.data_access.csv_inflow_agent.CsvInflowAgent",
                "CommunicationProxyAgent": "core_lib.distributor.communication_proxy_agent.CommunicationProxyAgent",
                "ConstantInflowAgent": "core_lib.local_agents.disturbances.inflow_agent.ConstantInflowAgent",
                "DataAggregator": "core_lib.local_agents.data_aggregator_agent.DataAggregator",
                "LocalGateControlAgent": "core_lib.local_agents.control.local_gate_control_agent.LocalGateControlAgent",
                "FailureInjectionAgent": "core_lib.local_agents.disturbances.failure_injection_agent.FailureInjectionAgent",
                "SupervisoryAgent": "core_lib.local_agents.supervisory.supervisory_agent.SupervisoryAgent",
                "TaskManagerAgent": "core_lib.local_agents.task_manager_agent.TaskManagerAgent",
                "WorkerAgent": "core_lib.local_agents.worker_agent.WorkerAgent",
            }

            if '.' in class_path:
                full_class_path = class_path
            elif class_path in CLASS_MAP:
                full_class_path = CLASS_MAP[class_path]
            else:
                raise ImportError(f"Class '{class_path}' not found in CLASS_MAP and is not a full import path.")
            module_name, class_name = full_class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logging.error(f"Could not find or import class '{class_path}': {e}")
            raise

    def _setup_infrastructure(self):
        """Initializes the message bus and simulation harness."""
        logging.info("Setting up simulation infrastructure...")
        self.message_bus = MessageBus()
        sim_config = self.config.get('simulation', {})
        self.harness = SimulationHarness(config=sim_config)

    def _load_components(self):
        """Loads and instantiates all physical components."""
        logging.info("Loading physical components...")
        for comp_conf in self.components_config.get('components', []):
            comp_id = comp_conf['id']
            comp_class_name = comp_conf['class']

            logging.info(f"  - Creating component '{comp_id}' of class '{comp_class_name}'")

            CompClass = self._get_class(comp_class_name)

            # Prepare constructor arguments
            args = {
                'name': comp_id,
                'initial_state': comp_conf.get('initial_state', {}),
                'parameters': comp_conf.get('parameters', {})
            }

            # Some components might need the message bus at init time
            # Make components message-aware if they have a topic defined
            if 'action_topic' in comp_conf:
                args['message_bus'] = self.message_bus
                args['action_topic'] = comp_conf['action_topic']
            elif 'Reservoir' in comp_class_name: # Legacy support for reservoir inflow
                args['message_bus'] = self.message_bus
                args['inflow_topic'] = f"inflow/{comp_id}"

            instance = CompClass(**args)

            self.harness.add_component(instance)
            self.component_instances[comp_id] = instance
        logging.info(f"Loaded {len(self.component_instances)} components.")

    def _load_topology(self):
        """Loads and defines the connections between components."""
        logging.info("Loading topology...")
        for conn_conf in self.topology_config.get('connections', []):
            upstream_id = conn_conf['upstream']
            downstream_id = conn_conf['downstream']

            logging.info(f"  - Connecting '{upstream_id}' -> '{downstream_id}'")
            self.harness.add_connection(upstream_id, downstream_id)
        logging.info("Topology loaded.")

    def _load_agents_and_controllers(self):
        """Loads and instantiates all agents and controllers."""
        logging.info("Loading agents and controllers...")

        # Load controllers
        for ctrl_conf in self.agents_config.get('controllers', []):
            ctrl_id = ctrl_conf['id']
            ctrl_class_name = ctrl_conf['class']
            logging.info(f"  - Creating controller '{ctrl_id}' of class '{ctrl_class_name}'")

            CtrlClass = self._get_class(ctrl_class_name)
            instance = CtrlClass(**ctrl_conf.get('config', {}))

            self.harness.add_controller(
                controller_id=ctrl_id,
                controller=instance,
                controlled_id=ctrl_conf['controlled_id'],
                observed_id=ctrl_conf['observed_id'],
                observation_key=ctrl_conf['observation_key']
            )

        # Load agents
        for agent_conf in self.agents_config.get('agents', []):
            agent_id = agent_conf['id']
            agent_class_path = agent_conf['class']
            short_class_name = agent_class_path.split('.')[-1]
            config = agent_conf.get('config', {})
            logging.info(f"  - Creating agent '{agent_id}' of class '{agent_class_path}'")

            AgentClass = self._get_class(agent_class_path)

            # Prepare constructor arguments dynamically based on agent type
            args = {'agent_id': agent_id, 'message_bus': self.message_bus}

            if short_class_name == 'DigitalTwinAgent':
                sim_obj_id = config['simulated_object_id']
                args['simulated_object'] = self.component_instances[sim_obj_id]
                args['state_topic'] = config['state_topic']

            elif short_class_name == 'EmergencyAgent':
                args['subscribed_topics'] = config['subscribed_topics']
                args['pressure_threshold'] = config['pressure_threshold']
                args['action_topic'] = config['action_topic']

            elif short_class_name == 'CentralDispatcherAgent':
                args['subscribed_topic'] = config['subscribed_topic']
                args['observation_key'] = config['observation_key']
                args['command_topic'] = config['command_topic']
                args['dispatcher_params'] = config['dispatcher_params']

            elif short_class_name == 'CsvInflowAgent':
                target_comp_id = config['target_component_id']
                args['target_component'] = self.component_instances[target_comp_id]
                # Resolve path relative to scenario directory
                csv_path = self.scenario_path / config['csv_file']
                args['csv_file_path'] = str(csv_path)
                args['time_column'] = config['time_column']
                args['data_column'] = config['data_column']

            elif short_class_name == 'CommunicationProxyAgent':
                # Pass all config parameters directly to the agent's constructor
                for key, value in config.items():
                    args[key] = value

            elif short_class_name == 'LocalControlAgent':
                # Handle the nested controller object
                controller_conf = config.pop('controller')
                CtrlClass = self._get_class(controller_conf['class'])
                controller_instance = CtrlClass(**controller_conf.get('config', {}))
                args['controller'] = controller_instance
                # Pass remaining config to the agent constructor
                args.update(config)
            else:
                # Default case for custom agents: pass the config dict as kwargs
                args.update(config)

            instance = AgentClass(**args)
            self.harness.add_agent(instance)

        logging.info("Agents and controllers loaded.")
