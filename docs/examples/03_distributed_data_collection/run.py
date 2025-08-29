#!/usr/bin/env python3
"""
Example runner for Scenario 3: Distributed Data Collection.
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


class DataAggregator(Agent):
    """
    A custom agent that subscribes to topics and aggregates the data it receives.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, topics_to_subscribe: List[str]):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.aggregated_data: Dict[str, List[Any]] = {topic: [] for topic in topics_to_subscribe}
        self.log = []

        for topic in topics_to_subscribe:
            # Use a factory function (or lambda) to create a listener that captures the topic
            listener = self._create_listener(topic)
            self.message_bus.subscribe(topic, listener)

    def _create_listener(self, topic: str):
        """Creates a callback function that knows which topic it's for."""
        def listener(message: Dict[str, Any]):
            log_entry = f"[{self.agent_id}] Received on '{topic}': {message}"
            logging.info(log_entry)
            self.log.append(log_entry)
            self.aggregated_data[topic].append(message)
        return listener

    def run(self, current_time: float):
        """
        The agent's main loop. For this reactive agent, it does nothing.
        """
        pass


class ConstantInflowAgent(Agent):
    """
    A simple agent that provides a constant inflow to a target component.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, inflow_topic: str, inflow_rate: float):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.inflow_topic = inflow_topic
        self.inflow_rate = inflow_rate

    def run(self, current_time: float):
        message = {'inflow_rate': self.inflow_rate}
        self.message_bus.publish(self.inflow_topic, message)


def run_data_collection_simulation():
    """
    Sets up and runs the distributed data collection simulation.
    """
    scenario_path = Path(__file__).parent
    logging.info("--- Setting up Example 3: Distributed Data Collection ---")

    # 1. We will manually load the simulation to inject our custom agents and configuration
    loader = SimulationLoader(scenario_path=str(scenario_path))
    message_bus = MessageBus()
    # Manually create the harness, as we are overriding the loading process
    harness = SimulationHarness(config=loader.config.get('simulation', {}))
    harness.message_bus = message_bus

    # 2. Load components manually, injecting the message bus
    logging.info("Loading physical components manually...")
    for comp_conf in loader.components_config.get('components', []):
        comp_id = comp_conf['id']
        CompClass = loader._get_class(comp_conf['class'])

        # Define the inflow topic for this component
        inflow_topic = f"inflow/{comp_id}"

        instance = CompClass(
            name=comp_id,
            initial_state=comp_conf.get('initial_state', {}),
            parameters=comp_conf.get('parameters', {}),
            message_bus=message_bus,
            inflow_topic=inflow_topic
        )
        harness.add_component(instance)
        loader.component_instances[comp_id] = instance

    # 3. Load topology
    loader._load_topology()

    # 4. Manually load agents from agents.yml
    logging.info("Loading agents manually...")
    for agent_conf in loader.agents_config.get('agents', []):
        agent_id = agent_conf['id']
        agent_class_name = agent_conf['class']
        config = agent_conf.get('config', {})

        if agent_class_name == "DigitalTwinAgent":
            AgentClass = loader._get_class(agent_class_name)
            sim_obj = loader.component_instances[config['simulated_object_id']]
            instance = AgentClass(agent_id=agent_id, message_bus=message_bus, simulated_object=sim_obj, state_topic=config['state_topic'])
            harness.add_agent(instance)

        elif agent_class_name == "DataAggregator":
            instance = DataAggregator(agent_id=agent_id, message_bus=message_bus, topics_to_subscribe=config['subscribed_topics'])
            harness.add_agent(instance)

        elif agent_class_name == "ConstantInflowAgent":
            target_comp_id = config['target_component_id']
            inflow_topic = f"inflow/{target_comp_id}" # Must match the topic the reservoir subscribed to
            instance = ConstantInflowAgent(
                agent_id=agent_id,
                message_bus=message_bus,
                inflow_topic=inflow_topic,
                inflow_rate=config['inflow_rate']
            )
            harness.add_agent(instance)

    # 5. Build and run
    logging.info("Building harness...")
    harness.build()
    logging.info("\n--- Running Simulation ---")
    harness.run_mas_simulation()
    logging.info("\n--- Simulation Complete ---")


if __name__ == "__main__":
    run_data_collection_simulation()
