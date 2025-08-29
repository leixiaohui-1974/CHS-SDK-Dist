#!/usr/bin/env python3
"""
Example runner for Scenario 4: Distributed Decision Making.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List

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
    """A custom agent that controls a gate based on a reservoir's water level."""
    def __init__(self, agent_id: str, message_bus: MessageBus, subscribed_topic: str, action_topic: str, setpoint: float):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.action_topic = action_topic
        self.setpoint = setpoint
        self.gate_is_open = False # Assume gate is initially closed

        self.message_bus.subscribe(subscribed_topic, self.handle_state_message)

    def handle_state_message(self, message: Dict[str, Any]):
        """Handles incoming reservoir state messages."""
        water_level = message.get('water_level')
        if water_level is None:
            return

        # Simple bang-bang control logic
        if water_level > self.setpoint and not self.gate_is_open:
            logging.info(f"[{self.agent_id}] Water level {water_level:.2f}m is above setpoint {self.setpoint:.2f}m. Opening gate.")
            action_message = {'opening': 1.0}
            self.message_bus.publish(self.action_topic, action_message)
            self.gate_is_open = True
        elif water_level <= self.setpoint and self.gate_is_open:
            logging.info(f"[{self.agent_id}] Water level {water_level:.2f}m is at/below setpoint {self.setpoint:.2f}m. Closing gate.")
            action_message = {'opening': 0.0}
            self.message_bus.publish(self.action_topic, action_message)
            self.gate_is_open = False

    def run(self, current_time: float):
        pass # This agent is purely reactive


def run_distributed_control_simulation():
    """Sets up and runs the distributed decision-making simulation."""
    scenario_path = Path(__file__).parent
    logging.info("--- Setting up Example 4: Distributed Decision Making ---")

    # 1. Manually load the simulation to inject custom agents and configuration
    loader = SimulationLoader(scenario_path=str(scenario_path))
    harness = SimulationHarness(config=loader.config.get('simulation', {}))
    message_bus = harness.message_bus # Use the harness's message bus
    loader.harness = harness # Assign the harness to the loader instance

    # 2. Load components manually, injecting the message bus and topics
    logging.info("Loading physical components manually...")
    for comp_conf in loader.components_config.get('components', []):
        comp_id = comp_conf['id']
        CompClass = loader._get_class(comp_conf['class'])

        # Pass constructor arguments based on component type
        if comp_conf['class'] == 'Reservoir':
            instance = CompClass(
                name=comp_id, initial_state=comp_conf.get('initial_state', {}),
                parameters=comp_conf.get('parameters', {}), message_bus=message_bus,
                inflow_topic=f"inflow/{comp_id}")
        elif comp_conf['class'] == 'Gate':
            instance = CompClass(
                name=comp_id, initial_state=comp_conf.get('initial_state', {}),
                parameters=comp_conf.get('parameters', {}), message_bus=message_bus,
                action_topic=f"action/gate/{comp_id}")
        else:
            instance = CompClass(name=comp_id, initial_state=comp_conf.get('initial_state', {}),
                                 parameters=comp_conf.get('parameters', {}))

        harness.add_component(instance)
        loader.component_instances[comp_id] = instance

    # 3. Load topology
    loader._load_topology()

    # 4. Manually load agents
    logging.info("Loading agents manually...")
    for agent_conf in loader.agents_config.get('agents', []):
        agent_id, agent_class, config = agent_conf['id'], agent_conf['class'], agent_conf.get('config', {})

        if agent_class == "DigitalTwinAgent":
            sim_obj = loader.component_instances[config['simulated_object_id']]
            instance = loader._get_class(agent_class)(agent_id=agent_id, message_bus=message_bus, simulated_object=sim_obj, state_topic=config['state_topic'])
        elif agent_class == "ConstantInflowAgent":
            instance = ConstantInflowAgent(agent_id=agent_id, message_bus=message_bus,
                                           inflow_topic=f"inflow/{config['target_component_id']}",
                                           inflow_rate=config['inflow_rate'])
        elif agent_class == "LocalGateControlAgent":
            instance = LocalGateControlAgent(agent_id=agent_id, message_bus=message_bus,
                                             subscribed_topic=config['subscribed_topic'],
                                             action_topic=config['action_topic'],
                                             setpoint=config['setpoint'])
        else:
            logging.warning(f"Unknown agent class in YAML: {agent_class}")
            continue

        harness.add_agent(instance)

    # 5. Build and run
    logging.info("Building harness...")
    harness.build()
    logging.info("\n--- Running Simulation ---")
    harness.run_mas_simulation()
    logging.info("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_distributed_control_simulation()
