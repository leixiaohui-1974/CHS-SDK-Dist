#!/usr/bin/env python3
"""
Example runner for Scenario 5: Hierarchical Control.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationLoader
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ConstantInflowAgent(Agent):
    """A simple agent that provides a constant inflow to a target component."""
    def __init__(self, agent_id: str, message_bus: MessageBus, inflow_topic: str, inflow_rate: float):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.inflow_topic = inflow_topic
        self.inflow_rate = inflow_rate

    def run(self, current_time: float):
        message = {'inflow_rate': self.inflow_rate}
        self.message_bus.publish(self.inflow_topic, message)


class LocalGateControlAgent(Agent):
    """A local agent that controls a gate based on a dynamic setpoint."""
    def __init__(self, agent_id: str, message_bus: MessageBus, state_subscription_topic: str,
                 command_subscription_topic: str, initial_setpoint: float, action_topic: str):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.action_topic = action_topic
        self.setpoint = initial_setpoint
        self.gate_is_open = False

        logging.info(f"[{self.agent_id}] Initialized with setpoint {self.setpoint:.2f}m")

        self.message_bus.subscribe(state_subscription_topic, self.handle_state_message)
        self.message_bus.subscribe(command_subscription_topic, self.handle_command_message)

    def handle_state_message(self, message: Dict[str, Any]):
        """Handles incoming reservoir state messages."""
        water_level = message.get('water_level')
        if water_level is None: return

        if water_level > self.setpoint and not self.gate_is_open:
            logging.info(f"[{self.agent_id}] Level {water_level:.2f}m > setpoint {self.setpoint:.2f}m. Opening gate.")
            self.message_bus.publish(self.action_topic, {'opening': 1.0})
            self.gate_is_open = True
        elif water_level <= self.setpoint and self.gate_is_open:
            logging.info(f"[{self.agent_id}] Level {water_level:.2f}m <= setpoint {self.setpoint:.2f}m. Closing gate.")
            self.message_bus.publish(self.action_topic, {'opening': 0.0})
            self.gate_is_open = False

    def handle_command_message(self, message: Dict[str, Any]):
        """Handles incoming setpoint command messages."""
        new_setpoint = message.get('setpoint')
        if new_setpoint is not None:
            logging.info(f"[{self.agent_id}] Received new setpoint command: {new_setpoint:.2f}m. Previous was {self.setpoint:.2f}m.")
            self.setpoint = new_setpoint

    def run(self, current_time: float):
        pass # Reactive agent


class CentralCommandAgent(Agent):
    """A supervisory agent that issues a command at a specific time."""
    def __init__(self, agent_id: str, message_bus: MessageBus, command_topic: str, new_setpoint: float, command_time: float):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.command_topic = command_topic
        self.new_setpoint = new_setpoint
        self.command_time = command_time
        self.command_sent = False

    def run(self, current_time: float):
        if not self.command_sent and current_time >= self.command_time:
            logging.info(f"[{self.agent_id}] Time {current_time:.2f}s >= command time {self.command_time:.2f}s. Issuing new setpoint.")
            command_message = {'setpoint': self.new_setpoint}
            self.message_bus.publish(self.command_topic, command_message)
            self.command_sent = True


def run_hierarchical_control_simulation():
    """Sets up and runs the hierarchical control simulation."""
    scenario_path = Path(__file__).parent
    logging.info("--- Setting up Example 5: Hierarchical Control ---")

    loader = SimulationLoader(scenario_path=str(scenario_path))
    harness = SimulationHarness(config=loader.config.get('simulation', {}))
    message_bus = harness.message_bus
    loader.harness = harness

    # Load components
    for comp_conf in loader.components_config.get('components', []):
        comp_id, CompClass = comp_conf['id'], loader._get_class(comp_conf['class'])
        params = {'name': comp_id, 'initial_state': comp_conf.get('initial_state', {}),
                  'parameters': comp_conf.get('parameters', {}), 'message_bus': message_bus}
        if comp_conf['class'] == 'Reservoir':
            params['inflow_topic'] = f"inflow/{comp_id}"
        elif comp_conf['class'] == 'Gate':
            params['action_topic'] = f"action/gate/{comp_id}"
        instance = CompClass(**params)
        harness.add_component(instance)
        loader.component_instances[comp_id] = instance

    loader._load_topology()

    # Load agents
    for agent_conf in loader.agents_config.get('agents', []):
        agent_id, agent_class, config = agent_conf['id'], agent_conf['class'], agent_conf.get('config', {})
        instance = None
        if agent_class == "DigitalTwinAgent":
            sim_obj = loader.component_instances[config['simulated_object_id']]
            instance = loader._get_class(agent_class)(agent_id=agent_id, message_bus=message_bus, simulated_object=sim_obj, state_topic=config['state_topic'])
        elif agent_class == "ConstantInflowAgent":
            instance = ConstantInflowAgent(agent_id=agent_id, message_bus=message_bus,
                                           inflow_topic=f"inflow/{config['target_component_id']}",
                                           inflow_rate=config['inflow_rate'])
        elif agent_class == "LocalGateControlAgent":
            instance = LocalGateControlAgent(agent_id=agent_id, message_bus=message_bus,
                                             state_subscription_topic=config['state_subscription_topic'],
                                             command_subscription_topic=config['command_subscription_topic'],
                                             initial_setpoint=config['initial_setpoint'],
                                             action_topic=config['action_topic'])
        elif agent_class == "CentralCommandAgent":
            instance = CentralCommandAgent(agent_id=agent_id, message_bus=message_bus,
                                           command_topic=config['command_topic'],
                                           new_setpoint=config['new_setpoint'],
                                           command_time=config['command_time'])
        if instance:
            harness.add_agent(instance)

    harness.build()
    logging.info("\n--- Running Simulation ---")
    harness.run_mas_simulation()
    logging.info("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_hierarchical_control_simulation()
